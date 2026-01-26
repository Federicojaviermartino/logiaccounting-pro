"""Supplier Invoice API Routes"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.purchasing.invoices.service import (
    SupplierInvoiceService, get_supplier_invoice_service
)

router = APIRouter(prefix="/supplier-invoices", tags=["Purchasing - Invoices"])


class InvoiceLineInput(BaseModel):
    product_id: Optional[UUID] = None
    description: str
    account_id: Optional[UUID] = None
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)
    order_line_id: Optional[UUID] = None
    receipt_line_id: Optional[UUID] = None


class CreateInvoice(BaseModel):
    supplier_id: UUID
    invoice_date: date
    due_date: date
    supplier_invoice_number: Optional[str] = None
    currency: str = "USD"
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    lines: List[InvoiceLineInput]
    notes: Optional[str] = None


class CreateFromReceipt(BaseModel):
    receipt_id: UUID
    supplier_invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None


class RecordPayment(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_date: Optional[date] = None
    payment_reference: Optional[str] = None


@router.get("")
def list_invoices(
    supplier_id: Optional[UUID] = None,
    status: Optional[str] = None,
    overdue_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_invoice_service(db)
    invoices, total = service.get_invoices(
        user.customer_id, supplier_id, status, overdue_only, page, page_size
    )
    return {
        "invoices": [i.to_dict() for i in invoices],
        "total": total,
    }


@router.get("/aging")
def get_aging_report(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_invoice_service(db)
    return service.get_ap_aging(user.customer_id)


@router.post("")
def create_invoice(
    data: CreateInvoice,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_invoice_service(db)
    try:
        lines = [l.dict() for l in data.lines]
        invoice = service.create_invoice(
            user.customer_id,
            data.supplier_id,
            data.invoice_date,
            data.due_date,
            lines,
            data.supplier_invoice_number,
            data.currency,
            data.discount_amount,
            data.notes,
            user.id,
        )
        return invoice.to_dict(include_lines=True)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/from-receipt")
def create_from_receipt(
    data: CreateFromReceipt,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_invoice_service(db)
    try:
        invoice = service.create_invoice_from_receipt(
            user.customer_id,
            data.receipt_id,
            data.supplier_invoice_number,
            data.invoice_date,
            data.due_date,
            user.id,
        )
        return invoice.to_dict(include_lines=True)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_invoice_service(db)
    invoice = service.get_invoice_by_id(invoice_id)
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    return invoice.to_dict(include_lines=True)


@router.post("/{invoice_id}/match")
def perform_matching(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_invoice_service(db)
    try:
        result = service.perform_3way_match(invoice_id)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{invoice_id}/approve")
def approve_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_invoice_service(db)
    try:
        invoice = service.approve_invoice(invoice_id, user.id)
        return invoice.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{invoice_id}/post")
def post_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_invoice_service(db)
    try:
        invoice = service.post_invoice(invoice_id, user.id)
        return invoice.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{invoice_id}/payment")
def record_payment(
    invoice_id: UUID,
    data: RecordPayment,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_invoice_service(db)
    try:
        invoice = service.record_payment(
            invoice_id, data.amount, data.payment_date, data.payment_reference
        )
        return invoice.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))
