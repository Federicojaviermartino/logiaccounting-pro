"""
Purchase Order Schemas
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class POStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    PARTIAL = "partial"
    RECEIVED = "received"
    INVOICED = "invoiced"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class POLineStatusEnum(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# ============== Order Line ==============

class OrderLineCreate(BaseModel):
    product_id: UUID
    description: Optional[str] = None
    supplier_sku: Optional[str] = None
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)
    expected_date: Optional[date] = None
    warehouse_id: Optional[UUID] = None
    notes: Optional[str] = None


class OrderLineUpdate(BaseModel):
    description: Optional[str] = None
    supplier_sku: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_rate: Optional[Decimal] = None
    expected_date: Optional[date] = None
    warehouse_id: Optional[UUID] = None
    notes: Optional[str] = None


class OrderLineResponse(BaseModel):
    id: UUID
    line_number: int
    product_id: UUID
    product_sku: Optional[str]
    product_name: Optional[str]
    description: Optional[str]
    supplier_sku: Optional[str]
    quantity: float
    uom: Optional[str]
    unit_price: float
    discount_percent: float
    tax_rate: float
    line_subtotal: float
    line_tax: float
    line_total: float
    quantity_received: float
    quantity_invoiced: float
    quantity_pending: float
    status: str
    expected_date: Optional[date]

    class Config:
        from_attributes = True


# ============== Purchase Order ==============

class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID
    order_date: Optional[date] = None
    expected_date: Optional[date] = None
    delivery_warehouse_id: Optional[UUID] = None
    delivery_address: Optional[str] = None
    payment_term_id: Optional[UUID] = None
    currency: str = "USD"
    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    shipping_amount: Decimal = Field(default=Decimal("0"), ge=0)
    supplier_contact_id: Optional[UUID] = None
    reference: Optional[str] = None
    requisition_id: Optional[UUID] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    lines: List[OrderLineCreate] = Field(..., min_length=1)

    @validator("expected_date")
    def validate_expected_date(cls, v, values):
        order_date = values.get("order_date") or date.today()
        if v and v < order_date:
            raise ValueError("Expected date cannot be before order date")
        return v


class PurchaseOrderUpdate(BaseModel):
    expected_date: Optional[date] = None
    delivery_warehouse_id: Optional[UUID] = None
    delivery_address: Optional[str] = None
    payment_term_id: Optional[UUID] = None
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    shipping_amount: Optional[Decimal] = None
    supplier_contact_id: Optional[UUID] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    id: UUID
    order_number: str
    supplier_id: UUID
    supplier_code: Optional[str]
    supplier_name: Optional[str]
    order_date: Optional[date]
    expected_date: Optional[date]
    delivery_warehouse_id: Optional[UUID]
    delivery_warehouse: Optional[str]
    currency: str
    exchange_rate: float
    subtotal: float
    tax_amount: float
    discount_amount: float
    shipping_amount: float
    total_amount: float
    status: str
    approval_required: bool
    approval_status: str
    received_amount: float
    invoiced_amount: float
    reference: Optional[str]
    notes: Optional[str]
    line_count: int
    created_at: Optional[datetime]
    lines: Optional[List[OrderLineResponse]] = None

    class Config:
        from_attributes = True


class PurchaseOrderFilter(BaseModel):
    supplier_id: Optional[UUID] = None
    status: Optional[POStatusEnum] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    warehouse_id: Optional[UUID] = None
    search: Optional[str] = None
    has_pending_receipt: Optional[bool] = None


# ============== Actions ==============

class OrderApprovalAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|return)$")
    comments: Optional[str] = None


class AddLineRequest(BaseModel):
    """Add line to existing order."""
    product_id: UUID
    quantity: Decimal = Field(..., gt=0)
    unit_price: Optional[Decimal] = None  # Auto-fetch from price list if not provided
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)
    expected_date: Optional[date] = None
    notes: Optional[str] = None


class CancelOrderRequest(BaseModel):
    reason: str = Field(..., min_length=1)


# ============== Dashboard ==============

class PODashboardStats(BaseModel):
    total_draft: int
    total_pending_approval: int
    total_pending_receipt: int
    total_this_month: int
    amount_this_month: float
    top_suppliers: List[dict]
