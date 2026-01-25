"""
Chart of Accounts Models
SQLAlchemy models for accounts and account types
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey,
    Numeric, Integer, Text, Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref

from app.database import Base


class AccountTypeEnum(str, Enum):
    """Account type enumeration."""
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class NormalBalanceEnum(str, Enum):
    """Normal balance side."""
    DEBIT = "debit"
    CREDIT = "credit"


class ReportTypeEnum(str, Enum):
    """Financial statement type."""
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"


class AccountType(Base):
    """Account type definition."""

    __tablename__ = "account_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    normal_balance = Column(
        SQLEnum(NormalBalanceEnum),
        nullable=False
    )
    report_type = Column(
        SQLEnum(ReportTypeEnum),
        nullable=False
    )
    display_order = Column(Integer, default=0)
    description = Column(Text)

    # Relationships
    accounts = relationship("Account", back_populates="account_type")

    def __repr__(self):
        return f"<AccountType {self.name}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "normal_balance": self.normal_balance.value,
            "report_type": self.report_type.value,
            "display_order": self.display_order,
            "description": self.description,
        }


class Account(Base):
    """Chart of accounts entry."""

    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Account identification
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Type and hierarchy
    account_type_id = Column(UUID(as_uuid=True), ForeignKey("account_types.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    level = Column(Integer, default=0)
    path = Column(String(500))  # Materialized path for fast queries

    # Configuration
    currency = Column(String(3), default="USD")
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # Cannot be deleted
    is_reconcilable = Column(Boolean, default=False)
    is_header = Column(Boolean, default=False)  # Summary account, no posting

    # Balances
    opening_balance = Column(Numeric(15, 2), default=Decimal("0"))
    current_balance = Column(Numeric(15, 2), default=Decimal("0"))

    # Tax configuration
    tax_code = Column(String(20))
    default_tax_rate = Column(Numeric(5, 2))

    # Cost center / Department
    cost_center = Column(String(50))
    department = Column(String(100))

    # Metadata
    external_id = Column(String(100))  # For integrations
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    account_type = relationship("AccountType", back_populates="accounts")
    parent = relationship(
        "Account",
        remote_side=[id],
        backref=backref("children", lazy="dynamic")
    )
    journal_lines = relationship("JournalLine", back_populates="account")

    # Indexes
    __table_args__ = (
        Index("idx_accounts_customer_code", "customer_id", "code", unique=True),
        Index("idx_accounts_customer", "customer_id"),
        Index("idx_accounts_parent", "parent_id"),
        Index("idx_accounts_type", "account_type_id"),
        Index("idx_accounts_path", "path"),
    )

    def __repr__(self):
        return f"<Account {self.code} - {self.name}>"

    @property
    def full_code(self) -> str:
        """Get full account code with parent codes."""
        if self.parent:
            return f"{self.parent.full_code}.{self.code}"
        return self.code

    @property
    def full_name(self) -> str:
        """Get full account name with hierarchy."""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name

    def get_balance(self, as_of_date: datetime = None) -> Decimal:
        """Get account balance, optionally as of a specific date."""
        # This would be implemented with actual ledger queries
        return self.current_balance

    def can_post(self) -> bool:
        """Check if transactions can be posted to this account."""
        return self.is_active and not self.is_header

    def to_dict(self, include_children: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "customer_id": str(self.customer_id),
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "account_type": self.account_type.to_dict() if self.account_type else None,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "level": self.level,
            "currency": self.currency,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "is_reconcilable": self.is_reconcilable,
            "is_header": self.is_header,
            "opening_balance": float(self.opening_balance),
            "current_balance": float(self.current_balance),
            "tax_code": self.tax_code,
            "cost_center": self.cost_center,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_children:
            result["children"] = [
                child.to_dict(include_children=True)
                for child in self.children
            ]

        return result

    def to_tree_node(self) -> dict:
        """Convert to tree node format for frontend."""
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "full_name": f"{self.code} - {self.name}",
            "type": self.account_type.name if self.account_type else None,
            "balance": float(self.current_balance),
            "is_header": self.is_header,
            "is_active": self.is_active,
            "level": self.level,
            "has_children": self.children.count() > 0,
            "children": [
                child.to_tree_node()
                for child in self.children.filter(Account.is_active == True)
            ],
        }


# Default account types (seeded on init)
DEFAULT_ACCOUNT_TYPES = [
    {
        "name": AccountTypeEnum.ASSET.value,
        "display_name": "Assets",
        "normal_balance": NormalBalanceEnum.DEBIT,
        "report_type": ReportTypeEnum.BALANCE_SHEET,
        "display_order": 1,
        "description": "Resources owned by the company",
    },
    {
        "name": AccountTypeEnum.LIABILITY.value,
        "display_name": "Liabilities",
        "normal_balance": NormalBalanceEnum.CREDIT,
        "report_type": ReportTypeEnum.BALANCE_SHEET,
        "display_order": 2,
        "description": "Obligations owed by the company",
    },
    {
        "name": AccountTypeEnum.EQUITY.value,
        "display_name": "Equity",
        "normal_balance": NormalBalanceEnum.CREDIT,
        "report_type": ReportTypeEnum.BALANCE_SHEET,
        "display_order": 3,
        "description": "Owner's stake in the company",
    },
    {
        "name": AccountTypeEnum.REVENUE.value,
        "display_name": "Revenue",
        "normal_balance": NormalBalanceEnum.CREDIT,
        "report_type": ReportTypeEnum.INCOME_STATEMENT,
        "display_order": 4,
        "description": "Income earned from operations",
    },
    {
        "name": AccountTypeEnum.EXPENSE.value,
        "display_name": "Expenses",
        "normal_balance": NormalBalanceEnum.DEBIT,
        "report_type": ReportTypeEnum.INCOME_STATEMENT,
        "display_order": 5,
        "description": "Costs incurred in operations",
    },
]
