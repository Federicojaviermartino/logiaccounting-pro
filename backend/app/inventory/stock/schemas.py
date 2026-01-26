"""
Stock Schemas
Pydantic schemas for stock levels and tracking
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class LotStatusEnum(str, Enum):
    AVAILABLE = "available"
    QUARANTINE = "quarantine"
    EXPIRED = "expired"
    CONSUMED = "consumed"


class SerialStatusEnum(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    SCRAPPED = "scrapped"
    IN_REPAIR = "in_repair"


# ============== Lot ==============

class LotCreate(BaseModel):
    product_id: UUID
    lot_number: str = Field(..., min_length=1, max_length=100)
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    supplier_id: Optional[UUID] = None
    supplier_lot: Optional[str] = None
    notes: Optional[str] = None

    @validator("expiry_date")
    def validate_expiry(cls, v, values):
        if v and values.get("manufacture_date") and v < values["manufacture_date"]:
            raise ValueError("Expiry date must be after manufacture date")
        return v


class LotUpdate(BaseModel):
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    supplier_id: Optional[UUID] = None
    supplier_lot: Optional[str] = None
    status: Optional[LotStatusEnum] = None
    notes: Optional[str] = None


class LotResponse(BaseModel):
    id: UUID
    product_id: UUID
    lot_number: str
    manufacture_date: Optional[date]
    expiry_date: Optional[date]
    is_expired: bool
    days_until_expiry: Optional[int]
    supplier_id: Optional[UUID]
    supplier_lot: Optional[str]
    status: str
    notes: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class LotFilter(BaseModel):
    product_id: Optional[UUID] = None
    status: Optional[LotStatusEnum] = None
    expiring_within_days: Optional[int] = None
    expired: Optional[bool] = None


# ============== Serial ==============

class SerialCreate(BaseModel):
    product_id: UUID
    serial_number: str = Field(..., min_length=1, max_length=100)
    lot_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None
    notes: Optional[str] = None


class SerialUpdate(BaseModel):
    lot_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    status: Optional[SerialStatusEnum] = None
    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None
    sold_to_customer_id: Optional[UUID] = None
    sold_date: Optional[date] = None
    notes: Optional[str] = None


class SerialResponse(BaseModel):
    id: UUID
    product_id: UUID
    lot_id: Optional[UUID]
    lot_number: Optional[str]
    serial_number: str
    warehouse_id: Optional[UUID]
    location_id: Optional[UUID]
    status: str
    warranty_start: Optional[date]
    warranty_end: Optional[date]
    is_warranty_active: bool
    notes: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class SerialFilter(BaseModel):
    product_id: Optional[UUID] = None
    lot_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    status: Optional[SerialStatusEnum] = None
    search: Optional[str] = None  # Search serial number


class BulkSerialCreate(BaseModel):
    """Create multiple serials at once."""
    product_id: UUID
    lot_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None

    serial_numbers: List[str] = Field(..., min_length=1)

    # Or generate from pattern
    prefix: Optional[str] = None
    start_number: Optional[int] = None
    count: Optional[int] = None

    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None


# ============== Stock Level ==============

class StockLevelResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_sku: Optional[str]
    product_name: Optional[str]
    warehouse_id: UUID
    warehouse_code: Optional[str]
    location_id: UUID
    location_code: Optional[str]
    lot_id: Optional[UUID]
    lot_number: Optional[str]
    quantity_on_hand: float
    quantity_reserved: float
    quantity_available: float
    unit_cost: float
    total_value: float
    last_movement_date: Optional[datetime]

    class Config:
        from_attributes = True


class StockSummaryByProduct(BaseModel):
    """Stock summary grouped by product."""
    product_id: UUID
    product_sku: str
    product_name: str
    total_on_hand: float
    total_reserved: float
    total_available: float
    total_value: float
    reorder_point: float
    is_low_stock: bool
    warehouse_breakdown: List[dict] = []


class StockSummaryByWarehouse(BaseModel):
    """Stock summary grouped by warehouse."""
    warehouse_id: UUID
    warehouse_code: str
    warehouse_name: str
    total_items: int
    total_value: float
    product_count: int


class StockFilter(BaseModel):
    product_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    lot_id: Optional[UUID] = None
    low_stock_only: Optional[bool] = None
    has_stock_only: Optional[bool] = None
    search: Optional[str] = None


class StockValuationReport(BaseModel):
    """Inventory valuation report."""
    as_of_date: datetime
    total_value: float
    total_items: int
    by_product: List[dict]
    by_warehouse: List[dict]
    by_category: List[dict]


# ============== Stock Reservation ==============

class StockReservation(BaseModel):
    """Reserve stock for an order."""
    product_id: UUID
    warehouse_id: UUID
    quantity: Decimal = Field(..., gt=0)
    lot_id: Optional[UUID] = None
    reference_type: str  # sales_order, production_order
    reference_id: UUID


class StockReservationResult(BaseModel):
    success: bool
    reserved_quantity: float
    remaining_quantity: float
    reservations: List[dict] = []
    message: Optional[str] = None
