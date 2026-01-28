"""
Journal Entry Service
Business logic for journal entry management
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session, joinedload

from app.utils.datetime_utils import utc_now

from app.accounting.journal.models import (
    JournalEntry, JournalLine, EntryTypeEnum, EntryStatusEnum
)
from app.accounting.journal.schemas import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryFilter,
    EntryReversalRequest
)
from app.accounting.journal.validator import JournalEntryValidator
from app.accounting.chart_of_accounts.service import ChartOfAccountsService

logger = logging.getLogger(__name__)


class JournalEntryService:
    """Service for managing journal entries."""

    def __init__(self, db: Session):
        self.db = db
        self.validator = JournalEntryValidator(db)
        self.coa_service = ChartOfAccountsService(db)

    # ============== Entry Number Generation ==============

    def _generate_entry_number(self, customer_id: UUID, entry_date: date) -> str:
        """Generate unique entry number."""
        year = entry_date.year
        prefix = f"JE-{year}-"

        # Get latest entry number for this year
        latest = self.db.query(JournalEntry).filter(
            and_(
                JournalEntry.customer_id == customer_id,
                JournalEntry.entry_number.like(f"{prefix}%")
            )
        ).order_by(JournalEntry.entry_number.desc()).first()

        if latest:
            try:
                last_num = int(latest.entry_number.split("-")[-1])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}{new_num:05d}"

    # ============== CRUD Operations ==============

    def create_entry(
        self,
        customer_id: UUID,
        data: JournalEntryCreate,
        created_by: UUID = None,
        auto_number: bool = True,
    ) -> JournalEntry:
        """Create a new journal entry."""
        # Generate entry number
        entry_number = self._generate_entry_number(customer_id, data.entry_date)

        # Determine fiscal period if not provided
        fiscal_period_id = data.fiscal_period_id
        if not fiscal_period_id:
            fiscal_period_id = self._find_fiscal_period(customer_id, data.entry_date)

        # Create entry
        entry = JournalEntry(
            customer_id=customer_id,
            entry_number=entry_number,
            entry_date=data.entry_date,
            entry_type=data.entry_type,
            status=EntryStatusEnum.DRAFT,
            description=data.description,
            memo=data.memo,
            reference=data.reference,
            source_type=data.source_type,
            source_id=data.source_id,
            fiscal_period_id=fiscal_period_id,
            currency=data.currency,
            exchange_rate=data.exchange_rate,
            created_by=created_by,
        )

        # Create lines
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for i, line_data in enumerate(data.lines):
            line = JournalLine(
                entry=entry,
                line_number=i + 1,
                account_id=line_data.account_id,
                debit_amount=line_data.debit_amount,
                credit_amount=line_data.credit_amount,
                description=line_data.description,
                memo=line_data.memo,
                tax_code=line_data.tax_code,
                tax_amount=line_data.tax_amount,
                cost_center=line_data.cost_center,
                department=line_data.department,
                project_id=line_data.project_id,
                currency=data.currency,
                exchange_rate=data.exchange_rate,
            )
            line.calculate_base_amounts()
            entry.lines.append(line)

            total_debit += line_data.debit_amount
            total_credit += line_data.credit_amount

        entry.total_debit = total_debit
        entry.total_credit = total_credit
        entry.base_total_debit = total_debit * data.exchange_rate
        entry.base_total_credit = total_credit * data.exchange_rate

        # Validate
        if not self.validator.validate(entry):
            raise ValueError(self.validator.get_errors())

        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)

        logger.info(f"Created journal entry: {entry.entry_number}")
        return entry

    def get_entry_by_id(self, entry_id: UUID) -> Optional[JournalEntry]:
        """Get entry by ID with lines."""
        return self.db.query(JournalEntry).options(
            joinedload(JournalEntry.lines).joinedload(JournalLine.account)
        ).filter(JournalEntry.id == entry_id).first()

    def get_entry_by_number(
        self,
        customer_id: UUID,
        entry_number: str,
    ) -> Optional[JournalEntry]:
        """Get entry by number."""
        return self.db.query(JournalEntry).options(
            joinedload(JournalEntry.lines).joinedload(JournalLine.account)
        ).filter(
            and_(
                JournalEntry.customer_id == customer_id,
                JournalEntry.entry_number == entry_number
            )
        ).first()

    def get_entries(
        self,
        customer_id: UUID,
        filters: JournalEntryFilter = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[JournalEntry], int, Decimal, Decimal]:
        """Get entries with filtering and pagination."""
        query = self.db.query(JournalEntry).filter(
            JournalEntry.customer_id == customer_id
        )

        if filters:
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        JournalEntry.entry_number.ilike(search_term),
                        JournalEntry.description.ilike(search_term),
                        JournalEntry.reference.ilike(search_term)
                    )
                )

            if filters.entry_type:
                query = query.filter(JournalEntry.entry_type == filters.entry_type)

            if filters.status:
                query = query.filter(JournalEntry.status == filters.status)

            if filters.start_date:
                query = query.filter(JournalEntry.entry_date >= filters.start_date)

            if filters.end_date:
                query = query.filter(JournalEntry.entry_date <= filters.end_date)

            if filters.fiscal_period_id:
                query = query.filter(JournalEntry.fiscal_period_id == filters.fiscal_period_id)

            if filters.account_id:
                query = query.join(JournalEntry.lines).filter(
                    JournalLine.account_id == filters.account_id
                )

            if filters.min_amount:
                query = query.filter(JournalEntry.total_debit >= filters.min_amount)

            if filters.max_amount:
                query = query.filter(JournalEntry.total_debit <= filters.max_amount)

            if filters.unposted_only:
                query = query.filter(JournalEntry.status != EntryStatusEnum.POSTED)

        # Get totals
        total_query = query.with_entities(
            func.count(JournalEntry.id),
            func.sum(JournalEntry.total_debit),
            func.sum(JournalEntry.total_credit)
        ).first()

        total_count = total_query[0] or 0
        total_debit = Decimal(str(total_query[1] or 0))
        total_credit = Decimal(str(total_query[2] or 0))

        # Apply pagination
        entries = query.options(
            joinedload(JournalEntry.lines)
        ).order_by(
            JournalEntry.entry_date.desc(),
            JournalEntry.entry_number.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return entries, total_count, total_debit, total_credit

    def update_entry(
        self,
        entry_id: UUID,
        data: JournalEntryUpdate,
    ) -> JournalEntry:
        """Update a draft/pending entry."""
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            raise ValueError("Entry not found")

        if not entry.can_edit:
            raise ValueError(f"Cannot edit entry with status: {entry.status.value}")

        # Update header fields
        if data.entry_date is not None:
            entry.entry_date = data.entry_date
        if data.description is not None:
            entry.description = data.description
        if data.memo is not None:
            entry.memo = data.memo
        if data.reference is not None:
            entry.reference = data.reference

        # Update lines if provided
        if data.lines is not None:
            # Remove existing lines
            for line in entry.lines:
                self.db.delete(line)

            entry.lines = []

            # Add new lines
            total_debit = Decimal("0")
            total_credit = Decimal("0")

            for i, line_data in enumerate(data.lines):
                line = JournalLine(
                    entry=entry,
                    line_number=i + 1,
                    account_id=line_data.account_id,
                    debit_amount=line_data.debit_amount,
                    credit_amount=line_data.credit_amount,
                    description=line_data.description,
                    memo=line_data.memo,
                    tax_code=line_data.tax_code,
                    tax_amount=line_data.tax_amount,
                    cost_center=line_data.cost_center,
                    project_id=line_data.project_id,
                    currency=entry.currency,
                    exchange_rate=entry.exchange_rate,
                )
                line.calculate_base_amounts()
                entry.lines.append(line)

                total_debit += line_data.debit_amount
                total_credit += line_data.credit_amount

            entry.total_debit = total_debit
            entry.total_credit = total_credit

        # Validate
        if not self.validator.validate(entry):
            raise ValueError(self.validator.get_errors())

        entry.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(entry)

        logger.info(f"Updated journal entry: {entry.entry_number}")
        return entry

    def delete_entry(self, entry_id: UUID) -> bool:
        """Delete a draft entry."""
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            raise ValueError("Entry not found")

        if entry.status != EntryStatusEnum.DRAFT:
            raise ValueError("Only draft entries can be deleted")

        self.db.delete(entry)
        self.db.commit()

        logger.info(f"Deleted journal entry: {entry.entry_number}")
        return True

    # ============== Workflow Operations ==============

    def submit_for_approval(
        self,
        entry_id: UUID,
        submitted_by: UUID,
        notes: str = None,
    ) -> JournalEntry:
        """Submit entry for approval."""
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            raise ValueError("Entry not found")

        if entry.status != EntryStatusEnum.DRAFT:
            raise ValueError("Only draft entries can be submitted")

        # Validate before submitting
        if not self.validator.validate(entry):
            raise ValueError(self.validator.get_errors())

        entry.status = EntryStatusEnum.PENDING
        entry.submitted_by = submitted_by
        entry.submitted_at = utc_now()

        self.db.commit()
        logger.info(f"Submitted entry for approval: {entry.entry_number}")
        return entry

    def approve_entry(
        self,
        entry_id: UUID,
        approved_by: UUID,
        notes: str = None,
    ) -> JournalEntry:
        """Approve an entry."""
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            raise ValueError("Entry not found")

        if entry.status != EntryStatusEnum.PENDING:
            raise ValueError("Only pending entries can be approved")

        entry.status = EntryStatusEnum.APPROVED
        entry.approved_by = approved_by
        entry.approved_at = utc_now()
        entry.approval_notes = notes

        self.db.commit()
        logger.info(f"Approved entry: {entry.entry_number}")
        return entry

    def reject_entry(
        self,
        entry_id: UUID,
        rejected_by: UUID,
        notes: str = None,
    ) -> JournalEntry:
        """Reject an entry (back to draft)."""
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            raise ValueError("Entry not found")

        if entry.status != EntryStatusEnum.PENDING:
            raise ValueError("Only pending entries can be rejected")

        entry.status = EntryStatusEnum.DRAFT
        entry.approval_notes = notes

        self.db.commit()
        logger.info(f"Rejected entry: {entry.entry_number}")
        return entry

    def post_entry(
        self,
        entry_id: UUID,
        posted_by: UUID,
    ) -> JournalEntry:
        """Post an approved entry to the ledger."""
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            raise ValueError("Entry not found")

        # Validate for posting
        if not self.validator.validate_for_posting(entry):
            raise ValueError(self.validator.get_errors())

        # Update account balances
        for line in entry.lines:
            self.coa_service.update_balance(
                line.account_id,
                line.debit_amount,
                line.credit_amount
            )

        entry.status = EntryStatusEnum.POSTED
        entry.posted_by = posted_by
        entry.posted_at = utc_now()

        self.db.commit()
        logger.info(f"Posted entry: {entry.entry_number}")
        return entry

    def reverse_entry(
        self,
        entry_id: UUID,
        reversal_data: EntryReversalRequest,
        reversed_by: UUID,
    ) -> JournalEntry:
        """Create a reversing entry."""
        original = self.get_entry_by_id(entry_id)
        if not original:
            raise ValueError("Entry not found")

        # Validate for reversal
        if not self.validator.validate_for_reversal(original):
            raise ValueError(self.validator.get_errors())

        # Create reversal entry
        reversal_number = self._generate_entry_number(
            original.customer_id,
            reversal_data.reversal_date
        )

        reversal = JournalEntry(
            customer_id=original.customer_id,
            entry_number=reversal_number,
            entry_date=reversal_data.reversal_date,
            entry_type=EntryTypeEnum.REVERSAL,
            status=EntryStatusEnum.APPROVED,  # Auto-approved
            description=reversal_data.description or f"Reversal of {original.entry_number}",
            reference=original.entry_number,
            source_type="reversal",
            source_id=original.id,
            fiscal_period_id=self._find_fiscal_period(
                original.customer_id,
                reversal_data.reversal_date
            ),
            currency=original.currency,
            exchange_rate=original.exchange_rate,
            is_reversing=True,
            reversed_entry_id=original.id,
            created_by=reversed_by,
            approved_by=reversed_by,
            approved_at=utc_now(),
        )

        # Create reversed lines (swap debit/credit)
        for i, orig_line in enumerate(original.lines):
            line = JournalLine(
                entry=reversal,
                line_number=i + 1,
                account_id=orig_line.account_id,
                debit_amount=orig_line.credit_amount,  # Swapped
                credit_amount=orig_line.debit_amount,  # Swapped
                description=f"Reversal: {orig_line.description or ''}",
                currency=orig_line.currency,
                exchange_rate=orig_line.exchange_rate,
            )
            line.calculate_base_amounts()
            reversal.lines.append(line)

        reversal.total_debit = original.total_credit
        reversal.total_credit = original.total_debit
        reversal.base_total_debit = original.base_total_credit
        reversal.base_total_credit = original.base_total_debit

        self.db.add(reversal)

        # Update original entry status
        original.status = EntryStatusEnum.REVERSED

        self.db.commit()

        # Post the reversal
        self.post_entry(reversal.id, reversed_by)

        logger.info(f"Created reversal entry: {reversal.entry_number}")
        return reversal

    def void_entry(
        self,
        entry_id: UUID,
        voided_by: UUID,
        reason: str,
    ) -> JournalEntry:
        """Void an unposted entry."""
        entry = self.get_entry_by_id(entry_id)
        if not entry:
            raise ValueError("Entry not found")

        if entry.status == EntryStatusEnum.POSTED:
            raise ValueError("Posted entries cannot be voided. Use reversal instead.")

        entry.status = EntryStatusEnum.VOIDED
        entry.voided_by = voided_by
        entry.voided_at = utc_now()
        entry.void_reason = reason

        self.db.commit()
        logger.info(f"Voided entry: {entry.entry_number}")
        return entry

    # ============== Batch Operations ==============

    def batch_post(
        self,
        entry_ids: List[UUID],
        posted_by: UUID,
    ) -> Dict[str, Any]:
        """Post multiple entries."""
        results = {
            "posted": [],
            "failed": [],
        }

        for entry_id in entry_ids:
            try:
                entry = self.post_entry(entry_id, posted_by)
                results["posted"].append(str(entry.id))
            except Exception as e:
                results["failed"].append({
                    "id": str(entry_id),
                    "error": str(e),
                })

        return results

    # ============== Helper Methods ==============

    def _find_fiscal_period(
        self,
        customer_id: UUID,
        entry_date: date,
    ) -> Optional[UUID]:
        """Find fiscal period for a date."""
        from app.accounting.periods.models import FiscalPeriod

        period = self.db.query(FiscalPeriod).filter(
            and_(
                FiscalPeriod.start_date <= entry_date,
                FiscalPeriod.end_date >= entry_date,
                FiscalPeriod.is_closed == False
            )
        ).first()

        return period.id if period else None


def get_journal_entry_service(db: Session) -> JournalEntryService:
    """Factory function."""
    return JournalEntryService(db)
