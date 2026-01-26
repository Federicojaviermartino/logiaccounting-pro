"""
Year-End Closing Service
Close fiscal year and generate closing entries
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any
from uuid import UUID
import logging

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.accounting.periods.models import FiscalYear, FiscalPeriod
from app.accounting.chart_of_accounts.models import Account, AccountType
from app.accounting.journal.models import JournalEntry, JournalLine, EntryTypeEnum, EntryStatusEnum
from app.accounting.journal.schemas import JournalEntryCreate, JournalLineCreate

logger = logging.getLogger(__name__)


class YearEndClosingService:
    """Service for year-end closing procedures."""

    def __init__(self, db: Session):
        # Lazy import to avoid circular dependency
        from app.accounting.journal.service import JournalEntryService

        self.db = db
        self.journal_service = JournalEntryService(db)

    def perform_year_end_closing(
        self,
        fiscal_year_id: UUID,
        closed_by: UUID,
    ) -> Dict[str, Any]:
        """Perform complete year-end closing."""
        fiscal_year = self.db.query(FiscalYear).get(fiscal_year_id)
        if not fiscal_year:
            raise ValueError("Fiscal year not found")

        if fiscal_year.is_closed:
            raise ValueError("Fiscal year is already closed")

        # Ensure all periods are closed
        open_periods = self.db.query(FiscalPeriod).filter(
            FiscalPeriod.fiscal_year_id == fiscal_year_id,
            FiscalPeriod.is_closed == False
        ).count()

        if open_periods > 0:
            raise ValueError(f"Cannot close year with {open_periods} open periods")

        customer_id = fiscal_year.customer_id

        # Create closing entries
        closing_entry = self._create_closing_entry(
            customer_id=customer_id,
            fiscal_year=fiscal_year,
            created_by=closed_by,
        )

        # Close the fiscal year
        fiscal_year.is_closed = True
        fiscal_year.closed_at = datetime.utcnow()
        fiscal_year.closed_by = closed_by

        self.db.commit()

        logger.info(f"Closed fiscal year: {fiscal_year.name}")

        return {
            "fiscal_year_id": str(fiscal_year.id),
            "fiscal_year_name": fiscal_year.name,
            "closing_entry_id": str(closing_entry.id) if closing_entry else None,
            "closing_entry_number": closing_entry.entry_number if closing_entry else None,
            "closed_at": fiscal_year.closed_at.isoformat(),
        }

    def _create_closing_entry(
        self,
        customer_id: UUID,
        fiscal_year: FiscalYear,
        created_by: UUID,
    ) -> JournalEntry:
        """Create closing journal entry to transfer income/expense to retained earnings."""
        # Get revenue and expense totals
        revenue_accounts = self.db.query(Account).join(AccountType).filter(
            Account.customer_id == customer_id,
            AccountType.name == "revenue",
            Account.is_header == False
        ).all()

        expense_accounts = self.db.query(Account).join(AccountType).filter(
            Account.customer_id == customer_id,
            AccountType.name == "expense",
            Account.is_header == False
        ).all()

        # Get retained earnings account
        retained_earnings = self.db.query(Account).filter(
            Account.customer_id == customer_id,
            Account.code == "3500"  # Standard retained earnings code
        ).first()

        if not retained_earnings:
            raise ValueError("Retained Earnings account (3500) not found")

        lines = []
        total_revenue = Decimal("0")
        total_expenses = Decimal("0")

        # Close revenue accounts (debit to close)
        for account in revenue_accounts:
            balance = self._get_period_balance(
                account.id,
                fiscal_year.start_date,
                fiscal_year.end_date
            )
            if balance != 0:
                lines.append({
                    "account_id": account.id,
                    "debit_amount": balance,
                    "credit_amount": Decimal("0"),
                    "description": f"Close {account.code} - {account.name}",
                })
                total_revenue += balance

        # Close expense accounts (credit to close)
        for account in expense_accounts:
            balance = self._get_period_balance(
                account.id,
                fiscal_year.start_date,
                fiscal_year.end_date
            )
            if balance != 0:
                lines.append({
                    "account_id": account.id,
                    "debit_amount": Decimal("0"),
                    "credit_amount": balance,
                    "description": f"Close {account.code} - {account.name}",
                })
                total_expenses += balance

        # Net income to retained earnings
        net_income = total_revenue - total_expenses

        if net_income > 0:
            # Profit: credit retained earnings
            lines.append({
                "account_id": retained_earnings.id,
                "debit_amount": Decimal("0"),
                "credit_amount": net_income,
                "description": f"Net income for {fiscal_year.name}",
            })
        elif net_income < 0:
            # Loss: debit retained earnings
            lines.append({
                "account_id": retained_earnings.id,
                "debit_amount": abs(net_income),
                "credit_amount": Decimal("0"),
                "description": f"Net loss for {fiscal_year.name}",
            })

        if not lines:
            return None

        # Create the closing entry
        entry_data = JournalEntryCreate(
            entry_date=fiscal_year.end_date,
            entry_type=EntryTypeEnum.CLOSING,
            description=f"Year-end closing entry - {fiscal_year.name}",
            lines=[JournalLineCreate(**line) for line in lines],
        )

        entry = self.journal_service.create_entry(
            customer_id=customer_id,
            data=entry_data,
            created_by=created_by,
        )

        # Auto-post closing entry
        self.journal_service.submit_for_approval(entry.id, created_by)
        self.journal_service.approve_entry(entry.id, created_by)
        self.journal_service.post_entry(entry.id, created_by)

        return entry

    def _get_period_balance(
        self,
        account_id: UUID,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """Get account balance for a period."""
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

        # For closing, we need the normal balance
        if account.account_type.normal_balance.value == "credit":
            return total_credit - total_debit
        return total_debit - total_credit


def get_year_end_closing_service(db: Session) -> YearEndClosingService:
    return YearEndClosingService(db)
