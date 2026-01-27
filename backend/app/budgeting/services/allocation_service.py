"""Budget allocation and distribution service."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List
from uuid import UUID
from calendar import monthrange

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.budgeting.models.budget import BudgetVersion
from app.budgeting.models.budget_line import BudgetLine, BudgetPeriod, DistributionMethod
from app.budgeting.models.distribution import DistributionPattern
from app.budgeting.schemas.budget_line import BudgetLineCreate, BudgetLineUpdate
from app.core.exceptions import NotFoundError, ValidationError, BusinessRuleError


class AllocationService:
    """Service for budget allocation operations."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    async def create_budget_line(self, version_id: UUID, data: BudgetLineCreate) -> BudgetLine:
        """Create budget line for an account."""
        version = await self._get_version(version_id)

        if version.is_locked:
            raise BusinessRuleError("Cannot modify locked version")

        account = await self._get_account(data.account_id)

        existing = self.db.execute(
            select(BudgetLine).where(
                BudgetLine.version_id == version_id,
                BudgetLine.account_id == data.account_id,
                BudgetLine.department_id == data.department_id,
                BudgetLine.cost_center_id == data.cost_center_id
            )
        ).scalar_one_or_none()

        if existing:
            raise ValidationError("Budget line already exists for this account")

        line = BudgetLine(
            version_id=version_id,
            account_id=data.account_id,
            account_code=account.account_code,
            account_name=account.account_name,
            account_type=account.account_type,
            department_id=data.department_id,
            cost_center_id=data.cost_center_id,
            annual_amount=data.annual_amount,
            distribution_method=data.distribution_method,
            notes=data.notes,
        )

        self.db.add(line)
        self.db.flush()

        budget = version.budget
        await self._create_periods(line, budget.start_date, budget.end_date)
        await self._distribute_amount(line)
        await self._update_version_totals(version)

        self.db.commit()
        self.db.refresh(line)
        return line

    async def update_budget_line(self, line_id: UUID, data: BudgetLineUpdate) -> BudgetLine:
        """Update budget line."""
        line = await self._get_line(line_id)
        version = await self._get_version(line.version_id)

        if version.is_locked:
            raise BusinessRuleError("Cannot modify locked version")

        update_data = data.model_dump(exclude_unset=True)
        needs_redistribution = False

        for key, value in update_data.items():
            if hasattr(line, key):
                if key in ('annual_amount', 'distribution_method'):
                    needs_redistribution = True
                setattr(line, key, value)

        if needs_redistribution:
            await self._distribute_amount(line)

        await self._update_version_totals(version)
        self.db.commit()
        self.db.refresh(line)
        return line

    async def delete_budget_line(self, line_id: UUID) -> None:
        """Delete budget line."""
        line = await self._get_line(line_id)
        version = await self._get_version(line.version_id)

        if version.is_locked:
            raise BusinessRuleError("Cannot modify locked version")

        self.db.delete(line)
        await self._update_version_totals(version)
        self.db.commit()

    async def get_lines(self, version_id: UUID, account_type: Optional[str] = None, department_id: Optional[UUID] = None) -> List[BudgetLine]:
        """Get budget lines for a version."""
        query = select(BudgetLine).where(BudgetLine.version_id == version_id)

        if account_type:
            query = query.where(BudgetLine.account_type == account_type)
        if department_id:
            query = query.where(BudgetLine.department_id == department_id)

        query = query.order_by(BudgetLine.account_code)
        result = self.db.execute(query)
        return result.scalars().all()

    async def get_line_periods(self, line_id: UUID) -> List[BudgetPeriod]:
        """Get periods for a budget line."""
        query = select(BudgetPeriod).where(
            BudgetPeriod.line_id == line_id
        ).order_by(BudgetPeriod.period_year, BudgetPeriod.period_month)

        result = self.db.execute(query)
        return result.scalars().all()

    async def _create_periods(self, line: BudgetLine, start_date: date, end_date: date) -> None:
        """Create budget periods for a line."""
        current = date(start_date.year, start_date.month, 1)

        while current <= end_date:
            _, last_day = monthrange(current.year, current.month)
            period_end = date(current.year, current.month, last_day)

            period = BudgetPeriod(
                line_id=line.id,
                period_year=current.year,
                period_month=current.month,
                period_start=current,
                period_end=min(period_end, end_date),
                budgeted_amount=Decimal(0),
            )
            self.db.add(period)

            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

    async def update_period(self, period_id: UUID, amount: Decimal, notes: Optional[str] = None) -> BudgetPeriod:
        """Update single period amount."""
        period = await self._get_period(period_id)
        line = await self._get_line(period.line_id)
        version = await self._get_version(line.version_id)

        if version.is_locked or period.is_locked:
            raise BusinessRuleError("Cannot modify locked period/version")

        period.budgeted_amount = amount
        if notes:
            period.notes = notes

        line.distribution_method = DistributionMethod.MANUAL
        line.annual_amount = sum(p.budgeted_amount for p in line.periods)

        await self._update_version_totals(version)
        self.db.commit()
        self.db.refresh(period)
        return period

    async def redistribute_line(self, line_id: UUID, method: str, pattern_id: Optional[UUID] = None) -> BudgetLine:
        """Redistribute budget line across periods."""
        line = await self._get_line(line_id)
        version = await self._get_version(line.version_id)

        if version.is_locked:
            raise BusinessRuleError("Cannot modify locked version")

        line.distribution_method = DistributionMethod(method)
        line.distribution_pattern_id = pattern_id

        await self._distribute_amount(line)

        self.db.commit()
        self.db.refresh(line)
        return line

    async def _distribute_amount(self, line: BudgetLine) -> None:
        """Distribute annual amount across periods."""
        if line.distribution_method == DistributionMethod.EQUAL:
            await self._distribute_equal(line)
        elif line.distribution_method == DistributionMethod.SEASONAL:
            await self._distribute_seasonal(line)

    async def _distribute_equal(self, line: BudgetLine) -> None:
        """Distribute equally across all periods."""
        periods = list(line.periods)
        if not periods:
            return

        num_periods = len(periods)
        base_amount = (line.annual_amount / num_periods).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_allocated = base_amount * (num_periods - 1)
        last_amount = line.annual_amount - total_allocated

        for i, period in enumerate(periods):
            if i == num_periods - 1:
                period.budgeted_amount = last_amount
            else:
                period.budgeted_amount = base_amount

    async def _distribute_seasonal(self, line: BudgetLine) -> None:
        """Distribute using seasonal pattern."""
        if not line.distribution_pattern_id:
            await self._distribute_equal(line)
            return

        pattern = self.db.get(DistributionPattern, line.distribution_pattern_id)
        if not pattern:
            await self._distribute_equal(line)
            return

        total_allocated = Decimal(0)
        periods_list = list(line.periods)

        for i, period in enumerate(periods_list):
            month_percent = pattern.get_month_percent(period.period_month)

            if i == len(periods_list) - 1:
                period.budgeted_amount = line.annual_amount - total_allocated
            else:
                amount = (line.annual_amount * month_percent / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                period.budgeted_amount = amount
                total_allocated += amount

    async def _update_version_totals(self, version: BudgetVersion) -> None:
        """Update version totals from lines."""
        version.recalculate_totals()

    async def _get_version(self, version_id: UUID) -> BudgetVersion:
        query = select(BudgetVersion).where(BudgetVersion.id == version_id)
        result = self.db.execute(query)
        version = result.scalar_one_or_none()
        if not version:
            raise NotFoundError(f"Version not found: {version_id}")
        return version

    async def _get_line(self, line_id: UUID) -> BudgetLine:
        query = select(BudgetLine).where(BudgetLine.id == line_id)
        result = self.db.execute(query)
        line = result.scalar_one_or_none()
        if not line:
            raise NotFoundError(f"Budget line not found: {line_id}")
        return line

    async def _get_period(self, period_id: UUID) -> BudgetPeriod:
        period = self.db.get(BudgetPeriod, period_id)
        if not period:
            raise NotFoundError(f"Budget period not found: {period_id}")
        return period

    async def _get_account(self, account_id: UUID):
        """Get account from chart of accounts."""
        from app.accounting.chart_of_accounts.models import ChartOfAccounts
        account = self.db.get(ChartOfAccounts, account_id)
        if not account:
            raise NotFoundError(f"Account not found: {account_id}")
        return account
