"""
Customer Schemas
Pydantic schemas for customers
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, validator


class CustomerTypeEnum(str, Enum):
    BUSINESS = "business"
    INDIVIDUAL = "individual"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class CustomerSegmentEnum(str, Enum):
    ENTERPRISE = "enterprise"
    MID_MARKET = "mid_market"
    SMB = "smb"
    RETAIL = "retail"


class AddressSchema(BaseModel):
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "USA"


class ShippingAddressCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    address_line1: str = Field(..., min_length=1)
    address_line2: Optional[str] = None
    city: str = Field(..., min_length=1)
    state: Optional[str] = None
    postal_code: str = Field(..., min_length=1)
    country: str = "USA"
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    delivery_instructions: Optional[str] = None
    is_default: bool = False


class ShippingAddressUpdate(BaseModel):
    name: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    delivery_instructions: Optional[str] = None
    is_default: Optional[bool] = None


class ShippingAddressResponse(BaseModel):
    id: UUID
    name: str
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: Optional[str]
    postal_code: str
    country: str
    contact_name: Optional[str]
    contact_phone: Optional[str]
    is_default: bool
    formatted_address: str

    class Config:
        from_attributes = True


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False
    is_billing: bool = False
    is_shipping: bool = False
    is_purchasing: bool = False
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: Optional[bool] = None
    is_billing: Optional[bool] = None
    is_shipping: Optional[bool] = None
    is_purchasing: Optional[bool] = None
    notes: Optional[str] = None


class ContactResponse(BaseModel):
    id: UUID
    name: str
    title: Optional[str]
    department: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    is_primary: bool
    is_billing: bool
    is_shipping: bool
    is_purchasing: bool

    class Config:
        from_attributes = True


class PriceListCreate(BaseModel):
    product_id: UUID
    unit_price: Decimal = Field(..., gt=0)
    currency: str = "USD"
    min_quantity: Decimal = Field(default=Decimal("1"), ge=1)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class PriceListUpdate(BaseModel):
    unit_price: Optional[Decimal] = None
    currency: Optional[str] = None
    min_quantity: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class PriceListResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_sku: Optional[str]
    product_name: Optional[str]
    unit_price: float
    currency: str
    min_quantity: float
    discount_percent: float
    valid_from: Optional[date]
    valid_to: Optional[date]
    is_current: bool

    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    customer_code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None

    customer_type: CustomerTypeEnum = CustomerTypeEnum.BUSINESS
    category: Optional[str] = None
    segment: Optional[CustomerSegmentEnum] = None

    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    billing_address: Optional[AddressSchema] = None
    shipping_same_as_billing: bool = True

    payment_term_id: Optional[UUID] = None
    currency: str = "USD"
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0)

    default_warehouse_id: Optional[UUID] = None
    default_shipping_method: Optional[str] = None

    receivable_account_id: Optional[UUID] = None
    revenue_account_id: Optional[UUID] = None

    tax_exempt: bool = False
    tax_exempt_number: Optional[str] = None
    tax_exempt_expiry: Optional[date] = None

    sales_rep_id: Optional[UUID] = None

    notes: Optional[str] = None

    contacts: Optional[List[ContactCreate]] = None
    shipping_addresses: Optional[List[ShippingAddressCreate]] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    customer_type: Optional[CustomerTypeEnum] = None
    category: Optional[str] = None
    segment: Optional[CustomerSegmentEnum] = None

    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    billing_address: Optional[AddressSchema] = None
    shipping_same_as_billing: Optional[bool] = None

    payment_term_id: Optional[UUID] = None
    currency: Optional[str] = None
    credit_limit: Optional[Decimal] = None

    default_warehouse_id: Optional[UUID] = None
    default_shipping_method: Optional[str] = None

    receivable_account_id: Optional[UUID] = None
    revenue_account_id: Optional[UUID] = None

    tax_exempt: Optional[bool] = None
    tax_exempt_number: Optional[str] = None
    tax_exempt_expiry: Optional[date] = None

    sales_rep_id: Optional[UUID] = None

    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CustomerResponse(BaseModel):
    id: UUID
    customer_code: str
    name: str
    legal_name: Optional[str]
    tax_id: Optional[str]
    customer_type: str
    category: Optional[str]
    segment: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    billing_address: Optional[dict]
    shipping_same_as_billing: bool
    currency: str
    payment_term_id: Optional[UUID]
    payment_term: Optional[str]
    credit_limit: float
    credit_hold: bool
    credit_hold_reason: Optional[str]
    tax_exempt: bool
    default_warehouse_id: Optional[UUID]
    default_shipping_method: Optional[str]
    sales_rep_id: Optional[UUID]
    sales_rep_name: Optional[str]
    is_active: bool
    notes: Optional[str]
    created_at: Optional[datetime]
    contacts: Optional[List[ContactResponse]] = None
    shipping_addresses: Optional[List[ShippingAddressResponse]] = None

    class Config:
        from_attributes = True


class CustomerFilter(BaseModel):
    search: Optional[str] = None
    customer_type: Optional[CustomerTypeEnum] = None
    segment: Optional[CustomerSegmentEnum] = None
    category: Optional[str] = None
    sales_rep_id: Optional[UUID] = None
    is_active: Optional[bool] = True
    credit_hold: Optional[bool] = None


class CustomerSummary(BaseModel):
    """Summary for dropdowns."""
    id: UUID
    customer_code: str
    name: str
    currency: str
    payment_term_id: Optional[UUID]
    credit_hold: bool


class CreditHoldRequest(BaseModel):
    hold: bool
    reason: Optional[str] = None


class CreditLimitUpdate(BaseModel):
    credit_limit: Decimal = Field(..., ge=0)
