"""Reorder Rule and Requisition Models"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Numeric, Integer, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class RequisitionStatusEnum(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class ReorderRule(Base):
    __tablename__ = "reorder_rules"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))

    reorder_point = Column(Numeric(18, 4), nullable=False)
    safety_stock = Column(Numeric(18, 4), default=0)

    min_order_quantity = Column(Numeric(18, 4), nullable=False)
    max_order_quantity = Column(Numeric(18, 4))
    order_multiple = Column(Numeric(18, 4), default=1)

    preferred_supplier_id = Column(PGUUID(as_uuid=True))
    lead_time_days = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    auto_create_requisition = Column(Boolean, default=False)

    last_triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")
    warehouse = relationship("Warehouse")

    __table_args__ = (
        Index("idx_reorder_rule_product", "customer_id", "product_id", "warehouse_id", unique=True),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "warehouse_id": str(self.warehouse_id) if self.warehouse_id else None,
            "reorder_point": float(self.reorder_point),
            "safety_stock": float(self.safety_stock) if self.safety_stock else 0,
            "min_order_quantity": float(self.min_order_quantity),
            "max_order_quantity": float(self.max_order_quantity) if self.max_order_quantity else None,
            "order_multiple": float(self.order_multiple) if self.order_multiple else 1,
            "lead_time_days": self.lead_time_days,
            "is_active": self.is_active,
            "auto_create_requisition": self.auto_create_requisition,
        }


class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    requisition_number = Column(String(30), nullable=False)

    source_type = Column(String(30), nullable=False)  # manual, reorder_rule
    reorder_rule_id = Column(PGUUID(as_uuid=True), ForeignKey("reorder_rules.id"))

    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))

    quantity_required = Column(Numeric(18, 4), nullable=False)
    quantity_ordered = Column(Numeric(18, 4), default=0)

    supplier_id = Column(PGUUID(as_uuid=True))
    estimated_cost = Column(Numeric(18, 4))

    required_date = Column(Date)

    status = Column(String(20), default=RequisitionStatusEnum.PENDING.value)

    purchase_order_id = Column(PGUUID(as_uuid=True))

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    approved_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")
    warehouse = relationship("Warehouse")
    reorder_rule = relationship("ReorderRule")

    __table_args__ = (
        Index("idx_requisition_number", "customer_id", "requisition_number", unique=True),
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "requisition_number": self.requisition_number,
            "source_type": self.source_type,
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "warehouse_id": str(self.warehouse_id) if self.warehouse_id else None,
            "quantity_required": float(self.quantity_required),
            "quantity_ordered": float(self.quantity_ordered) if self.quantity_ordered else 0,
            "estimated_cost": float(self.estimated_cost) if self.estimated_cost else None,
            "required_date": self.required_date.isoformat() if self.required_date else None,
            "status": self.status,
        }
