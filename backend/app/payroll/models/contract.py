"""Employee contract and compensation models."""
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
from app.payroll.models.employee import PayFrequency


class CompensationType(str, Enum):
    SALARY = "salary"  # Annual salary
    HOURLY = "hourly"  # Hourly rate
    COMMISSION = "commission"  # Commission-based
    MIXED = "mixed"  # Salary + Commission


class OvertimeEligibility(str, Enum):
    EXEMPT = "exempt"  # Not eligible for OT (salaried)
    NON_EXEMPT = "non_exempt"  # Eligible for OT


class EmployeeContract(Base):
    """Employee contract with compensation details."""
    __tablename__ = "employee_contracts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)

    contract_number: Mapped[str] = mapped_column(String(30), nullable=False)

    # Contract period
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date)  # NULL = indefinite

    # Position details
    job_title: Mapped[str] = mapped_column(String(100), nullable=False)
    job_description: Mapped[Optional[str]] = mapped_column(Text)
    department_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # Compensation
    compensation_type: Mapped[CompensationType] = mapped_column(
        SQLEnum(CompensationType), default=CompensationType.SALARY
    )

    # For salary employees
    annual_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # For hourly employees
    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))

    # For commission employees
    commission_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))  # Percentage
    commission_base: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))  # Base salary if mixed

    # Pay frequency
    pay_frequency: Mapped[PayFrequency] = mapped_column(
        SQLEnum(PayFrequency), default=PayFrequency.BIWEEKLY
    )

    # Working hours
    standard_hours_per_week: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=40)
    standard_hours_per_day: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=8)

    # Overtime
    overtime_eligibility: Mapped[OvertimeEligibility] = mapped_column(
        SQLEnum(OvertimeEligibility), default=OvertimeEligibility.NON_EXEMPT
    )
    overtime_rate_multiplier: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=1.5)  # 1.5x, 2x, etc.

    # Currency
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Probation
    probation_end_date: Mapped[Optional[date]] = mapped_column(Date)
    probation_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Time off accruals (annual entitlements)
    vacation_days_annual: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=15)
    sick_days_annual: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=10)
    personal_days_annual: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=3)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    termination_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Additional terms stored as JSON
    additional_terms: Mapped[Optional[dict]] = mapped_column(JSONB)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", back_populates="contracts")

    __table_args__ = (
        UniqueConstraint("employee_id", "contract_number", name="uq_contract_number"),
        Index("idx_employee_contracts_employee", "employee_id"),
        Index("idx_employee_contracts_active", "employee_id", "is_active"),
        Index("idx_employee_contracts_dates", "start_date", "end_date"),
    )

    @property
    def period_salary(self) -> Decimal:
        """Calculate salary per pay period."""
        if self.compensation_type == CompensationType.HOURLY:
            weekly = self.hourly_rate * self.standard_hours_per_week
            if self.pay_frequency == PayFrequency.WEEKLY:
                return weekly
            elif self.pay_frequency == PayFrequency.BIWEEKLY:
                return weekly * 2
            elif self.pay_frequency == PayFrequency.SEMIMONTHLY:
                return (weekly * 52) / 24
            else:  # MONTHLY
                return (weekly * 52) / 12
        else:
            # Salary-based
            annual = self.annual_salary or Decimal(0)
            if self.pay_frequency == PayFrequency.WEEKLY:
                return annual / 52
            elif self.pay_frequency == PayFrequency.BIWEEKLY:
                return annual / 26
            elif self.pay_frequency == PayFrequency.SEMIMONTHLY:
                return annual / 24
            else:  # MONTHLY
                return annual / 12

    def calculate_hourly_rate(self) -> Decimal:
        """Calculate effective hourly rate."""
        if self.hourly_rate:
            return self.hourly_rate
        if self.annual_salary:
            annual_hours = self.standard_hours_per_week * 52
            return self.annual_salary / annual_hours
        return Decimal(0)


# Import Employee for type hints
from app.payroll.models.employee import Employee
