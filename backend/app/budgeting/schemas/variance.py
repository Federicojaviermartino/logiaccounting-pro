"""Variance and alert schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class VarianceThresholdCreate(BaseModel):
    """Create variance threshold."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    budget_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    account_type: Optional[str] = None
    department_id: Optional[UUID] = None
    warning_percent: Decimal = Field(default=5, ge=0, le=100)
    critical_percent: Decimal = Field(default=10, ge=0, le=100)
    warning_amount: Optional[Decimal] = Field(None, ge=0)
    critical_amount: Optional[Decimal] = Field(None, ge=0)
    notify_on_warning: bool = True
    notify_on_critical: bool = True
    notify_users: Optional[List[UUID]] = None
    notify_emails: Optional[List[str]] = None


class VarianceThresholdUpdate(BaseModel):
    """Update variance threshold."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    warning_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    critical_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    warning_amount: Optional[Decimal] = Field(None, ge=0)
    critical_amount: Optional[Decimal] = Field(None, ge=0)
    notify_on_warning: Optional[bool] = None
    notify_on_critical: Optional[bool] = None
    is_active: Optional[bool] = None


class VarianceThresholdResponse(BaseModel):
    """Variance threshold response."""
    id: UUID
    name: str
    description: Optional[str]
    budget_id: Optional[UUID]
    account_id: Optional[UUID]
    account_type: Optional[str]
    department_id: Optional[UUID]
    warning_percent: Decimal
    critical_percent: Decimal
    warning_amount: Optional[Decimal]
    critical_amount: Optional[Decimal]
    notify_on_warning: bool
    notify_on_critical: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class VarianceAlertResponse(BaseModel):
    """Variance alert response."""
    id: UUID
    budget_id: UUID
    budget_name: str
    account_id: UUID
    account_code: str
    account_name: str
    period_year: int
    period_month: int
    budgeted_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal
    variance_percent: Decimal
    variance_type: str
    alert_level: str
    status: str
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    """Acknowledge alert."""
    notes: Optional[str] = None


class AlertResolve(BaseModel):
    """Resolve alert."""
    resolution_notes: str = Field(..., max_length=500)


class AlertSummary(BaseModel):
    """Alert counts summary."""
    total: int = 0
    new: int = 0
    acknowledged: int = 0
    critical: int = 0
    warning: int = 0


class BudgetVsActualLine(BaseModel):
    """Single line of budget vs actual comparison."""
    account_id: UUID
    account_code: str
    account_name: str
    account_type: str
    budgeted: Decimal
    actual: Decimal
    variance: Decimal
    variance_percent: Decimal
    variance_type: str  # favorable, unfavorable, on_target


class BudgetVsActualReport(BaseModel):
    """Budget vs actual comparison report."""
    budget_id: UUID
    budget_name: str
    period_type: str  # monthly, quarterly, ytd, annual
    period_year: int
    period_month: Optional[int] = None

    # Totals
    total_revenue_budget: Decimal
    total_revenue_actual: Decimal
    total_revenue_variance: Decimal
    total_expense_budget: Decimal
    total_expense_actual: Decimal
    total_expense_variance: Decimal
    net_income_budget: Decimal
    net_income_actual: Decimal
    net_income_variance: Decimal

    # Detail lines
    revenue_lines: List[BudgetVsActualLine]
    expense_lines: List[BudgetVsActualLine]
