"""
Asset transaction models for lifecycle events.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
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


class TransactionType(str, Enum):
    """Types of asset transactions."""
    ACQUISITION = "acquisition"
    DISPOSAL = "disposal"
    TRANSFER = "transfer"
    REVALUATION = "revaluation"
    IMPROVEMENT = "improvement"
    IMPAIRMENT = "impairment"
    WRITE_OFF = "write_off"


class TransactionStatus(str, Enum):
    """Transaction workflow status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    POSTED = "posted"
    CANCELLED = "cancelled"


class AssetTransaction(Base):
    """
    Asset transaction for tracking lifecycle events.

    Records acquisitions, disposals, transfers, revaluations,
    and other changes to fixed assets.
    """
    __tablename__ = "asset_transactions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    asset_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fixed_assets.id"),
        nullable=False
    )

    # Transaction identification
    transaction_number: Mapped[str] = mapped_column(String(30), nullable=False)
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType),
        nullable=False
    )
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # ==================== Disposal Fields ====================
    disposal_type: Mapped[Optional[str]] = mapped_column(String(20))
    proceeds: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    book_value_at_disposal: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    accumulated_at_disposal: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    gain_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    buyer_name: Mapped[Optional[str]] = mapped_column(String(200))
    buyer_contact: Mapped[Optional[str]] = mapped_column(String(200))

    # ==================== Transfer Fields ====================
    from_location: Mapped[Optional[str]] = mapped_column(String(200))
    to_location: Mapped[Optional[str]] = mapped_column(String(200))
    from_department_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    to_department_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    from_responsible_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    to_responsible_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # ==================== Revaluation Fields ====================
    old_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    new_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    old_useful_life: Mapped[Optional[int]] = mapped_column(Integer)
    new_useful_life: Mapped[Optional[int]] = mapped_column(Integer)
    revaluation_reason: Mapped[Optional[str]] = mapped_column(Text)
    appraiser: Mapped[Optional[str]] = mapped_column(String(200))
    appraisal_date: Mapped[Optional[date]] = mapped_column(Date)

    # ==================== Improvement Fields ====================
    improvement_description: Mapped[Optional[str]] = mapped_column(Text)
    extends_useful_life: Mapped[bool] = mapped_column(Boolean, default=False)
    additional_life_months: Mapped[Optional[int]] = mapped_column(Integer)

    # ==================== Accounting ====================
    journal_entry_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("journal_entries.id")
    )

    # Reference
    reference: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # ==================== Approval ====================
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column()
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500))

    # Status
    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus),
        default=TransactionStatus.DRAFT
    )

    # Audit
    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    asset: Mapped["FixedAsset"] = relationship("FixedAsset", back_populates="transactions")

    __table_args__ = (
        UniqueConstraint("customer_id", "transaction_number", name="uq_asset_transaction_number"),
        Index("idx_asset_transactions_asset", "asset_id"),
        Index("idx_asset_transactions_type", "customer_id", "transaction_type"),
        Index("idx_asset_transactions_date", "transaction_date"),
    )
