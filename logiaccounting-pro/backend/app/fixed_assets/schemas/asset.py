"""
Pydantic schemas for fixed assets.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class AssetStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    UNDER_MAINTENANCE = "under_maintenance"
    DISPOSED = "disposed"
    TRANSFERRED = "transferred"
    FULLY_DEPRECIATED = "fully_depreciated"


class AcquisitionType(str, Enum):
    PURCHASE = "purchase"
    LEASE = "lease"
    CONSTRUCTION = "construction"
    DONATION = "donation"
    TRANSFER_IN = "transfer_in"
    TRADE_IN = "trade_in"


class DepreciationMethod(str, Enum):
    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining_balance"
    DOUBLE_DECLINING = "double_declining"
    SUM_OF_YEARS = "sum_of_years"
    UNITS_OF_PRODUCTION = "units_of_production"


# ==================== Category Schemas ====================

class CategoryCreate(BaseModel):
    """Create asset category."""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None

    default_useful_life_months: int = Field(..., gt=0)
    default_salvage_percent: Decimal = Field(default=0, ge=0, le=100)
    default_depreciation_method: DepreciationMethod
    default_declining_rate: Optional[Decimal] = Field(None, ge=0, le=100)

    asset_account_id: Optional[UUID] = None
    accumulated_depreciation_account_id: Optional[UUID] = None
    depreciation_expense_account_id: Optional[UUID] = None
    gain_loss_disposal_account_id: Optional[UUID] = None

    capitalize_threshold: Decimal = Field(default=500, ge=0)
    track_maintenance: bool = True
    require_serial_number: bool = False


class CategoryUpdate(BaseModel):
    """Update asset category."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None

    default_useful_life_months: Optional[int] = Field(None, gt=0)
    default_salvage_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    default_depreciation_method: Optional[DepreciationMethod] = None

    asset_account_id: Optional[UUID] = None
    accumulated_depreciation_account_id: Optional[UUID] = None
    depreciation_expense_account_id: Optional[UUID] = None

    capitalize_threshold: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    """Category response."""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    parent_id: Optional[UUID]
    level: int

    default_useful_life_months: int
    default_salvage_percent: Decimal
    default_depreciation_method: DepreciationMethod

    asset_account_id: Optional[UUID]
    accumulated_depreciation_account_id: Optional[UUID]
    depreciation_expense_account_id: Optional[UUID]

    capitalize_threshold: Decimal
    track_maintenance: bool

    is_active: bool
    asset_count: Optional[int] = None

    class Config:
        from_attributes = True


class CategoryTree(CategoryResponse):
    """Category with children for tree view."""
    children: List["CategoryTree"] = []


# ==================== Asset Schemas ====================

class AssetCreate(BaseModel):
    """Create fixed asset."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    category_id: UUID

    # Location
    location: Optional[str] = Field(None, max_length=200)
    department_id: Optional[UUID] = None
    responsible_person_id: Optional[UUID] = None

    # Physical
    serial_number: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=50)

    # Acquisition
    acquisition_type: AcquisitionType
    acquisition_date: date
    in_service_date: Optional[date] = None

    supplier_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    invoice_reference: Optional[str] = Field(None, max_length=100)

    # Costs
    acquisition_cost: Decimal = Field(..., gt=0)
    installation_cost: Decimal = Field(default=0, ge=0)
    shipping_cost: Decimal = Field(default=0, ge=0)
    other_costs: Decimal = Field(default=0, ge=0)

    # Depreciation
    depreciation_method: Optional[DepreciationMethod] = None  # Use category default
    useful_life_months: Optional[int] = Field(None, gt=0)  # Use category default
    salvage_value: Optional[Decimal] = Field(None, ge=0)
    salvage_percent: Optional[Decimal] = Field(None, ge=0, le=100)

    # For units of production
    total_estimated_units: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)

    # Insurance
    insured_value: Optional[Decimal] = Field(None, ge=0)
    insurance_policy: Optional[str] = Field(None, max_length=100)
    insurance_expiry_date: Optional[date] = None

    # Warranty
    warranty_expiry_date: Optional[date] = None
    warranty_provider: Optional[str] = Field(None, max_length=100)

    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_units(self):
        """Validate units of production requirements."""
        if self.depreciation_method == DepreciationMethod.UNITS_OF_PRODUCTION:
            if not self.total_estimated_units:
                raise ValueError("Total estimated units required for units of production method")
        return self


class AssetUpdate(BaseModel):
    """Update fixed asset."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None

    location: Optional[str] = Field(None, max_length=200)
    department_id: Optional[UUID] = None
    responsible_person_id: Optional[UUID] = None

    serial_number: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    manufacturer: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=50)

    insured_value: Optional[Decimal] = Field(None, ge=0)
    insurance_policy: Optional[str] = Field(None, max_length=100)
    insurance_expiry_date: Optional[date] = None

    warranty_expiry_date: Optional[date] = None
    warranty_provider: Optional[str] = Field(None, max_length=100)

    notes: Optional[str] = None


class AssetResponse(BaseModel):
    """Asset response."""
    id: UUID
    asset_number: str
    name: str
    description: Optional[str]

    category_id: UUID
    category_name: Optional[str] = None

    # Location
    location: Optional[str]
    department_id: Optional[UUID]
    responsible_person_id: Optional[UUID]
    responsible_person_name: Optional[str] = None

    # Physical
    serial_number: Optional[str]
    model: Optional[str]
    manufacturer: Optional[str]
    barcode: Optional[str]

    # Acquisition
    acquisition_type: AcquisitionType
    acquisition_date: date
    in_service_date: Optional[date]

    # Costs
    acquisition_cost: Decimal
    total_cost: Decimal

    # Depreciation
    depreciation_method: DepreciationMethod
    useful_life_months: int
    salvage_value: Decimal

    # Current values
    accumulated_depreciation: Decimal
    book_value: Decimal
    depreciation_percent: Optional[Decimal] = None

    # Status
    status: AssetStatus
    is_fully_depreciated: bool
    depreciation_start_date: Optional[date]
    last_depreciation_date: Optional[date]

    # Insurance/Warranty
    is_insured: bool = False
    is_under_warranty: bool = False

    # Audit
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetSummary(BaseModel):
    """Asset summary for lists."""
    id: UUID
    asset_number: str
    name: str
    category_name: Optional[str]
    location: Optional[str]
    acquisition_date: date
    total_cost: Decimal
    book_value: Decimal
    status: AssetStatus

    class Config:
        from_attributes = True


class AssetFilter(BaseModel):
    """Asset list filters."""
    search: Optional[str] = None
    category_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    status: Optional[str] = None
    acquisition_date_from: Optional[date] = None
    acquisition_date_to: Optional[date] = None
    is_fully_depreciated: Optional[bool] = None
    fully_depreciated: Optional[bool] = None
    location: Optional[str] = None


class AssetImport(BaseModel):
    """Asset import data."""
    name: str
    category_code: str
    acquisition_date: date
    acquisition_cost: Decimal
    depreciation_method: Optional[str] = None
    useful_life_months: Optional[int] = None
    location: Optional[str] = None
    serial_number: Optional[str] = None


class BarcodeSearch(BaseModel):
    """Barcode search request."""
    barcode: str = Field(..., min_length=1)
