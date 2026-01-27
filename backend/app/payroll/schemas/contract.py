"""Contract schemas."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ContractCreate(BaseModel):
    """Create employee contract."""
    start_date: date
    end_date: Optional[date] = None

    job_title: str = Field(..., max_length=100)
    job_description: Optional[str] = None
    department_id: Optional[UUID] = None

    compensation_type: str = "salary"

    annual_salary: Optional[Decimal] = Field(None, ge=0)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    commission_base: Optional[Decimal] = Field(None, ge=0)

    pay_frequency: str = "biweekly"

    standard_hours_per_week: Decimal = Field(default=40, ge=0, le=80)
    standard_hours_per_day: Decimal = Field(default=8, ge=0, le=24)

    overtime_eligibility: str = "non_exempt"
    overtime_rate_multiplier: Decimal = Field(default=1.5, ge=1, le=3)

    currency: str = Field(default="USD", max_length=3)

    probation_end_date: Optional[date] = None

    vacation_days_annual: Decimal = Field(default=15, ge=0)
    sick_days_annual: Decimal = Field(default=10, ge=0)
    personal_days_annual: Decimal = Field(default=3, ge=0)

    additional_terms: Optional[dict] = None
    notes: Optional[str] = None


class ContractUpdate(BaseModel):
    """Update contract."""
    end_date: Optional[date] = None
    job_title: Optional[str] = Field(None, max_length=100)
    job_description: Optional[str] = None
    department_id: Optional[UUID] = None

    annual_salary: Optional[Decimal] = Field(None, ge=0)
    hourly_rate: Optional[Decimal] = Field(None, ge=0)

    standard_hours_per_week: Optional[Decimal] = Field(None, ge=0, le=80)

    overtime_eligibility: Optional[str] = None
    overtime_rate_multiplier: Optional[Decimal] = Field(None, ge=1, le=3)

    vacation_days_annual: Optional[Decimal] = Field(None, ge=0)
    sick_days_annual: Optional[Decimal] = Field(None, ge=0)
    personal_days_annual: Optional[Decimal] = Field(None, ge=0)

    probation_completed: Optional[bool] = None
    is_active: Optional[bool] = None

    notes: Optional[str] = None


class ContractResponse(BaseModel):
    """Contract response."""
    id: UUID
    employee_id: UUID
    contract_number: str

    start_date: date
    end_date: Optional[date]

    job_title: str
    job_description: Optional[str]
    department_id: Optional[UUID]

    compensation_type: str
    annual_salary: Optional[Decimal]
    hourly_rate: Optional[Decimal]
    commission_rate: Optional[Decimal]
    commission_base: Optional[Decimal]

    pay_frequency: str
    period_salary: Decimal

    standard_hours_per_week: Decimal
    standard_hours_per_day: Decimal

    overtime_eligibility: str
    overtime_rate_multiplier: Decimal

    currency: str

    probation_end_date: Optional[date]
    probation_completed: bool

    vacation_days_annual: Decimal
    sick_days_annual: Decimal
    personal_days_annual: Decimal

    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
