"""
Stock Models
Stock levels, lots, and serial numbers
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, ForeignKey,
    Numeric, Integer, Text, Index, Computed
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class LotStatusEnum(str, Enum):
    """Lot status."""
    AVAILABLE = "available"
    QUARANTINE = "quarantine"
    EXPIRED = "expired"
    CONSUMED = "consumed"


class SerialStatusEnum(str, Enum):
    """Serial number status."""
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    SCRAPPED = "scrapped"
    IN_REPAIR = "in_repair"


class StockLot(Base):
    """Lot/Batch tracking for products."""

    __tablename__ = "stock_lots"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    lot_number = Column(String(100), nullable=False)

    # Dates
    manufacture_date = Column(Date)
    expiry_date = Column(Date)

    # Supplier info
    supplier_id = Column(PGUUID(as_uuid=True))
    supplier_lot = Column(String(100))

    # Status
    status = Column(String(20), default=LotStatusEnum.AVAILABLE.value)

    # Additional attributes (optional)
    attributes = Column(Text)  # JSON for custom attributes

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    product = relationship("Product")
    serials = relationship("StockSerial", back_populates="lot")
    stock_levels = relationship("StockLevel", back_populates="lot")

    __table_args__ = (
        Index("idx_lot_customer_product_number", "customer_id", "product_id", "lot_number", unique=True),
        Index("idx_lot_expiry", "expiry_date"),
    )

    @property
    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date

    @property
    def days_until_expiry(self) -> Optional[int]:
        if not self.expiry_date:
            return None
        delta = self.expiry_date - date.today()
        return delta.days

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "lot_number": self.lot_number,
            "manufacture_date": self.manufacture_date.isoformat() if self.manufacture_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "is_expired": self.is_expired,
            "days_until_expiry": self.days_until_expiry,
            "supplier_id": str(self.supplier_id) if self.supplier_id else None,
            "supplier_lot": self.supplier_lot,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StockSerial(Base):
    """Serial number tracking for products."""

    __tablename__ = "stock_serials"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    lot_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_lots.id"))

    serial_number = Column(String(100), nullable=False)

    # Current location
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id"))

    # Status
    status = Column(String(20), default=SerialStatusEnum.AVAILABLE.value)

    # Warranty
    warranty_start = Column(Date)
    warranty_end = Column(Date)

    # Customer (if sold)
    sold_to_customer_id = Column(PGUUID(as_uuid=True))
    sold_date = Column(Date)

    # Additional info
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    product = relationship("Product")
    lot = relationship("StockLot", back_populates="serials")
    warehouse = relationship("Warehouse")
    location = relationship("WarehouseLocation")

    __table_args__ = (
        Index("idx_serial_customer_product_number", "customer_id", "product_id", "serial_number", unique=True),
        Index("idx_serial_status", "status"),
    )

    @property
    def is_warranty_active(self) -> bool:
        if not self.warranty_end:
            return False
        return date.today() <= self.warranty_end

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "lot_id": str(self.lot_id) if self.lot_id else None,
            "lot_number": self.lot.lot_number if self.lot else None,
            "serial_number": self.serial_number,
            "warehouse_id": str(self.warehouse_id) if self.warehouse_id else None,
            "location_id": str(self.location_id) if self.location_id else None,
            "status": self.status,
            "warranty_start": self.warranty_start.isoformat() if self.warranty_start else None,
            "warranty_end": self.warranty_end.isoformat() if self.warranty_end else None,
            "is_warranty_active": self.is_warranty_active,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StockLevel(Base):
    """Current stock level by product/location."""

    __tablename__ = "stock_levels"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id"), nullable=False)
    lot_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_lots.id"))

    # Quantities
    quantity_on_hand = Column(Numeric(18, 4), nullable=False, default=0)
    quantity_reserved = Column(Numeric(18, 4), nullable=False, default=0)
    quantity_available = Column(
        Numeric(18, 4),
        Computed("quantity_on_hand - quantity_reserved"),
        nullable=False
    )

    # Valuation
    unit_cost = Column(Numeric(18, 6), default=0)
    total_value = Column(
        Numeric(18, 4),
        Computed("quantity_on_hand * unit_cost")
    )

    # Tracking
    last_movement_date = Column(DateTime)
    last_count_date = Column(DateTime)

    # Relationships
    product = relationship("Product", back_populates="stock_levels")
    warehouse = relationship("Warehouse", back_populates="stock_levels")
    location = relationship("WarehouseLocation", back_populates="stock_levels")
    lot = relationship("StockLot", back_populates="stock_levels")

    __table_args__ = (
        Index(
            "idx_stock_level_unique",
            "customer_id", "product_id", "warehouse_id", "location_id", "lot_id",
            unique=True
        ),
        Index("idx_stock_product", "product_id"),
        Index("idx_stock_warehouse", "warehouse_id"),
        Index("idx_stock_location", "location_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "warehouse_id": str(self.warehouse_id),
            "warehouse_code": self.warehouse.code if self.warehouse else None,
            "location_id": str(self.location_id),
            "location_code": self.location.code if self.location else None,
            "lot_id": str(self.lot_id) if self.lot_id else None,
            "lot_number": self.lot.lot_number if self.lot else None,
            "quantity_on_hand": float(self.quantity_on_hand),
            "quantity_reserved": float(self.quantity_reserved),
            "quantity_available": float(self.quantity_available) if self.quantity_available else float(self.quantity_on_hand - self.quantity_reserved),
            "unit_cost": float(self.unit_cost) if self.unit_cost else 0,
            "total_value": float(self.total_value) if self.total_value else 0,
            "last_movement_date": self.last_movement_date.isoformat() if self.last_movement_date else None,
        }


class StockValuationLayer(Base):
    """Valuation layer for FIFO/LIFO tracking."""

    __tablename__ = "stock_valuation_layers"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    lot_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_lots.id"))

    # Layer info
    layer_date = Column(DateTime, nullable=False)
    movement_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_movements.id"))

    # Quantities
    quantity_initial = Column(Numeric(18, 4), nullable=False)
    quantity_remaining = Column(Numeric(18, 4), nullable=False)

    # Cost
    unit_cost = Column(Numeric(18, 6), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product")
    warehouse = relationship("Warehouse")

    __table_args__ = (
        Index("idx_valuation_product_warehouse", "product_id", "warehouse_id"),
        Index("idx_valuation_remaining", "quantity_remaining"),
    )

    @property
    def remaining_value(self) -> Decimal:
        return self.quantity_remaining * self.unit_cost

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "warehouse_id": str(self.warehouse_id),
            "lot_id": str(self.lot_id) if self.lot_id else None,
            "layer_date": self.layer_date.isoformat() if self.layer_date else None,
            "movement_id": str(self.movement_id) if self.movement_id else None,
            "quantity_initial": float(self.quantity_initial),
            "quantity_remaining": float(self.quantity_remaining),
            "unit_cost": float(self.unit_cost),
            "remaining_value": float(self.remaining_value),
        }
