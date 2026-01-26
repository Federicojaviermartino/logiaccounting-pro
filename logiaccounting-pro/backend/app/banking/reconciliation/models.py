"""
Bank Reconciliation Models
Reconciliation sessions and matching rules
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


class ReconciliationStatus(str, Enum):
    """Reconciliation session status"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchType(str, Enum):
    """Transaction match type"""
    EXACT = "exact"
    AMOUNT = "amount"
    MANUAL = "manual"
    RULE_BASED = "rule_based"


class LineStatus(str, Enum):
    """Reconciliation line status"""
    MATCHED = "matched"
    UNMATCHED_STATEMENT = "unmatched_statement"
    UNMATCHED_BOOK = "unmatched_book"
    EXCEPTION = "exception"
    ADJUSTED = "adjusted"


class BankReconciliation(Base):
    """Bank reconciliation sessions"""
    __tablename__ = "bank_reconciliations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False
    )

    # Identification
    reconciliation_number: Mapped[str] = mapped_column(String(30), nullable=False)

    # Period
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Statement balances
    statement_opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    statement_closing_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # Book balances
    book_opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    book_closing_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # Reconciliation amounts
    total_matched: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    total_unmatched_statement: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    total_unmatched_book: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))

    # Outstanding items
    outstanding_deposits: Mapped[int] = mapped_column(Integer, default=0)
    outstanding_withdrawals: Mapped[int] = mapped_column(Integer, default=0)

    # Difference
    reconciling_difference: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))

    # Status
    status: Mapped[str] = mapped_column(String(20), default=ReconciliationStatus.DRAFT.value)

    # Approval
    completed_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    lines: Mapped[List["BankReconciliationLine"]] = relationship(
        "BankReconciliationLine", back_populates="reconciliation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("customer_id", "reconciliation_number", name="uq_recon_number"),
        Index("idx_recon_account", "account_id"),
        Index("idx_recon_status", "status"),
    )

    @property
    def is_balanced(self) -> bool:
        """Check if reconciliation is balanced"""
        return abs(self.reconciling_difference) < Decimal("0.01")


class BankReconciliationLine(Base):
    """Reconciliation matched items"""
    __tablename__ = "bank_reconciliation_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reconciliation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_reconciliations.id", ondelete="CASCADE"),
        nullable=False
    )

    # Transaction link
    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Book entry link
    journal_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Match type
    match_type: Mapped[Optional[str]] = mapped_column(String(30))

    # Amounts
    statement_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    book_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    difference: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    # Match confidence
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Status
    status: Mapped[str] = mapped_column(String(20), default=LineStatus.MATCHED.value)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    matched_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    matched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    reconciliation: Mapped["BankReconciliation"] = relationship(
        "BankReconciliation", back_populates="lines"
    )


class BankMatchingRule(Base):
    """Auto-matching rules for transactions"""
    __tablename__ = "bank_matching_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Matching criteria
    match_criteria: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Action when matched
    match_action: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Priority
    priority: Mapped[int] = mapped_column(Integer, default=100)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Stats
    times_matched: Mapped[int] = mapped_column(Integer, default=0)
    last_matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
