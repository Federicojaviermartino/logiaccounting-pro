"""
Bank Transaction Models
Bank transactions and statement imports
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from enum import Enum
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean,
    Integer, Numeric, Text, Date, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.database import Base


class TransactionType(str, Enum):
    """Bank transaction types"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    FEE = "fee"
    INTEREST = "interest"
    CHECK = "check"
    WIRE_IN = "wire_in"
    WIRE_OUT = "wire_out"
    ACH_IN = "ach_in"
    ACH_OUT = "ach_out"
    CARD_PAYMENT = "card_payment"
    POS = "pos"
    ATM = "atm"


class MatchStatus(str, Enum):
    """Transaction matching status"""
    UNMATCHED = "unmatched"
    SUGGESTED = "suggested"
    MATCHED = "matched"
    RECONCILED = "reconciled"
    EXCEPTION = "exception"


class Direction(str, Enum):
    """Transaction direction"""
    DEBIT = "debit"
    CREDIT = "credit"


class BankTransaction(Base):
    """Bank transactions imported from statements or manual entry"""
    __tablename__ = "bank_transactions"

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
    transaction_ref: Mapped[Optional[str]] = mapped_column(String(50))
    internal_ref: Mapped[Optional[str]] = mapped_column(String(30))

    # Transaction details
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[date]] = mapped_column(Date)

    # Type and direction
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Running balance (from statement)
    running_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    # Counterparty
    payee_payer_name: Mapped[Optional[str]] = mapped_column(String(200))
    payee_payer_account: Mapped[Optional[str]] = mapped_column(String(50))
    payee_payer_bank: Mapped[Optional[str]] = mapped_column(String(100))

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text)
    memo: Mapped[Optional[str]] = mapped_column(Text)

    # Check details
    check_number: Mapped[Optional[str]] = mapped_column(String(20))

    # Categorization
    category: Mapped[Optional[str]] = mapped_column(String(50))

    # Matching status
    match_status: Mapped[str] = mapped_column(String(20), default=MatchStatus.UNMATCHED.value)

    # Matched to
    matched_invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    matched_bill_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    matched_journal_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    matched_transfer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Reconciliation
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False)
    reconciliation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reconciled_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # GL posting
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Import tracking
    import_batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    import_row_number: Mapped[Optional[int]] = mapped_column(Integer)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    account = relationship("BankAccount", back_populates="transactions")

    __table_args__ = (
        Index("idx_bank_trans_account_date", "account_id", "transaction_date"),
        Index("idx_bank_trans_match_status", "match_status"),
        Index("idx_bank_trans_reconciliation", "reconciliation_id"),
    )

    @property
    def is_debit(self) -> bool:
        """Check if transaction is a debit"""
        return self.direction == Direction.DEBIT.value

    @property
    def signed_amount(self) -> Decimal:
        """Return signed amount (negative for debits)"""
        return -self.amount if self.is_debit else self.amount


class BankStatementImport(Base):
    """Bank statement import batches"""
    __tablename__ = "bank_statement_imports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False
    )

    # File info
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_format: Mapped[Optional[str]] = mapped_column(String(20))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)

    # Statement period
    statement_date: Mapped[Optional[date]] = mapped_column(Date)
    period_start: Mapped[Optional[date]] = mapped_column(Date)
    period_end: Mapped[Optional[date]] = mapped_column(Date)

    # Totals
    opening_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    closing_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    total_transactions: Mapped[Optional[int]] = mapped_column(Integer)
    total_debits: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    total_credits: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    # Processing status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    transactions_imported: Mapped[int] = mapped_column(Integer, default=0)
    transactions_duplicates: Mapped[int] = mapped_column(Integer, default=0)
    transactions_errors: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[Optional[dict]] = mapped_column(JSONB)

    imported_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
