"""
Bank Account Models
Bank accounts, balances, and GL integration
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean,
    Integer, Numeric, Text, Date, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.database import Base


class AccountType(str, Enum):
    """Bank account types"""
    CHECKING = "checking"
    SAVINGS = "savings"
    MONEY_MARKET = "money_market"
    LINE_OF_CREDIT = "line_of_credit"
    MERCHANT = "merchant"
    INVESTMENT = "investment"


class BankAccount(Base):
    """Bank account master data"""
    __tablename__ = "bank_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # Identification
    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Bank details
    bank_name: Mapped[str] = mapped_column(String(200), nullable=False)
    bank_code: Mapped[Optional[str]] = mapped_column(String(20))
    branch_code: Mapped[Optional[str]] = mapped_column(String(20))
    branch_name: Mapped[Optional[str]] = mapped_column(String(200))

    # Account numbers
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    iban: Mapped[Optional[str]] = mapped_column(String(50))
    routing_number: Mapped[Optional[str]] = mapped_column(String(50))
    sort_code: Mapped[Optional[str]] = mapped_column(String(20))

    # Currency
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Account type
    account_type: Mapped[str] = mapped_column(
        String(30), default=AccountType.CHECKING.value
    )

    # Limits
    overdraft_limit: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0")
    )
    daily_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    # Balances (cached)
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0")
    )
    available_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0")
    )
    last_balance_date: Mapped[Optional[date]] = mapped_column(Date)

    # GL Integration
    gl_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    # Reconciliation tracking
    last_reconciled_date: Mapped[Optional[date]] = mapped_column(Date)
    last_reconciled_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    # Online banking
    is_online_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    api_credentials_encrypted: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    # Contact
    contact_name: Mapped[Optional[str]] = mapped_column(String(100))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50))
    contact_email: Mapped[Optional[str]] = mapped_column(String(200))

    # Bank address
    bank_address_line1: Mapped[Optional[str]] = mapped_column(String(200))
    bank_address_line2: Mapped[Optional[str]] = mapped_column(String(200))
    bank_city: Mapped[Optional[str]] = mapped_column(String(100))
    bank_state: Mapped[Optional[str]] = mapped_column(String(100))
    bank_postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    bank_country: Mapped[Optional[str]] = mapped_column(String(3))

    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Metadata
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    balances: Mapped[List["BankAccountBalance"]] = relationship(
        "BankAccountBalance", back_populates="account", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("customer_id", "account_code", name="uq_bank_account_code"),
        Index("idx_bank_accounts_currency", "currency"),
    )

    @property
    def masked_account_number(self) -> str:
        """Return masked account number for display"""
        if len(self.account_number) > 4:
            return f"****{self.account_number[-4:]}"
        return "****"

    @property
    def is_overdrawn(self) -> bool:
        """Check if account is overdrawn"""
        return self.current_balance < Decimal("0")

    @property
    def available_credit(self) -> Decimal:
        """Calculate available credit including overdraft"""
        return self.current_balance + self.overdraft_limit

    def update_balance(self, new_balance: Decimal, balance_date: date = None):
        """Update cached balance"""
        self.current_balance = new_balance
        self.available_balance = new_balance + self.overdraft_limit
        self.last_balance_date = balance_date or date.today()
        self.updated_at = datetime.utcnow()


class BankAccountBalance(Base):
    """Daily balance history for bank accounts"""
    __tablename__ = "bank_account_balances"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"),
        nullable=False
    )

    balance_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Balances
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_debits: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    total_credits: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # Transaction counts
    debit_count: Mapped[int] = mapped_column(Integer, default=0)
    credit_count: Mapped[int] = mapped_column(Integer, default=0)

    # Reconciliation status
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False)
    reconciliation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    account: Mapped["BankAccount"] = relationship(
        "BankAccount", back_populates="balances"
    )

    __table_args__ = (
        UniqueConstraint("account_id", "balance_date", name="uq_bank_balance_date"),
        Index("idx_bank_balances_date", "account_id", "balance_date"),
    )

    @property
    def net_change(self) -> Decimal:
        """Calculate net change for the day"""
        return self.total_credits - self.total_debits
