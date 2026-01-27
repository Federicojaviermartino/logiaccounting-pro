"""Variance threshold and alert models."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text,
    Numeric, Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class VarianceThreshold(Base):
    """Variance threshold configuration for alerts."""
    __tablename__ = "variance_thresholds"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Scope (all optional - more specific = higher priority)
    budget_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("budgets.id"))
    account_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))
    account_type: Mapped[Optional[str]] = mapped_column(String(20))
    department_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Thresholds (percent or absolute amount)
    warning_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=5)
    critical_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=10)
    warning_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    critical_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    # Notification settings
    notify_on_warning: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_on_critical: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_users: Mapped[Optional[List]] = mapped_column(JSONB)
    notify_emails: Mapped[Optional[List]] = mapped_column(JSONB)
    notify_roles: Mapped[Optional[List]] = mapped_column(JSONB)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_variance_thresholds_customer", "customer_id"),
        Index("idx_variance_thresholds_budget", "budget_id"),
    )


class VarianceAlert(Base):
    """Generated variance alert."""
    __tablename__ = "variance_alerts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # References
    budget_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False)
    budget_period_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("budget_periods.id"), nullable=False)
    account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False)
    threshold_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("variance_thresholds.id"))

    # Denormalized for display
    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    budget_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Period info
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Variance details
    budgeted_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    variance_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    variance_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    variance_type: Mapped[str] = mapped_column(String(20), nullable=False)  # favorable/unfavorable

    # Alert info
    alert_level: Mapped[AlertLevel] = mapped_column(SQLEnum(AlertLevel), nullable=False)
    threshold_used: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[AlertStatus] = mapped_column(SQLEnum(AlertStatus), default=AlertStatus.NEW)

    # Resolution tracking
    acknowledged_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column()
    resolved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column()
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        Index("idx_variance_alerts_customer", "customer_id"),
        Index("idx_variance_alerts_budget", "budget_id"),
        Index("idx_variance_alerts_status", "customer_id", "status"),
        Index("idx_variance_alerts_level", "customer_id", "alert_level"),
    )
