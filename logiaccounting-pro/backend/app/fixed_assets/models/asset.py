"""
Fixed asset model.
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
from sqlalchemy.ext.hybrid import hybrid_property

from app.database import Base
from app.fixed_assets.models.category import DepreciationMethod

if TYPE_CHECKING:
    from app.fixed_assets.models.category import AssetCategory
    from app.fixed_assets.models.depreciation import DepreciationSchedule, DepreciationEntry
    from app.fixed_assets.models.transaction import AssetTransaction
    from app.fixed_assets.models.maintenance import AssetMaintenance


class AssetStatus(str, Enum):
    """Asset lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    UNDER_MAINTENANCE = "under_maintenance"
    DISPOSED = "disposed"
    TRANSFERRED = "transferred"
    FULLY_DEPRECIATED = "fully_depreciated"


class AcquisitionType(str, Enum):
    """How the asset was acquired."""
    PURCHASE = "purchase"
    LEASE = "lease"
    CONSTRUCTION = "construction"
    DONATION = "donation"
    TRANSFER_IN = "transfer_in"
    TRADE_IN = "trade_in"


class DisposalType(str, Enum):
    """How the asset was disposed."""
    SOLD = "sold"
    SCRAPPED = "scrapped"
    DONATED = "donated"
    LOST = "lost"
    STOLEN = "stolen"
    TRADE_IN = "trade_in"
    WRITTEN_OFF = "written_off"


class FixedAsset(Base):
    """
    Fixed asset register entry.

    Represents a tangible long-term asset owned by the company,
    subject to depreciation over its useful life.
    """
    __tablename__ = "fixed_assets"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # ==================== Identification ====================
    asset_number: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # ==================== Classification ====================
    category_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("asset_categories.id"),
        nullable=False
    )
    depreciation_profile_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("depreciation_profiles.id")
    )

    # ==================== Location ====================
    location: Mapped[Optional[str]] = mapped_column(String(200))
    building: Mapped[Optional[str]] = mapped_column(String(100))
    floor: Mapped[Optional[str]] = mapped_column(String(50))
    room: Mapped[Optional[str]] = mapped_column(String(50))
    department_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    responsible_person_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id")
    )

    # ==================== Physical Attributes ====================
    serial_number: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100))
    barcode: Mapped[Optional[str]] = mapped_column(String(50))
    tag_number: Mapped[Optional[str]] = mapped_column(String(50))  # Physical tag

    # Dimensions (optional)
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    weight_unit: Mapped[Optional[str]] = mapped_column(String(10))  # kg, lb

    # ==================== Acquisition ====================
    acquisition_type: Mapped[AcquisitionType] = mapped_column(
        SQLEnum(AcquisitionType),
        nullable=False
    )
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    in_service_date: Mapped[Optional[date]] = mapped_column(Date)  # When depreciation starts

    # Vendor/Source
    supplier_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    purchase_order_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    invoice_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # ==================== Costs ====================
    acquisition_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    installation_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    other_costs: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Currency
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # ==================== Depreciation Settings ====================
    depreciation_method: Mapped[DepreciationMethod] = mapped_column(
        SQLEnum(DepreciationMethod),
        nullable=False
    )
    useful_life_months: Mapped[int] = mapped_column(Integer, nullable=False)
    salvage_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    salvage_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    # For declining balance
    declining_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # For units of production
    total_estimated_units: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    units_produced_to_date: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(20))  # hours, miles, units

    # ==================== Current Values ====================
    accumulated_depreciation: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    book_value: Mapped[Decimal] = mapped_column(Numeric(18, 2))

    # ==================== Depreciation Status ====================
    depreciation_start_date: Mapped[Optional[date]] = mapped_column(Date)
    last_depreciation_date: Mapped[Optional[date]] = mapped_column(Date)
    last_depreciation_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    is_fully_depreciated: Mapped[bool] = mapped_column(Boolean, default=False)
    fully_depreciated_date: Mapped[Optional[date]] = mapped_column(Date)

    # Depreciation suspended?
    depreciation_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    suspension_reason: Mapped[Optional[str]] = mapped_column(String(200))

    # ==================== Insurance ====================
    insured_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    insurance_policy: Mapped[Optional[str]] = mapped_column(String(100))
    insurance_company: Mapped[Optional[str]] = mapped_column(String(100))
    insurance_start_date: Mapped[Optional[date]] = mapped_column(Date)
    insurance_expiry_date: Mapped[Optional[date]] = mapped_column(Date)

    # ==================== Warranty ====================
    warranty_start_date: Mapped[Optional[date]] = mapped_column(Date)
    warranty_expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    warranty_provider: Mapped[Optional[str]] = mapped_column(String(100))
    warranty_terms: Mapped[Optional[str]] = mapped_column(Text)

    # ==================== Status ====================
    status: Mapped[AssetStatus] = mapped_column(
        SQLEnum(AssetStatus),
        default=AssetStatus.DRAFT
    )

    # ==================== Disposal ====================
    disposal_date: Mapped[Optional[date]] = mapped_column(Date)
    disposal_type: Mapped[Optional[DisposalType]] = mapped_column(SQLEnum(DisposalType))
    disposal_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    disposal_reason: Mapped[Optional[str]] = mapped_column(Text)
    disposal_buyer: Mapped[Optional[str]] = mapped_column(String(200))
    disposal_journal_entry_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # ==================== Notes ====================
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # ==================== Audit ====================
    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # ==================== Relationships ====================
    category: Mapped["AssetCategory"] = relationship("AssetCategory", back_populates="assets")
    depreciation_profile = relationship("DepreciationProfile")
    responsible_person = relationship("User", foreign_keys=[responsible_person_id])

    attachments: Mapped[List["AssetAttachment"]] = relationship(
        "AssetAttachment",
        back_populates="asset",
        cascade="all, delete-orphan"
    )
    depreciation_schedule: Mapped[List["DepreciationSchedule"]] = relationship(
        "DepreciationSchedule",
        back_populates="asset",
        cascade="all, delete-orphan"
    )
    depreciation_entries: Mapped[List["DepreciationEntry"]] = relationship(
        "DepreciationEntry",
        back_populates="asset"
    )
    transactions: Mapped[List["AssetTransaction"]] = relationship(
        "AssetTransaction",
        back_populates="asset"
    )
    maintenance_records: Mapped[List["AssetMaintenance"]] = relationship(
        "AssetMaintenance",
        back_populates="asset"
    )

    __table_args__ = (
        UniqueConstraint("customer_id", "asset_number", name="uq_fixed_asset_number"),
        Index("idx_fixed_assets_customer", "customer_id"),
        Index("idx_fixed_assets_category", "category_id"),
        Index("idx_fixed_assets_status", "customer_id", "status"),
        Index("idx_fixed_assets_location", "customer_id", "department_id"),
        Index("idx_fixed_assets_depreciation", "customer_id", "is_fully_depreciated"),
        Index("idx_fixed_assets_serial", "customer_id", "serial_number"),
    )

    # ==================== Computed Properties ====================

    @hybrid_property
    def depreciable_amount(self) -> Decimal:
        """Amount subject to depreciation."""
        return self.total_cost - self.salvage_value

    @hybrid_property
    def remaining_life_months(self) -> int:
        """Remaining useful life in months."""
        if self.is_fully_depreciated:
            return 0

        if not self.depreciation_start_date:
            return self.useful_life_months

        from dateutil.relativedelta import relativedelta
        months_elapsed = (
            (date.today().year - self.depreciation_start_date.year) * 12 +
            (date.today().month - self.depreciation_start_date.month)
        )
        return max(0, self.useful_life_months - months_elapsed)

    @hybrid_property
    def depreciation_percent(self) -> Decimal:
        """Percentage of asset depreciated."""
        if self.total_cost == 0:
            return Decimal(0)
        return (self.accumulated_depreciation / self.total_cost) * 100

    @hybrid_property
    def is_insured(self) -> bool:
        """Check if asset is currently insured."""
        if not self.insurance_expiry_date:
            return False
        return self.insurance_expiry_date >= date.today()

    @hybrid_property
    def is_under_warranty(self) -> bool:
        """Check if asset is under warranty."""
        if not self.warranty_expiry_date:
            return False
        return self.warranty_expiry_date >= date.today()

    @hybrid_property
    def age_in_months(self) -> int:
        """Asset age since acquisition."""
        if not self.acquisition_date:
            return 0

        from dateutil.relativedelta import relativedelta
        delta = relativedelta(date.today(), self.acquisition_date)
        return delta.years * 12 + delta.months

    def calculate_book_value(self) -> Decimal:
        """Calculate current book value."""
        return self.total_cost - self.accumulated_depreciation

    def update_book_value(self) -> None:
        """Update book value from accumulated depreciation."""
        self.book_value = self.calculate_book_value()

        # Check if fully depreciated
        if self.book_value <= self.salvage_value:
            self.is_fully_depreciated = True
            self.fully_depreciated_date = date.today()


class AssetAttachment(Base):
    """
    Documents and images attached to an asset.
    """
    __tablename__ = "asset_attachments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fixed_assets.id", ondelete="CASCADE"),
        nullable=False
    )

    # File info
    attachment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # image, document, warranty, invoice, manual, certificate

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))

    description: Mapped[Optional[str]] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    uploaded_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    asset: Mapped["FixedAsset"] = relationship("FixedAsset", back_populates="attachments")

    __table_args__ = (
        Index("idx_asset_attachments_asset", "asset_id"),
    )
