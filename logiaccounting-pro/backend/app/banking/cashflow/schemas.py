"""
Cash Flow Forecasting Schemas
Pydantic schemas for cash flow
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.banking.cashflow.models import ForecastStatus, Granularity, TransactionType, RecurrencePattern


class ForecastCreate(BaseModel):
    """Schema for creating a forecast"""
    forecast_name: str = Field(..., max_length=200)
    description: Optional[str] = None
    period_start: date
    period_end: date
    granularity: Granularity = Granularity.WEEKLY

    include_ar: bool = True
    include_ap: bool = True
    include_recurring: bool = True
    include_planned: bool = True

    bank_account_ids: Optional[List[UUID]] = None


class ForecastUpdate(BaseModel):
    """Schema for updating a forecast"""
    forecast_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    include_ar: Optional[bool] = None
    include_ap: Optional[bool] = None
    include_recurring: Optional[bool] = None
    include_planned: Optional[bool] = None


class ForecastLineResponse(BaseModel):
    """Schema for forecast line response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    forecast_id: UUID
    period_date: date
    period_label: Optional[str] = None

    opening_balance: Decimal
    ar_collections: Decimal
    other_income: Decimal
    planned_inflows: Decimal
    total_inflows: Decimal

    ap_payments: Decimal
    payroll: Decimal
    tax_payments: Decimal
    loan_payments: Decimal
    other_expenses: Decimal
    planned_outflows: Decimal
    total_outflows: Decimal

    net_cash_flow: Decimal
    closing_balance: Decimal

    min_balance_required: Optional[Decimal] = None
    shortfall: Optional[Decimal] = None


class ForecastResponse(BaseModel):
    """Schema for forecast response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    forecast_name: str
    description: Optional[str] = None

    period_start: date
    period_end: date
    granularity: str

    include_ar: bool
    include_ap: bool
    include_recurring: bool
    include_planned: bool

    status: str
    last_generated_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime


class ForecastDetailResponse(ForecastResponse):
    """Forecast with lines"""
    lines: List[ForecastLineResponse] = []


class PlannedTransactionCreate(BaseModel):
    """Schema for creating a planned transaction"""
    description: str = Field(..., max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    transaction_type: TransactionType
    amount: Decimal = Field(..., gt=0)
    currency: str = Field("USD", max_length=3)
    bank_account_id: Optional[UUID] = None
    scheduled_date: date

    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[date] = None

    notes: Optional[str] = None


class PlannedTransactionUpdate(BaseModel):
    """Schema for updating a planned transaction"""
    description: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    amount: Optional[Decimal] = Field(None, gt=0)
    scheduled_date: Optional[date] = None
    recurrence_end_date: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class PlannedTransactionResponse(BaseModel):
    """Schema for planned transaction response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    category: Optional[str] = None
    transaction_type: str
    amount: Decimal
    currency: str
    bank_account_id: Optional[UUID] = None
    scheduled_date: date

    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    recurrence_end_date: Optional[date] = None

    is_active: bool
    is_completed: bool

    notes: Optional[str] = None
    created_at: datetime


class CashPositionResponse(BaseModel):
    """Schema for cash position response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    snapshot_date: date
    total_cash: Decimal
    cash_by_currency: Optional[dict] = None
    cash_by_account: Optional[List[dict]] = None
    total_ar_outstanding: Optional[Decimal] = None
    total_ap_outstanding: Optional[Decimal] = None
    net_working_capital: Optional[Decimal] = None
    created_at: datetime


class ForecastSummary(BaseModel):
    """Brief forecast summary for dashboard"""
    current_cash: Decimal
    projected_cash_30_days: Decimal
    projected_cash_60_days: Decimal
    projected_cash_90_days: Decimal
    expected_ar_collections: Decimal
    expected_ap_payments: Decimal
    cash_burn_rate: Optional[Decimal] = None
    runway_days: Optional[int] = None
