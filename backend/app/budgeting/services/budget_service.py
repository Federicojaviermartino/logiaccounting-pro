"""Budget management service."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.budgeting.models.budget import Budget, BudgetVersion, BudgetStatus, VersionStatus
from app.budgeting.models.budget_line import BudgetLine, BudgetPeriod
from app.budgeting.schemas.budget import BudgetCreate, BudgetUpdate, VersionCreate
from app.core.exceptions import NotFoundError, ValidationError, BusinessRuleError


class BudgetService:
    """Service for budget operations."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    async def create_budget(self, data: BudgetCreate, created_by: Optional[UUID] = None) -> Budget:
        """Create a new budget."""
        budget_code = await self._generate_budget_code(data.fiscal_year)

        budget = Budget(
            customer_id=self.customer_id,
            budget_code=budget_code,
            name=data.name,
            description=data.description,
            budget_type=data.budget_type,
            fiscal_year=data.fiscal_year,
            start_date=data.start_date,
            end_date=data.end_date,
            department_id=data.department_id,
            project_id=data.project_id,
            currency=data.currency,
            requires_approval=data.requires_approval,
            allow_overspend=data.allow_overspend,
            status=BudgetStatus.DRAFT,
            created_by=created_by,
        )

        self.db.add(budget)

        try:
            self.db.commit()
            self.db.refresh(budget)
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Budget creation failed: {str(e)}")

        # Create initial version
        await self.create_version(
            budget.id,
            VersionCreate(version_name="Original", version_type="original"),
            created_by
        )

        return budget

    async def update_budget(self, budget_id: UUID, data: BudgetUpdate) -> Budget:
        """Update budget."""
        budget = await self.get_budget_by_id(budget_id)

        if budget.status in (BudgetStatus.CLOSED, BudgetStatus.ARCHIVED):
            raise BusinessRuleError("Cannot modify closed or archived budget")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(budget, key):
                setattr(budget, key, value)

        self.db.commit()
        self.db.refresh(budget)
        return budget

    async def get_budget_by_id(self, budget_id: UUID, include_versions: bool = False) -> Budget:
        """Get budget by ID."""
        query = select(Budget).where(
            Budget.id == budget_id,
            Budget.customer_id == self.customer_id
        )

        if include_versions:
            query = query.options(selectinload(Budget.versions))

        result = self.db.execute(query)
        budget = result.scalar_one_or_none()

        if not budget:
            raise NotFoundError(f"Budget not found: {budget_id}")
        return budget

    async def get_budgets(
        self,
        fiscal_year: Optional[int] = None,
        status: Optional[BudgetStatus] = None,
        department_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Budget], int]:
        """Get budgets with filtering."""
        query = select(Budget).where(Budget.customer_id == self.customer_id)

        if fiscal_year:
            query = query.where(Budget.fiscal_year == fiscal_year)
        if status:
            query = query.where(Budget.status == status)
        if department_id:
            query = query.where(Budget.department_id == department_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        query = query.order_by(Budget.fiscal_year.desc(), Budget.budget_code)
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        budgets = result.scalars().all()

        return budgets, total

    async def delete_budget(self, budget_id: UUID) -> None:
        """Delete draft budget."""
        budget = await self.get_budget_by_id(budget_id)

        if budget.status != BudgetStatus.DRAFT:
            raise BusinessRuleError("Only draft budgets can be deleted")

        self.db.delete(budget)
        self.db.commit()

    async def create_version(self, budget_id: UUID, data: VersionCreate, created_by: Optional[UUID] = None) -> BudgetVersion:
        """Create budget version."""
        budget = await self.get_budget_by_id(budget_id)
        version_number = len(budget.versions) + 1 if budget.versions else 1

        version = BudgetVersion(
            budget_id=budget_id,
            version_number=version_number,
            version_name=data.version_name,
            description=data.description,
            version_type=data.version_type,
            parent_version_id=data.parent_version_id,
            status=VersionStatus.DRAFT,
            created_by=created_by,
        )

        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        if data.parent_version_id:
            await self._copy_version_lines(data.parent_version_id, version.id)

        return version

    async def activate_version(self, version_id: UUID, user_id: UUID) -> BudgetVersion:
        """Set version as active."""
        version = await self._get_version(version_id)

        if version.status != VersionStatus.APPROVED:
            raise BusinessRuleError("Only approved versions can be activated")

        # Deactivate other versions
        self.db.execute(
            BudgetVersion.__table__.update()
            .where(BudgetVersion.budget_id == version.budget_id)
            .values(is_active=False, status=VersionStatus.SUPERSEDED)
        )

        version.is_active = True
        version.status = VersionStatus.ACTIVE

        budget = await self.get_budget_by_id(version.budget_id)
        budget.active_version_id = version.id
        budget.total_revenue = version.total_revenue
        budget.total_expenses = version.total_expenses
        budget.total_net_income = version.total_net_income
        budget.status = BudgetStatus.ACTIVE

        self.db.commit()
        self.db.refresh(version)
        return version

    async def submit_version(self, version_id: UUID, user_id: UUID) -> BudgetVersion:
        """Submit version for approval."""
        version = await self._get_version(version_id)

        if version.status != VersionStatus.DRAFT:
            raise BusinessRuleError("Only draft versions can be submitted")

        version.status = VersionStatus.SUBMITTED
        version.submitted_at = datetime.utcnow()
        version.submitted_by = user_id

        self.db.commit()
        self.db.refresh(version)
        return version

    async def approve_version(self, version_id: UUID, user_id: UUID) -> BudgetVersion:
        """Approve submitted version."""
        version = await self._get_version(version_id)

        if version.status != VersionStatus.SUBMITTED:
            raise BusinessRuleError("Only submitted versions can be approved")

        version.status = VersionStatus.APPROVED
        version.approved_at = datetime.utcnow()
        version.approved_by = user_id

        self.db.commit()
        self.db.refresh(version)
        return version

    async def reject_version(self, version_id: UUID, user_id: UUID, reason: str) -> BudgetVersion:
        """Reject submitted version."""
        version = await self._get_version(version_id)

        if version.status != VersionStatus.SUBMITTED:
            raise BusinessRuleError("Only submitted versions can be rejected")

        version.status = VersionStatus.REJECTED
        version.rejection_reason = reason

        self.db.commit()
        self.db.refresh(version)
        return version

    async def _generate_budget_code(self, fiscal_year: int) -> str:
        """Generate unique budget code."""
        count_query = select(func.count(Budget.id)).where(
            Budget.customer_id == self.customer_id,
            Budget.fiscal_year == fiscal_year
        )
        count = self.db.execute(count_query).scalar() or 0
        return f"BUD-{fiscal_year}-{(count + 1):03d}"

    async def _get_version(self, version_id: UUID) -> BudgetVersion:
        """Get version by ID."""
        query = select(BudgetVersion).where(BudgetVersion.id == version_id)
        result = self.db.execute(query)
        version = result.scalar_one_or_none()

        if not version:
            raise NotFoundError(f"Budget version not found: {version_id}")
        return version

    async def _copy_version_lines(self, source_version_id: UUID, target_version_id: UUID) -> None:
        """Copy budget lines from one version to another."""
        query = select(BudgetLine).where(BudgetLine.version_id == source_version_id)
        result = self.db.execute(query)
        source_lines = result.scalars().all()

        for source_line in source_lines:
            new_line = BudgetLine(
                version_id=target_version_id,
                account_id=source_line.account_id,
                account_code=source_line.account_code,
                account_name=source_line.account_name,
                account_type=source_line.account_type,
                department_id=source_line.department_id,
                cost_center_id=source_line.cost_center_id,
                annual_amount=source_line.annual_amount,
                distribution_method=source_line.distribution_method,
            )
            self.db.add(new_line)
            self.db.flush()

            for source_period in source_line.periods:
                new_period = BudgetPeriod(
                    line_id=new_line.id,
                    period_year=source_period.period_year,
                    period_month=source_period.period_month,
                    period_start=source_period.period_start,
                    period_end=source_period.period_end,
                    budgeted_amount=source_period.budgeted_amount,
                )
                self.db.add(new_period)

        self.db.commit()
