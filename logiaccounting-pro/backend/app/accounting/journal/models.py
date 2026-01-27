"""
Journal Entry Models
SQLAlchemy models for journal entries and lines
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, ForeignKey,
    Numeric, Integer, Text, Enum as SQLEnum, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class EntryTypeEnum(str, Enum):
    """Journal entry types."""
    STANDARD = "standard"      # Manual entry
    INVOICE = "invoice"        # From sales invoice
    BILL = "bill"              # From supplier bill
    PAYMENT = "payment"        # Payment received/made
    RECEIPT = "receipt"        # Cash receipt
    ADJUSTMENT = "adjustment"  # Period-end adjustments
    CLOSING = "closing"        # Year-end closing
    REVERSAL = "reversal"      # Reversal of previous entry
    OPENING = "opening"        # Opening balances
    DEPRECIATION = "depreciation"  # Asset depreciation
    ACCRUAL = "accrual"        # Accrual entries
    TRANSFER = "transfer"      # Inter-account transfers


class EntryStatusEnum(str, Enum):
    """Journal entry status."""
    DRAFT = "draft"
    PENDING = "pending"        # Awaiting approval
    APPROVED = "approved"      # Approved, ready to post
    POSTED = "posted"          # Posted to ledger
    REVERSED = "reversed"      # Reversed by another entry
    VOIDED = "voided"          # Voided/cancelled


class JournalEntry(Base):
    """Journal entry header."""

    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Entry identification
    entry_number = Column(String(50), nullable=False)  # JE-2026-0001
    entry_date = Column(Date, nullable=False)
    fiscal_period_id = Column(UUID(as_uuid=True), ForeignKey("fiscal_periods.id"))

    # Entry type and status
    entry_type = Column(SQLEnum(EntryTypeEnum), nullable=False, default=EntryTypeEnum.STANDARD)
    status = Column(SQLEnum(EntryStatusEnum), nullable=False, default=EntryStatusEnum.DRAFT)

    # Description and reference
    description = Column(Text)
    memo = Column(Text)
    reference = Column(String(100))  # External reference number

    # Source document tracking
    source_type = Column(String(50))  # 'invoice', 'bill', 'payment'
    source_id = Column(UUID(as_uuid=True))
    source_number = Column(String(50))

    # Totals (must balance)
    total_debit = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    total_credit = Column(Numeric(15, 2), nullable=False, default=Decimal("0"))

    # Multi-currency support
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Numeric(12, 6), default=Decimal("1"))
    base_total_debit = Column(Numeric(15, 2), default=Decimal("0"))
    base_total_credit = Column(Numeric(15, 2), default=Decimal("0"))

    # Reversal tracking
    is_reversing = Column(Boolean, default=False)
    reversed_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"))
    reversal_date = Column(Date)

    # Recurring entry reference
    recurring_entry_id = Column(UUID(as_uuid=True), ForeignKey("recurring_entries.id"))

    # Attachments
    attachments = Column(JSONB, default=list)  # List of file references

    # Audit trail
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    submitted_at = Column(DateTime)

    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)

    posted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    posted_at = Column(DateTime)

    voided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    voided_at = Column(DateTime)
    void_reason = Column(Text)

    # Relationships
    lines = relationship(
        "JournalLine",
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="JournalLine.line_number"
    )
    fiscal_period = relationship("FiscalPeriod")
    reversed_entry = relationship("JournalEntry", remote_side=[id])

    # Indexes
    __table_args__ = (
        Index("idx_journal_entries_customer", "customer_id"),
        Index("idx_journal_entries_number", "customer_id", "entry_number", unique=True),
        Index("idx_journal_entries_date", "entry_date"),
        Index("idx_journal_entries_period", "fiscal_period_id"),
        Index("idx_journal_entries_status", "status"),
        Index("idx_journal_entries_source", "source_type", "source_id"),
        CheckConstraint("total_debit = total_credit", name="check_entry_balanced"),
    )

    def __repr__(self):
        return f"<JournalEntry {self.entry_number}>"

    @property
    def is_balanced(self) -> bool:
        """Check if entry is balanced."""
        return self.total_debit == self.total_credit

    @property
    def can_edit(self) -> bool:
        """Check if entry can be edited."""
        return self.status in [EntryStatusEnum.DRAFT, EntryStatusEnum.PENDING]

    @property
    def can_post(self) -> bool:
        """Check if entry can be posted."""
        return (
            self.status == EntryStatusEnum.APPROVED and
            self.is_balanced and
            len(self.lines) >= 2
        )

    @property
    def can_reverse(self) -> bool:
        """Check if entry can be reversed."""
        return self.status == EntryStatusEnum.POSTED and not self.is_reversing

    def calculate_totals(self):
        """Calculate total debits and credits from lines."""
        self.total_debit = sum(line.debit_amount for line in self.lines)
        self.total_credit = sum(line.credit_amount for line in self.lines)

        # Base currency totals
        self.base_total_debit = sum(line.base_debit for line in self.lines)
        self.base_total_credit = sum(line.base_credit for line in self.lines)

    def to_dict(self, include_lines: bool = True) -> dict:
        result = {
            "id": str(self.id),
            "customer_id": str(self.customer_id),
            "entry_number": self.entry_number,
            "entry_date": self.entry_date.isoformat() if self.entry_date else None,
            "entry_type": self.entry_type.value,
            "status": self.status.value,
            "description": self.description,
            "memo": self.memo,
            "reference": self.reference,
            "source_type": self.source_type,
            "source_id": str(self.source_id) if self.source_id else None,
            "total_debit": float(self.total_debit),
            "total_credit": float(self.total_credit),
            "currency": self.currency,
            "exchange_rate": float(self.exchange_rate),
            "is_balanced": self.is_balanced,
            "is_reversing": self.is_reversing,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
        }

        if include_lines:
            result["lines"] = [line.to_dict() for line in self.lines]

        return result


class JournalLine(Base):
    """Journal entry line item."""

    __tablename__ = "journal_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)

    # Account
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)

    # Amounts
    debit_amount = Column(Numeric(15, 2), default=Decimal("0"))
    credit_amount = Column(Numeric(15, 2), default=Decimal("0"))

    # Multi-currency
    currency = Column(String(3), default="USD")
    exchange_rate = Column(Numeric(12, 6), default=Decimal("1"))
    base_debit = Column(Numeric(15, 2), default=Decimal("0"))
    base_credit = Column(Numeric(15, 2), default=Decimal("0"))

    # Description
    description = Column(Text)
    memo = Column(Text)

    # Tax
    tax_code = Column(String(20))
    tax_amount = Column(Numeric(15, 2), default=Decimal("0"))

    # Tracking dimensions
    cost_center = Column(String(50))
    department = Column(String(100))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))

    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciled_date = Column(Date)
    bank_transaction_id = Column(UUID(as_uuid=True))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account", back_populates="journal_lines")

    # Indexes
    __table_args__ = (
        Index("idx_journal_lines_entry", "entry_id"),
        Index("idx_journal_lines_account", "account_id"),
        Index("idx_journal_lines_project", "project_id"),
        CheckConstraint(
            "(debit_amount > 0 AND credit_amount = 0) OR (debit_amount = 0 AND credit_amount > 0) OR (debit_amount = 0 AND credit_amount = 0)",
            name="check_line_single_side"
        ),
    )

    def __repr__(self):
        return f"<JournalLine {self.entry_id}:{self.line_number}>"

    @property
    def amount(self) -> Decimal:
        """Get the line amount (debit or credit)."""
        return self.debit_amount or self.credit_amount

    @property
    def is_debit(self) -> bool:
        """Check if this is a debit line."""
        return self.debit_amount > 0

    def calculate_base_amounts(self):
        """Calculate base currency amounts."""
        self.base_debit = self.debit_amount * self.exchange_rate
        self.base_credit = self.credit_amount * self.exchange_rate

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "entry_id": str(self.entry_id),
            "line_number": self.line_number,
            "account_id": str(self.account_id),
            "account_code": self.account.code if self.account else None,
            "account_name": self.account.name if self.account else None,
            "debit_amount": float(self.debit_amount),
            "credit_amount": float(self.credit_amount),
            "description": self.description,
            "tax_code": self.tax_code,
            "tax_amount": float(self.tax_amount) if self.tax_amount else None,
            "cost_center": self.cost_center,
            "project_id": str(self.project_id) if self.project_id else None,
            "is_reconciled": self.is_reconciled,
        }
