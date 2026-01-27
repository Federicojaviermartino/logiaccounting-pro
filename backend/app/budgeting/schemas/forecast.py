"""Forecast schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class ForecastCreate(BaseModel):
    """Create rolling forecast."""
    budget_id: UUID
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    base_date: datetime
    forecast_months: int = Field(default=12, ge=1, le=36)
    forecast_method: str = "trend"


class ForecastUpdate(BaseModel):
    """Update forecast."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    forecast_method: Optional[str] = None
    status: Optional[str] = None


class ForecastLineResponse(BaseModel):
    """Forecast line response."""
    id: UUID
    account_id: UUID
    account_code: str
    account_name: str
    account_type: str
    period_year: int
    period_month: int
    data_type: str
    budget_amount: Decimal
    actual_amount: Decimal
    forecast_amount: Decimal
    confidence_percent: Optional[Decimal]

    class Config:
        from_attributes = True


class ForecastResponse(BaseModel):
    """Forecast response."""
    id: UUID
    budget_id: UUID
    forecast_number: str
    name: str
    description: Optional[str]
    base_date: datetime
    forecast_months: int
    forecast_method: str
    total_revenue: Decimal
    total_expenses: Decimal
    total_net_income: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ForecastWithLines(ForecastResponse):
    """Forecast with lines."""
    lines: List[ForecastLineResponse] = []


class TemplateCreate(BaseModel):
    """Create budget template."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    template_type: str = "standard"
    period_type: str = "annual"
    default_distribution: str = "equal"


class TemplateResponse(BaseModel):
    """Template response."""
    id: UUID
    name: str
    description: Optional[str]
    template_type: str
    period_type: str
    default_distribution: str
    is_active: bool
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True
