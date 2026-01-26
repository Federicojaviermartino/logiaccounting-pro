"""
Warehouse Schemas
Pydantic schemas for warehouses and locations
"""

from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class LocationTypeEnum(str, Enum):
    INTERNAL = "internal"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    PRODUCTION = "production"
    TRANSIT = "transit"
    VIEW = "view"
    SCRAP = "scrap"
    ADJUSTMENT = "adjustment"


class ZoneTypeEnum(str, Enum):
    RECEIVING = "receiving"
    STORAGE = "storage"
    PICKING = "picking"
    PACKING = "packing"
    SHIPPING = "shipping"
    QUARANTINE = "quarantine"
    RETURNS = "returns"


# ============== Address ==============

class AddressSchema(BaseModel):
    line1: Optional[str] = Field(None, max_length=200)
    line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)


class CoordinatesSchema(BaseModel):
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)


# ============== Warehouse ==============

class WarehouseCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)

    address: Optional[AddressSchema] = None

    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=200)

    coordinates: Optional[CoordinatesSchema] = None

    manager_id: Optional[UUID] = None

    allow_negative_stock: bool = False

    inventory_account_id: Optional[UUID] = None
    adjustment_account_id: Optional[UUID] = None


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[AddressSchema] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    coordinates: Optional[CoordinatesSchema] = None
    manager_id: Optional[UUID] = None
    allow_negative_stock: Optional[bool] = None
    inventory_account_id: Optional[UUID] = None
    adjustment_account_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class WarehouseResponse(BaseModel):
    id: UUID
    code: str
    name: str
    address: Optional[dict]
    phone: Optional[str]
    email: Optional[str]
    coordinates: Optional[dict]
    manager_id: Optional[UUID]
    is_active: bool
    allow_negative_stock: bool
    zones_count: int
    locations_count: int

    class Config:
        from_attributes = True


class WarehouseSummary(BaseModel):
    id: UUID
    code: str
    name: str
    city: Optional[str]
    is_active: bool


# ============== Zone ==============

class ZoneCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    zone_type: Optional[ZoneTypeEnum] = None
    description: Optional[str] = None
    sequence: int = 0


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    zone_type: Optional[ZoneTypeEnum] = None
    description: Optional[str] = None
    sequence: Optional[int] = None
    is_active: Optional[bool] = None


class ZoneResponse(BaseModel):
    id: UUID
    warehouse_id: UUID
    code: str
    name: str
    zone_type: Optional[str]
    description: Optional[str]
    is_active: bool
    sequence: int
    locations_count: int

    class Config:
        from_attributes = True


# ============== Location ==============

class LocationCapacity(BaseModel):
    max_weight: Optional[Decimal] = Field(None, ge=0)
    max_volume: Optional[Decimal] = Field(None, ge=0)
    max_items: Optional[int] = Field(None, ge=0)


class LocationCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=50)

    zone_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None

    location_type: LocationTypeEnum = LocationTypeEnum.INTERNAL

    capacity: Optional[LocationCapacity] = None

    is_scrap_location: bool = False
    is_return_location: bool = False
    is_pickable: bool = True
    is_receivable: bool = True


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    zone_id: Optional[UUID] = None
    capacity: Optional[LocationCapacity] = None
    is_active: Optional[bool] = None
    is_scrap_location: Optional[bool] = None
    is_return_location: Optional[bool] = None
    is_pickable: Optional[bool] = None
    is_receivable: Optional[bool] = None


class LocationResponse(BaseModel):
    id: UUID
    warehouse_id: UUID
    zone_id: Optional[UUID]
    zone_code: Optional[str]
    parent_id: Optional[UUID]
    code: str
    full_code: str
    name: Optional[str]
    barcode: Optional[str]
    location_type: str
    capacity: Optional[dict]
    is_active: bool
    is_scrap_location: bool
    is_return_location: bool
    is_pickable: bool
    is_receivable: bool
    level: int

    class Config:
        from_attributes = True


class LocationTreeNode(BaseModel):
    """Location with children for tree view."""
    id: UUID
    code: str
    name: Optional[str]
    location_type: str
    is_active: bool
    children: List["LocationTreeNode"] = []

    class Config:
        from_attributes = True


# ============== Bulk Operations ==============

class BulkLocationCreate(BaseModel):
    """Create multiple locations at once."""
    zone_id: Optional[UUID] = None

    # Pattern-based generation
    aisle_prefix: str = "A"
    aisle_count: int = Field(1, ge=1, le=100)
    rack_count: int = Field(1, ge=1, le=100)
    level_count: int = Field(1, ge=1, le=20)
    bin_count: int = Field(1, ge=1, le=100)

    # Format: {aisle}-{rack:02d}-{level:02d}-{bin:02d}
    code_format: str = "{aisle}-{rack:02d}-{level:02d}-{bin:02d}"

    capacity: Optional[LocationCapacity] = None

    @validator("aisle_prefix")
    def validate_prefix(cls, v):
        if len(v) > 5:
            raise ValueError("Prefix too long")
        return v.upper()


class BulkLocationResult(BaseModel):
    created: int
    skipped: int
    errors: List[dict] = []
