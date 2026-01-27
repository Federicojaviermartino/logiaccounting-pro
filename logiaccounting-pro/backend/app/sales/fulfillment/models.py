"""
Fulfillment Models
Pick lists and shipments for order fulfillment
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


class PickListStatusEnum(str, Enum):
    """Pick list status."""
    DRAFT = "draft"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PickLineStatusEnum(str, Enum):
    """Pick line status."""
    PENDING = "pending"
    PICKED = "picked"
    SHORT = "short"
    CANCELLED = "cancelled"


class ShipmentStatusEnum(str, Enum):
    """Shipment status."""
    DRAFT = "draft"
    PACKED = "packed"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PickList(Base):
    """Pick list for warehouse operations."""

    __tablename__ = "pick_lists"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    pick_number = Column(String(30), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)

    pick_date = Column(Date, default=date.today)
    due_date = Column(Date)

    status = Column(String(20), default=PickListStatusEnum.DRAFT.value)

    assigned_to = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    assigned_at = Column(DateTime)

    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    total_lines = Column(Integer, default=0)
    lines_picked = Column(Integer, default=0)
    lines_short = Column(Integer, default=0)

    notes = Column(Text)

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = relationship("Warehouse")
    lines = relationship("PickListLine", back_populates="pick_list", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("customer_id", "pick_number", name="uq_pick_number"),
        Index("idx_pick_warehouse", "warehouse_id"),
        Index("idx_pick_status", "status"),
        Index("idx_pick_date", "pick_date"),
    )

    @property
    def is_editable(self) -> bool:
        return self.status in [
            PickListStatusEnum.DRAFT.value,
            PickListStatusEnum.RELEASED.value
        ]

    @property
    def can_complete(self) -> bool:
        return (
            self.status == PickListStatusEnum.IN_PROGRESS.value and
            all(l.status != PickLineStatusEnum.PENDING.value for l in self.lines)
        )

    def update_counts(self):
        """Update line counts."""
        self.total_lines = len(self.lines)
        self.lines_picked = sum(
            1 for l in self.lines if l.status == PickLineStatusEnum.PICKED.value
        )
        self.lines_short = sum(
            1 for l in self.lines if l.status == PickLineStatusEnum.SHORT.value
        )

    def to_dict(self, include_lines: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "pick_number": self.pick_number,
            "warehouse_id": str(self.warehouse_id),
            "warehouse_name": self.warehouse.name if self.warehouse else None,
            "pick_date": self.pick_date.isoformat() if self.pick_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_lines": self.total_lines,
            "lines_picked": self.lines_picked,
            "lines_short": self.lines_short,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_lines:
            result["lines"] = [l.to_dict() for l in self.lines]

        return result


class PickListLine(Base):
    """Pick list line item."""

    __tablename__ = "pick_list_lines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pick_list_id = Column(PGUUID(as_uuid=True), ForeignKey("pick_lists.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)

    order_id = Column(PGUUID(as_uuid=True), ForeignKey("sales_orders.id"), nullable=False)
    order_line_id = Column(PGUUID(as_uuid=True), ForeignKey("sales_order_lines.id"), nullable=False)
    allocation_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_allocations.id"))

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id"))
    lot_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_lots.id"))

    quantity_requested = Column(Numeric(18, 4), nullable=False)
    quantity_picked = Column(Numeric(18, 4), default=0)

    status = Column(String(20), default=PickLineStatusEnum.PENDING.value)

    picked_at = Column(DateTime)
    picked_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    notes = Column(Text)

    pick_list = relationship("PickList", back_populates="lines")
    order = relationship("SalesOrder")
    order_line = relationship("SalesOrderLine")
    product = relationship("Product")
    location = relationship("WarehouseLocation")
    lot = relationship("StockLot")

    __table_args__ = (
        UniqueConstraint("pick_list_id", "line_number", name="uq_pick_line"),
        Index("idx_pick_line_order", "order_id"),
        Index("idx_pick_line_product", "product_id"),
    )

    @property
    def quantity_short(self) -> Decimal:
        """Quantity not picked."""
        return (self.quantity_requested or Decimal("0")) - (self.quantity_picked or Decimal("0"))

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "line_number": self.line_number,
            "order_id": str(self.order_id),
            "order_number": self.order.order_number if self.order else None,
            "order_line_id": str(self.order_line_id),
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "location_id": str(self.location_id) if self.location_id else None,
            "location_code": self.location.code if self.location else None,
            "lot_id": str(self.lot_id) if self.lot_id else None,
            "lot_number": self.lot.lot_number if self.lot else None,
            "quantity_requested": float(self.quantity_requested),
            "quantity_picked": float(self.quantity_picked) if self.quantity_picked else 0,
            "quantity_short": float(self.quantity_short),
            "status": self.status,
            "picked_at": self.picked_at.isoformat() if self.picked_at else None,
            "notes": self.notes,
        }


class Shipment(Base):
    """Shipment for delivering orders."""

    __tablename__ = "shipments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    shipment_number = Column(String(30), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)

    ship_date = Column(Date)
    expected_delivery = Column(Date)
    actual_delivery = Column(Date)

    carrier = Column(String(100))
    service_type = Column(String(50))
    tracking_number = Column(String(100))
    tracking_url = Column(String(500))

    ship_to_name = Column(String(200))
    ship_to_address = Column(Text)
    ship_to_city = Column(String(100))
    ship_to_state = Column(String(50))
    ship_to_postal = Column(String(20))
    ship_to_country = Column(String(50))
    ship_to_phone = Column(String(30))

    weight = Column(Numeric(18, 4))
    weight_uom = Column(String(10), default="LB")
    dimensions = Column(String(50))
    package_count = Column(Integer, default=1)

    shipping_cost = Column(Numeric(18, 4), default=0)
    insurance_cost = Column(Numeric(18, 4), default=0)

    status = Column(String(20), default=ShipmentStatusEnum.DRAFT.value)

    shipped_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    shipped_at = Column(DateTime)

    notes = Column(Text)
    special_instructions = Column(Text)

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = relationship("Warehouse")
    lines = relationship("ShipmentLine", back_populates="shipment", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("customer_id", "shipment_number", name="uq_shipment_number"),
        Index("idx_shipment_warehouse", "warehouse_id"),
        Index("idx_shipment_status", "status"),
        Index("idx_shipment_date", "ship_date"),
        Index("idx_shipment_tracking", "tracking_number"),
    )

    @property
    def is_editable(self) -> bool:
        return self.status in [
            ShipmentStatusEnum.DRAFT.value,
            ShipmentStatusEnum.PACKED.value
        ]

    @property
    def can_ship(self) -> bool:
        return (
            self.status == ShipmentStatusEnum.PACKED.value and
            len(self.lines) > 0
        )

    @property
    def full_address(self) -> str:
        """Full formatted shipping address."""
        parts = [self.ship_to_name]
        if self.ship_to_address:
            parts.append(self.ship_to_address)
        city_line = ", ".join(filter(None, [
            self.ship_to_city,
            self.ship_to_state,
            self.ship_to_postal
        ]))
        if city_line:
            parts.append(city_line)
        if self.ship_to_country:
            parts.append(self.ship_to_country)
        return "\n".join(filter(None, parts))

    def to_dict(self, include_lines: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "shipment_number": self.shipment_number,
            "warehouse_id": str(self.warehouse_id),
            "warehouse_name": self.warehouse.name if self.warehouse else None,
            "ship_date": self.ship_date.isoformat() if self.ship_date else None,
            "expected_delivery": self.expected_delivery.isoformat() if self.expected_delivery else None,
            "actual_delivery": self.actual_delivery.isoformat() if self.actual_delivery else None,
            "carrier": self.carrier,
            "service_type": self.service_type,
            "tracking_number": self.tracking_number,
            "tracking_url": self.tracking_url,
            "ship_to_name": self.ship_to_name,
            "ship_to_address": self.ship_to_address,
            "full_address": self.full_address,
            "weight": float(self.weight) if self.weight else None,
            "weight_uom": self.weight_uom,
            "package_count": self.package_count,
            "shipping_cost": float(self.shipping_cost) if self.shipping_cost else 0,
            "insurance_cost": float(self.insurance_cost) if self.insurance_cost else 0,
            "status": self.status,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "notes": self.notes,
            "line_count": len(self.lines),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_lines:
            result["lines"] = [l.to_dict() for l in self.lines]

        return result


class ShipmentLine(Base):
    """Shipment line item."""

    __tablename__ = "shipment_lines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(PGUUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)

    order_id = Column(PGUUID(as_uuid=True), ForeignKey("sales_orders.id"), nullable=False)
    order_line_id = Column(PGUUID(as_uuid=True), ForeignKey("sales_order_lines.id"), nullable=False)
    pick_line_id = Column(PGUUID(as_uuid=True), ForeignKey("pick_list_lines.id"))

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    lot_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_lots.id"))
    serial_numbers = Column(Text)

    quantity_shipped = Column(Numeric(18, 4), nullable=False)

    shipment = relationship("Shipment", back_populates="lines")
    order = relationship("SalesOrder")
    order_line = relationship("SalesOrderLine")
    product = relationship("Product")
    lot = relationship("StockLot")

    __table_args__ = (
        UniqueConstraint("shipment_id", "line_number", name="uq_shipment_line"),
        Index("idx_shipment_line_order", "order_id"),
        Index("idx_shipment_line_product", "product_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "line_number": self.line_number,
            "order_id": str(self.order_id),
            "order_number": self.order.order_number if self.order else None,
            "order_line_id": str(self.order_line_id),
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "lot_id": str(self.lot_id) if self.lot_id else None,
            "lot_number": self.lot.lot_number if self.lot else None,
            "serial_numbers": self.serial_numbers,
            "quantity_shipped": float(self.quantity_shipped),
        }
