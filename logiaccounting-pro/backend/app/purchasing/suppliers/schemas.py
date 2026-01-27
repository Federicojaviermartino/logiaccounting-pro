"""
Supplier Schemas
Pydantic schemas for suppliers
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, validator


class SupplierTypeEnum(str, Enum):
    VENDOR = "vendor"
    CONTRACTOR = "contractor"
    SERVICE = "service"
    DISTRIBUTOR = "distributor"
    MANUFACTURER = "manufacturer"


class AddressSchema(BaseModel):
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "USA"


class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False
    is_ordering: bool = False
    is_billing: bool = False
    is_technical: bool = False
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: Optional[bool] = None
    is_ordering: Optional[bool] = None
    is_billing: Optional[bool] = None
    is_technical: Optional[bool] = None
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
    is_ordering: bool
    is_billing: bool
    is_technical: bool

    class Config:
        from_attributes = True


class PriceListCreate(BaseModel):
    product_id: UUID
    supplier_sku: Optional[str] = None
    supplier_description: Optional[str] = None
    unit_price: Decimal = Field(..., gt=0)
    currency: str = "USD"
    min_quantity: Decimal = Field(default=Decimal("1"), ge=1)
    lead_time_days: int = Field(default=0, ge=0)
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_preferred: bool = False

    @validator("valid_to")
    def validate_dates(cls, v, values):
        if v and values.get("valid_from") and v < values["valid_from"]:
            raise ValueError("valid_to must be after valid_from")
        return v


class PriceListUpdate(BaseModel):
    supplier_sku: Optional[str] = None
    supplier_description: Optional[str] = None
    unit_price: Optional[Decimal] = None
    currency: Optional[str] = None
    min_quantity: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_preferred: Optional[bool] = None


class PriceListResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_sku: Optional[str]
    product_name: Optional[str]
    supplier_sku: Optional[str]
    unit_price: float
    currency: str
    min_quantity: float
    lead_time_days: int
    valid_from: Optional[date]
    valid_to: Optional[date]
    is_preferred: bool
    is_current: bool

    class Config:
        from_attributes = True


class SupplierCreate(BaseModel):
    supplier_code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None

    supplier_type: SupplierTypeEnum = SupplierTypeEnum.VENDOR
    category: Optional[str] = None

    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    address: Optional[AddressSchema] = None

    payment_term_id: Optional[UUID] = None
    currency: str = "USD"
    credit_limit: Optional[Decimal] = None

    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_routing: Optional[str] = None
    bank_swift: Optional[str] = None
    bank_iban: Optional[str] = None

    default_warehouse_id: Optional[UUID] = None
    default_lead_time_days: int = 0

    payable_account_id: Optional[UUID] = None
    expense_account_id: Optional[UUID] = None

    notes: Optional[str] = None

    contacts: Optional[List[ContactCreate]] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    supplier_type: Optional[SupplierTypeEnum] = None
    category: Optional[str] = None

    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    address: Optional[AddressSchema] = None

    payment_term_id: Optional[UUID] = None
    currency: Optional[str] = None
    credit_limit: Optional[Decimal] = None

    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_routing: Optional[str] = None
    bank_swift: Optional[str] = None
    bank_iban: Optional[str] = None

    default_warehouse_id: Optional[UUID] = None
    default_lead_time_days: Optional[int] = None

    payable_account_id: Optional[UUID] = None
    expense_account_id: Optional[UUID] = None

    is_active: Optional[bool] = None
    notes: Optional[str] = None


class SupplierResponse(BaseModel):
    id: UUID
    supplier_code: str
    name: str
    legal_name: Optional[str]
    tax_id: Optional[str]
    supplier_type: str
    category: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    address: Optional[dict]
    currency: str
    payment_term_id: Optional[UUID]
    payment_term: Optional[str]
    credit_limit: Optional[float]
    default_warehouse_id: Optional[UUID]
    default_lead_time_days: int
    is_active: bool
    is_approved: bool
    approved_at: Optional[datetime]
    notes: Optional[str]
    created_at: Optional[datetime]
    contacts: Optional[List[ContactResponse]] = None

    class Config:
        from_attributes = True


class SupplierFilter(BaseModel):
    search: Optional[str] = None
    supplier_type: Optional[SupplierTypeEnum] = None
    category: Optional[str] = None
    is_active: Optional[bool] = True
    is_approved: Optional[bool] = None


class SupplierSummary(BaseModel):
    """Summary for dropdowns."""
    id: UUID
    supplier_code: str
    name: str
    currency: str
    payment_term_id: Optional[UUID]


class BulkPriceListImport(BaseModel):
    """Import multiple prices."""
    items: List[PriceListCreate]


class SupplierApproval(BaseModel):
    """Approve or reject supplier."""
    action: str = Field(..., pattern="^(approve|reject)$")
    comments: Optional[str] = None
