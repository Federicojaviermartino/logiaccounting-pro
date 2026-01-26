"""
Stock Movement Models
All inventory transactions
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class MovementTypeEnum(str, Enum):
    RECEIPT = "receipt"
    ISSUE = "issue"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    SCRAP = "scrap"
    RETURN_SUPPLIER = "return_supplier"


class MovementStatusEnum(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    DONE = "done"
    CANCELLED = "cancelled"


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    movement_number = Column(String(30), nullable=False)
    movement_type = Column(String(30), nullable=False)
    movement_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    lot_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_lots.id"))
    serial_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_serials.id"))

    source_warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))
    source_location_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id"))
    dest_warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))
    dest_location_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id"))

    quantity = Column(Numeric(18, 4), nullable=False)
    uom_id = Column(PGUUID(as_uuid=True), ForeignKey("units_of_measure.id"), nullable=False)
    unit_cost = Column(Numeric(18, 6), default=0)
    total_cost = Column(Numeric(18, 4))

    reference_type = Column(String(50))
    reference_id = Column(PGUUID(as_uuid=True))
    reference_number = Column(String(50))

    status = Column(String(20), default=MovementStatusEnum.DRAFT.value)
    reason = Column(Text)
    notes = Column(Text)

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    confirmed_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    confirmed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")
    lot = relationship("StockLot")
    source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id])
    dest_warehouse = relationship("Warehouse", foreign_keys=[dest_warehouse_id])
    source_location = relationship("WarehouseLocation", foreign_keys=[source_location_id])
    dest_location = relationship("WarehouseLocation", foreign_keys=[dest_location_id])
    uom = relationship("UnitOfMeasure")

    __table_args__ = (
        Index("idx_movement_customer_number", "customer_id", "movement_number", unique=True),
        Index("idx_movement_product", "product_id"),
        Index("idx_movement_date", "movement_date"),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "movement_number": self.movement_number,
            "movement_type": self.movement_type,
            "movement_date": self.movement_date.isoformat() if self.movement_date else None,
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "lot_id": str(self.lot_id) if self.lot_id else None,
            "source_warehouse": self.source_warehouse.code if self.source_warehouse else None,
            "source_location": self.source_location.code if self.source_location else None,
            "dest_warehouse": self.dest_warehouse.code if self.dest_warehouse else None,
            "dest_location": self.dest_location.code if self.dest_location else None,
            "quantity": float(self.quantity),
            "unit_cost": float(self.unit_cost) if self.unit_cost else 0,
            "total_cost": float(self.total_cost) if self.total_cost else 0,
            "status": self.status,
            "reference_number": self.reference_number,
        }
