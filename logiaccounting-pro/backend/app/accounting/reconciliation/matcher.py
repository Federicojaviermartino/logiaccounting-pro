"""
Bank Transaction Matcher
Auto-match bank transactions to journal entries
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.utils.datetime_utils import utc_now

from app.accounting.reconciliation.models import BankTransaction, BankAccount
from app.accounting.journal.models import JournalEntry, JournalLine, EntryStatusEnum

logger = logging.getLogger(__name__)


class TransactionMatcher:
    """Auto-match bank transactions to GL entries."""

    def __init__(self, db: Session):
        self.db = db

    def auto_match_statement(
        self,
        statement_id: UUID,
    ) -> Dict[str, Any]:
        """Auto-match all unmatched transactions in a statement."""
        transactions = self.db.query(BankTransaction).filter(
            BankTransaction.statement_id == statement_id,
            BankTransaction.is_matched == False
        ).all()

        matched = 0
        for trans in transactions:
            match = self._find_best_match(trans)
            if match:
                self._apply_match(trans, match)
                matched += 1

        return {
            "total_transactions": len(transactions),
            "matched": matched,
            "unmatched": len(transactions) - matched,
        }

    def _find_best_match(
        self,
        transaction: BankTransaction,
    ) -> Optional[Tuple[JournalLine, float]]:
        """Find the best matching journal line for a transaction."""
        # Get bank account's GL account
        bank_account = self.db.query(BankAccount).join(
            BankTransaction.statement
        ).filter(
            BankTransaction.id == transaction.id
        ).first()

        if not bank_account:
            return None

        # Search for matching journal lines
        date_range = 7  # Days tolerance

        candidates = self.db.query(JournalLine).join(JournalEntry).filter(
            and_(
                JournalLine.account_id == bank_account.account_id,
                JournalEntry.status == EntryStatusEnum.POSTED,
                JournalEntry.entry_date >= transaction.transaction_date - timedelta(days=date_range),
                JournalEntry.entry_date <= transaction.transaction_date + timedelta(days=date_range),
                JournalLine.is_reconciled == False
            )
        ).all()

        best_match = None
        best_score = 0.0

        for line in candidates:
            score = self._calculate_match_score(transaction, line)
            if score > best_score and score >= 0.7:  # Minimum confidence
                best_score = score
                best_match = (line, score)

        return best_match

    def _calculate_match_score(
        self,
        transaction: BankTransaction,
        line: JournalLine,
    ) -> float:
        """Calculate match confidence score (0-1)."""
        score = 0.0

        # Amount match (most important)
        trans_amount = transaction.amount
        line_amount = line.debit_amount if transaction.transaction_type == "debit" else line.credit_amount

        if trans_amount == line_amount:
            score += 0.5  # Exact match
        elif abs(trans_amount - line_amount) <= Decimal("0.01"):
            score += 0.45  # Within rounding
        elif abs(trans_amount - line_amount) / trans_amount <= Decimal("0.01"):
            score += 0.3  # Within 1%
        else:
            return 0.0  # Amount mismatch, no point continuing

        # Date match
        entry_date = line.entry.entry_date
        trans_date = transaction.transaction_date
        date_diff = abs((entry_date - trans_date).days)

        if date_diff == 0:
            score += 0.3
        elif date_diff <= 1:
            score += 0.25
        elif date_diff <= 3:
            score += 0.15
        elif date_diff <= 7:
            score += 0.05

        # Reference match
        if transaction.reference and line.entry.reference:
            if transaction.reference.lower() in line.entry.reference.lower():
                score += 0.15

        # Description similarity
        if transaction.description and line.description:
            if self._text_similarity(transaction.description, line.description) > 0.5:
                score += 0.05

        return min(score, 1.0)

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity using common words."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        common = words1.intersection(words2)
        return len(common) / max(len(words1), len(words2))

    def _apply_match(
        self,
        transaction: BankTransaction,
        match: Tuple[JournalLine, float],
    ):
        """Apply a match between transaction and journal line."""
        line, confidence = match

        transaction.is_matched = True
        transaction.matched_entry_id = line.entry_id
        transaction.matched_line_id = line.id
        transaction.matched_at = utc_now()
        transaction.match_confidence = Decimal(str(confidence))
        transaction.match_method = "auto"

        line.is_reconciled = True
        line.reconciled_date = transaction.transaction_date
        line.bank_transaction_id = transaction.id

        self.db.commit()

    def manual_match(
        self,
        transaction_id: UUID,
        line_id: UUID,
    ) -> BankTransaction:
        """Manually match a transaction to a journal line."""
        transaction = self.db.query(BankTransaction).get(transaction_id)
        line = self.db.query(JournalLine).get(line_id)

        if not transaction or not line:
            raise ValueError("Transaction or line not found")

        self._apply_match(transaction, (line, 1.0))
        transaction.match_method = "manual"

        self.db.commit()
        return transaction

    def unmatch(self, transaction_id: UUID) -> BankTransaction:
        """Unmatch a previously matched transaction."""
        transaction = self.db.query(BankTransaction).get(transaction_id)
        if not transaction:
            raise ValueError("Transaction not found")

        if transaction.matched_line_id:
            line = self.db.query(JournalLine).get(transaction.matched_line_id)
            if line:
                line.is_reconciled = False
                line.reconciled_date = None
                line.bank_transaction_id = None

        transaction.is_matched = False
        transaction.matched_entry_id = None
        transaction.matched_line_id = None
        transaction.matched_at = None
        transaction.match_confidence = None
        transaction.match_method = None

        self.db.commit()
        return transaction


def get_transaction_matcher(db: Session) -> TransactionMatcher:
    return TransactionMatcher(db)
