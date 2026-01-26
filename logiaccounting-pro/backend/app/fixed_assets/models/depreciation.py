"""
Depreciation schedule and entry models.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    Column, String, Boolean, Integer, ForeignKey, Text, Date,
    Numeric, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    from app.fixed_assets.models.asset import FixedAsset
    from app.fixed_assets.models.category import AssetCategory


class DepreciationSchedule(Base):
    """
    Planned depreciation schedule for an asset.

    Pre-calculated depreciation amounts for each period
    over the asset's useful life.
    """
    __tablename__ = "depreciation_schedules"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fixed_assets.id", ondelete="CASCADE"),
        nullable=False
    )

    # Period identification
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Calculated amounts
    opening_book_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    depreciation_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    accumulated_depreciation: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    closing_book_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # For units of production
    units_this_period: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    cumulative_units: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # Status
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)
    posted_entry_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("depreciation_entries.id")
    )

    # Adjustments
    is_adjusted: Mapped[bool] = mapped_column(Boolean, default=False)
    original_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    adjustment_reason: Mapped[Optional[str]] = mapped_column(String(200))

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    asset: Mapped["FixedAsset"] = relationship("FixedAsset", back_populates="depreciation_schedule")

    __table_args__ = (
        UniqueConstraint("asset_id", "period_number", name="uq_depreciation_schedule_period"),
        Index("idx_depreciation_schedules_asset", "asset_id"),
        Index("idx_depreciation_schedules_period", "period_year", "period_month"),
    )


class DepreciationRunStatus(str, Enum):
    """Status of depreciation batch run."""
    DRAFT = "draft"
    CALCULATED = "calculated"
    POSTED = "posted"
    CANCELLED = "cancelled"


class DepreciationRun(Base):
    """
    Batch depreciation processing run.

    Groups depreciation entries for a period and
    manages the posting workflow.
    """
    __tablename__ = "depreciation_runs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Run identification
    run_number: Mapped[str] = mapped_column(String(30), nullable=False)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Period
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Scope
    category_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("asset_categories.id")
    )  # NULL = all categories
    department_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # Results
    assets_processed: Mapped[int] = mapped_column(Integer, default=0)
    assets_skipped: Mapped[int] = mapped_column(Integer, default=0)
    total_depreciation: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Status
    status: Mapped[DepreciationRunStatus] = mapped_column(
        SQLEnum(DepreciationRunStatus),
        default=DepreciationRunStatus.DRAFT
    )

    # Error tracking
    errors: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of errors

    # Posting
    journal_entry_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("journal_entries.id")
    )
    posted_at: Mapped[Optional[datetime]] = mapped_column()
    posted_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    # Audit
    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entries: Mapped[List["DepreciationEntry"]] = relationship(
        "DepreciationEntry",
        back_populates="depreciation_run"
    )
    category = relationship("AssetCategory")

    __table_args__ = (
        UniqueConstraint("customer_id", "run_number", name="uq_depreciation_run_number"),
        Index("idx_depreciation_runs_customer", "customer_id"),
        Index("idx_depreciation_runs_period", "customer_id", "period_year", "period_month"),
    )


class DepreciationEntryStatus(str, Enum):
    """Status of individual depreciation entry."""
    CALCULATED = "calculated"
    POSTED = "posted"
    REVERSED = "reversed"
    SKIPPED = "skipped"


class DepreciationEntry(Base):
    """
    Individual asset depreciation entry.

    Created during depreciation run for each asset,
    linked to journal entry when posted.
    """
    __tablename__ = "depreciation_entries"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Link to run
    depreciation_run_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("depreciation_runs.id")
    )

    # Period
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Asset
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fixed_assets.id"),
        nullable=False
    )
    asset_number: Mapped[str] = mapped_column(String(30), nullable=False)  # Denormalized
    asset_name: Mapped[str] = mapped_column(String(200), nullable=False)  # Denormalized

    # Category (denormalized for reporting)
    category_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Depreciation method used
    depreciation_method: Mapped[str] = mapped_column(String(30), nullable=False)

    # Amounts
    depreciation_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Before/After (for audit trail)
    book_value_before: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    book_value_after: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    accumulated_before: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    accumulated_after: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Units (for units of production)
    units_this_period: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # Accounting
    expense_account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    accumulated_account_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    journal_entry_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("journal_entries.id")
    )

    # Status
    status: Mapped[DepreciationEntryStatus] = mapped_column(
        SQLEnum(DepreciationEntryStatus),
        default=DepreciationEntryStatus.CALCULATED
    )
    skip_reason: Mapped[Optional[str]] = mapped_column(String(200))

    # Posting
    posted_at: Mapped[Optional[datetime]] = mapped_column()
    posted_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    asset: Mapped["FixedAsset"] = relationship("FixedAsset", back_populates="depreciation_entries")
    depreciation_run: Mapped[Optional["DepreciationRun"]] = relationship(
        "DepreciationRun",
        back_populates="entries"
    )

    __table_args__ = (
        Index("idx_depreciation_entries_asset", "asset_id"),
        Index("idx_depreciation_entries_period", "period_year", "period_month"),
        Index("idx_depreciation_entries_run", "depreciation_run_id"),
        Index("idx_depreciation_entries_customer", "customer_id"),
    )
