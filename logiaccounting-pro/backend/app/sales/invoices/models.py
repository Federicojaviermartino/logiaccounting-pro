"""
Invoice Models
Customer invoices and payments
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, ForeignKey,
    Numeric, Integer, Text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class InvoiceStatusEnum(str, Enum):
    """Invoice status."""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PARTIAL_PAID = "partial_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    VOID = "void"


class PaymentMethodEnum(str, Enum):
    """Payment method."""
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    ACH = "ach"
    WIRE = "wire"
    OTHER = "other"


class CustomerInvoice(Base):
    """Customer invoice for sales orders."""

    __tablename__ = "customer_invoices"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    invoice_number = Column(String(30), nullable=False)
    customer_master_id = Column(PGUUID(as_uuid=True), ForeignKey("customers_master.id"), nullable=False)

    invoice_date = Column(Date, nullable=False, default=date.today)
    due_date = Column(Date, nullable=False)
    payment_term_id = Column(PGUUID(as_uuid=True), ForeignKey("payment_terms.id"))

    billing_address = Column(Text)
    shipping_address = Column(Text)

    currency = Column(String(3), default="USD")
    exchange_rate = Column(Numeric(18, 8), default=1)

    subtotal = Column(Numeric(18, 4), default=0)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(18, 4), default=0)
    tax_amount = Column(Numeric(18, 4), default=0)
    shipping_amount = Column(Numeric(18, 4), default=0)
    total_amount = Column(Numeric(18, 4), default=0)

    paid_amount = Column(Numeric(18, 4), default=0)
    balance_due = Column(Numeric(18, 4), default=0)

    status = Column(String(20), default=InvoiceStatusEnum.DRAFT.value)

    po_number = Column(String(50))
    reference = Column(String(100))

    notes = Column(Text)
    terms_and_conditions = Column(Text)
    footer_text = Column(Text)

    sent_at = Column(DateTime)
    sent_to = Column(String(200))

    receivable_account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id"))
    revenue_account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id"))
    journal_entry_id = Column(PGUUID(as_uuid=True), ForeignKey("journal_entries.id"))

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer_master = relationship("CustomerMaster")
    payment_term = relationship("PaymentTerm")
    lines = relationship("CustomerInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("InvoicePayment", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("customer_id", "invoice_number", name="uq_invoice_number"),
        Index("idx_invoice_customer_master", "customer_master_id"),
        Index("idx_invoice_status", "status"),
        Index("idx_invoice_date", "invoice_date"),
        Index("idx_invoice_due_date", "due_date"),
    )

    @property
    def is_editable(self) -> bool:
        return self.status == InvoiceStatusEnum.DRAFT.value

    @property
    def can_send(self) -> bool:
        return self.status in [
            InvoiceStatusEnum.DRAFT.value,
            InvoiceStatusEnum.PENDING.value
        ] and len(self.lines) > 0

    @property
    def can_void(self) -> bool:
        return self.status not in [
            InvoiceStatusEnum.VOID.value,
            InvoiceStatusEnum.CANCELLED.value
        ] and self.paid_amount == 0

    @property
    def is_overdue(self) -> bool:
        return (
            self.status not in [
                InvoiceStatusEnum.PAID.value,
                InvoiceStatusEnum.CANCELLED.value,
                InvoiceStatusEnum.VOID.value
            ] and
            self.due_date < date.today() and
            self.balance_due > 0
        )

    @property
    def days_overdue(self) -> int:
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days

    def recalculate_totals(self):
        """Recalculate invoice totals from lines."""
        self.subtotal = sum(
            line.line_subtotal or Decimal("0")
            for line in self.lines
        )
        self.tax_amount = sum(
            line.line_tax or Decimal("0")
            for line in self.lines
        )

        discount = Decimal("0")
        if self.discount_percent and self.discount_percent > 0:
            discount = self.subtotal * self.discount_percent / 100
        elif self.discount_amount:
            discount = self.discount_amount

        self.discount_amount = discount
        self.total_amount = (
            self.subtotal + self.tax_amount - discount +
            (self.shipping_amount or Decimal("0"))
        )
        self.balance_due = self.total_amount - (self.paid_amount or Decimal("0"))

    def update_payment_status(self):
        """Update status based on payments."""
        if self.balance_due <= 0:
            self.status = InvoiceStatusEnum.PAID.value
        elif self.paid_amount > 0:
            self.status = InvoiceStatusEnum.PARTIAL_PAID.value
        elif self.is_overdue:
            self.status = InvoiceStatusEnum.OVERDUE.value

    def to_dict(self, include_lines: bool = False, include_payments: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "invoice_number": self.invoice_number,
            "customer_master_id": str(self.customer_master_id),
            "customer_code": self.customer_master.customer_code if self.customer_master else None,
            "customer_name": self.customer_master.name if self.customer_master else None,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "billing_address": self.billing_address,
            "currency": self.currency,
            "subtotal": float(self.subtotal) if self.subtotal else 0,
            "discount_percent": float(self.discount_percent) if self.discount_percent else 0,
            "discount_amount": float(self.discount_amount) if self.discount_amount else 0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0,
            "shipping_amount": float(self.shipping_amount) if self.shipping_amount else 0,
            "total_amount": float(self.total_amount) if self.total_amount else 0,
            "paid_amount": float(self.paid_amount) if self.paid_amount else 0,
            "balance_due": float(self.balance_due) if self.balance_due else 0,
            "status": self.status,
            "po_number": self.po_number,
            "reference": self.reference,
            "notes": self.notes,
            "is_overdue": self.is_overdue,
            "days_overdue": self.days_overdue,
            "line_count": len(self.lines),
            "payment_count": len(self.payments),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_lines:
            result["lines"] = [l.to_dict() for l in self.lines]

        if include_payments:
            result["payments"] = [p.to_dict() for p in self.payments]

        return result


class CustomerInvoiceLine(Base):
    """Invoice line item."""

    __tablename__ = "customer_invoice_lines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey("customer_invoices.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)

    order_id = Column(PGUUID(as_uuid=True), ForeignKey("sales_orders.id"))
    order_line_id = Column(PGUUID(as_uuid=True), ForeignKey("sales_order_lines.id"))
    shipment_id = Column(PGUUID(as_uuid=True), ForeignKey("shipments.id"))

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"))
    description = Column(String(500), nullable=False)

    quantity = Column(Numeric(18, 4), nullable=False)
    uom_id = Column(PGUUID(as_uuid=True), ForeignKey("units_of_measure.id"))

    unit_price = Column(Numeric(18, 6), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)

    line_subtotal = Column(Numeric(18, 4))
    line_discount = Column(Numeric(18, 4))
    line_tax = Column(Numeric(18, 4))
    line_total = Column(Numeric(18, 4))

    revenue_account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id"))

    invoice = relationship("CustomerInvoice", back_populates="lines")
    order = relationship("SalesOrder")
    order_line = relationship("SalesOrderLine")
    product = relationship("Product")
    uom = relationship("UnitOfMeasure")

    __table_args__ = (
        UniqueConstraint("invoice_id", "line_number", name="uq_invoice_line"),
        Index("idx_invoice_line_order", "order_id"),
        Index("idx_invoice_line_product", "product_id"),
    )

    def calculate_amounts(self):
        """Calculate line amounts."""
        qty = self.quantity or Decimal("0")
        price = self.unit_price or Decimal("0")
        discount = self.discount_percent or Decimal("0")
        tax_rate = self.tax_rate or Decimal("0")

        subtotal = qty * price
        line_discount = Decimal("0")
        if discount > 0:
            line_discount = subtotal * discount / 100
            subtotal = subtotal - line_discount

        self.line_subtotal = subtotal
        self.line_discount = line_discount
        self.line_tax = subtotal * tax_rate / 100
        self.line_total = self.line_subtotal + self.line_tax

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "line_number": self.line_number,
            "order_id": str(self.order_id) if self.order_id else None,
            "order_number": self.order.order_number if self.order else None,
            "shipment_id": str(self.shipment_id) if self.shipment_id else None,
            "product_id": str(self.product_id) if self.product_id else None,
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "description": self.description,
            "quantity": float(self.quantity),
            "uom": self.uom.code if self.uom else None,
            "unit_price": float(self.unit_price),
            "discount_percent": float(self.discount_percent) if self.discount_percent else 0,
            "tax_rate": float(self.tax_rate) if self.tax_rate else 0,
            "line_subtotal": float(self.line_subtotal) if self.line_subtotal else 0,
            "line_discount": float(self.line_discount) if self.line_discount else 0,
            "line_tax": float(self.line_tax) if self.line_tax else 0,
            "line_total": float(self.line_total) if self.line_total else 0,
        }


class InvoicePayment(Base):
    """Payment applied to invoice."""

    __tablename__ = "invoice_payments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey("customer_invoices.id", ondelete="CASCADE"), nullable=False)
    payment_id = Column(PGUUID(as_uuid=True), ForeignKey("customer_payments.id"))

    amount = Column(Numeric(18, 4), nullable=False)
    payment_date = Column(Date, nullable=False, default=date.today)
    payment_method = Column(String(20), default=PaymentMethodEnum.BANK_TRANSFER.value)

    reference_number = Column(String(50))
    notes = Column(Text)

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("CustomerInvoice", back_populates="payments")

    __table_args__ = (
        Index("idx_inv_payment_invoice", "invoice_id"),
        Index("idx_inv_payment_date", "payment_date"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "invoice_id": str(self.invoice_id),
            "payment_id": str(self.payment_id) if self.payment_id else None,
            "amount": float(self.amount),
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment_method": self.payment_method,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CustomerPayment(Base):
    """Customer payment that can be applied to invoices."""

    __tablename__ = "customer_payments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    payment_number = Column(String(30), nullable=False)
    customer_master_id = Column(PGUUID(as_uuid=True), ForeignKey("customers_master.id"), nullable=False)

    payment_date = Column(Date, nullable=False, default=date.today)
    payment_method = Column(String(20), default=PaymentMethodEnum.BANK_TRANSFER.value)

    amount = Column(Numeric(18, 4), nullable=False)
    applied_amount = Column(Numeric(18, 4), default=0)
    unapplied_amount = Column(Numeric(18, 4), default=0)

    currency = Column(String(3), default="USD")
    exchange_rate = Column(Numeric(18, 8), default=1)

    reference_number = Column(String(50))
    bank_account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id"))
    deposit_to_account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id"))

    journal_entry_id = Column(PGUUID(as_uuid=True), ForeignKey("journal_entries.id"))

    notes = Column(Text)
    memo = Column(String(200))

    is_void = Column(Boolean, default=False)
    void_reason = Column(Text)
    void_at = Column(DateTime)
    void_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer_master = relationship("CustomerMaster")
    applications = relationship("InvoicePayment", foreign_keys=[InvoicePayment.payment_id])

    __table_args__ = (
        UniqueConstraint("customer_id", "payment_number", name="uq_payment_number"),
        Index("idx_payment_customer_master", "customer_master_id"),
        Index("idx_payment_date", "payment_date"),
    )

    @property
    def is_fully_applied(self) -> bool:
        return self.unapplied_amount <= 0

    def recalculate_applied(self):
        """Recalculate applied amount."""
        self.applied_amount = sum(
            app.amount for app in self.applications
        ) if self.applications else Decimal("0")
        self.unapplied_amount = (self.amount or Decimal("0")) - self.applied_amount

    def to_dict(self, include_applications: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "payment_number": self.payment_number,
            "customer_master_id": str(self.customer_master_id),
            "customer_code": self.customer_master.customer_code if self.customer_master else None,
            "customer_name": self.customer_master.name if self.customer_master else None,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "payment_method": self.payment_method,
            "amount": float(self.amount),
            "applied_amount": float(self.applied_amount) if self.applied_amount else 0,
            "unapplied_amount": float(self.unapplied_amount) if self.unapplied_amount else 0,
            "currency": self.currency,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "memo": self.memo,
            "is_void": self.is_void,
            "is_fully_applied": self.is_fully_applied,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_applications:
            result["applications"] = [a.to_dict() for a in self.applications]

        return result
