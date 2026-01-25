"""
Cash Flow Statement Generator
Operating, Investing, Financing activities
"""

from datetime import date
from decimal import Decimal
from typing import Dict, Any
from uuid import UUID
import logging

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.accounting.chart_of_accounts.models import Account, AccountType
from app.accounting.journal.models import JournalEntry, JournalLine, EntryStatusEnum

logger = logging.getLogger(__name__)


class CashFlowGenerator:
    """Generates cash flow statement using indirect method."""

    def __init__(self, db: Session):
        self.db = db

    def generate(
        self,
        customer_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Generate cash flow statement."""
        # Get net income
        net_income = self._get_net_income(customer_id, start_date, end_date)

        # Operating activities (indirect method)
        operating = self._calculate_operating_activities(
            customer_id, start_date, end_date, net_income
        )

        # Investing activities
        investing = self._calculate_investing_activities(
            customer_id, start_date, end_date
        )

        # Financing activities
        financing = self._calculate_financing_activities(
            customer_id, start_date, end_date
        )

        # Cash change
        net_change = operating["total"] + investing["total"] + financing["total"]

        # Beginning and ending cash
        beginning_cash = self._get_cash_balance(customer_id, start_date)
        ending_cash = beginning_cash + net_change

        return {
            "report_type": "cash_flow",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "generated_at": date.today().isoformat(),
            "currency": "USD",
            "operating_activities": operating,
            "investing_activities": investing,
            "financing_activities": financing,
            "net_change_in_cash": float(net_change),
            "beginning_cash": float(beginning_cash),
            "ending_cash": float(ending_cash),
        }

    def _get_net_income(
        self,
        customer_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """Calculate net income for period."""
        from app.accounting.statements.income_statement import IncomeStatementGenerator
        generator = IncomeStatementGenerator(self.db)
        result = generator.generate(customer_id, start_date, end_date)
        return Decimal(str(result["net_income"]))

    def _calculate_operating_activities(
        self,
        customer_id: UUID,
        start_date: date,
        end_date: date,
        net_income: Decimal,
    ) -> Dict[str, Any]:
        """Calculate operating activities section."""
        items = [{"name": "Net Income", "amount": float(net_income)}]
        total = net_income

        # Add back non-cash expenses (depreciation)
        depreciation = self._get_depreciation(customer_id, start_date, end_date)
        if depreciation:
            items.append({"name": "Depreciation & Amortization", "amount": float(depreciation)})
            total += depreciation

        # Changes in working capital
        ar_change = self._get_account_change(customer_id, "1200", start_date, end_date)
        if ar_change:
            items.append({"name": "Change in Accounts Receivable", "amount": float(-ar_change)})
            total -= ar_change

        inventory_change = self._get_account_change(customer_id, "1300", start_date, end_date)
        if inventory_change:
            items.append({"name": "Change in Inventory", "amount": float(-inventory_change)})
            total -= inventory_change

        ap_change = self._get_account_change(customer_id, "2100", start_date, end_date)
        if ap_change:
            items.append({"name": "Change in Accounts Payable", "amount": float(ap_change)})
            total += ap_change

        return {"items": items, "total": float(total)}

    def _calculate_investing_activities(
        self,
        customer_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Calculate investing activities section."""
        items = []
        total = Decimal("0")

        # Fixed asset purchases (increase in 15XX accounts)
        fa_change = self._get_account_change(customer_id, "15", start_date, end_date)
        if fa_change:
            items.append({"name": "Purchase of Fixed Assets", "amount": float(-fa_change)})
            total -= fa_change

        return {"items": items, "total": float(total)}

    def _calculate_financing_activities(
        self,
        customer_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Calculate financing activities section."""
        items = []
        total = Decimal("0")

        # Loans (change in 24XX, 26XX accounts)
        loan_change = self._get_account_change(customer_id, "24", start_date, end_date)
        loan_change += self._get_account_change(customer_id, "26", start_date, end_date)
        if loan_change:
            items.append({"name": "Proceeds from Loans", "amount": float(loan_change)})
            total += loan_change

        # Dividends
        dividend_change = self._get_account_change(customer_id, "37", start_date, end_date)
        if dividend_change:
            items.append({"name": "Dividends Paid", "amount": float(-dividend_change)})
            total -= dividend_change

        return {"items": items, "total": float(total)}

    def _get_cash_balance(self, customer_id: UUID, as_of_date: date) -> Decimal:
        """Get total cash balance."""
        cash_accounts = self.db.query(Account).filter(
            Account.customer_id == customer_id,
            Account.code.like("11%"),
            Account.is_header == False
        ).all()

        total = Decimal("0")
        for account in cash_accounts:
            total += self._get_account_balance(account.id, as_of_date)

        return total

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
        return account.opening_balance + total_credit - total_debit

    def _get_account_change(
        self,
        customer_id: UUID,
        code_prefix: str,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """Get change in account balance over period."""
        accounts = self.db.query(Account).filter(
            Account.customer_id == customer_id,
            Account.code.like(f"{code_prefix}%"),
            Account.is_header == False
        ).all()

        total_change = Decimal("0")
        for account in accounts:
            start_balance = self._get_account_balance(account.id, start_date)
            end_balance = self._get_account_balance(account.id, end_date)
            total_change += end_balance - start_balance

        return total_change

    def _get_depreciation(
        self,
        customer_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """Get depreciation expense for period."""
        depr_accounts = self.db.query(Account).filter(
            Account.customer_id == customer_id,
            Account.code.like("56%"),
            Account.is_header == False
        ).all()

        total = Decimal("0")
        for account in depr_accounts:
            result = self.db.query(
                func.coalesce(func.sum(JournalLine.debit_amount), 0)
            ).join(JournalEntry).filter(
                and_(
                    JournalLine.account_id == account.id,
                    JournalEntry.status == EntryStatusEnum.POSTED,
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date
                )
            ).scalar()
            total += Decimal(str(result or 0))

        return total


def get_cash_flow_generator(db: Session) -> CashFlowGenerator:
    return CashFlowGenerator(db)
