"""
Product and Category Models
Core inventory item definitions
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, ForeignKey,
    Numeric, Integer, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship, Session

from app.database import Base


class ProductTypeEnum(str, Enum):
    """Product types."""
    STOCKABLE = "stockable"      # Track inventory
    CONSUMABLE = "consumable"    # No inventory tracking
    SERVICE = "service"          # No physical product


class ValuationMethodEnum(str, Enum):
    """Inventory valuation methods."""
    FIFO = "fifo"
    LIFO = "lifo"
    AVERAGE = "average"
    STANDARD = "standard"


class UOMCategoryEnum(str, Enum):
    """Unit of measure categories."""
    UNIT = "unit"
    WEIGHT = "weight"
    VOLUME = "volume"
    LENGTH = "length"
    TIME = "time"
    AREA = "area"


class UnitOfMeasure(Base):
    """Unit of measure for products."""

    __tablename__ = "units_of_measure"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    code = Column(String(10), nullable=False)  # EA, KG, LB, BOX
    name = Column(String(50), nullable=False)
    category = Column(String(20))  # UOMCategoryEnum

    # Conversion to base UOM
    base_uom_id = Column(PGUUID(as_uuid=True), ForeignKey("units_of_measure.id"))
    conversion_factor = Column(Numeric(18, 8), default=1)  # 1 BOX = 12 EA

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    base_uom = relationship("UnitOfMeasure", remote_side=[id])

    __table_args__ = (
        Index("idx_uom_customer_code", "customer_id", "code", unique=True),
    )

    def convert_to_base(self, quantity: Decimal) -> Decimal:
        """Convert quantity to base UOM."""
        return quantity * Decimal(str(self.conversion_factor))

    def convert_from_base(self, quantity: Decimal) -> Decimal:
        """Convert quantity from base UOM."""
        if self.conversion_factor == 0:
            return quantity
        return quantity / Decimal(str(self.conversion_factor))

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "base_uom_id": str(self.base_uom_id) if self.base_uom_id else None,
            "conversion_factor": float(self.conversion_factor),
            "is_active": self.is_active,
        }


class ProductCategory(Base):
    """Hierarchical product categories."""

    __tablename__ = "product_categories"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    parent_id = Column(PGUUID(as_uuid=True), ForeignKey("product_categories.id"))

    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Hierarchy
    level = Column(Integer, default=0)
    path = Column(String(500))  # Materialized path: /1/2/3/

    # Defaults for products
    default_uom_id = Column(PGUUID(as_uuid=True), ForeignKey("units_of_measure.id"))
    default_valuation_method = Column(String(20), default=ValuationMethodEnum.FIFO.value)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent = relationship("ProductCategory", remote_side=[id], backref="children")
    default_uom = relationship("UnitOfMeasure")
    products = relationship("Product", back_populates="category")

    __table_args__ = (
        Index("idx_category_customer_code", "customer_id", "code", unique=True),
    )

    def to_dict(self, include_children: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "level": self.level,
            "path": self.path,
            "default_valuation_method": self.default_valuation_method,
            "is_active": self.is_active,
        }

        if include_children and self.children:
            result["children"] = [c.to_dict(include_children=True) for c in self.children]

        return result


class Product(Base):
    """Product / Inventory Item."""

    __tablename__ = "products"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Identification
    sku = Column(String(50), nullable=False)
    barcode = Column(String(50))
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Classification
    category_id = Column(PGUUID(as_uuid=True), ForeignKey("product_categories.id"))
    product_type = Column(String(20), nullable=False, default=ProductTypeEnum.STOCKABLE.value)

    # Units
    uom_id = Column(PGUUID(as_uuid=True), ForeignKey("units_of_measure.id"), nullable=False)
    purchase_uom_id = Column(PGUUID(as_uuid=True), ForeignKey("units_of_measure.id"))

    # Pricing
    standard_cost = Column(Numeric(18, 4), default=0)
    list_price = Column(Numeric(18, 4), default=0)

    # Inventory Settings
    track_inventory = Column(Boolean, default=True)
    track_lots = Column(Boolean, default=False)
    track_serials = Column(Boolean, default=False)
    valuation_method = Column(String(20), default=ValuationMethodEnum.FIFO.value)

    # Reorder
    reorder_point = Column(Numeric(18, 4), default=0)
    reorder_quantity = Column(Numeric(18, 4), default=0)
    safety_stock = Column(Numeric(18, 4), default=0)
    lead_time_days = Column(Integer, default=0)

    # Physical Attributes
    weight = Column(Numeric(10, 4))
    weight_uom = Column(String(10))
    length = Column(Numeric(10, 4))
    width = Column(Numeric(10, 4))
    height = Column(Numeric(10, 4))
    dimension_uom = Column(String(10))

    # Accounting Integration
    inventory_account_id = Column(PGUUID(as_uuid=True))  # Asset
    cogs_account_id = Column(PGUUID(as_uuid=True))       # Expense
    revenue_account_id = Column(PGUUID(as_uuid=True))    # Revenue

    # Media
    image_url = Column(String(500))

    # Status
    is_active = Column(Boolean, default=True)
    is_purchasable = Column(Boolean, default=True)
    is_sellable = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    uom = relationship("UnitOfMeasure", foreign_keys=[uom_id])
    purchase_uom = relationship("UnitOfMeasure", foreign_keys=[purchase_uom_id])
    stock_levels = relationship("StockLevel", back_populates="product")

    __table_args__ = (
        Index("idx_product_customer_sku", "customer_id", "sku", unique=True),
        Index("idx_product_barcode", "barcode"),
        Index("idx_product_category", "category_id"),
    )

    @property
    def is_stockable(self) -> bool:
        return self.product_type == ProductTypeEnum.STOCKABLE.value

    @property
    def requires_lot(self) -> bool:
        return self.track_lots

    @property
    def requires_serial(self) -> bool:
        return self.track_serials

    def to_dict(self, include_stock: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "sku": self.sku,
            "barcode": self.barcode,
            "name": self.name,
            "description": self.description,
            "category_id": str(self.category_id) if self.category_id else None,
            "category": self.category.to_dict() if self.category else None,
            "product_type": self.product_type,
            "uom_id": str(self.uom_id),
            "uom": self.uom.to_dict() if self.uom else None,
            "purchase_uom_id": str(self.purchase_uom_id) if self.purchase_uom_id else None,
            "standard_cost": float(self.standard_cost) if self.standard_cost else 0,
            "list_price": float(self.list_price) if self.list_price else 0,
            "track_inventory": self.track_inventory,
            "track_lots": self.track_lots,
            "track_serials": self.track_serials,
            "valuation_method": self.valuation_method,
            "reorder_point": float(self.reorder_point) if self.reorder_point else 0,
            "reorder_quantity": float(self.reorder_quantity) if self.reorder_quantity else 0,
            "safety_stock": float(self.safety_stock) if self.safety_stock else 0,
            "lead_time_days": self.lead_time_days,
            "weight": float(self.weight) if self.weight else None,
            "weight_uom": self.weight_uom,
            "dimensions": {
                "length": float(self.length) if self.length else None,
                "width": float(self.width) if self.width else None,
                "height": float(self.height) if self.height else None,
                "uom": self.dimension_uom,
            } if any([self.length, self.width, self.height]) else None,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "is_purchasable": self.is_purchasable,
            "is_sellable": self.is_sellable,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        return result

    def to_summary(self) -> dict:
        """Minimal representation for lists."""
        return {
            "id": str(self.id),
            "sku": self.sku,
            "name": self.name,
            "barcode": self.barcode,
            "category": self.category.name if self.category else None,
            "uom": self.uom.code if self.uom else None,
            "list_price": float(self.list_price) if self.list_price else 0,
            "is_active": self.is_active,
        }
