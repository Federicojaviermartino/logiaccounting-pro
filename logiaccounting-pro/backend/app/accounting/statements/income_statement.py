"""
Income Statement Generator
Revenue - Expenses = Net Income
"""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, List
from uuid import UUID
import logging

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.accounting.chart_of_accounts.models import Account, AccountType
from app.accounting.journal.models import JournalEntry, JournalLine, EntryStatusEnum

logger = logging.getLogger(__name__)


class IncomeStatementGenerator:
    """Generates income statement (P&L) reports."""

    def __init__(self, db: Session):
        self.db = db

    def generate(
        self,
        customer_id: UUID,
        start_date: date,
        end_date: date,
        comparative_start: date = None,
        comparative_end: date = None,
        include_details: bool = True,
    ) -> Dict[str, Any]:
        """Generate income statement for a period."""
        # Get income statement accounts
        accounts = self._get_income_accounts(customer_id)

        # Calculate sections
        revenue = self._calculate_section(accounts, "revenue", start_date, end_date)
        expenses = self._calculate_section(accounts, "expense", start_date, end_date)

        # Calculate gross profit (if COGS is separated)
        cogs = self._get_cogs(accounts, start_date, end_date)
        gross_profit = revenue["total"] - cogs

        # Operating expenses (expenses minus COGS)
        operating_expenses = expenses["total"] - cogs

        # Net income
        net_income = revenue["total"] - expenses["total"]

        # Comparative period
        comparative = None
        if comparative_start and comparative_end:
            comp_revenue = self._calculate_section(accounts, "revenue", comparative_start, comparative_end)
            comp_expenses = self._calculate_section(accounts, "expense", comparative_start, comparative_end)
            comparative = {
                "period": {
                    "start": comparative_start.isoformat(),
                    "end": comparative_end.isoformat(),
                },
                "revenue": comp_revenue,
                "expenses": comp_expenses,
                "net_income": comp_revenue["total"] - comp_expenses["total"],
            }

        return {
            "report_type": "income_statement",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "generated_at": date.today().isoformat(),
            "currency": "USD",
            "revenue": revenue,
            "cost_of_goods_sold": cogs,
            "gross_profit": gross_profit,
            "operating_expenses": operating_expenses,
            "expenses": expenses,
            "net_income": net_income,
            "comparative": comparative,
        }

    def _get_income_accounts(self, customer_id: UUID) -> List[Account]:
        """Get all income statement accounts."""
        return self.db.query(Account).join(AccountType).filter(
            Account.customer_id == customer_id,
            Account.is_active == True,
            AccountType.report_type == "income_statement"
        ).order_by(Account.code).all()

    def _calculate_section(
        self,
        accounts: List[Account],
        section_type: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Calculate totals for an income statement section."""
        section_accounts = [a for a in accounts if a.account_type.name == section_type]

        items = []
        total = Decimal("0")

        for account in section_accounts:
            if account.is_header:
                continue

            balance = self._get_period_activity(account.id, start_date, end_date)

            if balance != 0:
                items.append({
                    "id": str(account.id),
                    "code": account.code,
                    "name": account.name,
                    "amount": float(balance),
                })
                total += balance

        return {
            "items": items,
            "total": float(total),
        }

    def _get_period_activity(
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

        # For income statement: revenue is credit normal, expense is debit normal
        if account.account_type.normal_balance.value == "credit":
            return total_credit - total_debit
        else:
            return total_debit - total_credit

    def _get_cogs(
        self,
        accounts: List[Account],
        start_date: date,
        end_date: date,
    ) -> float:
        """Get cost of goods sold."""
        cogs_accounts = [a for a in accounts if a.code.startswith("51")]
        total = sum(
            self._get_period_activity(a.id, start_date, end_date)
            for a in cogs_accounts if not a.is_header
        )
        return float(total)


def get_income_statement_generator(db: Session) -> IncomeStatementGenerator:
    return IncomeStatementGenerator(db)
