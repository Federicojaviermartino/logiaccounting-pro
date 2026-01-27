"""
Fulfillment Schemas
Pydantic schemas for pick lists and shipments
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


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


class PickLineCreate(BaseModel):
    """Schema for creating pick line."""
    order_id: UUID
    order_line_id: UUID
    allocation_id: Optional[UUID] = None
    product_id: UUID
    location_id: Optional[UUID] = None
    lot_id: Optional[UUID] = None
    quantity_requested: Decimal = Field(..., gt=0)
    notes: Optional[str] = None


class PickLineUpdate(BaseModel):
    """Schema for updating pick line."""
    location_id: Optional[UUID] = None
    lot_id: Optional[UUID] = None
    quantity_picked: Optional[Decimal] = Field(None, ge=0)
    status: Optional[PickLineStatusEnum] = None
    notes: Optional[str] = None


class PickLineResponse(BaseModel):
    """Response schema for pick line."""
    id: UUID
    line_number: int
    order_id: UUID
    order_number: Optional[str]
    order_line_id: UUID
    product_id: UUID
    product_sku: Optional[str]
    product_name: Optional[str]
    location_id: Optional[UUID]
    location_code: Optional[str]
    lot_id: Optional[UUID]
    lot_number: Optional[str]
    quantity_requested: float
    quantity_picked: float
    quantity_short: float
    status: str
    picked_at: Optional[datetime]
    notes: Optional[str]

    class Config:
        from_attributes = True


class PickListCreate(BaseModel):
    """Schema for creating pick list."""
    warehouse_id: UUID
    pick_date: Optional[date] = None
    due_date: Optional[date] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None
    lines: Optional[List[PickLineCreate]] = None


class PickListUpdate(BaseModel):
    """Schema for updating pick list."""
    due_date: Optional[date] = None
    assigned_to: Optional[UUID] = None
    notes: Optional[str] = None


class PickListResponse(BaseModel):
    """Response schema for pick list."""
    id: UUID
    pick_number: str
    warehouse_id: UUID
    warehouse_name: Optional[str]
    pick_date: Optional[date]
    due_date: Optional[date]
    status: str
    assigned_to: Optional[UUID]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_lines: int
    lines_picked: int
    lines_short: int
    notes: Optional[str]
    created_at: Optional[datetime]
    lines: Optional[List[PickLineResponse]] = None

    class Config:
        from_attributes = True


class PickListFilter(BaseModel):
    """Filter for listing pick lists."""
    warehouse_id: Optional[UUID] = None
    status: Optional[PickListStatusEnum] = None
    statuses: Optional[List[PickListStatusEnum]] = None
    assigned_to: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None


class PickConfirmLine(BaseModel):
    """Confirm picked quantity for a line."""
    line_id: UUID
    quantity_picked: Decimal = Field(..., ge=0)
    location_id: Optional[UUID] = None
    lot_id: Optional[UUID] = None
    notes: Optional[str] = None


class PickConfirmRequest(BaseModel):
    """Request to confirm picks."""
    lines: List[PickConfirmLine]


class GeneratePickListRequest(BaseModel):
    """Request to generate pick list from orders."""
    order_ids: List[UUID]
    warehouse_id: UUID
    assigned_to: Optional[UUID] = None
    combine_orders: bool = True
    due_date: Optional[date] = None


class ShipmentLineCreate(BaseModel):
    """Schema for creating shipment line."""
    order_id: UUID
    order_line_id: UUID
    pick_line_id: Optional[UUID] = None
    product_id: UUID
    lot_id: Optional[UUID] = None
    serial_numbers: Optional[str] = None
    quantity_shipped: Decimal = Field(..., gt=0)


class ShipmentLineResponse(BaseModel):
    """Response schema for shipment line."""
    id: UUID
    line_number: int
    order_id: UUID
    order_number: Optional[str]
    order_line_id: UUID
    product_id: UUID
    product_sku: Optional[str]
    product_name: Optional[str]
    lot_id: Optional[UUID]
    lot_number: Optional[str]
    serial_numbers: Optional[str]
    quantity_shipped: float

    class Config:
        from_attributes = True


class ShipmentCreate(BaseModel):
    """Schema for creating shipment."""
    warehouse_id: UUID
    ship_date: Optional[date] = None
    expected_delivery: Optional[date] = None
    carrier: Optional[str] = None
    service_type: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    ship_to_name: Optional[str] = None
    ship_to_address: Optional[str] = None
    ship_to_city: Optional[str] = None
    ship_to_state: Optional[str] = None
    ship_to_postal: Optional[str] = None
    ship_to_country: Optional[str] = None
    ship_to_phone: Optional[str] = None
    weight: Optional[Decimal] = Field(None, ge=0)
    weight_uom: str = "LB"
    dimensions: Optional[str] = None
    package_count: int = Field(default=1, ge=1)
    shipping_cost: Decimal = Field(default=Decimal("0"), ge=0)
    insurance_cost: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None
    special_instructions: Optional[str] = None
    lines: Optional[List[ShipmentLineCreate]] = None


class ShipmentUpdate(BaseModel):
    """Schema for updating shipment."""
    ship_date: Optional[date] = None
    expected_delivery: Optional[date] = None
    carrier: Optional[str] = None
    service_type: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    ship_to_name: Optional[str] = None
    ship_to_address: Optional[str] = None
    ship_to_city: Optional[str] = None
    ship_to_state: Optional[str] = None
    ship_to_postal: Optional[str] = None
    ship_to_country: Optional[str] = None
    ship_to_phone: Optional[str] = None
    weight: Optional[Decimal] = Field(None, ge=0)
    weight_uom: Optional[str] = None
    dimensions: Optional[str] = None
    package_count: Optional[int] = Field(None, ge=1)
    shipping_cost: Optional[Decimal] = Field(None, ge=0)
    insurance_cost: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    special_instructions: Optional[str] = None


class ShipmentResponse(BaseModel):
    """Response schema for shipment."""
    id: UUID
    shipment_number: str
    warehouse_id: UUID
    warehouse_name: Optional[str]
    ship_date: Optional[date]
    expected_delivery: Optional[date]
    actual_delivery: Optional[date]
    carrier: Optional[str]
    service_type: Optional[str]
    tracking_number: Optional[str]
    tracking_url: Optional[str]
    ship_to_name: Optional[str]
    ship_to_address: Optional[str]
    full_address: Optional[str]
    weight: Optional[float]
    weight_uom: Optional[str]
    package_count: int
    shipping_cost: float
    insurance_cost: float
    status: str
    shipped_at: Optional[datetime]
    notes: Optional[str]
    line_count: int
    created_at: Optional[datetime]
    lines: Optional[List[ShipmentLineResponse]] = None

    class Config:
        from_attributes = True


class ShipmentFilter(BaseModel):
    """Filter for listing shipments."""
    warehouse_id: Optional[UUID] = None
    status: Optional[ShipmentStatusEnum] = None
    statuses: Optional[List[ShipmentStatusEnum]] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    order_id: Optional[UUID] = None


class ShipConfirmRequest(BaseModel):
    """Request to confirm shipment."""
    ship_date: Optional[date] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    carrier: Optional[str] = None


class DeliveryConfirmRequest(BaseModel):
    """Request to confirm delivery."""
    delivery_date: date
    signature: Optional[str] = None
    notes: Optional[str] = None


class CreateShipmentFromPickRequest(BaseModel):
    """Request to create shipment from pick list."""
    pick_list_id: UUID
    ship_to_name: Optional[str] = None
    ship_to_address: Optional[str] = None
    carrier: Optional[str] = None
    service_type: Optional[str] = None


class CreateShipmentFromOrderRequest(BaseModel):
    """Request to create shipment directly from order."""
    order_id: UUID
    lines: Optional[List[ShipmentLineCreate]] = None
    ship_to_name: Optional[str] = None
    ship_to_address: Optional[str] = None
    carrier: Optional[str] = None
    service_type: Optional[str] = None
