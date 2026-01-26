"""
Warehouse and Location Models
Physical storage structure definitions
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey,
    Numeric, Integer, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class LocationTypeEnum(str, Enum):
    """Location types."""
    INTERNAL = "internal"       # Standard storage
    CUSTOMER = "customer"       # Customer locations (for consignment)
    SUPPLIER = "supplier"       # Supplier locations
    PRODUCTION = "production"   # Production/manufacturing
    TRANSIT = "transit"         # In-transit locations
    VIEW = "view"              # Virtual location for grouping
    SCRAP = "scrap"            # Scrap/waste location
    ADJUSTMENT = "adjustment"  # Inventory adjustment location


class ZoneTypeEnum(str, Enum):
    """Warehouse zone types."""
    RECEIVING = "receiving"
    STORAGE = "storage"
    PICKING = "picking"
    PACKING = "packing"
    SHIPPING = "shipping"
    QUARANTINE = "quarantine"
    RETURNS = "returns"


class Warehouse(Base):
    """Warehouse / Distribution Center."""

    __tablename__ = "warehouses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)

    # Address
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(2))  # ISO country code

    # Contact
    manager_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    phone = Column(String(30))
    email = Column(String(200))

    # Coordinates for mapping
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))

    # Settings
    is_active = Column(Boolean, default=True)
    allow_negative_stock = Column(Boolean, default=False)

    # Default accounts for adjustments
    inventory_account_id = Column(PGUUID(as_uuid=True))
    adjustment_account_id = Column(PGUUID(as_uuid=True))

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    zones = relationship("WarehouseZone", back_populates="warehouse", cascade="all, delete-orphan")
    locations = relationship("WarehouseLocation", back_populates="warehouse", cascade="all, delete-orphan")
    stock_levels = relationship("StockLevel", back_populates="warehouse")

    __table_args__ = (
        Index("idx_warehouse_customer_code", "customer_id", "code", unique=True),
    )

    def to_dict(self, include_locations: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
            },
            "phone": self.phone,
            "email": self.email,
            "coordinates": {
                "latitude": float(self.latitude) if self.latitude else None,
                "longitude": float(self.longitude) if self.longitude else None,
            } if self.latitude else None,
            "is_active": self.is_active,
            "allow_negative_stock": self.allow_negative_stock,
            "manager_id": str(self.manager_id) if self.manager_id else None,
            "zones_count": len(self.zones) if self.zones else 0,
            "locations_count": len(self.locations) if self.locations else 0,
        }

        if include_locations and self.zones:
            result["zones"] = [z.to_dict(include_locations=True) for z in self.zones]

        return result


class WarehouseZone(Base):
    """Warehouse zone for organizing locations."""

    __tablename__ = "warehouse_zones"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)

    code = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    zone_type = Column(String(30))  # ZoneTypeEnum
    description = Column(Text)

    # Settings
    is_active = Column(Boolean, default=True)
    sequence = Column(Integer, default=0)  # For ordering

    # Relationships
    warehouse = relationship("Warehouse", back_populates="zones")
    locations = relationship("WarehouseLocation", back_populates="zone")

    __table_args__ = (
        Index("idx_zone_warehouse_code", "warehouse_id", "code", unique=True),
    )

    def to_dict(self, include_locations: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "warehouse_id": str(self.warehouse_id),
            "code": self.code,
            "name": self.name,
            "zone_type": self.zone_type,
            "description": self.description,
            "is_active": self.is_active,
            "sequence": self.sequence,
            "locations_count": len(self.locations) if self.locations else 0,
        }

        if include_locations and self.locations:
            result["locations"] = [l.to_dict() for l in self.locations]

        return result


class WarehouseLocation(Base):
    """Storage location / bin within a warehouse."""

    __tablename__ = "warehouse_locations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    zone_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouse_zones.id"))
    parent_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouse_locations.id"))

    # Identification
    code = Column(String(50), nullable=False)  # A-01-01-01 (Aisle-Rack-Level-Bin)
    name = Column(String(100))
    barcode = Column(String(50))

    # Type
    location_type = Column(String(30), nullable=False, default=LocationTypeEnum.INTERNAL.value)

    # Capacity constraints
    max_weight = Column(Numeric(10, 2))       # in KG
    max_volume = Column(Numeric(10, 4))       # in cubic meters
    max_items = Column(Integer)               # Max number of items/pallets

    # Settings
    is_active = Column(Boolean, default=True)
    is_scrap_location = Column(Boolean, default=False)
    is_return_location = Column(Boolean, default=False)
    is_pickable = Column(Boolean, default=True)  # Can be picked from
    is_receivable = Column(Boolean, default=True)  # Can receive stock

    # Hierarchy
    path = Column(String(500))  # Materialized path
    level = Column(Integer, default=0)

    # Relationships
    warehouse = relationship("Warehouse", back_populates="locations")
    zone = relationship("WarehouseZone", back_populates="locations")
    parent = relationship("WarehouseLocation", remote_side=[id], backref="children")
    stock_levels = relationship("StockLevel", back_populates="location")

    __table_args__ = (
        Index("idx_location_warehouse_code", "warehouse_id", "code", unique=True),
        Index("idx_location_barcode", "barcode"),
        Index("idx_location_zone", "zone_id"),
    )

    @property
    def full_code(self) -> str:
        """Get full location code including zone."""
        if self.zone:
            return f"{self.zone.code}/{self.code}"
        return self.code

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "warehouse_id": str(self.warehouse_id),
            "zone_id": str(self.zone_id) if self.zone_id else None,
            "zone_code": self.zone.code if self.zone else None,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "code": self.code,
            "full_code": self.full_code,
            "name": self.name,
            "barcode": self.barcode,
            "location_type": self.location_type,
            "capacity": {
                "max_weight": float(self.max_weight) if self.max_weight else None,
                "max_volume": float(self.max_volume) if self.max_volume else None,
                "max_items": self.max_items,
            },
            "is_active": self.is_active,
            "is_scrap_location": self.is_scrap_location,
            "is_return_location": self.is_return_location,
            "is_pickable": self.is_pickable,
            "is_receivable": self.is_receivable,
            "level": self.level,
        }
