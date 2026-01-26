"""
Depreciation-related schemas.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class DepreciationScheduleResponse(BaseModel):
    """Depreciation schedule line."""
    id: UUID
    period_number: int
    period_year: int
    period_month: int
    period_start: date
    period_end: date

    opening_book_value: Decimal
    depreciation_amount: Decimal
    accumulated_depreciation: Decimal
    closing_book_value: Decimal

    is_posted: bool

    class Config:
        from_attributes = True


class DepreciationRunCreate(BaseModel):
    """Create depreciation run."""
    period_year: int = Field(..., ge=2000, le=2100)
    period_month: int = Field(..., ge=1, le=12)
    category_id: Optional[UUID] = None
    department_id: Optional[UUID] = None


class DepreciationRunResponse(BaseModel):
    """Depreciation run response."""
    id: UUID
    run_number: str
    run_date: date
    period_year: int
    period_month: int

    category_id: Optional[UUID]
    category_name: Optional[str] = None

    assets_processed: int
    assets_skipped: int
    total_depreciation: Decimal

    status: str

    journal_entry_id: Optional[UUID]
    posted_at: Optional[datetime]

    created_at: datetime

    class Config:
        from_attributes = True


class DepreciationEntryResponse(BaseModel):
    """Depreciation entry response."""
    id: UUID
    asset_id: UUID
    asset_number: str
    asset_name: str
    category_name: str

    period_year: int
    period_month: int
    entry_date: date

    depreciation_method: str
    depreciation_amount: Decimal

    book_value_before: Decimal
    book_value_after: Decimal

    status: str

    class Config:
        from_attributes = True


class UnitsOfProductionUpdate(BaseModel):
    """Record units for UOP depreciation."""
    asset_id: UUID
    period_year: int
    period_month: int
    units_produced: Decimal = Field(..., gt=0)


class UnitsUpdateRequest(BaseModel):
    """Request to record units produced."""
    asset_id: UUID
    period_year: int
    period_month: int
    units: Decimal = Field(..., gt=0)
