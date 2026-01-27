"""KPI schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel


class KPIValue(BaseModel):
    name: str
    value: Decimal
    formatted_value: str
    unit: str = ""
    trend: Optional[str] = None
    trend_percent: Optional[Decimal] = None
    is_good: Optional[bool] = None


class KPICategory(BaseModel):
    name: str
    kpis: List[KPIValue]


class FinancialDashboard(BaseModel):
    as_of_date: date
    period_start: date
    period_end: date
    currency: str = "USD"
    total_revenue: Decimal
    total_expenses: Decimal
    net_income: Decimal
    cash_balance: Decimal
    revenue_trend: List[Dict[str, Any]]
    expense_breakdown: List[Dict[str, Any]]
    liquidity: KPICategory
    profitability: KPICategory
    efficiency: KPICategory
    ar_total: Decimal
    ap_total: Decimal
    alerts: List[Dict[str, Any]]


class KPISnapshotResponse(BaseModel):
    id: UUID
    snapshot_date: date
    period_type: str
    total_assets: Decimal
    total_liabilities: Decimal
    total_revenue: Decimal
    net_income: Decimal
    current_ratio: Optional[Decimal]
    net_profit_margin: Optional[Decimal]
    class Config:
        from_attributes = True
