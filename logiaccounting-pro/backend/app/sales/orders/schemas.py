"""
Sales Order Schemas
Pydantic schemas for sales orders
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class SOStatusEnum(str, Enum):
    """Sales order status."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    PARTIAL_SHIPPED = "partial_shipped"
    SHIPPED = "shipped"
    INVOICED = "invoiced"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class SOLineStatusEnum(str, Enum):
    """Line status."""
    PENDING = "pending"
    ALLOCATED = "allocated"
    PICKING = "picking"
    PARTIAL_SHIPPED = "partial_shipped"
    SHIPPED = "shipped"
    INVOICED = "invoiced"
    CANCELLED = "cancelled"
    BACKORDERED = "backordered"


class PriorityEnum(str, Enum):
    """Order priority."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class OrderLineCreate(BaseModel):
    """Schema for creating order line."""
    product_id: UUID
    description: Optional[str] = None
    quantity: Decimal = Field(..., gt=0)
    uom_id: Optional[UUID] = None
    unit_price: Decimal = Field(..., ge=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    requested_date: Optional[date] = None
    promised_date: Optional[date] = None
    warehouse_id: Optional[UUID] = None
    notes: Optional[str] = None


class OrderLineUpdate(BaseModel):
    """Schema for updating order line."""
    description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    uom_id: Optional[UUID] = None
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    requested_date: Optional[date] = None
    promised_date: Optional[date] = None
    warehouse_id: Optional[UUID] = None
    notes: Optional[str] = None


class OrderLineResponse(BaseModel):
    """Response schema for order line."""
    id: UUID
    line_number: int
    product_id: UUID
    product_sku: Optional[str]
    product_name: Optional[str]
    description: Optional[str]
    quantity: float
    uom: Optional[str]
    unit_price: float
    discount_percent: float
    tax_rate: float
    line_subtotal: float
    line_discount: float
    line_tax: float
    line_total: float
    qty_allocated: float
    qty_picked: float
    qty_shipped: float
    qty_invoiced: float
    qty_pending: float
    status: str
    requested_date: Optional[date]
    promised_date: Optional[date]
    warehouse_id: Optional[UUID]
    notes: Optional[str]

    class Config:
        from_attributes = True


class SalesOrderCreate(BaseModel):
    """Schema for creating sales order."""
    customer_master_id: UUID
    customer_po_number: Optional[str] = None
    order_date: Optional[date] = None
    requested_date: Optional[date] = None
    promised_date: Optional[date] = None
    ship_to_address_id: Optional[UUID] = None
    shipping_address: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_carrier: Optional[str] = None
    warehouse_id: Optional[UUID] = None
    payment_term_id: Optional[UUID] = None
    currency: str = "USD"
    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    shipping_amount: Decimal = Field(default=Decimal("0"), ge=0)
    priority: PriorityEnum = PriorityEnum.NORMAL
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    lines: Optional[List[OrderLineCreate]] = None


class SalesOrderUpdate(BaseModel):
    """Schema for updating sales order."""
    customer_po_number: Optional[str] = None
    requested_date: Optional[date] = None
    promised_date: Optional[date] = None
    ship_to_address_id: Optional[UUID] = None
    shipping_address: Optional[str] = None
    shipping_method: Optional[str] = None
    shipping_carrier: Optional[str] = None
    warehouse_id: Optional[UUID] = None
    payment_term_id: Optional[UUID] = None
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = Field(None, gt=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    shipping_amount: Optional[Decimal] = Field(None, ge=0)
    priority: Optional[PriorityEnum] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class SalesOrderResponse(BaseModel):
    """Response schema for sales order."""
    id: UUID
    order_number: str
    customer_master_id: UUID
    customer_code: Optional[str]
    customer_name: Optional[str]
    customer_po_number: Optional[str]
    order_date: Optional[date]
    requested_date: Optional[date]
    promised_date: Optional[date]
    shipping_address: Optional[str]
    shipping_method: Optional[str]
    warehouse_id: Optional[UUID]
    warehouse_name: Optional[str]
    currency: str
    subtotal: float
    discount_percent: float
    discount_amount: float
    tax_amount: float
    shipping_amount: float
    total_amount: float
    status: str
    priority: str
    qty_ordered: float
    qty_allocated: float
    qty_shipped: float
    qty_invoiced: float
    invoiced_amount: float
    paid_amount: float
    balance_due: float
    hold_reason: Optional[str]
    notes: Optional[str]
    line_count: int
    created_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    lines: Optional[List[OrderLineResponse]] = None

    class Config:
        from_attributes = True


class SalesOrderFilter(BaseModel):
    """Filter for listing sales orders."""
    search: Optional[str] = None
    customer_master_id: Optional[UUID] = None
    status: Optional[SOStatusEnum] = None
    statuses: Optional[List[SOStatusEnum]] = None
    priority: Optional[PriorityEnum] = None
    warehouse_id: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    requested_date_from: Optional[date] = None
    requested_date_to: Optional[date] = None
    has_backorders: Optional[bool] = None


class SalesOrderSummary(BaseModel):
    """Summary for dropdowns."""
    id: UUID
    order_number: str
    customer_name: str
    order_date: date
    total_amount: float
    status: str


class OrderConfirmRequest(BaseModel):
    """Request to confirm order."""
    auto_allocate: bool = False


class OrderHoldRequest(BaseModel):
    """Request to put order on hold."""
    hold: bool
    reason: Optional[str] = None


class OrderCancelRequest(BaseModel):
    """Request to cancel order."""
    reason: Optional[str] = None


class AllocationCreate(BaseModel):
    """Schema for creating stock allocation."""
    order_line_id: UUID
    warehouse_id: UUID
    location_id: Optional[UUID] = None
    lot_id: Optional[UUID] = None
    quantity: Decimal = Field(..., gt=0)


class AllocationResponse(BaseModel):
    """Response schema for allocation."""
    id: UUID
    order_line_id: UUID
    product_id: UUID
    product_sku: Optional[str]
    warehouse_id: UUID
    location_id: Optional[UUID]
    location_code: Optional[str]
    lot_id: Optional[UUID]
    lot_number: Optional[str]
    quantity_allocated: float
    quantity_picked: float
    status: str
    allocated_at: Optional[datetime]

    class Config:
        from_attributes = True


class BulkLineUpdate(BaseModel):
    """Bulk update for order lines."""
    line_ids: List[UUID]
    warehouse_id: Optional[UUID] = None
    requested_date: Optional[date] = None
    promised_date: Optional[date] = None


class OrderDuplicateRequest(BaseModel):
    """Request to duplicate an order."""
    new_customer_id: Optional[UUID] = None
    copy_dates: bool = False
    copy_prices: bool = True
