"""
Cash Flow Forecasting Models
Forecasts, planned transactions, and cash positions
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
from enum import Enum
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean,
    Integer, Numeric, Text, Date, Time, Index, UniqueConstraint, ARRAY
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.database import Base


class ForecastStatus(str, Enum):
    """Forecast status"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Granularity(str, Enum):
    """Forecast granularity"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TransactionType(str, Enum):
    """Planned transaction type"""
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class RecurrencePattern(str, Enum):
    """Recurrence patterns"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class CashFlowForecast(Base):
    """Cash flow forecast definition"""
    __tablename__ = "cash_flow_forecasts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # Identification
    forecast_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Period
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    granularity: Mapped[str] = mapped_column(String(20), default=Granularity.WEEKLY.value)

    # Settings
    include_ar: Mapped[bool] = mapped_column(Boolean, default=True)
    include_ap: Mapped[bool] = mapped_column(Boolean, default=True)
    include_recurring: Mapped[bool] = mapped_column(Boolean, default=True)
    include_planned: Mapped[bool] = mapped_column(Boolean, default=True)

    # Accounts included (empty = all)
    bank_account_ids: Mapped[Optional[List[str]]] = mapped_column(JSONB)

    # Status
    status: Mapped[str] = mapped_column(String(20), default=ForecastStatus.DRAFT.value)

    # Generation
    last_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    generated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    lines: Mapped[List["CashFlowForecastLine"]] = relationship(
        "CashFlowForecastLine", back_populates="forecast", cascade="all, delete-orphan"
    )


class CashFlowForecastLine(Base):
    """Individual period in a forecast"""
    __tablename__ = "cash_flow_forecast_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    forecast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cash_flow_forecasts.id", ondelete="CASCADE"),
        nullable=False
    )

    # Period
    period_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_label: Mapped[Optional[str]] = mapped_column(String(50))

    # Opening balance
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # Inflows
    ar_collections: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    other_income: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    planned_inflows: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    total_inflows: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))

    # Outflows
    ap_payments: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    payroll: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    tax_payments: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    loan_payments: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    other_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    planned_outflows: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    total_outflows: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))

    # Net and closing
    net_cash_flow: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # Minimum balance requirement
    min_balance_required: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    shortfall: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    # Breakdown details
    inflow_details: Mapped[Optional[dict]] = mapped_column(JSONB)
    outflow_details: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    forecast: Mapped["CashFlowForecast"] = relationship(
        "CashFlowForecast", back_populates="lines"
    )

    __table_args__ = (
        UniqueConstraint("forecast_id", "period_date", name="uq_forecast_period"),
        Index("idx_forecast_lines_period", "forecast_id", "period_date"),
    )


class PlannedCashTransaction(Base):
    """Planned cash transactions for forecasting"""
    __tablename__ = "planned_cash_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # Description
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))

    # Type
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Account
    bank_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Schedule
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_pattern: Mapped[Optional[str]] = mapped_column(String(20))
    recurrence_end_date: Mapped[Optional[date]] = mapped_column(Date)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_planned_trans_date", "scheduled_date"),
    )


class CashPosition(Base):
    """Daily cash position snapshot"""
    __tablename__ = "cash_positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    snapshot_time: Mapped[time] = mapped_column(Time, default=time(23, 59, 59))

    # Total cash position
    total_cash: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # By currency
    cash_by_currency: Mapped[Optional[dict]] = mapped_column(JSONB)

    # By account
    cash_by_account: Mapped[Optional[List[dict]]] = mapped_column(JSONB)

    # AR/AP position
    total_ar_outstanding: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    total_ap_outstanding: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    net_working_capital: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("customer_id", "snapshot_date", name="uq_cash_position_date"),
        Index("idx_cash_position_date", "customer_id", "snapshot_date"),
    )
