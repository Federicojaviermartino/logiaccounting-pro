"""Employee model for HR and Payroll."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text, Date,
    Numeric, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class EmploymentStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    RETIRED = "retired"


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERN = "intern"


class PayFrequency(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    SEMIMONTHLY = "semimonthly"
    MONTHLY = "monthly"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    DOMESTIC_PARTNER = "domestic_partner"


class Employee(Base):
    """Employee master record."""
    __tablename__ = "employees"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Employee identification
    employee_number: Mapped[str] = mapped_column(String(20), nullable=False)

    # Personal information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    preferred_name: Mapped[Optional[str]] = mapped_column(String(100))

    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[Gender]] = mapped_column(SQLEnum(Gender))
    marital_status: Mapped[Optional[MaritalStatus]] = mapped_column(SQLEnum(MaritalStatus))
    nationality: Mapped[Optional[str]] = mapped_column(String(50))

    # Contact information
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    personal_email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    mobile: Mapped[Optional[str]] = mapped_column(String(30))

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(2), default="US")

    # Tax information (US)
    ssn_last_four: Mapped[Optional[str]] = mapped_column(String(4))  # Last 4 digits only
    federal_filing_status: Mapped[Optional[str]] = mapped_column(String(30))  # single, married, head_of_household
    federal_allowances: Mapped[int] = mapped_column(Integer, default=0)
    state_filing_status: Mapped[Optional[str]] = mapped_column(String(30))
    state_allowances: Mapped[int] = mapped_column(Integer, default=0)
    additional_withholding: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Tax information (EU) - stored as JSON for flexibility
    tax_info_eu: Mapped[Optional[dict]] = mapped_column(JSONB)  # tax_id, tax_class, church_tax, etc.

    # Employment details
    department_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    job_title: Mapped[Optional[str]] = mapped_column(String(100))
    manager_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("employees.id"))
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    location: Mapped[Optional[str]] = mapped_column(String(100))

    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    termination_date: Mapped[Optional[date]] = mapped_column(Date)
    termination_reason: Mapped[Optional[str]] = mapped_column(Text)

    employment_status: Mapped[EmploymentStatus] = mapped_column(
        SQLEnum(EmploymentStatus), default=EmploymentStatus.ACTIVE
    )
    employment_type: Mapped[EmploymentType] = mapped_column(
        SQLEnum(EmploymentType), default=EmploymentType.FULL_TIME
    )

    # Bank information for direct deposit
    bank_name: Mapped[Optional[str]] = mapped_column(String(100))
    bank_account_type: Mapped[Optional[str]] = mapped_column(String(20))  # checking, savings
    bank_routing_number: Mapped[Optional[str]] = mapped_column(String(20))
    bank_account_last_four: Mapped[Optional[str]] = mapped_column(String(4))  # Last 4 only

    # Emergency contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(200))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(30))
    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(String(50))

    # System fields
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contracts: Mapped[List["EmployeeContract"]] = relationship(
        "EmployeeContract", back_populates="employee", cascade="all, delete-orphan"
    )
    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee", remote_side=[id], foreign_keys=[manager_id]
    )

    __table_args__ = (
        UniqueConstraint("customer_id", "employee_number", name="uq_employee_number"),
        UniqueConstraint("customer_id", "email", name="uq_employee_email"),
        Index("idx_employees_customer", "customer_id"),
        Index("idx_employees_status", "customer_id", "employment_status"),
        Index("idx_employees_department", "customer_id", "department_id"),
        Index("idx_employees_manager", "manager_id"),
    )

    @property
    def full_name(self) -> str:
        """Get employee full name."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    @property
    def display_name(self) -> str:
        """Get display name (preferred or full)."""
        if self.preferred_name:
            return f"{self.preferred_name} {self.last_name}"
        return self.full_name

    @property
    def active_contract(self) -> Optional["EmployeeContract"]:
        """Get current active contract."""
        today = date.today()
        for contract in self.contracts:
            if contract.is_active and contract.start_date <= today:
                if not contract.end_date or contract.end_date >= today:
                    return contract
        return None
