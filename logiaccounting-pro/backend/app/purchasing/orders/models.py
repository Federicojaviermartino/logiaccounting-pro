"""
Purchase Order Models
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
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


class POStatusEnum(str, Enum):
    """Purchase order status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    PARTIAL = "partial"          # Partially received
    RECEIVED = "received"        # Fully received
    INVOICED = "invoiced"        # Invoice received
    CLOSED = "closed"
    CANCELLED = "cancelled"


class POLineStatusEnum(str, Enum):
    """Line status."""
    PENDING = "pending"
    PARTIAL = "partial"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PurchaseOrder(Base):
    """Purchase order header."""

    __tablename__ = "purchase_orders"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Identification
    order_number = Column(String(30), nullable=False)
    supplier_id = Column(PGUUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)

    # Dates
    order_date = Column(Date, nullable=False, default=date.today)
    expected_date = Column(Date)

    # Delivery
    delivery_warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))
    delivery_address = Column(Text)

    # Terms
    payment_term_id = Column(PGUUID(as_uuid=True), ForeignKey("payment_terms.id"))
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Numeric(18, 8), default=1)

    # Amounts
    subtotal = Column(Numeric(18, 4), default=0)
    tax_amount = Column(Numeric(18, 4), default=0)
    discount_amount = Column(Numeric(18, 4), default=0)
    shipping_amount = Column(Numeric(18, 4), default=0)
    total_amount = Column(Numeric(18, 4), default=0)

    # Status
    status = Column(String(20), default=POStatusEnum.DRAFT.value)

    # Approval
    approval_required = Column(Boolean, default=False)
    approval_status = Column(String(20), default="not_required")
    approved_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # Receiving tracking
    received_amount = Column(Numeric(18, 4), default=0)

    # Invoicing tracking
    invoiced_amount = Column(Numeric(18, 4), default=0)

    # Reference
    requisition_id = Column(PGUUID(as_uuid=True), ForeignKey("purchase_requisitions.id"))
    reference = Column(String(100))  # External reference

    # Supplier contact
    supplier_contact_id = Column(PGUUID(as_uuid=True), ForeignKey("supplier_contacts.id"))

    # Metadata
    notes = Column(Text)
    internal_notes = Column(Text)

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier")
    lines = relationship("PurchaseOrderLine", back_populates="order", cascade="all, delete-orphan")
    delivery_warehouse = relationship("Warehouse")
    payment_term = relationship("PaymentTerm")
    supplier_contact = relationship("SupplierContact")
    approvals = relationship("PurchaseOrderApproval", back_populates="order")

    __table_args__ = (
        UniqueConstraint("customer_id", "order_number", name="uq_po_number"),
        Index("idx_po_supplier", "supplier_id"),
        Index("idx_po_status", "status"),
        Index("idx_po_date", "order_date"),
    )

    @property
    def is_editable(self) -> bool:
        """Check if order can be edited."""
        return self.status in [POStatusEnum.DRAFT.value, POStatusEnum.PENDING_APPROVAL.value]

    @property
    def can_receive(self) -> bool:
        """Check if order can receive goods."""
        return self.status in [
            POStatusEnum.APPROVED.value,
            POStatusEnum.SENT.value,
            POStatusEnum.PARTIAL.value,
        ]

    @property
    def fully_received(self) -> bool:
        """Check if all lines are received."""
        return all(
            line.quantity_received >= line.quantity
            for line in self.lines
            if line.status != POLineStatusEnum.CANCELLED.value
        )

    @property
    def fully_invoiced(self) -> bool:
        """Check if order is fully invoiced."""
        return self.invoiced_amount >= self.total_amount

    def recalculate_totals(self):
        """Recalculate order totals from lines."""
        self.subtotal = sum(
            line.line_subtotal or Decimal("0")
            for line in self.lines
            if line.status != POLineStatusEnum.CANCELLED.value
        )
        self.tax_amount = sum(
            line.line_tax or Decimal("0")
            for line in self.lines
            if line.status != POLineStatusEnum.CANCELLED.value
        )
        self.total_amount = self.subtotal + self.tax_amount - (self.discount_amount or Decimal("0")) + (self.shipping_amount or Decimal("0"))

    def to_dict(self, include_lines: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "order_number": self.order_number,
            "supplier_id": str(self.supplier_id),
            "supplier_code": self.supplier.supplier_code if self.supplier else None,
            "supplier_name": self.supplier.name if self.supplier else None,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "expected_date": self.expected_date.isoformat() if self.expected_date else None,
            "delivery_warehouse_id": str(self.delivery_warehouse_id) if self.delivery_warehouse_id else None,
            "delivery_warehouse": self.delivery_warehouse.name if self.delivery_warehouse else None,
            "currency": self.currency,
            "exchange_rate": float(self.exchange_rate) if self.exchange_rate else 1,
            "subtotal": float(self.subtotal) if self.subtotal else 0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0,
            "discount_amount": float(self.discount_amount) if self.discount_amount else 0,
            "shipping_amount": float(self.shipping_amount) if self.shipping_amount else 0,
            "total_amount": float(self.total_amount) if self.total_amount else 0,
            "status": self.status,
            "approval_required": self.approval_required,
            "approval_status": self.approval_status,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "received_amount": float(self.received_amount) if self.received_amount else 0,
            "invoiced_amount": float(self.invoiced_amount) if self.invoiced_amount else 0,
            "reference": self.reference,
            "notes": self.notes,
            "line_count": len(self.lines),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_lines:
            result["lines"] = [l.to_dict() for l in self.lines]

        return result


class PurchaseOrderLine(Base):
    """Purchase order line item."""

    __tablename__ = "purchase_order_lines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)

    # Product
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    description = Column(String(500))
    supplier_sku = Column(String(50))  # Supplier's product code

    # Quantity
    quantity = Column(Numeric(18, 4), nullable=False)
    uom_id = Column(PGUUID(as_uuid=True), ForeignKey("units_of_measure.id"))

    # Pricing
    unit_price = Column(Numeric(18, 6), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)

    # Calculated amounts
    line_subtotal = Column(Numeric(18, 4))
    line_tax = Column(Numeric(18, 4))
    line_total = Column(Numeric(18, 4))

    # Receiving tracking
    quantity_received = Column(Numeric(18, 4), default=0)
    quantity_invoiced = Column(Numeric(18, 4), default=0)

    # Status
    status = Column(String(20), default=POLineStatusEnum.PENDING.value)

    # Scheduling
    expected_date = Column(Date)

    # Destination
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))

    notes = Column(Text)

    # Relationships
    order = relationship("PurchaseOrder", back_populates="lines")
    product = relationship("Product")
    uom = relationship("UnitOfMeasure")
    warehouse = relationship("Warehouse")

    __table_args__ = (
        UniqueConstraint("order_id", "line_number", name="uq_po_line"),
        Index("idx_po_line_product", "product_id"),
    )

    @property
    def quantity_pending(self) -> Decimal:
        """Quantity not yet received."""
        return (self.quantity or Decimal("0")) - (self.quantity_received or Decimal("0"))

    def calculate_amounts(self):
        """Calculate line amounts."""
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
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "description": self.description,
            "supplier_sku": self.supplier_sku,
            "quantity": float(self.quantity),
            "uom": self.uom.code if self.uom else None,
            "unit_price": float(self.unit_price),
            "discount_percent": float(self.discount_percent) if self.discount_percent else 0,
            "tax_rate": float(self.tax_rate) if self.tax_rate else 0,
            "line_subtotal": float(self.line_subtotal) if self.line_subtotal else 0,
            "line_tax": float(self.line_tax) if self.line_tax else 0,
            "line_total": float(self.line_total) if self.line_total else 0,
            "quantity_received": float(self.quantity_received) if self.quantity_received else 0,
            "quantity_invoiced": float(self.quantity_invoiced) if self.quantity_invoiced else 0,
            "quantity_pending": float(self.quantity_pending),
            "status": self.status,
            "expected_date": self.expected_date.isoformat() if self.expected_date else None,
            "warehouse_id": str(self.warehouse_id) if self.warehouse_id else None,
            "notes": self.notes,
        }


class PurchaseOrderApproval(Base):
    """PO approval history."""

    __tablename__ = "purchase_order_approvals"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)

    approver_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(20), nullable=False)  # approved, rejected, returned
    comments = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    order = relationship("PurchaseOrder", back_populates="approvals")
    approver = relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "approver_id": str(self.approver_id),
            "approver_name": self.approver.full_name if self.approver else None,
            "action": self.action,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
