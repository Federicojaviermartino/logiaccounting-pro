"""Movement Schemas"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, root_validator


class MovementTypeEnum(str, Enum):
    RECEIPT = "receipt"
    ISSUE = "issue"
    TRANSFER = "transfer"
    ADJUSTMENT = "adjustment"
    SCRAP = "scrap"


class MovementStatusEnum(str, Enum):
    DRAFT = "draft"
    DONE = "done"
    CANCELLED = "cancelled"


class ReceiptCreate(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    location_id: UUID
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    lot_id: Optional[UUID] = None
    lot_number: Optional[str] = None
    lot_expiry_date: Optional[datetime] = None
    serial_numbers: Optional[List[str]] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None
    movement_date: Optional[datetime] = None
    notes: Optional[str] = None


class IssueCreate(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    location_id: UUID
    quantity: Decimal = Field(..., gt=0)
    lot_id: Optional[UUID] = None
    serial_ids: Optional[List[UUID]] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None
    movement_date: Optional[datetime] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class TransferCreate(BaseModel):
    product_id: UUID
    source_warehouse_id: UUID
    source_location_id: UUID
    dest_warehouse_id: UUID
    dest_location_id: UUID
    quantity: Decimal = Field(..., gt=0)
    lot_id: Optional[UUID] = None
    serial_ids: Optional[List[UUID]] = None
    movement_date: Optional[datetime] = None
    reason: Optional[str] = None
    notes: Optional[str] = None

    @root_validator
    def validate_locations(cls, values):
        if values.get("source_location_id") == values.get("dest_location_id"):
            raise ValueError("Source and destination must differ")
        return values


class AdjustmentCreate(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    location_id: UUID
    quantity_change: Decimal
    lot_id: Optional[UUID] = None
    reason: str = Field(..., min_length=1)
    count_id: Optional[UUID] = None
    movement_date: Optional[datetime] = None
    notes: Optional[str] = None


class MovementResponse(BaseModel):
    id: UUID
    movement_number: str
    movement_type: str
    movement_date: Optional[datetime]
    product_id: UUID
    product_sku: Optional[str]
    quantity: float
    unit_cost: float
    total_cost: float
    source_warehouse: Optional[str]
    source_location: Optional[str]
    dest_warehouse: Optional[str]
    dest_location: Optional[str]
    status: str
    reference_number: Optional[str]

    class Config:
        from_attributes = True


class MovementFilter(BaseModel):
    product_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    movement_type: Optional[MovementTypeEnum] = None
    status: Optional[MovementStatusEnum] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
