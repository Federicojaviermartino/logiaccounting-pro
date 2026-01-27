"""Budget line and period schemas."""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BudgetLineCreate(BaseModel):
    """Create budget line."""
    account_id: UUID
    department_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    annual_amount: Decimal = Field(..., ge=0)
    distribution_method: str = "equal"
    notes: Optional[str] = None


class BudgetLineUpdate(BaseModel):
    """Update budget line."""
    annual_amount: Optional[Decimal] = Field(None, ge=0)
    distribution_method: Optional[str] = None
    notes: Optional[str] = None


class BudgetLineResponse(BaseModel):
    """Budget line response."""
    id: UUID
    version_id: UUID
    account_id: UUID
    account_code: str
    account_name: str
    account_type: str
    annual_amount: Decimal
    ytd_actual: Decimal
    ytd_variance: Decimal
    distribution_method: str

    class Config:
        from_attributes = True


class BudgetPeriodResponse(BaseModel):
    """Budget period response."""
    id: UUID
    line_id: UUID
    period_year: int
    period_month: int
    period_start: date
    period_end: date
    budgeted_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal
    variance_percent: Decimal
    is_locked: bool

    class Config:
        from_attributes = True
