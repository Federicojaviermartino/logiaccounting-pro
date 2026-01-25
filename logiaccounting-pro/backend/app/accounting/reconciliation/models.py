"""
Bank Reconciliation Models
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Numeric, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class BankAccount(Base):
    """Bank account linked to GL account."""

    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)

    bank_name = Column(String(200), nullable=False)
    account_number = Column(String(50))
    routing_number = Column(String(50))
    account_type = Column(String(50))  # checking, savings, credit
    currency = Column(String(3), default="USD")

    current_balance = Column(Numeric(15, 2), default=Decimal("0"))
    last_reconciled_date = Column(Date)
    last_reconciled_balance = Column(Numeric(15, 2))

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    gl_account = relationship("Account")
    statements = relationship("BankStatement", back_populates="bank_account")


class BankStatement(Base):
    """Imported bank statement."""

    __tablename__ = "bank_statements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)

    statement_date = Column(Date, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    opening_balance = Column(Numeric(15, 2), nullable=False)
    closing_balance = Column(Numeric(15, 2), nullable=False)

    import_source = Column(String(50))  # 'ofx', 'csv', 'manual'
    import_file_name = Column(String(200))
    is_reconciled = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    bank_account = relationship("BankAccount", back_populates="statements")
    transactions = relationship("BankTransaction", back_populates="statement")


class BankTransaction(Base):
    """Bank transaction from statement."""

    __tablename__ = "bank_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_id = Column(UUID(as_uuid=True), ForeignKey("bank_statements.id"), nullable=False)

    transaction_date = Column(Date, nullable=False)
    post_date = Column(Date)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text)
    reference = Column(String(100))
    transaction_type = Column(String(20))  # debit, credit
    check_number = Column(String(20))
    payee = Column(String(200))

    # Matching
    is_matched = Column(Boolean, default=False)
    matched_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"))
    matched_line_id = Column(UUID(as_uuid=True), ForeignKey("journal_lines.id"))
    matched_at = Column(DateTime)
    match_confidence = Column(Numeric(3, 2))
    match_method = Column(String(50))  # 'auto', 'manual', 'rule'

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    statement = relationship("BankStatement", back_populates="transactions")
    matched_entry = relationship("JournalEntry")
    matched_line = relationship("JournalLine")


class Reconciliation(Base):
    """Bank reconciliation session."""

    __tablename__ = "reconciliations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    statement_id = Column(UUID(as_uuid=True), ForeignKey("bank_statements.id"))

    reconciliation_date = Column(Date, nullable=False)
    statement_balance = Column(Numeric(15, 2), nullable=False)
    gl_balance = Column(Numeric(15, 2), nullable=False)
    adjusted_balance = Column(Numeric(15, 2), nullable=False)
    difference = Column(Numeric(15, 2), nullable=False)

    status = Column(String(20), default="in_progress")  # in_progress, completed, discrepancy

    completed_at = Column(DateTime)
    completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
