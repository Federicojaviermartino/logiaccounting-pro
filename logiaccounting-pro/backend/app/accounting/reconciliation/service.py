"""
Bank Reconciliation Service
Complete reconciliation workflow
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.utils.datetime_utils import utc_now

from app.accounting.reconciliation.models import (
    BankAccount, BankStatement, BankTransaction, Reconciliation
)
from app.accounting.journal.models import JournalEntry, JournalLine, EntryStatusEnum
from app.accounting.reconciliation.matcher import TransactionMatcher

logger = logging.getLogger(__name__)


class ReconciliationService:
    """Service for bank reconciliation."""

    def __init__(self, db: Session):
        self.db = db
        self.matcher = TransactionMatcher(db)

    def create_bank_account(
        self,
        customer_id: UUID,
        gl_account_id: UUID,
        bank_name: str,
        account_number: str = None,
        routing_number: str = None,
        account_type: str = "checking",
        currency: str = "USD",
    ) -> BankAccount:
        """Create a new bank account linked to GL."""
        bank_account = BankAccount(
            customer_id=customer_id,
            account_id=gl_account_id,
            bank_name=bank_name,
            account_number=account_number,
            routing_number=routing_number,
            account_type=account_type,
            currency=currency,
        )

        self.db.add(bank_account)
        self.db.commit()
        self.db.refresh(bank_account)

        return bank_account

    def start_reconciliation(
        self,
        bank_account_id: UUID,
        statement_id: UUID = None,
        statement_balance: Decimal = None,
        reconciliation_date: date = None,
        created_by: UUID = None,
    ) -> Reconciliation:
        """Start a new reconciliation session."""
        bank_account = self.db.query(BankAccount).get(bank_account_id)
        if not bank_account:
            raise ValueError("Bank account not found")

        reconciliation_date = reconciliation_date or date.today()

        # Get GL balance
        gl_balance = self._get_gl_balance(bank_account.account_id, reconciliation_date)

        # Get statement balance
        if statement_id:
            statement = self.db.query(BankStatement).get(statement_id)
            if statement:
                statement_balance = statement.closing_balance

        if statement_balance is None:
            raise ValueError("Statement balance required")

        # Calculate difference
        difference = statement_balance - gl_balance

        reconciliation = Reconciliation(
            bank_account_id=bank_account_id,
            statement_id=statement_id,
            reconciliation_date=reconciliation_date,
            statement_balance=statement_balance,
            gl_balance=gl_balance,
            adjusted_balance=gl_balance,
            difference=difference,
            status="in_progress",
            created_by=created_by,
        )

        self.db.add(reconciliation)
        self.db.commit()
        self.db.refresh(reconciliation)

        return reconciliation

    def get_reconciliation_summary(
        self,
        reconciliation_id: UUID,
    ) -> Dict[str, Any]:
        """Get reconciliation summary with matched/unmatched items."""
        recon = self.db.query(Reconciliation).get(reconciliation_id)
        if not recon:
            raise ValueError("Reconciliation not found")

        bank_account = self.db.query(BankAccount).get(recon.bank_account_id)

        # Get unreconciled GL transactions
        unreconciled_gl = self.db.query(JournalLine).join(JournalEntry).filter(
            and_(
                JournalLine.account_id == bank_account.account_id,
                JournalEntry.status == EntryStatusEnum.POSTED,
                JournalEntry.entry_date <= recon.reconciliation_date,
                JournalLine.is_reconciled == False
            )
        ).all()

        # Get unmatched bank transactions
        unmatched_bank = []
        if recon.statement_id:
            unmatched_bank = self.db.query(BankTransaction).filter(
                BankTransaction.statement_id == recon.statement_id,
                BankTransaction.is_matched == False
            ).all()

        # Calculate outstanding
        outstanding_deposits = sum(
            float(l.debit_amount) for l in unreconciled_gl
        )
        outstanding_payments = sum(
            float(l.credit_amount) for l in unreconciled_gl
        )

        adjusted_balance = float(recon.gl_balance) + outstanding_deposits - outstanding_payments

        return {
            "id": str(recon.id),
            "reconciliation_date": recon.reconciliation_date.isoformat(),
            "statement_balance": float(recon.statement_balance),
            "gl_balance": float(recon.gl_balance),
            "adjusted_balance": adjusted_balance,
            "difference": float(recon.statement_balance) - adjusted_balance,
            "status": recon.status,
            "outstanding_deposits": outstanding_deposits,
            "outstanding_payments": outstanding_payments,
            "unreconciled_gl_count": len(unreconciled_gl),
            "unmatched_bank_count": len(unmatched_bank),
            "unreconciled_gl": [
                {
                    "id": str(l.id),
                    "date": l.entry.entry_date.isoformat(),
                    "description": l.description or l.entry.description,
                    "debit": float(l.debit_amount),
                    "credit": float(l.credit_amount),
                }
                for l in unreconciled_gl
            ],
            "unmatched_bank": [
                {
                    "id": str(t.id),
                    "date": t.transaction_date.isoformat(),
                    "description": t.description,
                    "amount": float(t.amount),
                    "type": t.transaction_type,
                }
                for t in unmatched_bank
            ],
        }

    def complete_reconciliation(
        self,
        reconciliation_id: UUID,
        completed_by: UUID,
        notes: str = None,
    ) -> Reconciliation:
        """Complete a reconciliation session."""
        recon = self.db.query(Reconciliation).get(reconciliation_id)
        if not recon:
            raise ValueError("Reconciliation not found")

        # Recalculate final difference
        summary = self.get_reconciliation_summary(reconciliation_id)

        recon.adjusted_balance = Decimal(str(summary["adjusted_balance"]))
        recon.difference = Decimal(str(summary["difference"]))

        if abs(recon.difference) < Decimal("0.01"):
            recon.status = "completed"
        else:
            recon.status = "discrepancy"

        recon.completed_at = utc_now()
        recon.completed_by = completed_by
        recon.notes = notes

        # Update bank account
        bank_account = self.db.query(BankAccount).get(recon.bank_account_id)
        bank_account.last_reconciled_date = recon.reconciliation_date
        bank_account.last_reconciled_balance = recon.statement_balance

        self.db.commit()

        return recon

    def _get_gl_balance(self, account_id: UUID, as_of_date: date) -> Decimal:
        """Get GL account balance as of date."""
        from app.accounting.chart_of_accounts.models import Account

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


def get_reconciliation_service(db: Session) -> ReconciliationService:
    return ReconciliationService(db)
