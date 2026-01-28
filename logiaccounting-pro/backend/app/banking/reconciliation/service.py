"""
Bank Reconciliation Service
Business logic for bank reconciliation
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID, uuid4
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session

from app.utils.datetime_utils import utc_now

from app.banking.reconciliation.models import (
    BankReconciliation, BankReconciliationLine, BankMatchingRule,
    ReconciliationStatus, MatchType, LineStatus
)
from app.banking.reconciliation.schemas import (
    ReconciliationCreate, ReconciliationUpdate, ReconciliationLineCreate,
    AutoMatchResult
)
from app.banking.transactions.models import BankTransaction, MatchStatus
from app.banking.accounts.models import BankAccountBalance


class BankReconciliationService:
    """Service for bank reconciliation operations"""

    def __init__(self, db: Session, customer_id: UUID = None):
        self.db = db
        self.customer_id = customer_id

    def create_reconciliation(
        self,
        data: ReconciliationCreate,
        created_by: UUID
    ) -> BankReconciliation:
        """Create a new reconciliation session"""
        # Generate reconciliation number
        recon_number = f"RECON-{data.account_id.hex[:8].upper()}-{datetime.now().strftime('%Y%m%d')}"

        # Get book balances from balance history
        book_opening = self._get_book_balance(data.account_id, data.period_start)
        book_closing = self._get_book_balance(data.account_id, data.period_end)

        reconciliation = BankReconciliation(
            customer_id=self.customer_id,
            account_id=data.account_id,
            reconciliation_number=recon_number,
            period_start=data.period_start,
            period_end=data.period_end,
            statement_opening_balance=data.statement_opening_balance,
            statement_closing_balance=data.statement_closing_balance,
            book_opening_balance=book_opening,
            book_closing_balance=book_closing,
            notes=data.notes,
            created_by=created_by
        )

        self.db.add(reconciliation)
        self.db.commit()
        self.db.refresh(reconciliation)

        return reconciliation

    def get_reconciliation_by_id(self, reconciliation_id: UUID) -> BankReconciliation:
        """Get reconciliation by ID"""
        result = self.db.execute(
            select(BankReconciliation).where(BankReconciliation.id == reconciliation_id)
        )
        reconciliation = result.scalar_one_or_none()

        if not reconciliation:
            raise ValueError(f"Reconciliation {reconciliation_id} not found")

        return reconciliation

    def get_reconciliations(
        self,
        account_id: UUID = None,
        status: ReconciliationStatus = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[BankReconciliation], int]:
        """Get reconciliations with filtering"""
        query = select(BankReconciliation).where(
            BankReconciliation.customer_id == self.customer_id
        )

        if account_id:
            query = query.where(BankReconciliation.account_id == account_id)

        if status:
            query = query.where(BankReconciliation.status == status.value)

        # Count total
        count_result = self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(BankReconciliation.period_end.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        reconciliations = list(result.scalars().all())

        return reconciliations, total

    def add_reconciliation_line(
        self,
        reconciliation_id: UUID,
        data: ReconciliationLineCreate,
        matched_by: UUID
    ) -> BankReconciliationLine:
        """Add a line to reconciliation"""
        reconciliation = self.get_reconciliation_by_id(reconciliation_id)

        if reconciliation.status == ReconciliationStatus.COMPLETED.value:
            raise ValueError("Cannot modify completed reconciliation")

        # Calculate difference
        difference = None
        if data.statement_amount is not None and data.book_amount is not None:
            difference = data.statement_amount - data.book_amount

        line = BankReconciliationLine(
            reconciliation_id=reconciliation_id,
            transaction_id=data.transaction_id,
            journal_line_id=data.journal_line_id,
            match_type=data.match_type.value,
            statement_amount=data.statement_amount,
            book_amount=data.book_amount,
            difference=difference,
            notes=data.notes,
            matched_by=matched_by
        )

        self.db.add(line)

        # Update transaction status if linked
        if data.transaction_id:
            self._update_transaction_match_status(
                data.transaction_id,
                MatchStatus.RECONCILED,
                reconciliation_id
            )

        # Recalculate totals
        self._recalculate_totals(reconciliation)

        self.db.commit()
        self.db.refresh(line)

        return line

    def remove_reconciliation_line(
        self,
        line_id: UUID
    ):
        """Remove a line from reconciliation"""
        result = self.db.execute(
            select(BankReconciliationLine).where(BankReconciliationLine.id == line_id)
        )
        line = result.scalar_one_or_none()

        if not line:
            raise ValueError(f"Reconciliation line {line_id} not found")

        reconciliation = self.get_reconciliation_by_id(line.reconciliation_id)

        if reconciliation.status == ReconciliationStatus.COMPLETED.value:
            raise ValueError("Cannot modify completed reconciliation")

        # Reset transaction status if linked
        if line.transaction_id:
            self._update_transaction_match_status(
                line.transaction_id,
                MatchStatus.UNMATCHED,
                None
            )

        self.db.delete(line)
        self._recalculate_totals(reconciliation)
        self.db.commit()

    def auto_match_transactions(
        self,
        reconciliation_id: UUID,
        apply_rules: bool = True,
        match_threshold: Decimal = Decimal("0.8")
    ) -> AutoMatchResult:
        """Automatically match transactions using rules and amount matching"""
        reconciliation = self.get_reconciliation_by_id(reconciliation_id)

        # Get unmatched transactions for the period
        result = self.db.execute(
            select(BankTransaction).where(
                and_(
                    BankTransaction.account_id == reconciliation.account_id,
                    BankTransaction.transaction_date >= reconciliation.period_start,
                    BankTransaction.transaction_date <= reconciliation.period_end,
                    BankTransaction.is_reconciled == False
                )
            )
        )
        transactions = list(result.scalars().all())

        matched_count = 0
        suggested_count = 0
        matches = []

        if apply_rules:
            rules = self._get_active_rules()

            for txn in transactions:
                for rule in rules:
                    if self._rule_matches(rule, txn):
                        # Apply rule action
                        matches.append({
                            "transaction_id": str(txn.id),
                            "rule_id": str(rule.id),
                            "match_type": "rule_based",
                            "confidence": 1.0
                        })
                        matched_count += 1

                        # Update rule stats
                        rule.times_matched += 1
                        rule.last_matched_at = utc_now()
                        break

        # Amount-based matching for remaining transactions
        unmatched = [t for t in transactions if str(t.id) not in [m["transaction_id"] for m in matches]]

        for txn in unmatched:
            # Look for matching journal entries by amount
            # This is a simplified example - real implementation would be more sophisticated
            matches.append({
                "transaction_id": str(txn.id),
                "match_type": "suggested",
                "confidence": 0.5
            })
            suggested_count += 1

        self.db.commit()

        return AutoMatchResult(
            total_transactions=len(transactions),
            matched_count=matched_count,
            suggested_count=suggested_count,
            unmatched_count=len(transactions) - matched_count - suggested_count,
            matches=matches
        )

    def complete_reconciliation(
        self,
        reconciliation_id: UUID,
        completed_by: UUID
    ) -> BankReconciliation:
        """Complete and finalize reconciliation"""
        reconciliation = self.get_reconciliation_by_id(reconciliation_id)

        if not reconciliation.is_balanced:
            raise ValueError("Reconciliation is not balanced")

        reconciliation.status = ReconciliationStatus.COMPLETED.value
        reconciliation.completed_by = completed_by
        reconciliation.completed_at = utc_now()

        # Update account reconciliation date
        from app.banking.accounts.models import BankAccount
        account = self.db.execute(
            select(BankAccount).where(BankAccount.id == reconciliation.account_id)
        ).scalar_one()

        account.last_reconciled_date = reconciliation.period_end
        account.last_reconciled_balance = reconciliation.statement_closing_balance

        self.db.commit()
        self.db.refresh(reconciliation)

        return reconciliation

    def _get_book_balance(self, account_id: UUID, as_of_date: date) -> Decimal:
        """Get book balance as of a specific date"""
        result = self.db.execute(
            select(BankAccountBalance).where(
                and_(
                    BankAccountBalance.account_id == account_id,
                    BankAccountBalance.balance_date <= as_of_date
                )
            ).order_by(BankAccountBalance.balance_date.desc()).limit(1)
        )
        balance = result.scalar_one_or_none()

        return balance.closing_balance if balance else Decimal("0")

    def _recalculate_totals(self, reconciliation: BankReconciliation):
        """Recalculate reconciliation totals"""
        result = self.db.execute(
            select(BankReconciliationLine).where(
                BankReconciliationLine.reconciliation_id == reconciliation.id
            )
        )
        lines = list(result.scalars().all())

        total_matched = Decimal("0")
        total_unmatched_statement = Decimal("0")
        total_unmatched_book = Decimal("0")
        outstanding_deposits = 0
        outstanding_withdrawals = 0

        for line in lines:
            if line.status == LineStatus.MATCHED.value:
                total_matched += line.statement_amount or Decimal("0")
            elif line.status == LineStatus.UNMATCHED_STATEMENT.value:
                total_unmatched_statement += line.statement_amount or Decimal("0")
                if line.statement_amount and line.statement_amount > 0:
                    outstanding_deposits += 1
                else:
                    outstanding_withdrawals += 1
            elif line.status == LineStatus.UNMATCHED_BOOK.value:
                total_unmatched_book += line.book_amount or Decimal("0")

        reconciliation.total_matched = total_matched
        reconciliation.total_unmatched_statement = total_unmatched_statement
        reconciliation.total_unmatched_book = total_unmatched_book
        reconciliation.outstanding_deposits = outstanding_deposits
        reconciliation.outstanding_withdrawals = outstanding_withdrawals

        # Calculate reconciling difference
        reconciliation.reconciling_difference = (
            reconciliation.statement_closing_balance -
            reconciliation.book_closing_balance -
            total_unmatched_statement +
            total_unmatched_book
        )

    def _update_transaction_match_status(
        self,
        transaction_id: UUID,
        status: MatchStatus,
        reconciliation_id: UUID = None
    ):
        """Update transaction match status"""
        result = self.db.execute(
            select(BankTransaction).where(BankTransaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()

        if transaction:
            transaction.match_status = status.value
            transaction.reconciliation_id = reconciliation_id
            if status == MatchStatus.RECONCILED:
                transaction.is_reconciled = True
                transaction.reconciled_at = utc_now()

    def _get_active_rules(self) -> List[BankMatchingRule]:
        """Get active matching rules ordered by priority"""
        result = self.db.execute(
            select(BankMatchingRule).where(
                and_(
                    BankMatchingRule.customer_id == self.customer_id,
                    BankMatchingRule.is_active == True
                )
            ).order_by(BankMatchingRule.priority)
        )
        return list(result.scalars().all())

    def _rule_matches(self, rule: BankMatchingRule, transaction: BankTransaction) -> bool:
        """Check if a rule matches a transaction"""
        criteria = rule.match_criteria

        field = criteria.get("field", "description")
        operator = criteria.get("operator", "contains")
        value = criteria.get("value", "")

        # Get transaction field value
        txn_value = getattr(transaction, field, "") or ""

        if operator == "contains":
            return value.lower() in txn_value.lower()
        elif operator == "equals":
            return value.lower() == txn_value.lower()
        elif operator == "starts_with":
            return txn_value.lower().startswith(value.lower())
        elif operator == "ends_with":
            return txn_value.lower().endswith(value.lower())

        return False
