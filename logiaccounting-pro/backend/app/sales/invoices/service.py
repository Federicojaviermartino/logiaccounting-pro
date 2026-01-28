"""
Invoice Service
Business logic for invoices and payments
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID
import uuid

from sqlalchemy import select, func, and_, or_

from app.utils.datetime_utils import utc_now
from sqlalchemy.orm import Session, selectinload
from fastapi import Depends, HTTPException, status

from app.database import get_db
from app.sales.invoices.models import (
    CustomerInvoice, CustomerInvoiceLine, InvoicePayment,
    CustomerPayment, InvoiceStatusEnum, PaymentMethodEnum
)
from app.sales.invoices.schemas import (
    InvoiceCreate, InvoiceUpdate, InvoiceFilter,
    InvoiceLineCreate, InvoiceLineUpdate,
    SendInvoiceRequest, VoidInvoiceRequest,
    CreateFromOrderRequest, CreateFromShipmentRequest,
    InvoicePaymentCreate,
    CustomerPaymentCreate, CustomerPaymentUpdate, CustomerPaymentFilter,
    ApplyPaymentRequest, VoidPaymentRequest,
    AgingBucket, CustomerAgingReport, AgingReportFilter
)
from app.sales.orders.models import SalesOrder, SalesOrderLine, SOStatusEnum, SOLineStatusEnum
from app.sales.fulfillment.models import Shipment, ShipmentLine


class InvoiceService:
    """Service for invoice operations."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number."""
        today = date.today()
        prefix = f"INV-{today.strftime('%Y%m')}"

        result = self.db.execute(
            select(func.count(CustomerInvoice.id)).where(
                and_(
                    CustomerInvoice.customer_id == self.customer_id,
                    CustomerInvoice.invoice_number.like(f"{prefix}%")
                )
            )
        )
        count = result.scalar() or 0

        return f"{prefix}-{count + 1:04d}"

    def create_invoice(
        self,
        data: InvoiceCreate,
        created_by: Optional[UUID] = None
    ) -> CustomerInvoice:
        """Create new invoice."""
        invoice = CustomerInvoice(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            invoice_number=self._generate_invoice_number(),
            customer_master_id=data.customer_master_id,
            invoice_date=data.invoice_date or date.today(),
            due_date=data.due_date or date.today(),
            payment_term_id=data.payment_term_id,
            billing_address=data.billing_address,
            shipping_address=data.shipping_address,
            currency=data.currency,
            exchange_rate=data.exchange_rate,
            discount_percent=data.discount_percent,
            shipping_amount=data.shipping_amount,
            po_number=data.po_number,
            reference=data.reference,
            notes=data.notes,
            terms_and_conditions=data.terms_and_conditions,
            footer_text=data.footer_text,
            receivable_account_id=data.receivable_account_id,
            revenue_account_id=data.revenue_account_id,
            status=InvoiceStatusEnum.DRAFT.value,
            created_by=created_by,
        )

        self.db.add(invoice)
        self.db.flush()

        if data.lines:
            for idx, line_data in enumerate(data.lines, start=1):
                line = self._create_line(invoice.id, idx, line_data)
                self.db.add(line)

            self.db.flush()
            self._refresh_with_lines(invoice)
            invoice.recalculate_totals()

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def _create_line(
        self,
        invoice_id: UUID,
        line_number: int,
        data: InvoiceLineCreate
    ) -> CustomerInvoiceLine:
        """Create invoice line."""
        line = CustomerInvoiceLine(
            id=uuid.uuid4(),
            invoice_id=invoice_id,
            line_number=line_number,
            order_id=data.order_id,
            order_line_id=data.order_line_id,
            shipment_id=data.shipment_id,
            product_id=data.product_id,
            description=data.description,
            quantity=data.quantity,
            uom_id=data.uom_id,
            unit_price=data.unit_price,
            discount_percent=data.discount_percent,
            tax_rate=data.tax_rate,
            revenue_account_id=data.revenue_account_id,
        )
        line.calculate_amounts()
        return line

    def update_invoice(
        self,
        invoice_id: UUID,
        data: InvoiceUpdate
    ) -> CustomerInvoice:
        """Update invoice."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if not invoice.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit invoice in current status"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invoice, field, value)

        invoice.updated_at = utc_now()
        invoice.recalculate_totals()

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_invoice(
        self,
        invoice_id: UUID,
        include_lines: bool = True,
        include_payments: bool = False
    ) -> Optional[CustomerInvoice]:
        """Get invoice by ID."""
        query = select(CustomerInvoice).where(
            and_(
                CustomerInvoice.id == invoice_id,
                CustomerInvoice.customer_id == self.customer_id
            )
        )

        if include_lines:
            query = query.options(
                selectinload(CustomerInvoice.lines),
                selectinload(CustomerInvoice.customer_master)
            )

        if include_payments:
            query = query.options(selectinload(CustomerInvoice.payments))

        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_invoices(
        self,
        filters: InvoiceFilter,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[CustomerInvoice], int]:
        """Get invoices with filters."""
        query = select(CustomerInvoice).where(
            CustomerInvoice.customer_id == self.customer_id
        )

        if filters.search:
            search = f"%{filters.search}%"
            query = query.join(CustomerInvoice.customer_master).where(
                or_(
                    CustomerInvoice.invoice_number.ilike(search),
                    CustomerInvoice.po_number.ilike(search),
                )
            )

        if filters.customer_master_id:
            query = query.where(
                CustomerInvoice.customer_master_id == filters.customer_master_id
            )

        if filters.status:
            query = query.where(CustomerInvoice.status == filters.status.value)

        if filters.statuses:
            query = query.where(
                CustomerInvoice.status.in_([s.value for s in filters.statuses])
            )

        if filters.date_from:
            query = query.where(CustomerInvoice.invoice_date >= filters.date_from)

        if filters.date_to:
            query = query.where(CustomerInvoice.invoice_date <= filters.date_to)

        if filters.due_date_from:
            query = query.where(CustomerInvoice.due_date >= filters.due_date_from)

        if filters.due_date_to:
            query = query.where(CustomerInvoice.due_date <= filters.due_date_to)

        if filters.is_overdue:
            query = query.where(
                and_(
                    CustomerInvoice.due_date < date.today(),
                    CustomerInvoice.balance_due > 0,
                    CustomerInvoice.status.notin_([
                        InvoiceStatusEnum.PAID.value,
                        InvoiceStatusEnum.CANCELLED.value,
                        InvoiceStatusEnum.VOID.value
                    ])
                )
            )

        if filters.order_id:
            query = query.join(CustomerInvoice.lines).where(
                CustomerInvoiceLine.order_id == filters.order_id
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar() or 0

        query = query.options(
            selectinload(CustomerInvoice.customer_master),
            selectinload(CustomerInvoice.lines),
            selectinload(CustomerInvoice.payments)
        )
        query = query.order_by(CustomerInvoice.invoice_date.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        invoices = result.scalars().all()

        return list(invoices), total

    def add_line(
        self,
        invoice_id: UUID,
        data: InvoiceLineCreate
    ) -> CustomerInvoiceLine:
        """Add line to invoice."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if not invoice.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add lines to this invoice"
            )

        max_line = max([l.line_number for l in invoice.lines], default=0)

        line = self._create_line(invoice_id, max_line + 1, data)
        self.db.add(line)
        self.db.flush()

        self._refresh_with_lines(invoice)
        invoice.recalculate_totals()

        self.db.commit()
        self.db.refresh(line)
        return line

    def update_line(
        self,
        invoice_id: UUID,
        line_id: UUID,
        data: InvoiceLineUpdate
    ) -> CustomerInvoiceLine:
        """Update invoice line."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if not invoice.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit lines on this invoice"
            )

        line = next((l for l in invoice.lines if l.id == line_id), None)
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Line not found"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(line, field, value)

        line.calculate_amounts()
        invoice.recalculate_totals()

        self.db.commit()
        self.db.refresh(line)
        return line

    def delete_line(self, invoice_id: UUID, line_id: UUID) -> bool:
        """Delete invoice line."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if not invoice.is_editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete lines from this invoice"
            )

        line = next((l for l in invoice.lines if l.id == line_id), None)
        if not line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Line not found"
            )

        self.db.delete(line)
        self.db.flush()

        self._refresh_with_lines(invoice)
        invoice.recalculate_totals()

        self.db.commit()
        return True

    def finalize_invoice(
        self,
        invoice_id: UUID
    ) -> CustomerInvoice:
        """Finalize invoice for sending."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if invoice.status != InvoiceStatusEnum.DRAFT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft invoices can be finalized"
            )

        if not invoice.lines:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice has no lines"
            )

        invoice.status = InvoiceStatusEnum.PENDING.value
        invoice.updated_at = utc_now()

        self._update_order_invoiced(invoice)

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def _update_order_invoiced(self, invoice: CustomerInvoice):
        """Update order lines as invoiced."""
        for line in invoice.lines:
            if line.order_line_id:
                order_line = self.db.get(SalesOrderLine, line.order_line_id)
                if order_line:
                    order_line.qty_invoiced = (
                        (order_line.qty_invoiced or Decimal("0")) + line.quantity
                    )
                    if order_line.qty_invoiced >= order_line.quantity:
                        order_line.status = SOLineStatusEnum.INVOICED.value

            if line.order_id:
                order = self.db.get(SalesOrder, line.order_id)
                if order:
                    order.invoiced_amount = (
                        (order.invoiced_amount or Decimal("0")) + line.line_total
                    )
                    order.qty_invoiced = sum(
                        l.qty_invoiced or Decimal("0") for l in order.lines
                    )
                    if order.fully_invoiced:
                        order.status = SOStatusEnum.INVOICED.value

    def send_invoice(
        self,
        invoice_id: UUID,
        request: SendInvoiceRequest
    ) -> CustomerInvoice:
        """Mark invoice as sent."""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if not invoice.can_send:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice cannot be sent"
            )

        invoice.status = InvoiceStatusEnum.SENT.value
        invoice.sent_at = utc_now()
        invoice.sent_to = request.email_to

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def void_invoice(
        self,
        invoice_id: UUID,
        request: VoidInvoiceRequest
    ) -> CustomerInvoice:
        """Void invoice."""
        invoice = self.get_invoice(invoice_id, include_payments=True)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if not invoice.can_void:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invoice cannot be voided"
            )

        invoice.status = InvoiceStatusEnum.VOID.value
        invoice.notes = f"{invoice.notes or ''}\nVoided: {request.reason}".strip()

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def create_from_order(
        self,
        request: CreateFromOrderRequest,
        created_by: Optional[UUID] = None
    ) -> CustomerInvoice:
        """Create invoice from sales order."""
        order = self.db.execute(
            select(SalesOrder).where(
                and_(
                    SalesOrder.id == request.order_id,
                    SalesOrder.customer_id == self.customer_id
                )
            ).options(selectinload(SalesOrder.lines))
        ).scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        invoice = CustomerInvoice(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            invoice_number=self._generate_invoice_number(),
            customer_master_id=order.customer_master_id,
            invoice_date=date.today(),
            due_date=date.today(),
            payment_term_id=order.payment_term_id,
            shipping_address=order.shipping_address,
            currency=order.currency,
            exchange_rate=order.exchange_rate,
            discount_percent=order.discount_percent,
            shipping_amount=order.shipping_amount,
            po_number=order.customer_po_number,
            status=InvoiceStatusEnum.DRAFT.value,
            created_by=created_by,
        )

        self.db.add(invoice)
        self.db.flush()

        line_number = 0
        for order_line in order.lines:
            if order_line.status == SOLineStatusEnum.CANCELLED.value:
                continue

            qty_to_invoice = order_line.quantity
            if request.invoice_shipped_only:
                qty_to_invoice = order_line.qty_shipped - (order_line.qty_invoiced or Decimal("0"))

            if qty_to_invoice <= 0:
                continue

            line_number += 1
            inv_line = CustomerInvoiceLine(
                id=uuid.uuid4(),
                invoice_id=invoice.id,
                line_number=line_number,
                order_id=order.id,
                order_line_id=order_line.id,
                product_id=order_line.product_id,
                description=order_line.description or "",
                quantity=qty_to_invoice,
                uom_id=order_line.uom_id,
                unit_price=order_line.unit_price,
                discount_percent=order_line.discount_percent,
                tax_rate=order_line.tax_rate,
            )
            inv_line.calculate_amounts()
            self.db.add(inv_line)

        self.db.flush()
        self._refresh_with_lines(invoice)
        invoice.recalculate_totals()

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def apply_payment(
        self,
        invoice_id: UUID,
        data: InvoicePaymentCreate,
        created_by: Optional[UUID] = None
    ) -> InvoicePayment:
        """Apply payment to invoice."""
        invoice = self.get_invoice(invoice_id, include_payments=True)
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )

        if invoice.status in [
            InvoiceStatusEnum.VOID.value,
            InvoiceStatusEnum.CANCELLED.value
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot apply payment to voided/cancelled invoice"
            )

        if data.amount > invoice.balance_due:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount exceeds balance due"
            )

        payment = InvoicePayment(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            invoice_id=invoice_id,
            amount=data.amount,
            payment_date=data.payment_date or date.today(),
            payment_method=data.payment_method.value,
            reference_number=data.reference_number,
            notes=data.notes,
            created_by=created_by,
        )

        self.db.add(payment)

        invoice.paid_amount = (invoice.paid_amount or Decimal("0")) + data.amount
        invoice.balance_due = invoice.total_amount - invoice.paid_amount
        invoice.update_payment_status()

        self._update_order_payment(invoice, data.amount)

        self.db.commit()
        self.db.refresh(payment)
        return payment

    def _update_order_payment(self, invoice: CustomerInvoice, amount: Decimal):
        """Update order with payment amount."""
        order_ids = set(l.order_id for l in invoice.lines if l.order_id)
        for order_id in order_ids:
            order = self.db.get(SalesOrder, order_id)
            if order:
                order.paid_amount = (order.paid_amount or Decimal("0")) + amount
                if order.balance_due <= 0:
                    order.status = SOStatusEnum.CLOSED.value

    def _refresh_with_lines(self, invoice: CustomerInvoice):
        """Refresh invoice with lines loaded."""
        self.db.refresh(invoice)


class PaymentService:
    """Service for customer payment operations."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    def _generate_payment_number(self) -> str:
        """Generate unique payment number."""
        today = date.today()
        prefix = f"PMT-{today.strftime('%Y%m%d')}"

        result = self.db.execute(
            select(func.count(CustomerPayment.id)).where(
                and_(
                    CustomerPayment.customer_id == self.customer_id,
                    CustomerPayment.payment_number.like(f"{prefix}%")
                )
            )
        )
        count = result.scalar() or 0

        return f"{prefix}-{count + 1:04d}"

    def create_payment(
        self,
        data: CustomerPaymentCreate,
        created_by: Optional[UUID] = None
    ) -> CustomerPayment:
        """Create customer payment."""
        payment = CustomerPayment(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            payment_number=self._generate_payment_number(),
            customer_master_id=data.customer_master_id,
            payment_date=data.payment_date or date.today(),
            payment_method=data.payment_method.value,
            amount=data.amount,
            unapplied_amount=data.amount,
            currency=data.currency,
            exchange_rate=data.exchange_rate,
            reference_number=data.reference_number,
            bank_account_id=data.bank_account_id,
            deposit_to_account_id=data.deposit_to_account_id,
            notes=data.notes,
            memo=data.memo,
            created_by=created_by,
        )

        self.db.add(payment)
        self.db.flush()

        if data.invoice_applications:
            for app in data.invoice_applications:
                self._apply_to_invoice(payment, app.invoice_id, app.amount, created_by)

            payment.recalculate_applied()

        self.db.commit()
        self.db.refresh(payment)
        return payment

    def _apply_to_invoice(
        self,
        payment: CustomerPayment,
        invoice_id: UUID,
        amount: Decimal,
        created_by: Optional[UUID] = None
    ):
        """Apply payment amount to invoice."""
        invoice = self.db.execute(
            select(CustomerInvoice).where(
                and_(
                    CustomerInvoice.id == invoice_id,
                    CustomerInvoice.customer_id == self.customer_id
                )
            ).options(selectinload(CustomerInvoice.lines))
        ).scalar_one_or_none()

        if not invoice:
            return

        if amount > invoice.balance_due:
            amount = invoice.balance_due

        if amount <= 0:
            return

        inv_payment = InvoicePayment(
            id=uuid.uuid4(),
            customer_id=self.customer_id,
            invoice_id=invoice_id,
            payment_id=payment.id,
            amount=amount,
            payment_date=payment.payment_date,
            payment_method=payment.payment_method,
            reference_number=payment.reference_number,
            created_by=created_by,
        )

        self.db.add(inv_payment)

        invoice.paid_amount = (invoice.paid_amount or Decimal("0")) + amount
        invoice.balance_due = invoice.total_amount - invoice.paid_amount
        invoice.update_payment_status()

    def get_payment(
        self,
        payment_id: UUID,
        include_applications: bool = True
    ) -> Optional[CustomerPayment]:
        """Get payment by ID."""
        query = select(CustomerPayment).where(
            and_(
                CustomerPayment.id == payment_id,
                CustomerPayment.customer_id == self.customer_id
            )
        )

        if include_applications:
            query = query.options(
                selectinload(CustomerPayment.applications),
                selectinload(CustomerPayment.customer_master)
            )

        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_payments(
        self,
        filters: CustomerPaymentFilter,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[CustomerPayment], int]:
        """Get payments with filters."""
        query = select(CustomerPayment).where(
            CustomerPayment.customer_id == self.customer_id
        )

        if filters.search:
            search = f"%{filters.search}%"
            query = query.where(
                or_(
                    CustomerPayment.payment_number.ilike(search),
                    CustomerPayment.reference_number.ilike(search),
                )
            )

        if filters.customer_master_id:
            query = query.where(
                CustomerPayment.customer_master_id == filters.customer_master_id
            )

        if filters.payment_method:
            query = query.where(
                CustomerPayment.payment_method == filters.payment_method.value
            )

        if filters.date_from:
            query = query.where(CustomerPayment.payment_date >= filters.date_from)

        if filters.date_to:
            query = query.where(CustomerPayment.payment_date <= filters.date_to)

        if filters.has_unapplied:
            query = query.where(CustomerPayment.unapplied_amount > 0)

        if filters.is_void is not None:
            query = query.where(CustomerPayment.is_void == filters.is_void)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar() or 0

        query = query.options(
            selectinload(CustomerPayment.customer_master),
            selectinload(CustomerPayment.applications)
        )
        query = query.order_by(CustomerPayment.payment_date.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        payments = result.scalars().all()

        return list(payments), total

    def apply_payment(
        self,
        payment_id: UUID,
        request: ApplyPaymentRequest,
        created_by: Optional[UUID] = None
    ) -> CustomerPayment:
        """Apply payment to invoices."""
        payment = self.get_payment(payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        if payment.is_void:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot apply voided payment"
            )

        total_to_apply = sum(app.amount for app in request.applications)
        if total_to_apply > payment.unapplied_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application amount exceeds unapplied balance"
            )

        for app in request.applications:
            self._apply_to_invoice(payment, app.invoice_id, app.amount, created_by)

        payment.recalculate_applied()

        self.db.commit()
        self.db.refresh(payment)
        return payment

    def void_payment(
        self,
        payment_id: UUID,
        request: VoidPaymentRequest,
        void_by: Optional[UUID] = None
    ) -> CustomerPayment:
        """Void payment."""
        payment = self.get_payment(payment_id, include_applications=True)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        if payment.is_void:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment is already void"
            )

        for app in payment.applications:
            invoice = self.db.get(CustomerInvoice, app.invoice_id)
            if invoice:
                invoice.paid_amount = (invoice.paid_amount or Decimal("0")) - app.amount
                invoice.balance_due = invoice.total_amount - invoice.paid_amount
                invoice.update_payment_status()

            self.db.delete(app)

        payment.is_void = True
        payment.void_reason = request.reason
        payment.void_at = utc_now()
        payment.void_by = void_by
        payment.applied_amount = Decimal("0")
        payment.unapplied_amount = payment.amount

        self.db.commit()
        self.db.refresh(payment)
        return payment

    def get_aging_report(
        self,
        filters: AgingReportFilter
    ) -> List[CustomerAgingReport]:
        """Generate customer aging report."""
        as_of = filters.as_of_date or date.today()

        query = select(CustomerInvoice).where(
            and_(
                CustomerInvoice.customer_id == self.customer_id,
                CustomerInvoice.balance_due > 0,
                CustomerInvoice.status.notin_([
                    InvoiceStatusEnum.VOID.value,
                    InvoiceStatusEnum.CANCELLED.value,
                    InvoiceStatusEnum.PAID.value
                ])
            )
        ).options(selectinload(CustomerInvoice.customer_master))

        if filters.customer_master_id:
            query = query.where(
                CustomerInvoice.customer_master_id == filters.customer_master_id
            )

        if filters.min_balance:
            query = query.where(CustomerInvoice.balance_due >= filters.min_balance)

        result = self.db.execute(query)
        invoices = result.scalars().all()

        customer_aging = {}

        for invoice in invoices:
            customer_id = invoice.customer_master_id
            if customer_id not in customer_aging:
                customer_aging[customer_id] = {
                    "customer_id": customer_id,
                    "customer_code": invoice.customer_master.customer_code if invoice.customer_master else "",
                    "customer_name": invoice.customer_master.name if invoice.customer_master else "",
                    "aging": AgingBucket(),
                    "invoice_count": 0
                }

            aging = customer_aging[customer_id]["aging"]
            days_due = (as_of - invoice.due_date).days
            balance = float(invoice.balance_due)

            if days_due <= 0:
                aging.current += balance
            elif days_due <= 30:
                aging.days_1_30 += balance
            elif days_due <= 60:
                aging.days_31_60 += balance
            elif days_due <= 90:
                aging.days_61_90 += balance
            else:
                aging.over_90 += balance

            aging.total += balance
            customer_aging[customer_id]["invoice_count"] += 1

        return [
            CustomerAgingReport(**data)
            for data in customer_aging.values()
        ]


def get_invoice_service(
    db: Session = Depends(get_db),
    customer_id: UUID = None
) -> InvoiceService:
    """Get invoice service instance."""
    return InvoiceService(db, customer_id)


def get_payment_service(
    db: Session = Depends(get_db),
    customer_id: UUID = None
) -> PaymentService:
    """Get payment service instance."""
    return PaymentService(db, customer_id)
