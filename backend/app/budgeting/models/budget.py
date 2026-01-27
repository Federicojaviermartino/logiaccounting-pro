"""Budget and BudgetVersion models."""
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


class BudgetType(str, Enum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    PROJECT = "project"
    DEPARTMENTAL = "departmental"


class BudgetStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class VersionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class Budget(Base):
    """Budget master record."""
    __tablename__ = "budgets"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    budget_code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    budget_type: Mapped[BudgetType] = mapped_column(SQLEnum(BudgetType), default=BudgetType.ANNUAL)

    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    department_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    project_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[BudgetStatus] = mapped_column(SQLEnum(BudgetStatus), default=BudgetStatus.DRAFT)
    active_version_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_overspend: Mapped[bool] = mapped_column(Boolean, default=False)
    overspend_threshold_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=10)

    total_revenue: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    total_net_income: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)

    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column()

    versions: Mapped[List["BudgetVersion"]] = relationship("BudgetVersion", back_populates="budget", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("customer_id", "budget_code", name="uq_budget_code"),
        Index("idx_budgets_customer", "customer_id"),
        Index("idx_budgets_fiscal_year", "customer_id", "fiscal_year"),
        Index("idx_budgets_status", "customer_id", "status"),
    )


class BudgetVersion(Base):
    """Budget version/scenario."""
    __tablename__ = "budget_versions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    budget_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version_type: Mapped[str] = mapped_column(String(30), default="original")

    parent_version_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("budget_versions.id"))

    total_revenue: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    total_net_income: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)

    status: Mapped[VersionStatus] = mapped_column(SQLEnum(VersionStatus), default=VersionStatus.DRAFT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    submitted_at: Mapped[Optional[datetime]] = mapped_column()
    submitted_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column()
    approved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    budget: Mapped["Budget"] = relationship("Budget", back_populates="versions")
    lines: Mapped[List["BudgetLine"]] = relationship("BudgetLine", back_populates="version", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("budget_id", "version_number", name="uq_budget_version_number"),
        Index("idx_budget_versions_budget", "budget_id"),
        Index("idx_budget_versions_active", "budget_id", "is_active"),
    )

    def recalculate_totals(self):
        """Recalculate totals from lines."""
        total_revenue = Decimal(0)
        total_expenses = Decimal(0)
        for line in self.lines:
            if line.account_type in ('revenue', 'income'):
                total_revenue += line.annual_amount
            elif line.account_type in ('expense', 'cost'):
                total_expenses += line.annual_amount
        self.total_revenue = total_revenue
        self.total_expenses = total_expenses
        self.total_net_income = total_revenue - total_expenses
