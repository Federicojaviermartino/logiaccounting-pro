"""
Journal Entry Validator
Validation rules for double-entry bookkeeping
"""

from datetime import date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from sqlalchemy.orm import Session

from app.accounting.chart_of_accounts.models import Account
from app.accounting.journal.models import JournalEntry, JournalLine, EntryStatusEnum
from app.accounting.periods.models import FiscalPeriod

logger = logging.getLogger(__name__)


class ValidationError:
    """Validation error container."""

    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity  # 'error', 'warning'

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity,
        }


class JournalEntryValidator:
    """Validates journal entries for accounting rules."""

    def __init__(self, db: Session):
        self.db = db
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def validate(
        self,
        entry: JournalEntry,
        lines: List[JournalLine] = None,
    ) -> bool:
        """Validate a journal entry. Returns True if valid."""
        self.errors = []
        self.warnings = []

        lines = lines or entry.lines

        # Core validations
        self._validate_balance(lines)
        self._validate_line_count(lines)
        self._validate_accounts(lines)
        self._validate_amounts(lines)
        self._validate_date(entry)
        self._validate_period(entry)
        self._validate_status_transition(entry)

        return len(self.errors) == 0

    def _validate_balance(self, lines: List[JournalLine]):
        """Validate that debits equal credits."""
        total_debit = sum(line.debit_amount or Decimal("0") for line in lines)
        total_credit = sum(line.credit_amount or Decimal("0") for line in lines)

        if total_debit != total_credit:
            self.errors.append(ValidationError(
                field="lines",
                message=f"Entry is not balanced: Debits ({total_debit}) != Credits ({total_credit})"
            ))

    def _validate_line_count(self, lines: List[JournalLine]):
        """Validate minimum line count."""
        if len(lines) < 2:
            self.errors.append(ValidationError(
                field="lines",
                message="Entry must have at least 2 lines"
            ))

    def _validate_accounts(self, lines: List[JournalLine]):
        """Validate all accounts exist and can receive postings."""
        account_ids = [line.account_id for line in lines]

        accounts = self.db.query(Account).filter(
            Account.id.in_(account_ids)
        ).all()

        account_map = {str(a.id): a for a in accounts}

        for i, line in enumerate(lines):
            account = account_map.get(str(line.account_id))

            if not account:
                self.errors.append(ValidationError(
                    field=f"lines[{i}].account_id",
                    message=f"Account not found: {line.account_id}"
                ))
                continue

            if not account.is_active:
                self.errors.append(ValidationError(
                    field=f"lines[{i}].account_id",
                    message=f"Account {account.code} is inactive"
                ))

            if account.is_header:
                self.errors.append(ValidationError(
                    field=f"lines[{i}].account_id",
                    message=f"Cannot post to header account {account.code}"
                ))

    def _validate_amounts(self, lines: List[JournalLine]):
        """Validate line amounts."""
        for i, line in enumerate(lines):
            debit = line.debit_amount or Decimal("0")
            credit = line.credit_amount or Decimal("0")

            # Check for both debit and credit
            if debit > 0 and credit > 0:
                self.errors.append(ValidationError(
                    field=f"lines[{i}]",
                    message="Line cannot have both debit and credit amounts"
                ))

            # Check for zero amounts
            if debit == 0 and credit == 0:
                self.errors.append(ValidationError(
                    field=f"lines[{i}]",
                    message="Line must have either debit or credit amount"
                ))

            # Check for negative amounts
            if debit < 0 or credit < 0:
                self.errors.append(ValidationError(
                    field=f"lines[{i}]",
                    message="Amounts cannot be negative"
                ))

            # Check for excessive precision
            if debit != round(debit, 2) or credit != round(credit, 2):
                self.warnings.append(ValidationError(
                    field=f"lines[{i}]",
                    message="Amount has more than 2 decimal places",
                    severity="warning"
                ))

    def _validate_date(self, entry: JournalEntry):
        """Validate entry date."""
        if not entry.entry_date:
            self.errors.append(ValidationError(
                field="entry_date",
                message="Entry date is required"
            ))
            return

        # Check future date
        if entry.entry_date > date.today():
            self.warnings.append(ValidationError(
                field="entry_date",
                message="Entry date is in the future",
                severity="warning"
            ))

    def _validate_period(self, entry: JournalEntry):
        """Validate fiscal period."""
        if not entry.fiscal_period_id:
            # Try to auto-assign period
            return

        period = self.db.query(FiscalPeriod).get(entry.fiscal_period_id)

        if not period:
            self.errors.append(ValidationError(
                field="fiscal_period_id",
                message="Fiscal period not found"
            ))
            return

        # Check if period is closed
        if period.is_closed:
            self.errors.append(ValidationError(
                field="fiscal_period_id",
                message=f"Fiscal period {period.name} is closed"
            ))

        # Check if date is within period
        if entry.entry_date:
            if entry.entry_date < period.start_date or entry.entry_date > period.end_date:
                self.errors.append(ValidationError(
                    field="entry_date",
                    message=f"Entry date {entry.entry_date} is not within period {period.name}"
                ))

    def _validate_status_transition(self, entry: JournalEntry):
        """Validate status transitions."""
        # Get original status if existing entry
        if hasattr(entry, '_original_status'):
            old_status = entry._original_status
            new_status = entry.status

            valid_transitions = {
                EntryStatusEnum.DRAFT: [EntryStatusEnum.PENDING, EntryStatusEnum.VOIDED],
                EntryStatusEnum.PENDING: [EntryStatusEnum.DRAFT, EntryStatusEnum.APPROVED, EntryStatusEnum.VOIDED],
                EntryStatusEnum.APPROVED: [EntryStatusEnum.PENDING, EntryStatusEnum.POSTED, EntryStatusEnum.VOIDED],
                EntryStatusEnum.POSTED: [EntryStatusEnum.REVERSED],
                EntryStatusEnum.REVERSED: [],
                EntryStatusEnum.VOIDED: [],
            }

            if new_status not in valid_transitions.get(old_status, []):
                self.errors.append(ValidationError(
                    field="status",
                    message=f"Invalid status transition from {old_status.value} to {new_status.value}"
                ))

    def validate_for_posting(self, entry: JournalEntry) -> bool:
        """Additional validations for posting."""
        self.errors = []
        self.warnings = []

        # Basic validation first
        if not self.validate(entry):
            return False

        # Must be approved
        if entry.status != EntryStatusEnum.APPROVED:
            self.errors.append(ValidationError(
                field="status",
                message="Entry must be approved before posting"
            ))

        # Period must be open
        if entry.fiscal_period_id:
            period = self.db.query(FiscalPeriod).get(entry.fiscal_period_id)
            if period and period.is_closed:
                self.errors.append(ValidationError(
                    field="fiscal_period_id",
                    message="Cannot post to closed period"
                ))

        return len(self.errors) == 0

    def validate_for_reversal(self, entry: JournalEntry) -> bool:
        """Validate entry can be reversed."""
        self.errors = []
        self.warnings = []

        if entry.status != EntryStatusEnum.POSTED:
            self.errors.append(ValidationError(
                field="status",
                message="Only posted entries can be reversed"
            ))

        if entry.is_reversing:
            self.errors.append(ValidationError(
                field="is_reversing",
                message="Reversal entries cannot be reversed"
            ))

        return len(self.errors) == 0

    def get_errors(self) -> List[dict]:
        """Get validation errors."""
        return [e.to_dict() for e in self.errors]

    def get_warnings(self) -> List[dict]:
        """Get validation warnings."""
        return [w.to_dict() for w in self.warnings]

    def get_all_issues(self) -> Dict[str, List[dict]]:
        """Get all validation issues."""
        return {
            "errors": self.get_errors(),
            "warnings": self.get_warnings(),
        }


def get_journal_validator(db: Session) -> JournalEntryValidator:
    """Factory function."""
    return JournalEntryValidator(db)
