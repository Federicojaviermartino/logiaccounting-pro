"""
Sales Order Models
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
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class SOStatusEnum(str, Enum):
    """Sales order status."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    PARTIAL_SHIPPED = "partial_shipped"
    SHIPPED = "shipped"
    INVOICED = "invoiced"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class SOLineStatusEnum(str, Enum):
    """Line status."""
    PENDING = "pending"
    ALLOCATED = "allocated"
    PICKING = "picking"
    PARTIAL_SHIPPED = "partial_shipped"
    SHIPPED = "shipped"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"
    BACKORDERED = "backordered"


class PriorityEnum(str, Enum):
    """Order priority."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SalesOrder(Base):
    """Sales order header."""

    __tablename__ = "sales_orders"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    order_number = Column(String(30), nullable=False)
    customer_master_id = Column(PGUUID(as_uuid=True), ForeignKey("customers_master.id"), nullable=False)
    customer_po_number = Column(String(50))

    order_date = Column(Date, nullable=False, default=date.today)
    requested_date = Column(Date)
    promised_date = Column(Date)

    ship_to_address_id = Column(PGUUID(as_uuid=True), ForeignKey("customer_shipping_addresses.id"))
    shipping_address = Column(Text)
    shipping_method = Column(String(50))
    shipping_carrier = Column(String(50))

    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))

    payment_term_id = Column(PGUUID(as_uuid=True), ForeignKey("payment_terms.id"))
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Numeric(18, 8), default=1)

    subtotal = Column(Numeric(18, 4), default=0)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(18, 4), default=0)
    tax_amount = Column(Numeric(18, 4), default=0)
    shipping_amount = Column(Numeric(18, 4), default=0)
    total_amount = Column(Numeric(18, 4), default=0)

    status = Column(String(20), default=SOStatusEnum.DRAFT.value)

    qty_ordered = Column(Numeric(18, 4), default=0)
    qty_allocated = Column(Numeric(18, 4), default=0)
    qty_picked = Column(Numeric(18, 4), default=0)
    qty_shipped = Column(Numeric(18, 4), default=0)
    qty_invoiced = Column(Numeric(18, 4), default=0)

    invoiced_amount = Column(Numeric(18, 4), default=0)
    paid_amount = Column(Numeric(18, 4), default=0)

    priority = Column(String(10), default=PriorityEnum.NORMAL.value)

    hold_reason = Column(Text)
    hold_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    hold_at = Column(DateTime)

    notes = Column(Text)
    internal_notes = Column(Text)

    confirmed_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    confirmed_at = Column(DateTime)

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer_master = relationship("CustomerMaster")
    lines = relationship("SalesOrderLine", back_populates="order", cascade="all, delete-orphan")
    ship_to_address = relationship("CustomerShippingAddress")
    warehouse = relationship("Warehouse")
    payment_term = relationship("PaymentTerm")
    allocations = relationship("StockAllocation", back_populates="order")

    __table_args__ = (
        UniqueConstraint("customer_id", "order_number", name="uq_so_number"),
        Index("idx_so_customer_master", "customer_master_id"),
        Index("idx_so_status", "status"),
        Index("idx_so_date", "order_date"),
        Index("idx_so_requested_date", "requested_date"),
    )

    @property
    def is_editable(self) -> bool:
        return self.status in [SOStatusEnum.DRAFT.value, SOStatusEnum.ON_HOLD.value]

    @property
    def can_confirm(self) -> bool:
        return self.status == SOStatusEnum.DRAFT.value and len(self.lines) > 0

    @property
    def can_ship(self) -> bool:
        return self.status in [
            SOStatusEnum.CONFIRMED.value,
            SOStatusEnum.PROCESSING.value,
            SOStatusEnum.PARTIAL_SHIPPED.value,
        ]

    @property
    def fully_shipped(self) -> bool:
        return all(
            line.qty_shipped >= line.quantity
            for line in self.lines
            if line.status != SOLineStatusEnum.CANCELLED.value
        )

    @property
    def fully_invoiced(self) -> bool:
        return self.invoiced_amount >= self.total_amount

    @property
    def balance_due(self) -> Decimal:
        return (self.total_amount or Decimal("0")) - (self.paid_amount or Decimal("0"))

    def recalculate_totals(self):
        """Recalculate order totals from lines."""
        self.subtotal = sum(
            line.line_subtotal or Decimal("0")
            for line in self.lines
            if line.status != SOLineStatusEnum.CANCELLED.value
        )
        self.tax_amount = sum(
            line.line_tax or Decimal("0")
            for line in self.lines
            if line.status != SOLineStatusEnum.CANCELLED.value
        )

        discount = Decimal("0")
        if self.discount_percent and self.discount_percent > 0:
            discount = self.subtotal * self.discount_percent / 100
        elif self.discount_amount:
            discount = self.discount_amount

        self.discount_amount = discount
        self.total_amount = self.subtotal + self.tax_amount - discount + (self.shipping_amount or Decimal("0"))

        self.qty_ordered = sum(
            line.quantity or Decimal("0")
            for line in self.lines
            if line.status != SOLineStatusEnum.CANCELLED.value
        )

    def to_dict(self, include_lines: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "order_number": self.order_number,
            "customer_master_id": str(self.customer_master_id),
            "customer_code": self.customer_master.customer_code if self.customer_master else None,
            "customer_name": self.customer_master.name if self.customer_master else None,
            "customer_po_number": self.customer_po_number,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "requested_date": self.requested_date.isoformat() if self.requested_date else None,
            "promised_date": self.promised_date.isoformat() if self.promised_date else None,
            "shipping_address": self.shipping_address,
            "shipping_method": self.shipping_method,
            "warehouse_id": str(self.warehouse_id) if self.warehouse_id else None,
            "warehouse_name": self.warehouse.name if self.warehouse else None,
            "currency": self.currency,
            "subtotal": float(self.subtotal) if self.subtotal else 0,
            "discount_percent": float(self.discount_percent) if self.discount_percent else 0,
            "discount_amount": float(self.discount_amount) if self.discount_amount else 0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0,
            "shipping_amount": float(self.shipping_amount) if self.shipping_amount else 0,
            "total_amount": float(self.total_amount) if self.total_amount else 0,
            "status": self.status,
            "priority": self.priority,
            "qty_ordered": float(self.qty_ordered) if self.qty_ordered else 0,
            "qty_allocated": float(self.qty_allocated) if self.qty_allocated else 0,
            "qty_shipped": float(self.qty_shipped) if self.qty_shipped else 0,
            "qty_invoiced": float(self.qty_invoiced) if self.qty_invoiced else 0,
            "invoiced_amount": float(self.invoiced_amount) if self.invoiced_amount else 0,
            "paid_amount": float(self.paid_amount) if self.paid_amount else 0,
            "balance_due": float(self.balance_due),
            "hold_reason": self.hold_reason,
            "notes": self.notes,
            "line_count": len(self.lines),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
        }

        if include_lines:
            result["lines"] = [l.to_dict() for l in self.lines]

        return result


class SalesOrderLine(Base):
    """Sales order line item."""

    __tablename__ = "sales_order_lines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    description = Column(String(500))

    quantity = Column(Numeric(18, 4), nullable=False)
    uom_id = Column(PGUUID(as_uuid=True), ForeignKey("units_of_measure.id"))

    unit_price = Column(Numeric(18, 6), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)

    line_subtotal = Column(Numeric(18, 4))
    line_discount = Column(Numeric(18, 4))
    line_tax = Column(Numeric(18, 4))
    line_total = Column(Numeric(18, 4))

    qty_allocated = Column(Numeric(18, 4), default=0)
    qty_picked = Column(Numeric(18, 4), default=0)
    qty_shipped = Column(Numeric(18, 4), default=0)
    qty_invoiced = Column(Numeric(18, 4), default=0)
    qty_returned = Column(Numeric(18, 4), default=0)

    status = Column(String(20), default=SOLineStatusEnum.PENDING.value)

    requested_date = Column(Date)
    promised_date = Column(Date)

    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))

    notes = Column(Text)

    order = relationship("SalesOrder", back_populates="lines")
    product = relationship("Product")
    uom = relationship("UnitOfMeasure")
    warehouse = relationship("Warehouse")
    allocations = relationship("StockAllocation", back_populates="order_line")

    __table_args__ = (
        UniqueConstraint("order_id", "line_number", name="uq_so_line"),
        Index("idx_so_line_product", "product_id"),
    )

    @property
    def qty_pending(self) -> Decimal:
        """Quantity not yet shipped."""
        return (self.quantity or Decimal("0")) - (self.qty_shipped or Decimal("0"))

    @property
    def qty_to_allocate(self) -> Decimal:
        """Quantity not yet allocated."""
        return (self.quantity or Decimal("0")) - (self.qty_allocated or Decimal("0"))

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
            "product_id": str(self.product_id),
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
            "qty_allocated": float(self.qty_allocated) if self.qty_allocated else 0,
            "qty_picked": float(self.qty_picked) if self.qty_picked else 0,
            "qty_shipped": float(self.qty_shipped) if self.qty_shipped else 0,
            "qty_invoiced": float(self.qty_invoiced) if self.qty_invoiced else 0,
            "qty_pending": float(self.qty_pending),
            "status": self.status,
            "requested_date": self.requested_date.isoformat() if self.requested_date else None,
            "promised_date": self.promised_date.isoformat() if self.promised_date else None,
            "warehouse_id": str(self.warehouse_id) if self.warehouse_id else None,
            "notes": self.notes,
        }


class StockAllocation(Base):
    """Stock reserved for sales orders."""

    __tablename__ = "stock_allocations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    order_id = Column(PGUUID(as_uuid=True), ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False)
    order_line_id = Column(PGUUID(as_uuid=True), ForeignKey("sales_order_lines.id", ondelete="CASCADE"), nullable=False)

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id"))
    lot_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_lots.id"))

    quantity_allocated = Column(Numeric(18, 4), nullable=False)
    quantity_picked = Column(Numeric(18, 4), default=0)

    status = Column(String(20), default="allocated")

    allocated_at = Column(DateTime, default=datetime.utcnow)
    allocated_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    order = relationship("SalesOrder", back_populates="allocations")
    order_line = relationship("SalesOrderLine", back_populates="allocations")
    product = relationship("Product")
    warehouse = relationship("Warehouse")
    location = relationship("WarehouseLocation")
    lot = relationship("StockLot")

    __table_args__ = (
        Index("idx_allocation_order", "order_id"),
        Index("idx_allocation_product", "product_id", "warehouse_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "order_line_id": str(self.order_line_id),
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "warehouse_id": str(self.warehouse_id),
            "location_id": str(self.location_id) if self.location_id else None,
            "location_code": self.location.code if self.location else None,
            "lot_id": str(self.lot_id) if self.lot_id else None,
            "lot_number": self.lot.lot_number if self.lot else None,
            "quantity_allocated": float(self.quantity_allocated),
            "quantity_picked": float(self.quantity_picked) if self.quantity_picked else 0,
            "status": self.status,
            "allocated_at": self.allocated_at.isoformat() if self.allocated_at else None,
        }
