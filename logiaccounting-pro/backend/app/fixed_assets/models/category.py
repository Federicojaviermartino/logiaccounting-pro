"""
Asset category and depreciation profile models.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    Column, String, Boolean, Integer, ForeignKey, Text,
    Numeric, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    from app.fixed_assets.models.asset import FixedAsset


class DepreciationMethod(str, Enum):
    """Supported depreciation methods."""
    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining_balance"
    DOUBLE_DECLINING = "double_declining"
    SUM_OF_YEARS = "sum_of_years"
    UNITS_OF_PRODUCTION = "units_of_production"


class PostingFrequency(str, Enum):
    """Depreciation posting frequency."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class AssetCategory(Base):
    """
    Asset category with default depreciation settings.

    Categories can be hierarchical and define default
    depreciation methods and useful lives for assets.
    """
    __tablename__ = "asset_categories"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Identification
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Hierarchy
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("asset_categories.id")
    )
    level: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[Optional[str]] = mapped_column(String(500))  # Materialized path

    # Default depreciation settings
    default_useful_life_months: Mapped[int] = mapped_column(Integer, nullable=False)
    default_salvage_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    default_depreciation_method: Mapped[DepreciationMethod] = mapped_column(
        SQLEnum(DepreciationMethod),
        nullable=False
    )

    # For declining balance
    default_declining_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Accounting - GL account mapping
    asset_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id")
    )
    accumulated_depreciation_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id")
    )
    depreciation_expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id")
    )
    gain_loss_disposal_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id")
    )

    # Settings
    capitalize_threshold: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=500)
    track_maintenance: Mapped[bool] = mapped_column(Boolean, default=True)
    require_serial_number: Mapped[bool] = mapped_column(Boolean, default=False)
    require_location: Mapped[bool] = mapped_column(Boolean, default=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parent = relationship("AssetCategory", remote_side=[id], backref="children")
    assets: Mapped[List["FixedAsset"]] = relationship("FixedAsset", back_populates="category")

    # Account relationships
    asset_account = relationship("ChartOfAccounts", foreign_keys=[asset_account_id])
    accumulated_depreciation_account = relationship("ChartOfAccounts", foreign_keys=[accumulated_depreciation_account_id])
    depreciation_expense_account = relationship("ChartOfAccounts", foreign_keys=[depreciation_expense_account_id])
    gain_loss_account = relationship("ChartOfAccounts", foreign_keys=[gain_loss_disposal_account_id])

    __table_args__ = (
        UniqueConstraint("customer_id", "code", name="uq_asset_category_code"),
        Index("idx_asset_categories_customer", "customer_id"),
        Index("idx_asset_categories_parent", "parent_id"),
    )

    @property
    def full_path(self) -> str:
        """Get full category path."""
        return self.path or self.code


class DepreciationProfile(Base):
    """
    Reusable depreciation configuration.

    Profiles define standard depreciation settings that
    can be applied to multiple assets.
    """
    __tablename__ = "depreciation_profiles"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Method
    depreciation_method: Mapped[DepreciationMethod] = mapped_column(
        SQLEnum(DepreciationMethod),
        nullable=False
    )

    # Rates and life
    useful_life_months: Mapped[Optional[int]] = mapped_column(Integer)
    salvage_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    declining_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Accounting
    depreciation_expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id")
    )
    accumulated_depreciation_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("chart_of_accounts.id")
    )

    # Posting
    posting_frequency: Mapped[PostingFrequency] = mapped_column(
        SQLEnum(PostingFrequency),
        default=PostingFrequency.MONTHLY
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("customer_id", "name", name="uq_depreciation_profile_name"),
        Index("idx_depreciation_profiles_customer", "customer_id"),
    )
