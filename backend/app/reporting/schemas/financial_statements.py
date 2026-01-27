"""Financial statement schemas."""
from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel


class AccountLine(BaseModel):
    account_id: Optional[UUID] = None
    account_code: str
    account_name: str
    level: int = 0
    is_header: bool = False
    is_total: bool = False
    current_balance: Decimal = Decimal(0)
    prior_balance: Optional[Decimal] = None
    variance: Optional[Decimal] = None
    variance_percent: Optional[Decimal] = None


class BalanceSheetSection(BaseModel):
    name: str
    lines: List[AccountLine]
    total: Decimal


class BalanceSheet(BaseModel):
    as_of_date: date
    prior_date: Optional[date] = None
    currency: str = "USD"
    current_assets: BalanceSheetSection
    non_current_assets: BalanceSheetSection
    total_assets: Decimal
    current_liabilities: BalanceSheetSection
    non_current_liabilities: BalanceSheetSection
    total_liabilities: Decimal
    equity: BalanceSheetSection
    total_equity: Decimal
    total_liabilities_and_equity: Decimal
    is_balanced: bool


class IncomeStatementSection(BaseModel):
    name: str
    lines: List[AccountLine]
    total: Decimal


class IncomeStatement(BaseModel):
    start_date: date
    end_date: date
    currency: str = "USD"
    revenue: IncomeStatementSection
    total_revenue: Decimal
    cost_of_goods_sold: IncomeStatementSection
    total_cogs: Decimal
    gross_profit: Decimal
    gross_profit_margin: Optional[Decimal] = None
    operating_expenses: IncomeStatementSection
    total_operating_expenses: Decimal
    operating_income: Decimal
    operating_margin: Optional[Decimal] = None
    other_income: IncomeStatementSection
    other_expenses: IncomeStatementSection
    income_before_tax: Decimal
    income_tax: Decimal
    net_income: Decimal
    net_profit_margin: Optional[Decimal] = None


class CashFlowSection(BaseModel):
    name: str
    lines: List[AccountLine]
    total: Decimal


class CashFlowStatement(BaseModel):
    start_date: date
    end_date: date
    currency: str = "USD"
    opening_cash: Decimal
    operating_activities: CashFlowSection
    net_cash_from_operations: Decimal
    investing_activities: CashFlowSection
    net_cash_from_investing: Decimal
    financing_activities: CashFlowSection
    net_cash_from_financing: Decimal
    net_change_in_cash: Decimal
    closing_cash: Decimal


class TrialBalanceLine(BaseModel):
    account_id: UUID
    account_code: str
    account_name: str
    account_type: str
    debit: Decimal = Decimal(0)
    credit: Decimal = Decimal(0)


class TrialBalance(BaseModel):
    as_of_date: date
    currency: str = "USD"
    lines: List[TrialBalanceLine]
    total_debits: Decimal
    total_credits: Decimal
    is_balanced: bool


class AgingLine(BaseModel):
    entity_id: UUID
    entity_name: str
    current: Decimal = Decimal(0)
    days_1_30: Decimal = Decimal(0)
    days_31_60: Decimal = Decimal(0)
    days_61_90: Decimal = Decimal(0)
    days_over_90: Decimal = Decimal(0)
    total: Decimal = Decimal(0)


class AgingReport(BaseModel):
    as_of_date: date
    report_type: str
    currency: str = "USD"
    lines: List[AgingLine]
    total_current: Decimal
    total_1_30: Decimal
    total_31_60: Decimal
    total_61_90: Decimal
    total_over_90: Decimal
    grand_total: Decimal
