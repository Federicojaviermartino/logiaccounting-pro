"""
Balance Sheet Generator
Assets = Liabilities + Equity
"""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from uuid import UUID
import logging

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.accounting.chart_of_accounts.models import Account, AccountType, AccountTypeEnum
from app.accounting.journal.models import JournalEntry, JournalLine, EntryStatusEnum

logger = logging.getLogger(__name__)


class BalanceSheetGenerator:
    """Generates balance sheet reports."""

    def __init__(self, db: Session):
        self.db = db

    def generate(
        self,
        customer_id: UUID,
        as_of_date: date = None,
        comparative_date: date = None,
        include_details: bool = True,
    ) -> Dict[str, Any]:
        """Generate balance sheet."""
        as_of_date = as_of_date or date.today()

        # Get all balance sheet accounts
        accounts = self._get_balance_sheet_accounts(customer_id)

        # Calculate balances
        assets = self._calculate_section(accounts, "asset", as_of_date)
        liabilities = self._calculate_section(accounts, "liability", as_of_date)
        equity = self._calculate_section(accounts, "equity", as_of_date)

        # Add current year earnings to equity
        current_earnings = self._calculate_current_earnings(customer_id, as_of_date)
        equity["current_year_earnings"] = float(current_earnings)
        equity["total"] += float(current_earnings)

        # Calculate comparative if requested
        comparative = None
        if comparative_date:
            comparative = {
                "as_of_date": comparative_date.isoformat(),
                "assets": self._calculate_section(accounts, "asset", comparative_date),
                "liabilities": self._calculate_section(accounts, "liability", comparative_date),
                "equity": self._calculate_section(accounts, "equity", comparative_date),
            }

        total_assets = assets["total"]
        total_liabilities_equity = liabilities["total"] + equity["total"]

        return {
            "report_type": "balance_sheet",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": date.today().isoformat(),
            "currency": "USD",
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "total_assets": total_assets,
            "total_liabilities_equity": total_liabilities_equity,
            "is_balanced": abs(total_assets - total_liabilities_equity) < 0.01,
            "comparative": comparative,
        }

    def _get_balance_sheet_accounts(self, customer_id: UUID) -> List[Account]:
        """Get all balance sheet accounts."""
        return self.db.query(Account).join(AccountType).filter(
            Account.customer_id == customer_id,
            Account.is_active == True,
            AccountType.report_type == "balance_sheet"
        ).order_by(Account.code).all()

    def _calculate_section(
        self,
        accounts: List[Account],
        section_type: str,
        as_of_date: date,
    ) -> Dict[str, Any]:
        """Calculate totals for a balance sheet section."""
        section_accounts = [a for a in accounts if a.account_type.name == section_type]

        items = []
        total = Decimal("0")

        # Group by parent for hierarchy
        root_accounts = [a for a in section_accounts if not a.parent_id or a.parent.account_type.name != section_type]

        for account in root_accounts:
            balance = self._get_account_balance(account.id, as_of_date)

            # Get children balances
            children = [a for a in section_accounts if a.parent_id == account.id]
            children_items = []

            for child in children:
                child_balance = self._get_account_balance(child.id, as_of_date)
                if child_balance != 0 or not account.is_header:
                    children_items.append({
                        "id": str(child.id),
                        "code": child.code,
                        "name": child.name,
                        "balance": float(child_balance),
                    })
                    if not account.is_header:
                        balance += child_balance

            if balance != 0 or children_items:
                item = {
                    "id": str(account.id),
                    "code": account.code,
                    "name": account.name,
                    "balance": float(balance),
                    "is_header": account.is_header,
                }
                if children_items:
                    item["children"] = children_items
                items.append(item)

                if not account.is_header:
                    total += balance

        return {
            "items": items,
            "total": float(total),
        }

    def _get_account_balance(self, account_id: UUID, as_of_date: date) -> Decimal:
        """Get account balance as of date."""
        account = self.db.query(Account).get(account_id)

        result = self.db.query(
            func.coalesce(func.sum(JournalLine.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalLine.credit_amount), 0).label("total_credit")
        ).join(JournalEntry).filter(
            and_(
                JournalLine.account_id == account_id,
                JournalEntry.status == EntryStatusEnum.POSTED,
                JournalEntry.entry_date <= as_of_date
            )
        ).first()

        total_debit = Decimal(str(result.total_debit))
        total_credit = Decimal(str(result.total_credit))

        if account.account_type.normal_balance.value == "debit":
            return account.opening_balance + total_debit - total_credit
        else:
            return account.opening_balance + total_credit - total_debit

    def _calculate_current_earnings(self, customer_id: UUID, as_of_date: date) -> Decimal:
        """Calculate current year earnings (net income)."""
        # Get fiscal year start
        year_start = date(as_of_date.year, 1, 1)

        # Revenue - Expenses
        revenue_accounts = self.db.query(Account).join(AccountType).filter(
            Account.customer_id == customer_id,
            AccountType.name == "revenue"
        ).all()

        expense_accounts = self.db.query(Account).join(AccountType).filter(
            Account.customer_id == customer_id,
            AccountType.name == "expense"
        ).all()

        total_revenue = sum(
            self._get_period_balance(a.id, year_start, as_of_date)
            for a in revenue_accounts
        )

        total_expenses = sum(
            self._get_period_balance(a.id, year_start, as_of_date)
            for a in expense_accounts
        )

        return total_revenue - total_expenses

    def _get_period_balance(
        self,
        account_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """Get account activity for a period."""
        account = self.db.query(Account).get(account_id)

        result = self.db.query(
            func.coalesce(func.sum(JournalLine.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalLine.credit_amount), 0).label("total_credit")
        ).join(JournalEntry).filter(
            and_(
                JournalLine.account_id == account_id,
                JournalEntry.status == EntryStatusEnum.POSTED,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            )
        ).first()

        total_debit = Decimal(str(result.total_debit))
        total_credit = Decimal(str(result.total_credit))

        if account.account_type.normal_balance.value == "debit":
            return total_debit - total_credit
        else:
            return total_credit - total_debit


def get_balance_sheet_generator(db: Session) -> BalanceSheetGenerator:
    return BalanceSheetGenerator(db)
