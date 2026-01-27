"""
Supplier Invoice Models
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, ForeignKey,
    Numeric, Integer, Text, Index, UniqueConstraint, Computed
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class InvoiceStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTED = "posted"
    PARTIAL_PAID = "partial_paid"
    PAID = "paid"
    CANCELLED = "cancelled"


class MatchStatusEnum(str, Enum):
    UNMATCHED = "unmatched"
    PARTIAL = "partial"
    MATCHED = "matched"
    EXCEPTION = "exception"


class SupplierInvoice(Base):
    """Supplier invoice header."""

    __tablename__ = "supplier_invoices"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Identification
    invoice_number = Column(String(30), nullable=False)
    supplier_id = Column(PGUUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    supplier_invoice_number = Column(String(50))  # Supplier's invoice number

    # Dates
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    posting_date = Column(Date, nullable=False, default=date.today)

    # Terms
    payment_term_id = Column(PGUUID(as_uuid=True), ForeignKey("payment_terms.id"))
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Numeric(18, 8), default=1)

    # Amounts
    subtotal = Column(Numeric(18, 4), default=0)
    tax_amount = Column(Numeric(18, 4), default=0)
    discount_amount = Column(Numeric(18, 4), default=0)
    total_amount = Column(Numeric(18, 4), default=0)
    amount_paid = Column(Numeric(18, 4), default=0)

    # Matching
    match_status = Column(String(20), default=MatchStatusEnum.UNMATCHED.value)

    # Status
    status = Column(String(20), default=InvoiceStatusEnum.DRAFT.value)

    # Approval
    approved_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # Accounting
    journal_entry_id = Column(PGUUID(as_uuid=True), ForeignKey("journal_entries.id"))

    # Metadata
    notes = Column(Text)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier")
    payment_term = relationship("PaymentTerm")
    lines = relationship("SupplierInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    journal_entry = relationship("JournalEntry")

    __table_args__ = (
        UniqueConstraint("customer_id", "invoice_number", name="uq_supplier_invoice_number"),
        Index("idx_sinv_supplier", "supplier_id"),
        Index("idx_sinv_status", "status"),
        Index("idx_sinv_due_date", "due_date"),
    )

    @property
    def amount_due(self) -> Decimal:
        """Calculate amount due."""
        return (self.total_amount or Decimal("0")) - (self.amount_paid or Decimal("0"))

    @property
    def is_overdue(self) -> bool:
        if self.status in [InvoiceStatusEnum.PAID.value, InvoiceStatusEnum.CANCELLED.value]:
            return False
        return self.due_date < date.today() and self.amount_due > 0

    def recalculate_totals(self):
        self.subtotal = sum(
            l.line_subtotal or Decimal("0") for l in self.lines
        )
        self.tax_amount = sum(
            l.line_tax or Decimal("0") for l in self.lines
        )
        self.total_amount = self.subtotal + self.tax_amount - (self.discount_amount or Decimal("0"))

    def to_dict(self, include_lines: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "invoice_number": self.invoice_number,
            "supplier_id": str(self.supplier_id),
            "supplier_name": self.supplier.name if self.supplier else None,
            "supplier_invoice_number": self.supplier_invoice_number,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "posting_date": self.posting_date.isoformat() if self.posting_date else None,
            "currency": self.currency,
            "subtotal": float(self.subtotal) if self.subtotal else 0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0,
            "discount_amount": float(self.discount_amount) if self.discount_amount else 0,
            "total_amount": float(self.total_amount) if self.total_amount else 0,
            "amount_paid": float(self.amount_paid) if self.amount_paid else 0,
            "amount_due": float(self.amount_due) if self.amount_due else 0,
            "match_status": self.match_status,
            "status": self.status,
            "is_overdue": self.is_overdue,
            "line_count": len(self.lines),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_lines:
            result["lines"] = [l.to_dict() for l in self.lines]

        return result


class SupplierInvoiceLine(Base):
    """Supplier invoice line."""

    __tablename__ = "supplier_invoice_lines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey("supplier_invoices.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)

    # Matching references
    order_line_id = Column(PGUUID(as_uuid=True), ForeignKey("purchase_order_lines.id"))
    receipt_line_id = Column(PGUUID(as_uuid=True), ForeignKey("goods_receipt_lines.id"))

    # Product/Service
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"))
    description = Column(String(500), nullable=False)

    # Accounting
    account_id = Column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))

    # Quantity
    quantity = Column(Numeric(18, 4), nullable=False)
    uom_id = Column(PGUUID(as_uuid=True), ForeignKey("units_of_measure.id"))

    # Pricing
    unit_price = Column(Numeric(18, 6), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)

    # Calculated
    line_subtotal = Column(Numeric(18, 4))
    line_tax = Column(Numeric(18, 4))
    line_total = Column(Numeric(18, 4))

    # 3-way match
    match_status = Column(String(20), default="pending")
    price_variance = Column(Numeric(18, 4), default=0)
    quantity_variance = Column(Numeric(18, 4), default=0)

    notes = Column(Text)

    # Relationships
    invoice = relationship("SupplierInvoice", back_populates="lines")
    order_line = relationship("PurchaseOrderLine")
    receipt_line = relationship("GoodsReceiptLine")
    product = relationship("Product")
    account = relationship("ChartOfAccount")
    uom = relationship("UnitOfMeasure")

    __table_args__ = (
        UniqueConstraint("invoice_id", "line_number", name="uq_sinv_line"),
    )

    def calculate_amounts(self):
        qty = self.quantity or Decimal("0")
        price = self.unit_price or Decimal("0")
        discount = self.discount_percent or Decimal("0")
        tax_rate = self.tax_rate or Decimal("0")

        subtotal = qty * price
        if discount > 0:
            subtotal = subtotal * (1 - discount / 100)

        self.line_subtotal = subtotal
        self.line_tax = subtotal * tax_rate / 100
        self.line_total = self.line_subtotal + self.line_tax

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "line_number": self.line_number,
            "order_line_id": str(self.order_line_id) if self.order_line_id else None,
            "receipt_line_id": str(self.receipt_line_id) if self.receipt_line_id else None,
            "product_id": str(self.product_id) if self.product_id else None,
            "product_sku": self.product.sku if self.product else None,
            "description": self.description,
            "account_id": str(self.account_id) if self.account_id else None,
            "quantity": float(self.quantity),
            "unit_price": float(self.unit_price),
            "discount_percent": float(self.discount_percent) if self.discount_percent else 0,
            "tax_rate": float(self.tax_rate) if self.tax_rate else 0,
            "line_subtotal": float(self.line_subtotal) if self.line_subtotal else 0,
            "line_tax": float(self.line_tax) if self.line_tax else 0,
            "line_total": float(self.line_total) if self.line_total else 0,
            "match_status": self.match_status,
            "price_variance": float(self.price_variance) if self.price_variance else 0,
            "quantity_variance": float(self.quantity_variance) if self.quantity_variance else 0,
        }
