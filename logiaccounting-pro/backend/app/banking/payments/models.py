"""
Payment Processing Models
Payment batches and instructions
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from enum import Enum
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean,
    Integer, Numeric, Text, Date, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.database import Base


class BatchStatus(str, Enum):
    """Payment batch status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PROCESSING = "processing"
    SENT = "sent"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    """Payment methods"""
    ACH = "ach"
    WIRE = "wire"
    CHECK = "check"
    INTERNATIONAL_WIRE = "international_wire"


class BatchType(str, Enum):
    """Batch types"""
    AP = "ap"
    AR = "ar"
    PAYROLL = "payroll"
    OTHER = "other"


class InstructionStatus(str, Enum):
    """Payment instruction status"""
    PENDING = "pending"
    APPROVED = "approved"
    SENT = "sent"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentBatch(Base):
    """Payment batches for processing multiple payments"""
    __tablename__ = "payment_batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # Identification
    batch_number: Mapped[str] = mapped_column(String(30), nullable=False)
    batch_name: Mapped[Optional[str]] = mapped_column(String(200))

    # Bank account
    bank_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False
    )

    # Payment method and type
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    batch_type: Mapped[str] = mapped_column(String(20), default=BatchType.AP.value)

    # Currency
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Totals
    payment_count: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))

    # Dates
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[date]] = mapped_column(Date)

    # Status
    status: Mapped[str] = mapped_column(String(20), default=BatchStatus.DRAFT.value)

    # Approval workflow
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_threshold: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # File generation
    file_format: Mapped[Optional[str]] = mapped_column(String(20))
    file_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    file_reference: Mapped[Optional[str]] = mapped_column(String(100))

    # Processing
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Errors
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    instructions: Mapped[List["PaymentInstruction"]] = relationship(
        "PaymentInstruction", back_populates="batch", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("customer_id", "batch_number", name="uq_batch_number"),
        Index("idx_payment_batches_status", "status"),
    )


class PaymentInstruction(Base):
    """Individual payments within a batch"""
    __tablename__ = "payment_instructions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_batches.id", ondelete="CASCADE"),
        nullable=False
    )

    # Sequence
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Source
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Payee
    payee_type: Mapped[Optional[str]] = mapped_column(String(20))
    payee_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    payee_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Bank details
    payee_bank_name: Mapped[Optional[str]] = mapped_column(String(200))
    payee_account_number: Mapped[Optional[str]] = mapped_column(String(50))
    payee_routing_number: Mapped[Optional[str]] = mapped_column(String(50))
    payee_iban: Mapped[Optional[str]] = mapped_column(String(50))
    payee_swift: Mapped[Optional[str]] = mapped_column(String(20))

    # Address
    payee_address_line1: Mapped[Optional[str]] = mapped_column(String(200))
    payee_address_line2: Mapped[Optional[str]] = mapped_column(String(200))
    payee_city: Mapped[Optional[str]] = mapped_column(String(100))
    payee_state: Mapped[Optional[str]] = mapped_column(String(100))
    payee_postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    payee_country: Mapped[Optional[str]] = mapped_column(String(3))

    # Amount
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=Decimal("1"))
    base_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    # Payment details
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))
    remittance_info: Mapped[Optional[str]] = mapped_column(Text)

    # Check specific
    check_number: Mapped[Optional[str]] = mapped_column(String(20))

    # Wire specific
    purpose_code: Mapped[Optional[str]] = mapped_column(String(10))
    charge_bearer: Mapped[Optional[str]] = mapped_column(String(10))

    # Status
    status: Mapped[str] = mapped_column(String(20), default=InstructionStatus.PENDING.value)

    # Processing
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    confirmation_number: Mapped[Optional[str]] = mapped_column(String(100))

    # Errors
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    batch: Mapped["PaymentBatch"] = relationship(
        "PaymentBatch", back_populates="instructions"
    )

    __table_args__ = (
        UniqueConstraint("batch_id", "line_number", name="uq_instruction_line"),
    )


class PaymentHistory(Base):
    """Track all payments for documents"""
    __tablename__ = "payment_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # Source document
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Payment reference
    payment_instruction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    bank_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Details
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(30))
    reference: Mapped[Optional[str]] = mapped_column(String(100))

    # Allocation
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_payment_history_doc", "document_type", "document_id"),
    )
