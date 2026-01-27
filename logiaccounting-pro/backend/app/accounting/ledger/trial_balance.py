"""
Trial Balance Service
Generate trial balance reports
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.accounting.chart_of_accounts.models import Account, AccountType
from app.accounting.journal.models import JournalEntry, JournalLine, EntryStatusEnum
from app.accounting.periods.models import FiscalPeriod

logger = logging.getLogger(__name__)


class TrialBalanceService:
    """Service for generating trial balance reports."""

    def __init__(self, db: Session):
        self.db = db

    def generate_trial_balance(
        self,
        customer_id: UUID,
        as_of_date: date = None,
        period_id: UUID = None,
        include_zero_balances: bool = False,
        group_by_type: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate trial balance report.

        Shows all accounts with their debit/credit balances.
        Total debits must equal total credits.
        """
        as_of_date = as_of_date or date.today()

        # Build base query
        query = self.db.query(
            Account,
            func.coalesce(func.sum(JournalLine.debit_amount), 0).label("total_debit"),
            func.coalesce(func.sum(JournalLine.credit_amount), 0).label("total_credit"),
        ).outerjoin(
            JournalLine, JournalLine.account_id == Account.id
        ).outerjoin(
            JournalEntry,
            and_(
                JournalLine.entry_id == JournalEntry.id,
                JournalEntry.status == EntryStatusEnum.POSTED,
            )
        ).filter(
            and_(
                Account.customer_id == customer_id,
                Account.is_active == True,
                Account.is_header == False,  # Exclude header accounts
            )
        )

        # Apply date filter
        if period_id:
            query = query.filter(JournalEntry.fiscal_period_id == period_id)
        else:
            query = query.filter(
                or_(
                    JournalEntry.entry_date == None,
                    JournalEntry.entry_date <= as_of_date
                )
            )

        # Group and order
        results = query.options(
            joinedload(Account.account_type)
        ).group_by(Account.id).order_by(Account.code).all()

        # Process results
        accounts = []
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for account, sum_debit, sum_credit in results:
            opening = account.opening_balance
            period_debit = Decimal(str(sum_debit))
            period_credit = Decimal(str(sum_credit))

            # Calculate closing balance
            if account.account_type.normal_balance.value == "debit":
                closing = opening + period_debit - period_credit
                # Show as debit balance if positive
                if closing >= 0:
                    debit_balance = closing
                    credit_balance = Decimal("0")
                else:
                    debit_balance = Decimal("0")
                    credit_balance = abs(closing)
            else:
                closing = opening + period_credit - period_debit
                # Show as credit balance if positive
                if closing >= 0:
                    debit_balance = Decimal("0")
                    credit_balance = closing
                else:
                    debit_balance = abs(closing)
                    credit_balance = Decimal("0")

            # Skip zero balances if not requested
            if not include_zero_balances and debit_balance == 0 and credit_balance == 0:
                continue

            accounts.append({
                "account_id": str(account.id),
                "account_code": account.code,
                "account_name": account.name,
                "account_type": account.account_type.name if account.account_type else None,
                "account_type_display": account.account_type.display_name if account.account_type else None,
                "normal_balance": account.account_type.normal_balance.value if account.account_type else None,
                "opening_balance": float(opening),
                "period_debit": float(period_debit),
                "period_credit": float(period_credit),
                "debit_balance": float(debit_balance),
                "credit_balance": float(credit_balance),
                "closing_balance": float(closing),
            })

            total_debit += debit_balance
            total_credit += credit_balance

        # Group by account type if requested
        grouped_accounts = {}
        if group_by_type:
            for acc in accounts:
                acc_type = acc["account_type"] or "Other"
                if acc_type not in grouped_accounts:
                    grouped_accounts[acc_type] = {
                        "type": acc_type,
                        "type_display": acc["account_type_display"] or "Other",
                        "accounts": [],
                        "subtotal_debit": 0,
                        "subtotal_credit": 0,
                    }
                grouped_accounts[acc_type]["accounts"].append(acc)
                grouped_accounts[acc_type]["subtotal_debit"] += acc["debit_balance"]
                grouped_accounts[acc_type]["subtotal_credit"] += acc["credit_balance"]

        # Check if balanced
        is_balanced = total_debit == total_credit
        difference = total_debit - total_credit

        return {
            "report_type": "trial_balance",
            "as_of_date": as_of_date.isoformat(),
            "generated_at": date.today().isoformat(),
            "customer_id": str(customer_id),
            "is_balanced": is_balanced,
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "difference": float(difference),
            "account_count": len(accounts),
            "accounts": accounts,
            "grouped_accounts": list(grouped_accounts.values()) if group_by_type else None,
        }

    def generate_adjusted_trial_balance(
        self,
        customer_id: UUID,
        period_id: UUID,
    ) -> Dict[str, Any]:
        """
        Generate adjusted trial balance after adjusting entries.
        Shows unadjusted, adjustments, and adjusted columns.
        """
        period = self.db.query(FiscalPeriod).get(period_id)
        if not period:
            raise ValueError("Period not found")

        # Get all accounts
        accounts_query = self.db.query(Account).filter(
            and_(
                Account.customer_id == customer_id,
                Account.is_active == True,
                Account.is_header == False,
            )
        ).options(joinedload(Account.account_type)).order_by(Account.code)

        accounts = accounts_query.all()

        results = []
        totals = {
            "unadjusted_debit": Decimal("0"),
            "unadjusted_credit": Decimal("0"),
            "adjustments_debit": Decimal("0"),
            "adjustments_credit": Decimal("0"),
            "adjusted_debit": Decimal("0"),
            "adjusted_credit": Decimal("0"),
        }

        for account in accounts:
            # Unadjusted: All entries except adjusting
            unadjusted = self.db.query(
                func.coalesce(func.sum(JournalLine.debit_amount), 0),
                func.coalesce(func.sum(JournalLine.credit_amount), 0),
            ).join(JournalEntry).filter(
                and_(
                    JournalLine.account_id == account.id,
                    JournalEntry.status == EntryStatusEnum.POSTED,
                    JournalEntry.fiscal_period_id == period_id,
                    JournalEntry.entry_type != "adjustment"
                )
            ).first()

            # Adjustments only
            adjustments = self.db.query(
                func.coalesce(func.sum(JournalLine.debit_amount), 0),
                func.coalesce(func.sum(JournalLine.credit_amount), 0),
            ).join(JournalEntry).filter(
                and_(
                    JournalLine.account_id == account.id,
                    JournalEntry.status == EntryStatusEnum.POSTED,
                    JournalEntry.fiscal_period_id == period_id,
                    JournalEntry.entry_type == "adjustment"
                )
            ).first()

            unadj_debit = Decimal(str(unadjusted[0]))
            unadj_credit = Decimal(str(unadjusted[1]))
            adj_debit = Decimal(str(adjustments[0]))
            adj_credit = Decimal(str(adjustments[1]))

            # Calculate balances
            opening = account.opening_balance

            if account.account_type.normal_balance.value == "debit":
                unadj_balance = opening + unadj_debit - unadj_credit
                adj_balance = opening + unadj_debit + adj_debit - unadj_credit - adj_credit
            else:
                unadj_balance = opening + unadj_credit - unadj_debit
                adj_balance = opening + unadj_credit + adj_credit - unadj_debit - adj_debit

            # Convert to debit/credit columns
            def to_columns(balance, normal):
                if normal == "debit":
                    if balance >= 0:
                        return balance, Decimal("0")
                    return Decimal("0"), abs(balance)
                else:
                    if balance >= 0:
                        return Decimal("0"), balance
                    return abs(balance), Decimal("0")

            normal = account.account_type.normal_balance.value
            unadj_d, unadj_c = to_columns(unadj_balance, normal)
            adj_d, adj_c = to_columns(adj_balance, normal)

            # Skip if all zeros
            if all(x == 0 for x in [unadj_d, unadj_c, adj_debit, adj_credit, adj_d, adj_c]):
                continue

            results.append({
                "account_code": account.code,
                "account_name": account.name,
                "unadjusted_debit": float(unadj_d),
                "unadjusted_credit": float(unadj_c),
                "adjustments_debit": float(adj_debit),
                "adjustments_credit": float(adj_credit),
                "adjusted_debit": float(adj_d),
                "adjusted_credit": float(adj_c),
            })

            totals["unadjusted_debit"] += unadj_d
            totals["unadjusted_credit"] += unadj_c
            totals["adjustments_debit"] += adj_debit
            totals["adjustments_credit"] += adj_credit
            totals["adjusted_debit"] += adj_d
            totals["adjusted_credit"] += adj_c

        return {
            "report_type": "adjusted_trial_balance",
            "period": period.name,
            "period_id": str(period_id),
            "start_date": period.start_date.isoformat(),
            "end_date": period.end_date.isoformat(),
            "accounts": results,
            "totals": {k: float(v) for k, v in totals.items()},
            "is_balanced": totals["adjusted_debit"] == totals["adjusted_credit"],
        }

    def generate_comparative_trial_balance(
        self,
        customer_id: UUID,
        current_date: date,
        prior_date: date,
    ) -> Dict[str, Any]:
        """
        Generate comparative trial balance showing two periods.
        """
        # Get current period
        current_tb = self.generate_trial_balance(
            customer_id, as_of_date=current_date, include_zero_balances=True
        )

        # Get prior period
        prior_tb = self.generate_trial_balance(
            customer_id, as_of_date=prior_date, include_zero_balances=True
        )

        # Merge accounts
        prior_map = {a["account_code"]: a for a in prior_tb["accounts"]}

        comparative = []
        for curr_acc in current_tb["accounts"]:
            code = curr_acc["account_code"]
            prior_acc = prior_map.get(code, {})

            curr_balance = curr_acc["closing_balance"]
            prior_balance = prior_acc.get("closing_balance", 0)
            change = curr_balance - prior_balance

            if prior_balance != 0:
                change_pct = (change / abs(prior_balance)) * 100
            else:
                change_pct = 100 if curr_balance != 0 else 0

            comparative.append({
                "account_code": code,
                "account_name": curr_acc["account_name"],
                "account_type": curr_acc["account_type"],
                "current_debit": curr_acc["debit_balance"],
                "current_credit": curr_acc["credit_balance"],
                "prior_debit": prior_acc.get("debit_balance", 0),
                "prior_credit": prior_acc.get("credit_balance", 0),
                "change": change,
                "change_percent": round(change_pct, 2),
            })

        return {
            "report_type": "comparative_trial_balance",
            "current_date": current_date.isoformat(),
            "prior_date": prior_date.isoformat(),
            "current_totals": {
                "debit": current_tb["total_debit"],
                "credit": current_tb["total_credit"],
            },
            "prior_totals": {
                "debit": prior_tb["total_debit"],
                "credit": prior_tb["total_credit"],
            },
            "accounts": comparative,
        }


def get_trial_balance_service(db: Session) -> TrialBalanceService:
    """Factory function."""
    return TrialBalanceService(db)
