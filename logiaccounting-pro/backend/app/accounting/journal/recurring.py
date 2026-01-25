"""
Recurring Journal Entries
Scheduled automatic journal entry generation
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum
import logging
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Session, relationship

from app.database import Base
from app.accounting.journal.service import JournalEntryService
from app.accounting.journal.schemas import JournalEntryCreate, JournalLineCreate

logger = logging.getLogger(__name__)


class RecurrenceFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"


class RecurringEntry(Base):
    """Recurring journal entry template."""

    __tablename__ = "recurring_entries"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    name = Column(String(200), nullable=False)
    description = Column(Text)

    frequency = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    day_of_month = Column(Integer)
    day_of_week = Column(Integer)

    next_run_date = Column(Date)
    last_run_date = Column(Date)
    run_count = Column(Integer, default=0)
    max_occurrences = Column(Integer)

    entry_type = Column(String(20), default="standard")
    memo = Column(Text)
    template_lines = Column(JSONB, nullable=False)

    is_active = Column(Boolean, default=True)
    is_auto_post = Column(Boolean, default=False)

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "frequency": self.frequency,
            "next_run_date": self.next_run_date.isoformat() if self.next_run_date else None,
            "run_count": self.run_count,
            "is_active": self.is_active,
        }


class RecurringEntryService:
    """Service for managing recurring journal entries."""

    def __init__(self, db: Session):
        self.db = db
        self.journal_service = JournalEntryService(db)

    def create_recurring_entry(
        self,
        customer_id: UUID,
        name: str,
        frequency: RecurrenceFrequency,
        start_date: date,
        template_lines: List[Dict[str, Any]],
        description: str = None,
        end_date: date = None,
        day_of_month: int = None,
        max_occurrences: int = None,
        is_auto_post: bool = False,
        memo: str = None,
        created_by: UUID = None,
    ) -> RecurringEntry:
        """Create a new recurring entry template."""
        total_debit = sum(Decimal(str(l.get("debit_amount", 0))) for l in template_lines)
        total_credit = sum(Decimal(str(l.get("credit_amount", 0))) for l in template_lines)

        if total_debit != total_credit:
            raise ValueError("Template lines must balance")

        recurring = RecurringEntry(
            customer_id=customer_id,
            name=name,
            description=description,
            frequency=frequency.value,
            start_date=start_date,
            end_date=end_date,
            day_of_month=day_of_month,
            next_run_date=start_date,
            max_occurrences=max_occurrences,
            is_auto_post=is_auto_post,
            memo=memo,
            template_lines=template_lines,
            created_by=created_by,
        )

        self.db.add(recurring)
        self.db.commit()
        self.db.refresh(recurring)

        return recurring

    def get_due_entries(self, as_of_date: date = None) -> List[RecurringEntry]:
        """Get all recurring entries due for execution."""
        as_of_date = as_of_date or date.today()
        return self.db.query(RecurringEntry).filter(
            RecurringEntry.is_active == True,
            RecurringEntry.next_run_date <= as_of_date,
        ).all()

    def execute_recurring_entry(
        self,
        recurring_id: UUID,
        execution_date: date = None,
        created_by: UUID = None,
    ) -> Optional[Dict[str, Any]]:
        """Execute a recurring entry and create journal entry."""
        recurring = self.db.query(RecurringEntry).get(recurring_id)
        if not recurring or not recurring.is_active:
            return None

        execution_date = execution_date or date.today()

        if recurring.end_date and execution_date > recurring.end_date:
            recurring.is_active = False
            self.db.commit()
            return None

        if recurring.max_occurrences and recurring.run_count >= recurring.max_occurrences:
            recurring.is_active = False
            self.db.commit()
            return None

        lines = [
            JournalLineCreate(
                account_id=UUID(line["account_id"]),
                debit_amount=Decimal(str(line.get("debit_amount", 0))),
                credit_amount=Decimal(str(line.get("credit_amount", 0))),
                description=line.get("description", ""),
            )
            for line in recurring.template_lines
        ]

        entry_data = JournalEntryCreate(
            entry_date=execution_date,
            entry_type=recurring.entry_type or "standard",
            description=f"{recurring.name} - {execution_date.strftime('%B %Y')}",
            memo=recurring.memo,
            lines=lines,
        )

        entry = self.journal_service.create_entry(
            customer_id=recurring.customer_id,
            data=entry_data,
            created_by=created_by,
        )

        entry.recurring_entry_id = recurring.id

        if recurring.is_auto_post and created_by:
            self.journal_service.submit_for_approval(entry.id, created_by)
            self.journal_service.approve_entry(entry.id, created_by)
            self.journal_service.post_entry(entry.id, created_by)

        recurring.last_run_date = execution_date
        recurring.run_count += 1
        recurring.next_run_date = self._calculate_next_run_date(recurring, execution_date)

        self.db.commit()

        return {
            "recurring_entry_id": str(recurring.id),
            "journal_entry_id": str(entry.id),
            "journal_entry_number": entry.entry_number,
        }

    def _calculate_next_run_date(self, recurring: RecurringEntry, from_date: date) -> Optional[date]:
        """Calculate the next run date based on frequency."""
        freq = RecurrenceFrequency(recurring.frequency)

        if freq == RecurrenceFrequency.DAILY:
            next_date = from_date + timedelta(days=1)
        elif freq == RecurrenceFrequency.WEEKLY:
            next_date = from_date + timedelta(weeks=1)
        elif freq == RecurrenceFrequency.BIWEEKLY:
            next_date = from_date + timedelta(weeks=2)
        elif freq == RecurrenceFrequency.MONTHLY:
            month = from_date.month + 1
            year = from_date.year
            if month > 12:
                month = 1
                year += 1
            day = recurring.day_of_month or from_date.day
            while day > 28:
                try:
                    next_date = date(year, month, day)
                    break
                except ValueError:
                    day -= 1
            else:
                next_date = date(year, month, day)
        elif freq == RecurrenceFrequency.QUARTERLY:
            month = from_date.month + 3
            year = from_date.year
            while month > 12:
                month -= 12
                year += 1
            next_date = date(year, month, min(from_date.day, 28))
        elif freq == RecurrenceFrequency.ANNUAL:
            next_date = date(from_date.year + 1, from_date.month, from_date.day)
        else:
            return None

        if recurring.end_date and next_date > recurring.end_date:
            return None

        return next_date

    def process_all_due_entries(self, created_by: UUID = None) -> List[Dict[str, Any]]:
        """Process all recurring entries that are due."""
        results = []
        for recurring in self.get_due_entries():
            try:
                result = self.execute_recurring_entry(recurring.id, created_by=created_by)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error processing recurring entry {recurring.id}: {e}")
        return results


def get_recurring_entry_service(db: Session) -> RecurringEntryService:
    return RecurringEntryService(db)
