"""
Invoice Routes
API endpoints for invoices and payments
"""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, get_customer_id
from app.sales.invoices import (
    InvoiceService,
    PaymentService,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceFilter,
    InvoiceSummary,
    InvoiceLineCreate,
    InvoiceLineUpdate,
    InvoiceLineResponse,
    SendInvoiceRequest,
    VoidInvoiceRequest,
    CreateFromOrderRequest,
    InvoicePaymentCreate,
    InvoicePaymentResponse,
    CustomerPaymentCreate,
    CustomerPaymentUpdate,
    CustomerPaymentResponse,
    CustomerPaymentFilter,
    ApplyPaymentRequest,
    VoidPaymentRequest,
    CustomerAgingReport,
    AgingReportFilter,
    InvoiceStatusEnum,
    PaymentMethodEnum,
)

router = APIRouter(tags=["Invoices & Payments"])


def get_invoice_service(
    db: Session = Depends(get_db),
    customer_id: UUID = Depends(get_customer_id)
) -> InvoiceService:
    return InvoiceService(db, customer_id)


def get_payment_service(
    db: Session = Depends(get_db),
    customer_id: UUID = Depends(get_customer_id)
) -> PaymentService:
    return PaymentService(db, customer_id)


# Invoice Routes

@router.post("/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    service: InvoiceService = Depends(get_invoice_service),
    current_user: dict = Depends(get_current_user)
):
    """Create a new invoice."""
    invoice = service.create_invoice(data, created_by=current_user.get("id"))
    return invoice.to_dict(include_lines=True)


@router.post("/invoices/from-order", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_from_order(
    data: CreateFromOrderRequest,
    service: InvoiceService = Depends(get_invoice_service),
    current_user: dict = Depends(get_current_user)
):
    """Create invoice from sales order."""
    invoice = service.create_from_order(data, created_by=current_user.get("id"))
    return invoice.to_dict(include_lines=True)


@router.get("/invoices", response_model=dict)
async def list_invoices(
    search: Optional[str] = None,
    customer_master_id: Optional[UUID] = None,
    status: Optional[InvoiceStatusEnum] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    due_date_from: Optional[date] = None,
    due_date_to: Optional[date] = None,
    is_overdue: Optional[bool] = None,
    order_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: InvoiceService = Depends(get_invoice_service)
):
    """List invoices with filters."""
    filters = InvoiceFilter(
        search=search,
        customer_master_id=customer_master_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        is_overdue=is_overdue,
        order_id=order_id
    )
    invoices, total = service.get_invoices(filters, skip, limit)
    return {
        "items": [i.to_dict() for i in invoices],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/invoices/overdue", response_model=dict)
async def list_overdue_invoices(
    customer_master_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: InvoiceService = Depends(get_invoice_service)
):
    """List overdue invoices."""
    filters = InvoiceFilter(
        customer_master_id=customer_master_id,
        is_overdue=True
    )
    invoices, total = service.get_invoices(filters, skip, limit)
    return {
        "items": [i.to_dict() for i in invoices],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/invoices/unpaid", response_model=List[InvoiceSummary])
async def list_unpaid_invoices(
    customer_master_id: Optional[UUID] = None,
    service: InvoiceService = Depends(get_invoice_service)
):
    """List unpaid invoices for payment application."""
    filters = InvoiceFilter(
        customer_master_id=customer_master_id,
        statuses=[
            InvoiceStatusEnum.PENDING,
            InvoiceStatusEnum.SENT,
            InvoiceStatusEnum.PARTIAL_PAID,
            InvoiceStatusEnum.OVERDUE
        ]
    )
    invoices, _ = service.get_invoices(filters, 0, 1000)
    return [
        InvoiceSummary(
            id=i.id,
            invoice_number=i.invoice_number,
            customer_name=i.customer_master.name if i.customer_master else "",
            invoice_date=i.invoice_date,
            total_amount=float(i.total_amount),
            balance_due=float(i.balance_due),
            status=i.status
        )
        for i in invoices if i.balance_due > 0
    ]


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    service: InvoiceService = Depends(get_invoice_service)
):
    """Get invoice by ID."""
    invoice = service.get_invoice(invoice_id, include_payments=True)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return invoice.to_dict(include_lines=True, include_payments=True)


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    data: InvoiceUpdate,
    service: InvoiceService = Depends(get_invoice_service)
):
    """Update invoice."""
    invoice = service.update_invoice(invoice_id, data)
    return invoice.to_dict(include_lines=True)


@router.post("/invoices/{invoice_id}/finalize", response_model=InvoiceResponse)
async def finalize_invoice(
    invoice_id: UUID,
    service: InvoiceService = Depends(get_invoice_service)
):
    """Finalize invoice for sending."""
    invoice = service.finalize_invoice(invoice_id)
    return invoice.to_dict(include_lines=True)


@router.post("/invoices/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: UUID,
    data: SendInvoiceRequest,
    service: InvoiceService = Depends(get_invoice_service)
):
    """Send invoice to customer."""
    invoice = service.send_invoice(invoice_id, data)
    return invoice.to_dict(include_lines=True)


@router.post("/invoices/{invoice_id}/void", response_model=InvoiceResponse)
async def void_invoice(
    invoice_id: UUID,
    data: VoidInvoiceRequest,
    service: InvoiceService = Depends(get_invoice_service)
):
    """Void invoice."""
    invoice = service.void_invoice(invoice_id, data)
    return invoice.to_dict(include_lines=True)


@router.post("/invoices/{invoice_id}/lines", response_model=InvoiceLineResponse, status_code=status.HTTP_201_CREATED)
async def add_invoice_line(
    invoice_id: UUID,
    data: InvoiceLineCreate,
    service: InvoiceService = Depends(get_invoice_service)
):
    """Add line to invoice."""
    line = service.add_line(invoice_id, data)
    return line.to_dict()


@router.put("/invoices/{invoice_id}/lines/{line_id}", response_model=InvoiceLineResponse)
async def update_invoice_line(
    invoice_id: UUID,
    line_id: UUID,
    data: InvoiceLineUpdate,
    service: InvoiceService = Depends(get_invoice_service)
):
    """Update invoice line."""
    line = service.update_line(invoice_id, line_id, data)
    return line.to_dict()


@router.delete("/invoices/{invoice_id}/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice_line(
    invoice_id: UUID,
    line_id: UUID,
    service: InvoiceService = Depends(get_invoice_service)
):
    """Delete invoice line."""
    service.delete_line(invoice_id, line_id)
    return None


@router.post("/invoices/{invoice_id}/payments", response_model=InvoicePaymentResponse, status_code=status.HTTP_201_CREATED)
async def apply_payment_to_invoice(
    invoice_id: UUID,
    data: InvoicePaymentCreate,
    service: InvoiceService = Depends(get_invoice_service),
    current_user: dict = Depends(get_current_user)
):
    """Apply payment to invoice."""
    data.invoice_id = invoice_id
    payment = service.apply_payment(invoice_id, data, created_by=current_user.get("id"))
    return payment.to_dict()


# Customer Payment Routes

@router.post("/payments", response_model=CustomerPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: CustomerPaymentCreate,
    service: PaymentService = Depends(get_payment_service),
    current_user: dict = Depends(get_current_user)
):
    """Create a customer payment."""
    payment = service.create_payment(data, created_by=current_user.get("id"))
    return payment.to_dict(include_applications=True)


@router.get("/payments", response_model=dict)
async def list_payments(
    search: Optional[str] = None,
    customer_master_id: Optional[UUID] = None,
    payment_method: Optional[PaymentMethodEnum] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    has_unapplied: Optional[bool] = None,
    is_void: Optional[bool] = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: PaymentService = Depends(get_payment_service)
):
    """List customer payments with filters."""
    filters = CustomerPaymentFilter(
        search=search,
        customer_master_id=customer_master_id,
        payment_method=payment_method,
        date_from=date_from,
        date_to=date_to,
        has_unapplied=has_unapplied,
        is_void=is_void
    )
    payments, total = service.get_payments(filters, skip, limit)
    return {
        "items": [p.to_dict() for p in payments],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/payments/unapplied", response_model=dict)
async def list_unapplied_payments(
    customer_master_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: PaymentService = Depends(get_payment_service)
):
    """List payments with unapplied balance."""
    filters = CustomerPaymentFilter(
        customer_master_id=customer_master_id,
        has_unapplied=True,
        is_void=False
    )
    payments, total = service.get_payments(filters, skip, limit)
    return {
        "items": [p.to_dict(include_applications=True) for p in payments],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/payments/{payment_id}", response_model=CustomerPaymentResponse)
async def get_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service)
):
    """Get payment by ID."""
    payment = service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment.to_dict(include_applications=True)


@router.post("/payments/{payment_id}/apply", response_model=CustomerPaymentResponse)
async def apply_payment(
    payment_id: UUID,
    data: ApplyPaymentRequest,
    service: PaymentService = Depends(get_payment_service),
    current_user: dict = Depends(get_current_user)
):
    """Apply payment to invoices."""
    payment = service.apply_payment(payment_id, data, created_by=current_user.get("id"))
    return payment.to_dict(include_applications=True)


@router.post("/payments/{payment_id}/void", response_model=CustomerPaymentResponse)
async def void_payment(
    payment_id: UUID,
    data: VoidPaymentRequest,
    service: PaymentService = Depends(get_payment_service),
    current_user: dict = Depends(get_current_user)
):
    """Void payment."""
    payment = service.void_payment(payment_id, data, void_by=current_user.get("id"))
    return payment.to_dict(include_applications=True)


# Aging Report

@router.get("/reports/aging", response_model=List[CustomerAgingReport])
async def get_aging_report(
    as_of_date: Optional[date] = None,
    customer_master_id: Optional[UUID] = None,
    min_balance: Optional[float] = None,
    service: PaymentService = Depends(get_payment_service)
):
    """Get customer aging report."""
    filters = AgingReportFilter(
        as_of_date=as_of_date,
        customer_master_id=customer_master_id,
        min_balance=min_balance
    )
    return service.get_aging_report(filters)
