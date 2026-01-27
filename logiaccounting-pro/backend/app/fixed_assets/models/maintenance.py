"""
Asset maintenance tracking models.
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
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    from app.fixed_assets.models.asset import FixedAsset


class MaintenanceType(str, Enum):
    """Types of maintenance."""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    INSPECTION = "inspection"
    UPGRADE = "upgrade"
    REPAIR = "repair"
    CALIBRATION = "calibration"


class MaintenanceStatus(str, Enum):
    """Maintenance work order status."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AssetMaintenance(Base):
    """
    Maintenance record for an asset.

    Tracks preventive and corrective maintenance,
    repairs, inspections, and upgrades.
    """
    __tablename__ = "asset_maintenance"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fixed_assets.id"),
        nullable=False
    )

    # Identification
    maintenance_number: Mapped[str] = mapped_column(String(30), nullable=False)
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        SQLEnum(MaintenanceType),
        nullable=False
    )

    # Schedule
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date)
    performed_date: Mapped[Optional[date]] = mapped_column(Date)
    next_due_date: Mapped[Optional[date]] = mapped_column(Date)

    # Description
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    work_performed: Mapped[Optional[str]] = mapped_column(Text)
    findings: Mapped[Optional[str]] = mapped_column(Text)

    # Costs
    labor_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    labor_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    labor_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    parts_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    external_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Capitalization
    is_capitalized: Mapped[bool] = mapped_column(Boolean, default=False)
    capitalized_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # Vendor
    vendor_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    vendor_name: Mapped[Optional[str]] = mapped_column(String(200))
    invoice_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # Parts used (JSON array)
    parts_used: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Status
    status: Mapped[MaintenanceStatus] = mapped_column(
        SQLEnum(MaintenanceStatus),
        default=MaintenanceStatus.SCHEDULED
    )

    # Completion
    completed_at: Mapped[Optional[datetime]] = mapped_column()
    performed_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    # Audit
    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    asset: Mapped["FixedAsset"] = relationship("FixedAsset", back_populates="maintenance_records")

    __table_args__ = (
        Index("idx_asset_maintenance_asset", "asset_id"),
        Index("idx_asset_maintenance_date", "scheduled_date"),
        Index("idx_asset_maintenance_status", "status"),
    )


class MaintenanceSchedule(Base):
    """
    Recurring maintenance schedule template.
    """
    __tablename__ = "maintenance_schedules"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Apply to
    category_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("asset_categories.id")
    )
    asset_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fixed_assets.id")
    )

    # Schedule
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    # daily, weekly, monthly, quarterly, yearly, usage_based
    frequency_value: Mapped[int] = mapped_column(Integer, default=1)

    # Usage-based
    usage_interval: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    usage_unit: Mapped[Optional[str]] = mapped_column(String(20))  # hours, miles, cycles

    # Details
    maintenance_type: Mapped[MaintenanceType] = mapped_column(SQLEnum(MaintenanceType))
    estimated_duration_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    instructions: Mapped[Optional[str]] = mapped_column(Text)
    checklist: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Notifications
    notify_days_before: Mapped[int] = mapped_column(Integer, default=7)
    notify_users: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Tracking
    last_generated: Mapped[Optional[date]] = mapped_column(Date)
    next_due_date: Mapped[Optional[date]] = mapped_column(Date)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        Index("idx_maintenance_schedules_customer", "customer_id"),
        Index("idx_maintenance_schedules_category", "category_id"),
    )
