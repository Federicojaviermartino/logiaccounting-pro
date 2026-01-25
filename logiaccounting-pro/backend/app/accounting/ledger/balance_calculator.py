"""
Balance Calculator
Utility functions for balance calculations
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.accounting.chart_of_accounts.models import Account, AccountTypeEnum
from app.accounting.journal.models import JournalEntry, JournalLine, EntryStatusEnum
from app.accounting.ledger.models import AccountBalance
from app.accounting.periods.models import FiscalPeriod

logger = logging.getLogger(__name__)


class BalanceCalculator:
    """Utility class for balance calculations."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_account_balance(
        self,
        account_id: UUID,
        as_of_date: date = None,
        include_unposted: bool = False,
    ) -> Decimal:
        """Calculate account balance as of a specific date."""
        account = self.db.query(Account).get(account_id)
        if not account:
            return Decimal("0")

        as_of_date = as_of_date or date.today()

        # Query conditions
        conditions = [
            JournalLine.account_id == account_id,
            JournalEntry.entry_date <= as_of_date,
        ]

        if include_unposted:
            conditions.append(
                JournalEntry.status.in_([EntryStatusEnum.POSTED, EntryStatusEnum.APPROVED])
            )
        else:
            conditions.append(JournalEntry.status == EntryStatusEnum.POSTED)

        result = self.db.query(
            func.coalesce(func.sum(JournalLine.debit_amount), 0),
            func.coalesce(func.sum(JournalLine.credit_amount), 0),
        ).join(JournalEntry).filter(and_(*conditions)).first()

        total_debit = Decimal(str(result[0]))
        total_credit = Decimal(str(result[1]))

        # Calculate based on normal balance
        if account.account_type.normal_balance.value == "debit":
            return account.opening_balance + total_debit - total_credit
        else:
            return account.opening_balance + total_credit - total_debit

    def calculate_type_totals(
        self,
        customer_id: UUID,
        account_type: str,
        as_of_date: date = None,
    ) -> Decimal:
        """Calculate total balance for an account type."""
        from app.accounting.chart_of_accounts.models import AccountType

        accounts = self.db.query(Account).join(AccountType).filter(
            and_(
                Account.customer_id == customer_id,
                AccountType.name == account_type,
                Account.is_active == True,
                Account.is_header == False,
            )
        ).all()

        total = Decimal("0")
        for account in accounts:
            balance = self.calculate_account_balance(account.id, as_of_date)
            total += balance

        return total

    def calculate_net_income(
        self,
        customer_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """Calculate net income for a period."""
        from app.accounting.chart_of_accounts.models import AccountType

        # Revenue - Expenses
        revenue_accounts = self.db.query(Account).join(AccountType).filter(
            and_(
                Account.customer_id == customer_id,
                AccountType.name == "revenue",
                Account.is_active == True,
            )
        ).all()

        expense_accounts = self.db.query(Account).join(AccountType).filter(
            and_(
                Account.customer_id == customer_id,
                AccountType.name == "expense",
                Account.is_active == True,
            )
        ).all()

        total_revenue = Decimal("0")
        total_expenses = Decimal("0")

        for account in revenue_accounts:
            activity = self._get_period_activity(account.id, start_date, end_date)
            total_revenue += activity["credit"] - activity["debit"]

        for account in expense_accounts:
            activity = self._get_period_activity(account.id, start_date, end_date)
            total_expenses += activity["debit"] - activity["credit"]

        return total_revenue - total_expenses

    def _get_period_activity(
        self,
        account_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Decimal]:
        """Get debit/credit activity for an account in a period."""
        result = self.db.query(
            func.coalesce(func.sum(JournalLine.debit_amount), 0),
            func.coalesce(func.sum(JournalLine.credit_amount), 0),
        ).join(JournalEntry).filter(
            and_(
                JournalLine.account_id == account_id,
                JournalEntry.status == EntryStatusEnum.POSTED,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
            )
        ).first()

        return {
            "debit": Decimal(str(result[0])),
            "credit": Decimal(str(result[1])),
        }

    def recalculate_all_balances(
        self,
        customer_id: UUID,
    ) -> int:
        """Recalculate all account balances from journal entries."""
        accounts = self.db.query(Account).filter(
            Account.customer_id == customer_id
        ).all()

        updated = 0
        for account in accounts:
            new_balance = self.calculate_account_balance(account.id)
            if account.current_balance != new_balance:
                account.current_balance = new_balance
                updated += 1

        self.db.commit()
        logger.info(f"Recalculated {updated} account balances")
        return updated

    def update_period_balances(
        self,
        customer_id: UUID,
        period_id: UUID,
    ):
        """Update account balances for a specific period."""
        period = self.db.query(FiscalPeriod).get(period_id)
        if not period:
            raise ValueError("Period not found")

        accounts = self.db.query(Account).filter(
            and_(
                Account.customer_id == customer_id,
                Account.is_active == True,
            )
        ).all()

        for account in accounts:
            # Get or create balance record
            balance = self.db.query(AccountBalance).filter(
                and_(
                    AccountBalance.account_id == account.id,
                    AccountBalance.period_id == period_id,
                )
            ).first()

            if not balance:
                balance = AccountBalance(
                    account_id=account.id,
                    period_id=period_id,
                )
                self.db.add(balance)

            # Calculate period activity
            activity = self._get_period_activity(
                account.id, period.start_date, period.end_date
            )

            balance.period_debit = activity["debit"]
            balance.period_credit = activity["credit"]
            balance.calculate_closing()

        self.db.commit()
        logger.info(f"Updated period balances for period {period.name}")

    def get_balance_summary(
        self,
        customer_id: UUID,
        as_of_date: date = None,
    ) -> Dict[str, Decimal]:
        """Get summary of balances by account type."""
        as_of_date = as_of_date or date.today()

        summary = {
            "assets": Decimal("0"),
            "liabilities": Decimal("0"),
            "equity": Decimal("0"),
            "revenue": Decimal("0"),
            "expenses": Decimal("0"),
        }

        for acc_type in summary.keys():
            summary[acc_type] = self.calculate_type_totals(
                customer_id, acc_type, as_of_date
            )

        # Add calculated fields
        summary["net_assets"] = summary["assets"] - summary["liabilities"]
        summary["net_income"] = summary["revenue"] - summary["expenses"]
        summary["total_equity_check"] = summary["equity"] + summary["net_income"]

        return summary


def get_balance_calculator(db: Session) -> BalanceCalculator:
    """Factory function."""
    return BalanceCalculator(db)
