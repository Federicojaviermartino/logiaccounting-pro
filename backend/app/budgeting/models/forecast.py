"""Rolling forecast models."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text,
    Numeric, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class ForecastMethod(str, Enum):
    TREND = "trend"
    MOVING_AVERAGE = "moving_average"
    REGRESSION = "regression"
    MANUAL = "manual"
    SEASONAL = "seasonal"
    HYBRID = "hybrid"


class ForecastStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class RollingForecast(Base):
    """Rolling forecast projection."""
    __tablename__ = "rolling_forecasts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    budget_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False)

    forecast_number: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Forecast parameters
    base_date: Mapped[datetime] = mapped_column(nullable=False)  # Current month
    forecast_months: Mapped[int] = mapped_column(Integer, default=12)  # Horizon
    forecast_method: Mapped[ForecastMethod] = mapped_column(SQLEnum(ForecastMethod), default=ForecastMethod.TREND)

    # Calculated totals
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    total_net_income: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)

    status: Mapped[ForecastStatus] = mapped_column(SQLEnum(ForecastStatus), default=ForecastStatus.DRAFT)

    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    lines: Mapped[List["ForecastLine"]] = relationship("ForecastLine", back_populates="forecast", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("customer_id", "forecast_number", name="uq_forecast_number"),
        Index("idx_rolling_forecasts_customer", "customer_id"),
        Index("idx_rolling_forecasts_budget", "budget_id"),
    )


class ForecastLine(Base):
    """Forecast line detail by account and period."""
    __tablename__ = "forecast_lines"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    forecast_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("rolling_forecasts.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False)

    # Denormalized
    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Period
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Data type: actual (historical) or forecast (projected)
    data_type: Mapped[str] = mapped_column(String(20), nullable=False)  # actual, forecast, budget

    # Amounts
    budget_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    forecast_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)

    # Calculation details
    calculation_method: Mapped[Optional[str]] = mapped_column(String(50))
    calculation_basis: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Confidence metrics
    confidence_percent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    range_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    range_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    forecast: Mapped["RollingForecast"] = relationship("RollingForecast", back_populates="lines")

    __table_args__ = (
        UniqueConstraint("forecast_id", "account_id", "period_year", "period_month", name="uq_forecast_line"),
        Index("idx_forecast_lines_forecast", "forecast_id"),
    )
