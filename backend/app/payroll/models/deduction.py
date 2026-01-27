"""Deduction and benefit type models."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text,
    Numeric, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DeductionCategory(str, Enum):
    TAX = "tax"  # Federal, state, local taxes
    INSURANCE = "insurance"  # Health, dental, vision
    RETIREMENT = "retirement"  # 401k, pension
    GARNISHMENT = "garnishment"  # Court-ordered
    UNION = "union"  # Union dues
    OTHER = "other"


class CalculationMethod(str, Enum):
    FIXED = "fixed"  # Fixed amount per period
    PERCENTAGE = "percentage"  # Percentage of gross
    PERCENTAGE_OF_NET = "percentage_of_net"  # Percentage of net
    TIERED = "tiered"  # Tax brackets
    CUSTOM = "custom"  # Custom calculation


class DeductionType(Base):
    """Deduction type configuration."""
    __tablename__ = "deduction_types"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    category: Mapped[DeductionCategory] = mapped_column(SQLEnum(DeductionCategory), nullable=False)
    calculation_method: Mapped[CalculationMethod] = mapped_column(
        SQLEnum(CalculationMethod), default=CalculationMethod.FIXED
    )

    # Default values (can be overridden per employee)
    default_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    default_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))  # e.g., 0.0765 for 7.65%

    # Limits
    annual_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))  # e.g., 401k limit
    per_period_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Employer contribution (if any)
    employer_match: Mapped[bool] = mapped_column(Boolean, default=False)
    employer_match_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    employer_match_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))

    # Tax treatment
    pre_tax: Mapped[bool] = mapped_column(Boolean, default=False)  # Reduces taxable income

    # GL Account mapping
    expense_account_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    liability_account_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # Applicability
    applies_to_all: Mapped[bool] = mapped_column(Boolean, default=False)  # Auto-apply to all employees

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("customer_id", "code", name="uq_deduction_type_code"),
        Index("idx_deduction_types_customer", "customer_id"),
        Index("idx_deduction_types_category", "customer_id", "category"),
    )


class EmployeeDeduction(Base):
    """Employee-specific deduction assignment."""
    __tablename__ = "employee_deductions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    deduction_type_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("deduction_types.id"), nullable=False)

    # Override default values
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))

    # Track YTD
    ytd_employee_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    ytd_employer_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Effective dates
    start_date: Mapped[Optional[datetime]] = mapped_column()
    end_date: Mapped[Optional[datetime]] = mapped_column()

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("employee_id", "deduction_type_id", name="uq_employee_deduction"),
        Index("idx_employee_deductions_employee", "employee_id"),
    )


class BenefitType(Base):
    """Benefit type configuration."""
    __tablename__ = "benefit_types"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    category: Mapped[str] = mapped_column(String(30), nullable=False)  # health, dental, vision, life, disability, etc.

    # Cost to employee per period
    employee_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Cost to employer per period
    employer_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Coverage details
    coverage_type: Mapped[Optional[str]] = mapped_column(String(30))  # employee_only, employee_spouse, family

    # GL Account mapping
    expense_account_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("customer_id", "code", name="uq_benefit_type_code"),
        Index("idx_benefit_types_customer", "customer_id"),
    )


class EmployeeBenefit(Base):
    """Employee benefit enrollment."""
    __tablename__ = "employee_benefits"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    benefit_type_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("benefit_types.id"), nullable=False)

    # Coverage selection
    coverage_type: Mapped[Optional[str]] = mapped_column(String(30))

    # Override costs
    employee_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    employer_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Enrollment dates
    enrollment_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    effective_date: Mapped[datetime] = mapped_column(nullable=False)
    termination_date: Mapped[Optional[datetime]] = mapped_column()

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        Index("idx_employee_benefits_employee", "employee_id"),
    )
