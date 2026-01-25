"""
Ledger Models
Account balance tracking models
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class AccountBalance(Base):
    """Account balance per fiscal period."""

    __tablename__ = "account_balances"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    period_id = Column(PGUUID(as_uuid=True), ForeignKey("fiscal_periods.id"), nullable=False)

    # Opening balances (from previous period)
    opening_debit = Column(Numeric(15, 2), default=Decimal("0"))
    opening_credit = Column(Numeric(15, 2), default=Decimal("0"))

    # Period activity
    period_debit = Column(Numeric(15, 2), default=Decimal("0"))
    period_credit = Column(Numeric(15, 2), default=Decimal("0"))

    # Closing balances (calculated)
    closing_debit = Column(Numeric(15, 2), default=Decimal("0"))
    closing_credit = Column(Numeric(15, 2), default=Decimal("0"))

    # Year-to-date
    ytd_debit = Column(Numeric(15, 2), default=Decimal("0"))
    ytd_credit = Column(Numeric(15, 2), default=Decimal("0"))

    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("Account")
    period = relationship("FiscalPeriod")

    __table_args__ = (
        Index("idx_account_balances_account_period", "account_id", "period_id", unique=True),
        Index("idx_account_balances_period", "period_id"),
    )

    def calculate_closing(self):
        """Calculate closing balances."""
        self.closing_debit = self.opening_debit + self.period_debit
        self.closing_credit = self.opening_credit + self.period_credit

    @property
    def opening_balance(self) -> Decimal:
        """Net opening balance."""
        return self.opening_debit - self.opening_credit

    @property
    def period_activity(self) -> Decimal:
        """Net period activity."""
        return self.period_debit - self.period_credit

    @property
    def closing_balance(self) -> Decimal:
        """Net closing balance."""
        return self.closing_debit - self.closing_credit

    @property
    def ytd_balance(self) -> Decimal:
        """Net YTD balance."""
        return self.ytd_debit - self.ytd_credit

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "account_id": str(self.account_id),
            "period_id": str(self.period_id),
            "opening_debit": float(self.opening_debit),
            "opening_credit": float(self.opening_credit),
            "opening_balance": float(self.opening_balance),
            "period_debit": float(self.period_debit),
            "period_credit": float(self.period_credit),
            "period_activity": float(self.period_activity),
            "closing_debit": float(self.closing_debit),
            "closing_credit": float(self.closing_credit),
            "closing_balance": float(self.closing_balance),
            "ytd_debit": float(self.ytd_debit),
            "ytd_credit": float(self.ytd_credit),
            "ytd_balance": float(self.ytd_balance),
        }
