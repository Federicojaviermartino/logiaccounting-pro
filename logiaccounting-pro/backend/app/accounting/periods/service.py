"""
Period Management Service
Create and manage fiscal years and periods
"""

from datetime import datetime, date, timedelta
from typing import List, Optional
from uuid import UUID
from calendar import monthrange
import logging

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.accounting.periods.models import FiscalYear, FiscalPeriod

logger = logging.getLogger(__name__)


class PeriodService:
    """Service for fiscal period management."""

    def __init__(self, db: Session):
        self.db = db

    def create_fiscal_year(
        self,
        customer_id: UUID,
        start_date: date,
        end_date: date = None,
        name: str = None,
        create_periods: bool = True,
        created_by: UUID = None,
    ) -> FiscalYear:
        """Create a new fiscal year with periods."""
        if not end_date:
            # Default to 12 months
            end_date = date(start_date.year + 1, start_date.month, start_date.day) - timedelta(days=1)

        if not name:
            name = f"FY {start_date.year}"

        # Check for overlap
        existing = self.db.query(FiscalYear).filter(
            FiscalYear.customer_id == customer_id,
            FiscalYear.start_date <= end_date,
            FiscalYear.end_date >= start_date
        ).first()

        if existing:
            raise ValueError(f"Fiscal year overlaps with {existing.name}")

        fiscal_year = FiscalYear(
            customer_id=customer_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by,
        )

        self.db.add(fiscal_year)
        self.db.flush()  # Get the ID

        if create_periods:
            self._create_monthly_periods(fiscal_year)

        self.db.commit()
        self.db.refresh(fiscal_year)

        logger.info(f"Created fiscal year: {fiscal_year.name}")
        return fiscal_year

    def _create_monthly_periods(self, fiscal_year: FiscalYear):
        """Create monthly periods for a fiscal year."""
        current = fiscal_year.start_date
        period_num = 1

        while current <= fiscal_year.end_date:
            # Get month end
            _, days_in_month = monthrange(current.year, current.month)
            month_end = date(current.year, current.month, days_in_month)

            # Don't exceed fiscal year end
            period_end = min(month_end, fiscal_year.end_date)

            period = FiscalPeriod(
                fiscal_year_id=fiscal_year.id,
                name=current.strftime("%B %Y"),
                period_number=period_num,
                start_date=current,
                end_date=period_end,
            )

            self.db.add(period)

            # Move to next month
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

            period_num += 1

    def get_fiscal_year(self, fiscal_year_id: UUID) -> Optional[FiscalYear]:
        """Get fiscal year by ID."""
        return self.db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()

    def get_fiscal_years(
        self,
        customer_id: UUID,
        include_closed: bool = True,
    ) -> List[FiscalYear]:
        """Get all fiscal years for a customer."""
        query = self.db.query(FiscalYear).filter(
            FiscalYear.customer_id == customer_id
        )

        if not include_closed:
            query = query.filter(FiscalYear.is_closed == False)

        return query.order_by(FiscalYear.start_date.desc()).all()

    def get_current_period(self, customer_id: UUID, as_of_date: date = None) -> Optional[FiscalPeriod]:
        """Get the current open fiscal period."""
        as_of_date = as_of_date or date.today()

        return self.db.query(FiscalPeriod).join(FiscalYear).filter(
            FiscalYear.customer_id == customer_id,
            FiscalPeriod.start_date <= as_of_date,
            FiscalPeriod.end_date >= as_of_date,
            FiscalPeriod.is_closed == False
        ).first()

    def get_period_for_date(self, customer_id: UUID, entry_date: date) -> Optional[FiscalPeriod]:
        """Find the fiscal period for a given date."""
        return self.db.query(FiscalPeriod).join(FiscalYear).filter(
            FiscalYear.customer_id == customer_id,
            FiscalPeriod.start_date <= entry_date,
            FiscalPeriod.end_date >= entry_date
        ).first()

    def close_period(
        self,
        period_id: UUID,
        closed_by: UUID,
        notes: str = None,
    ) -> FiscalPeriod:
        """Close a fiscal period."""
        period = self.db.query(FiscalPeriod).get(period_id)
        if not period:
            raise ValueError("Period not found")

        if period.is_closed:
            raise ValueError("Period is already closed")

        # Check previous periods are closed
        previous_periods = self.db.query(FiscalPeriod).filter(
            FiscalPeriod.fiscal_year_id == period.fiscal_year_id,
            FiscalPeriod.period_number < period.period_number,
            FiscalPeriod.is_closed == False
        ).all()

        if previous_periods:
            raise ValueError("Previous periods must be closed first")

        period.is_closed = True
        period.closed_at = datetime.utcnow()
        period.closed_by = closed_by
        period.close_notes = notes

        self.db.commit()

        logger.info(f"Closed period: {period.name}")
        return period

    def reopen_period(
        self,
        period_id: UUID,
        reopened_by: UUID,
    ) -> FiscalPeriod:
        """Reopen a closed period (requires special permission)."""
        period = self.db.query(FiscalPeriod).get(period_id)
        if not period:
            raise ValueError("Period not found")

        if not period.is_closed:
            raise ValueError("Period is not closed")

        # Check if fiscal year is closed
        if period.fiscal_year.is_closed:
            raise ValueError("Cannot reopen period in closed fiscal year")

        period.is_closed = False
        period.closed_at = None
        period.closed_by = None

        self.db.commit()

        logger.info(f"Reopened period: {period.name}")
        return period


def get_period_service(db: Session) -> PeriodService:
    return PeriodService(db)
