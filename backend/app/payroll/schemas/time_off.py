"""Time off schemas."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TimeOffRequestCreate(BaseModel):
    """Create time off request."""
    time_off_type: str = Field(..., pattern="^(vacation|sick|personal|bereavement|jury_duty|military|maternity|paternity|unpaid|other)$")
    start_date: date
    end_date: date
    hours_requested: Decimal = Field(..., gt=0)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    reason: Optional[str] = None


class TimeOffRequestUpdate(BaseModel):
    """Update time off request."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hours_requested: Optional[Decimal] = Field(None, gt=0)
    reason: Optional[str] = None


class TimeOffRequestResponse(BaseModel):
    """Time off request response."""
    id: UUID
    employee_id: UUID
    request_number: str
    time_off_type: str
    start_date: date
    end_date: date
    hours_requested: Decimal
    start_time: Optional[str]
    end_time: Optional[str]
    reason: Optional[str]
    status: str
    reviewed_by: Optional[UUID]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TimeOffReview(BaseModel):
    """Review time off request."""
    action: str = Field(..., pattern="^(approve|reject)$")
    notes: Optional[str] = None


class TimeOffBalanceResponse(BaseModel):
    """Time off balance response."""
    id: UUID
    employee_id: UUID
    year: int
    time_off_type: str
    annual_entitlement: Decimal
    carryover_from_previous: Decimal
    hours_used: Decimal
    hours_pending: Decimal
    adjustments: Decimal
    available_balance: Decimal

    class Config:
        from_attributes = True


class TimeOffBalanceAdjust(BaseModel):
    """Adjust time off balance."""
    adjustment: Decimal
    reason: str = Field(..., max_length=200)
