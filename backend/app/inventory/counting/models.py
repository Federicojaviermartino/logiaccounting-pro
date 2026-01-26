"""Inventory Count Models"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Numeric, Integer, Text, Index, Computed
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class CountTypeEnum(str, Enum):
    FULL = "full"
    CYCLE = "cycle"
    SPOT = "spot"


class CountStatusEnum(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    POSTED = "posted"


class InventoryCount(Base):
    __tablename__ = "inventory_counts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    count_number = Column(String(30), nullable=False)
    count_type = Column(String(30), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)

    include_all_products = Column(Boolean, default=False)
    category_ids = Column(ARRAY(PGUUID(as_uuid=True)))
    location_ids = Column(ARRAY(PGUUID(as_uuid=True)))

    scheduled_date = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    status = Column(String(20), default=CountStatusEnum.DRAFT.value)

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    approved_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime)

    total_lines = Column(Integer, default=0)
    lines_counted = Column(Integer, default=0)
    lines_with_variance = Column(Integer, default=0)
    total_variance_value = Column(Numeric(18, 4))

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    warehouse = relationship("Warehouse")
    lines = relationship("InventoryCountLine", back_populates="count", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_count_customer_number", "customer_id", "count_number", unique=True),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "count_number": self.count_number,
            "count_type": self.count_type,
            "warehouse_id": str(self.warehouse_id),
            "warehouse_name": self.warehouse.name if self.warehouse else None,
            "status": self.status,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_lines": self.total_lines,
            "lines_counted": self.lines_counted,
            "lines_with_variance": self.lines_with_variance,
            "total_variance_value": float(self.total_variance_value) if self.total_variance_value else 0,
            "progress_percent": (self.lines_counted / self.total_lines * 100) if self.total_lines > 0 else 0,
        }


class InventoryCountLine(Base):
    __tablename__ = "inventory_count_lines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    count_id = Column(PGUUID(as_uuid=True), ForeignKey("inventory_counts.id", ondelete="CASCADE"), nullable=False)

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    location_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id"), nullable=False)
    lot_id = Column(PGUUID(as_uuid=True), ForeignKey("stock_lots.id"))

    system_quantity = Column(Numeric(18, 4), nullable=False)
    system_unit_cost = Column(Numeric(18, 6))

    counted_quantity = Column(Numeric(18, 4))
    counted_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    counted_at = Column(DateTime)

    variance_quantity = Column(Numeric(18, 4), Computed("counted_quantity - system_quantity"))
    variance_value = Column(Numeric(18, 4))

    recount_quantity = Column(Numeric(18, 4))
    recounted_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    recounted_at = Column(DateTime)

    status = Column(String(20), default="pending")
    notes = Column(Text)

    count = relationship("InventoryCount", back_populates="lines")
    product = relationship("Product")
    location = relationship("WarehouseLocation")
    lot = relationship("StockLot")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "location_id": str(self.location_id),
            "location_code": self.location.code if self.location else None,
            "lot_id": str(self.lot_id) if self.lot_id else None,
            "lot_number": self.lot.lot_number if self.lot else None,
            "system_quantity": float(self.system_quantity),
            "counted_quantity": float(self.counted_quantity) if self.counted_quantity is not None else None,
            "variance_quantity": float(self.variance_quantity) if self.variance_quantity else 0,
            "variance_value": float(self.variance_value) if self.variance_value else 0,
            "status": self.status,
        }
