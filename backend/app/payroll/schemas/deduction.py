"""Deduction and benefit schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class DeductionTypeCreate(BaseModel):
    """Create deduction type."""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    category: str = Field(..., pattern="^(tax|insurance|retirement|garnishment|union|other)$")
    calculation_method: str = Field(default="fixed", pattern="^(fixed|percentage|percentage_of_net|tiered|custom)$")

    default_amount: Optional[Decimal] = Field(None, ge=0)
    default_percentage: Optional[Decimal] = Field(None, ge=0, le=1)

    annual_limit: Optional[Decimal] = Field(None, ge=0)
    per_period_limit: Optional[Decimal] = Field(None, ge=0)

    employer_match: bool = False
    employer_match_percentage: Optional[Decimal] = Field(None, ge=0, le=1)
    employer_match_limit: Optional[Decimal] = Field(None, ge=0)

    pre_tax: bool = False
    applies_to_all: bool = False


class DeductionTypeUpdate(BaseModel):
    """Update deduction type."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    default_amount: Optional[Decimal] = Field(None, ge=0)
    default_percentage: Optional[Decimal] = Field(None, ge=0, le=1)
    annual_limit: Optional[Decimal] = Field(None, ge=0)
    employer_match_percentage: Optional[Decimal] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None


class DeductionTypeResponse(BaseModel):
    """Deduction type response."""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    category: str
    calculation_method: str
    default_amount: Optional[Decimal]
    default_percentage: Optional[Decimal]
    annual_limit: Optional[Decimal]
    employer_match: bool
    employer_match_percentage: Optional[Decimal]
    pre_tax: bool
    applies_to_all: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeDeductionCreate(BaseModel):
    """Assign deduction to employee."""
    deduction_type_id: UUID
    amount: Optional[Decimal] = Field(None, ge=0)
    percentage: Optional[Decimal] = Field(None, ge=0, le=1)
    start_date: Optional[datetime] = None


class EmployeeDeductionUpdate(BaseModel):
    """Update employee deduction."""
    amount: Optional[Decimal] = Field(None, ge=0)
    percentage: Optional[Decimal] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None


class EmployeeDeductionResponse(BaseModel):
    """Employee deduction response."""
    id: UUID
    employee_id: UUID
    deduction_type_id: UUID
    amount: Optional[Decimal]
    percentage: Optional[Decimal]
    ytd_employee_amount: Decimal
    ytd_employer_amount: Decimal
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class BenefitTypeCreate(BaseModel):
    """Create benefit type."""
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    category: str = Field(..., max_length=30)  # health, dental, vision, life, disability
    employee_cost: Decimal = Field(default=0, ge=0)
    employer_cost: Decimal = Field(default=0, ge=0)
    coverage_type: Optional[str] = None


class BenefitTypeResponse(BaseModel):
    """Benefit type response."""
    id: UUID
    code: str
    name: str
    description: Optional[str]
    category: str
    employee_cost: Decimal
    employer_cost: Decimal
    coverage_type: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
