"""Employee schemas."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


class EmployeeCreate(BaseModel):
    """Create employee."""
    first_name: str = Field(..., max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)

    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = Field(None, max_length=50)

    email: EmailStr
    personal_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    mobile: Optional[str] = Field(None, max_length=30)

    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="US", max_length=2)

    department_id: Optional[UUID] = None
    job_title: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[UUID] = None
    cost_center_id: Optional[UUID] = None
    location: Optional[str] = Field(None, max_length=100)

    hire_date: date
    employment_type: str = "full_time"

    notes: Optional[str] = None


class EmployeeUpdate(BaseModel):
    """Update employee."""
    first_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)

    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None

    email: Optional[EmailStr] = None
    personal_email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    mobile: Optional[str] = Field(None, max_length=30)

    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)

    department_id: Optional[UUID] = None
    job_title: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[UUID] = None
    location: Optional[str] = Field(None, max_length=100)

    employment_status: Optional[str] = None
    employment_type: Optional[str] = None

    notes: Optional[str] = None


class TaxInfoUpdate(BaseModel):
    """Update employee tax information."""
    # US Tax
    federal_filing_status: Optional[str] = None
    federal_allowances: Optional[int] = None
    state_filing_status: Optional[str] = None
    state_allowances: Optional[int] = None
    additional_withholding: Optional[Decimal] = None

    # EU Tax (stored as JSON)
    tax_info_eu: Optional[dict] = None


class BankInfoUpdate(BaseModel):
    """Update employee bank information."""
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_type: Optional[str] = Field(None, max_length=20)
    bank_routing_number: Optional[str] = Field(None, max_length=20)
    bank_account_number: str = Field(..., min_length=4)  # Full number provided, store last 4


class EmergencyContactUpdate(BaseModel):
    """Update emergency contact."""
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=30)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)


class EmployeeResponse(BaseModel):
    """Employee response."""
    id: UUID
    employee_number: str

    first_name: str
    middle_name: Optional[str]
    last_name: str
    preferred_name: Optional[str]
    full_name: str
    display_name: str

    date_of_birth: Optional[date]
    gender: Optional[str]
    marital_status: Optional[str]
    nationality: Optional[str]

    email: str
    personal_email: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]

    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: str

    department_id: Optional[UUID]
    job_title: Optional[str]
    manager_id: Optional[UUID]
    cost_center_id: Optional[UUID]
    location: Optional[str]

    hire_date: date
    termination_date: Optional[date]
    employment_status: str
    employment_type: str

    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeSummary(BaseModel):
    """Employee summary for lists."""
    id: UUID
    employee_number: str
    display_name: str
    email: str
    job_title: Optional[str]
    department_id: Optional[UUID]
    employment_status: str
    employment_type: str
    hire_date: date
    is_active: bool

    class Config:
        from_attributes = True


class TerminateEmployee(BaseModel):
    """Terminate employee."""
    termination_date: date
    termination_reason: str = Field(..., max_length=500)
