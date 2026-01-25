"""
General Ledger Service
Ledger queries and account activity
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy import and_, or_, func, case
from sqlalchemy.orm import Session, joinedload

from app.accounting.chart_of_accounts.models import Account, AccountTypeEnum
from app.accounting.journal.models import JournalEntry, JournalLine, EntryStatusEnum
from app.accounting.ledger.models import AccountBalance
from app.accounting.periods.models import FiscalPeriod

logger = logging.getLogger(__name__)


class GeneralLedgerService:
    """Service for general ledger operations."""

    def __init__(self, db: Session):
        self.db = db

    # ============== Account Ledger ==============

    def get_account_ledger(
        self,
        account_id: UUID,
        start_date: date = None,
        end_date: date = None,
        period_id: UUID = None,
        include_unposted: bool = False,
    ) -> Dict[str, Any]:
        """
        Get ledger for a specific account with all transactions.
        """
        account = self.db.query(Account).options(
            joinedload(Account.account_type)
        ).get(account_id)

        if not account:
            raise ValueError("Account not found")

        # Build query
        query = self.db.query(JournalLine).join(JournalEntry).filter(
            JournalLine.account_id == account_id
        )

        # Status filter
        if include_unposted:
            query = query.filter(
                JournalEntry.status.in_([EntryStatusEnum.POSTED, EntryStatusEnum.APPROVED])
            )
        else:
            query = query.filter(JournalEntry.status == EntryStatusEnum.POSTED)

        # Date filters
        if start_date:
            query = query.filter(JournalEntry.entry_date >= start_date)
        if end_date:
            query = query.filter(JournalEntry.entry_date <= end_date)

        # Period filter
        if period_id:
            query = query.filter(JournalEntry.fiscal_period_id == period_id)

        # Get lines ordered by date
        lines = query.options(
            joinedload(JournalLine.entry)
        ).order_by(
            JournalEntry.entry_date,
            JournalEntry.entry_number,
            JournalLine.line_number
        ).all()

        # Calculate running balance
        running_balance = account.opening_balance
        transactions = []

        for line in lines:
            entry = line.entry

            # Calculate balance change
            if account.account_type.normal_balance.value == "debit":
                balance_change = line.debit_amount - line.credit_amount
            else:
                balance_change = line.credit_amount - line.debit_amount

            running_balance += balance_change

            transactions.append({
                "date": entry.entry_date.isoformat(),
                "entry_number": entry.entry_number,
                "entry_id": str(entry.id),
                "entry_type": entry.entry_type.value,
                "reference": entry.reference,
                "description": line.description or entry.description,
                "debit": float(line.debit_amount),
                "credit": float(line.credit_amount),
                "balance": float(running_balance),
                "is_posted": entry.status == EntryStatusEnum.POSTED,
            })

        # Calculate totals
        total_debit = sum(t["debit"] for t in transactions)
        total_credit = sum(t["credit"] for t in transactions)

        return {
            "account": {
                "id": str(account.id),
                "code": account.code,
                "name": account.name,
                "type": account.account_type.name if account.account_type else None,
                "normal_balance": account.account_type.normal_balance.value if account.account_type else None,
            },
            "opening_balance": float(account.opening_balance),
            "closing_balance": float(running_balance),
            "total_debit": total_debit,
            "total_credit": total_credit,
            "transaction_count": len(transactions),
            "transactions": transactions,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
        }

    # ============== Account Balances ==============

    def get_account_balance(
        self,
        account_id: UUID,
        as_of_date: date = None,
    ) -> Dict[str, Any]:
        """Get current balance for an account."""
        account = self.db.query(Account).options(
            joinedload(Account.account_type)
        ).get(account_id)

        if not account:
            raise ValueError("Account not found")

        as_of_date = as_of_date or date.today()

        # Sum posted transactions up to date
        result = self.db.query(
            func.coalesce(func.sum(JournalLine.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalLine.credit_amount), 0).label("total_credit"),
            func.count(JournalLine.id).label("transaction_count")
        ).join(JournalEntry).filter(
            and_(
                JournalLine.account_id == account_id,
                JournalEntry.status == EntryStatusEnum.POSTED,
                JournalEntry.entry_date <= as_of_date
            )
        ).first()

        total_debit = Decimal(str(result.total_debit))
        total_credit = Decimal(str(result.total_credit))

        # Calculate balance based on normal balance
        if account.account_type.normal_balance.value == "debit":
            balance = account.opening_balance + total_debit - total_credit
        else:
            balance = account.opening_balance + total_credit - total_debit

        return {
            "account_id": str(account_id),
            "account_code": account.code,
            "account_name": account.name,
            "account_type": account.account_type.name if account.account_type else None,
            "as_of_date": as_of_date.isoformat(),
            "opening_balance": float(account.opening_balance),
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "current_balance": float(balance),
            "transaction_count": result.transaction_count,
        }

    def get_all_balances(
        self,
        customer_id: UUID,
        as_of_date: date = None,
        account_type: str = None,
        with_activity_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get balances for all accounts."""
        as_of_date = as_of_date or date.today()

        # Query accounts with aggregated balances
        query = self.db.query(
            Account,
            func.coalesce(func.sum(JournalLine.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalLine.credit_amount), 0).label("total_credit"),
            func.count(JournalLine.id).label("transaction_count")
        ).outerjoin(
            JournalLine, JournalLine.account_id == Account.id
        ).outerjoin(
            JournalEntry,
            and_(
                JournalLine.entry_id == JournalEntry.id,
                JournalEntry.status == EntryStatusEnum.POSTED,
                JournalEntry.entry_date <= as_of_date
            )
        ).filter(
            and_(
                Account.customer_id == customer_id,
                Account.is_active == True
            )
        ).group_by(Account.id)

        if account_type:
            query = query.join(Account.account_type).filter(
                Account.account_type.has(name=account_type)
            )

        results = query.order_by(Account.code).all()

        balances = []
        for account, total_debit, total_credit, tx_count in results:
            # Calculate balance
            if account.account_type and account.account_type.normal_balance.value == "debit":
                balance = account.opening_balance + Decimal(str(total_debit)) - Decimal(str(total_credit))
            else:
                balance = account.opening_balance + Decimal(str(total_credit)) - Decimal(str(total_debit))

            if with_activity_only and tx_count == 0 and balance == 0:
                continue

            balances.append({
                "account_id": str(account.id),
                "account_code": account.code,
                "account_name": account.name,
                "account_type": account.account_type.name if account.account_type else None,
                "level": account.level,
                "is_header": account.is_header,
                "opening_balance": float(account.opening_balance),
                "total_debit": float(total_debit),
                "total_credit": float(total_credit),
                "current_balance": float(balance),
                "transaction_count": tx_count,
            })

        return balances

    # ============== Period Activity ==============

    def get_period_activity(
        self,
        customer_id: UUID,
        period_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get account activity for a specific period."""
        period = self.db.query(FiscalPeriod).get(period_id)
        if not period:
            raise ValueError("Period not found")

        # Get all activity in period
        results = self.db.query(
            Account,
            func.coalesce(func.sum(JournalLine.debit_amount), 0).label("period_debit"),
            func.coalesce(func.sum(JournalLine.credit_amount), 0).label("period_credit"),
            func.count(JournalLine.id).label("transaction_count")
        ).outerjoin(
            JournalLine, JournalLine.account_id == Account.id
        ).outerjoin(
            JournalEntry,
            and_(
                JournalLine.entry_id == JournalEntry.id,
                JournalEntry.status == EntryStatusEnum.POSTED,
                JournalEntry.fiscal_period_id == period_id
            )
        ).filter(
            and_(
                Account.customer_id == customer_id,
                Account.is_active == True
            )
        ).group_by(Account.id).order_by(Account.code).all()

        activity = []
        for account, period_debit, period_credit, tx_count in results:
            if tx_count > 0:
                activity.append({
                    "account_id": str(account.id),
                    "account_code": account.code,
                    "account_name": account.name,
                    "account_type": account.account_type.name if account.account_type else None,
                    "period_debit": float(period_debit),
                    "period_credit": float(period_credit),
                    "net_activity": float(period_debit - period_credit),
                    "transaction_count": tx_count,
                })

        return activity

    # ============== Subsidiary Ledgers ==============

    def get_ar_ledger(
        self,
        customer_id: UUID,
        as_of_date: date = None,
    ) -> List[Dict[str, Any]]:
        """Get Accounts Receivable subsidiary ledger by customer."""
        # This would typically join with customer data
        # For now, return AR account transactions grouped by reference
        ar_accounts = self.db.query(Account).filter(
            and_(
                Account.customer_id == customer_id,
                Account.code.like("12%"),  # AR accounts
                Account.is_active == True
            )
        ).all()

        ar_ids = [a.id for a in ar_accounts]

        query = self.db.query(
            JournalEntry.reference,
            JournalLine.description,
            func.sum(JournalLine.debit_amount).label("total_debit"),
            func.sum(JournalLine.credit_amount).label("total_credit"),
            func.min(JournalEntry.entry_date).label("first_date"),
            func.max(JournalEntry.entry_date).label("last_date"),
        ).join(JournalEntry).filter(
            and_(
                JournalLine.account_id.in_(ar_ids),
                JournalEntry.status == EntryStatusEnum.POSTED
            )
        )

        if as_of_date:
            query = query.filter(JournalEntry.entry_date <= as_of_date)

        results = query.group_by(
            JournalEntry.reference,
            JournalLine.description
        ).having(
            func.sum(JournalLine.debit_amount) != func.sum(JournalLine.credit_amount)
        ).all()

        return [
            {
                "reference": r.reference,
                "description": r.description,
                "total_debit": float(r.total_debit or 0),
                "total_credit": float(r.total_credit or 0),
                "balance": float((r.total_debit or 0) - (r.total_credit or 0)),
                "first_date": r.first_date.isoformat() if r.first_date else None,
                "last_date": r.last_date.isoformat() if r.last_date else None,
            }
            for r in results
        ]

    def get_ap_ledger(
        self,
        customer_id: UUID,
        as_of_date: date = None,
    ) -> List[Dict[str, Any]]:
        """Get Accounts Payable subsidiary ledger by supplier."""
        # Similar to AR, grouped by supplier/reference
        ap_accounts = self.db.query(Account).filter(
            and_(
                Account.customer_id == customer_id,
                Account.code.like("21%"),  # AP accounts
                Account.is_active == True
            )
        ).all()

        ap_ids = [a.id for a in ap_accounts]

        query = self.db.query(
            JournalEntry.reference,
            JournalLine.description,
            func.sum(JournalLine.debit_amount).label("total_debit"),
            func.sum(JournalLine.credit_amount).label("total_credit"),
            func.min(JournalEntry.entry_date).label("first_date"),
            func.max(JournalEntry.entry_date).label("last_date"),
        ).join(JournalEntry).filter(
            and_(
                JournalLine.account_id.in_(ap_ids),
                JournalEntry.status == EntryStatusEnum.POSTED
            )
        )

        if as_of_date:
            query = query.filter(JournalEntry.entry_date <= as_of_date)

        results = query.group_by(
            JournalEntry.reference,
            JournalLine.description
        ).having(
            func.sum(JournalLine.credit_amount) != func.sum(JournalLine.debit_amount)
        ).all()

        return [
            {
                "reference": r.reference,
                "description": r.description,
                "total_debit": float(r.total_debit or 0),
                "total_credit": float(r.total_credit or 0),
                "balance": float((r.total_credit or 0) - (r.total_debit or 0)),
                "first_date": r.first_date.isoformat() if r.first_date else None,
                "last_date": r.last_date.isoformat() if r.last_date else None,
            }
            for r in results
        ]


def get_general_ledger_service(db: Session) -> GeneralLedgerService:
    """Factory function."""
    return GeneralLedgerService(db)
