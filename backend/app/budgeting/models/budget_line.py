"""Budget line and period models."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text, Date,
    Numeric, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class DistributionMethod(str, Enum):
    EQUAL = "equal"
    SEASONAL = "seasonal"
    MANUAL = "manual"
    HISTORICAL = "historical"


class VarianceType(str, Enum):
    FAVORABLE = "favorable"
    UNFAVORABLE = "unfavorable"
    ON_TARGET = "on_target"


class BudgetLine(Base):
    """Budget line item by GL account."""
    __tablename__ = "budget_lines"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    version_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("budget_versions.id", ondelete="CASCADE"), nullable=False)

    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False)
    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)

    department_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    annual_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)

    ytd_actual: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    ytd_variance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    ytd_variance_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0)

    distribution_method: Mapped[DistributionMethod] = mapped_column(SQLEnum(DistributionMethod), default=DistributionMethod.EQUAL)
    distribution_pattern_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("distribution_patterns.id"))

    notes: Mapped[Optional[str]] = mapped_column(Text)
    assumptions: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    version: Mapped["BudgetVersion"] = relationship("BudgetVersion", back_populates="lines")
    periods: Mapped[List["BudgetPeriod"]] = relationship("BudgetPeriod", back_populates="line", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("version_id", "account_id", "department_id", "cost_center_id", name="uq_budget_line_account"),
        Index("idx_budget_lines_version", "version_id"),
        Index("idx_budget_lines_account", "account_id"),
    )


class BudgetPeriod(Base):
    """Monthly budget period."""
    __tablename__ = "budget_periods"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    line_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("budget_lines.id", ondelete="CASCADE"), nullable=False)

    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    budgeted_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    committed_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)

    variance_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    variance_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0)
    variance_type: Mapped[Optional[VarianceType]] = mapped_column(SQLEnum(VarianceType))

    forecast_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    line: Mapped["BudgetLine"] = relationship("BudgetLine", back_populates="periods")

    __table_args__ = (
        UniqueConstraint("line_id", "period_year", "period_month", name="uq_budget_period"),
        Index("idx_budget_periods_line", "line_id"),
    )
