"""
Goods Receipt Models
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, ForeignKey,
    Numeric, Integer, Text, Index, UniqueConstraint, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class ReceiptStatusEnum(str, Enum):
    DRAFT = "draft"
    POSTED = "posted"
    CANCELLED = "cancelled"


class QualityStatusEnum(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    QUARANTINE = "quarantine"


class GoodsReceipt(Base):
    """Goods receipt header."""

    __tablename__ = "goods_receipts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Identification
    receipt_number = Column(String(30), nullable=False)

    # Source
    purchase_order_id = Column(PGUUID(as_uuid=True), ForeignKey("purchase_orders.id"))
    supplier_id = Column(PGUUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)

    # Dates
    receipt_date = Column(Date, nullable=False, default=date.today)
    posting_date = Column(Date, nullable=False, default=date.today)

    # Location
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)

    # Reference
    supplier_delivery_note = Column(String(50))

    # Status
    status = Column(String(20), default=ReceiptStatusEnum.DRAFT.value)

    # Metadata
    notes = Column(Text)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    posted_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    posted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    purchase_order = relationship("PurchaseOrder")
    supplier = relationship("Supplier")
    warehouse = relationship("Warehouse")
    lines = relationship("GoodsReceiptLine", back_populates="receipt", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("customer_id", "receipt_number", name="uq_receipt_number"),
        Index("idx_receipt_po", "purchase_order_id"),
        Index("idx_receipt_supplier", "supplier_id"),
    )

    @property
    def total_value(self) -> Decimal:
        return sum(
            (l.quantity_received * (l.unit_cost or Decimal("0")))
            for l in self.lines
        )

    def to_dict(self, include_lines: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "receipt_number": self.receipt_number,
            "purchase_order_id": str(self.purchase_order_id) if self.purchase_order_id else None,
            "po_number": self.purchase_order.order_number if self.purchase_order else None,
            "supplier_id": str(self.supplier_id),
            "supplier_name": self.supplier.name if self.supplier else None,
            "receipt_date": self.receipt_date.isoformat() if self.receipt_date else None,
            "posting_date": self.posting_date.isoformat() if self.posting_date else None,
            "warehouse_id": str(self.warehouse_id),
            "warehouse_name": self.warehouse.name if self.warehouse else None,
            "supplier_delivery_note": self.supplier_delivery_note,
            "status": self.status,
            "total_value": float(self.total_value),
            "line_count": len(self.lines),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_lines:
            result["lines"] = [l.to_dict() for l in self.lines]

        return result


class GoodsReceiptLine(Base):
    """Goods receipt line."""

    __tablename__ = "goods_receipt_lines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(PGUUID(as_uuid=True), ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)

    # Reference to PO line
    order_line_id = Column(PGUUID(as_uuid=True), ForeignKey("purchase_order_lines.id"))

    # Product
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # Quantity
    quantity_ordered = Column(Numeric(18, 4))  # From PO
    quantity_received = Column(Numeric(18, 4), nullable=False)
    uom_id = Column(PGUUID(as_uuid=True), ForeignKey("units_of_measure.id"))

    # Location
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id"))

    # Lot/Serial
    lot_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_lots.id"))
    lot_number = Column(String(50))  # For creating new lot
    expiry_date = Column(Date)
    serial_numbers = Column(ARRAY(String(50)))

    # Cost
    unit_cost = Column(Numeric(18, 6))

    # Quality
    quality_status = Column(String(20), default=QualityStatusEnum.ACCEPTED.value)
    rejection_reason = Column(Text)

    # Link to inventory movement
    movement_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_movements.id"))

    notes = Column(Text)

    # Relationships
    receipt = relationship("GoodsReceipt", back_populates="lines")
    order_line = relationship("PurchaseOrderLine")
    product = relationship("Product")
    location = relationship("WarehouseLocation")
    lot = relationship("StockLot")
    uom = relationship("UnitOfMeasure")

    __table_args__ = (
        UniqueConstraint("receipt_id", "line_number", name="uq_receipt_line"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "line_number": self.line_number,
            "order_line_id": str(self.order_line_id) if self.order_line_id else None,
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "quantity_ordered": float(self.quantity_ordered) if self.quantity_ordered else None,
            "quantity_received": float(self.quantity_received),
            "uom": self.uom.code if self.uom else None,
            "location_id": str(self.location_id) if self.location_id else None,
            "location_code": self.location.code if self.location else None,
            "lot_id": str(self.lot_id) if self.lot_id else None,
            "lot_number": self.lot_number,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "serial_numbers": self.serial_numbers,
            "unit_cost": float(self.unit_cost) if self.unit_cost else 0,
            "line_value": float(self.quantity_received * (self.unit_cost or Decimal("0"))),
            "quality_status": self.quality_status,
            "rejection_reason": self.rejection_reason,
            "movement_id": str(self.movement_id) if self.movement_id else None,
        }
