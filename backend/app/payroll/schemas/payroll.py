"""Payroll run schemas."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class PayPeriodCreate(BaseModel):
    """Create pay period."""
    frequency: str = Field(..., pattern="^(weekly|biweekly|semimonthly|monthly)$")
    start_date: date
    end_date: date
    pay_date: date


class PayPeriodResponse(BaseModel):
    """Pay period response."""
    id: UUID
    period_number: int
    period_year: int
    start_date: date
    end_date: date
    pay_date: date
    frequency: str
    status: str
    total_gross: Decimal
    total_deductions: Decimal
    total_net: Decimal
    employee_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class PayrollRunCreate(BaseModel):
    """Create payroll run."""
    pay_period_id: UUID
    run_type: str = Field(default="regular", pattern="^(regular|bonus|correction|final)$")


class PayrollRunResponse(BaseModel):
    """Payroll run response."""
    id: UUID
    run_number: str
    pay_period_id: UUID
    run_type: str
    status: str
    run_date: datetime
    calculated_at: Optional[datetime]
    approved_at: Optional[datetime]
    completed_at: Optional[datetime]

    total_gross_pay: Decimal
    total_deductions: Decimal
    total_net_pay: Decimal
    total_employer_taxes: Decimal
    total_employer_benefits: Decimal
    employee_count: int

    created_at: datetime

    class Config:
        from_attributes = True


class PayrollLineDeductionResponse(BaseModel):
    """Payroll line deduction."""
    id: UUID
    deduction_code: str
    deduction_name: str
    category: str
    employee_amount: Decimal
    employer_amount: Decimal
    ytd_employee: Decimal
    ytd_employer: Decimal

    class Config:
        from_attributes = True


class PayrollLineResponse(BaseModel):
    """Payroll line response."""
    id: UUID
    employee_id: UUID
    employee_number: str
    employee_name: str

    regular_hours: Decimal
    overtime_hours: Decimal
    regular_rate: Decimal
    overtime_rate: Decimal

    regular_pay: Decimal
    overtime_pay: Decimal
    holiday_pay: Decimal
    pto_pay: Decimal
    bonus: Decimal
    commission: Decimal
    gross_pay: Decimal

    federal_tax: Decimal
    state_tax: Decimal
    social_security: Decimal
    medicare: Decimal
    total_deductions: Decimal

    net_pay: Decimal

    employer_social_security: Decimal
    employer_medicare: Decimal
    total_employer_cost: Decimal

    ytd_gross: Decimal
    ytd_net: Decimal

    payment_method: str
    payment_status: str

    deductions: List[PayrollLineDeductionResponse] = []

    class Config:
        from_attributes = True


class PayrollRunWithLines(PayrollRunResponse):
    """Payroll run with employee lines."""
    payroll_lines: List[PayrollLineResponse] = []


class PayrollSummary(BaseModel):
    """Payroll summary statistics."""
    total_runs: int
    total_employees_paid: int
    total_gross_ytd: Decimal
    total_taxes_ytd: Decimal
    total_net_ytd: Decimal
    pending_runs: int
    completed_runs: int
