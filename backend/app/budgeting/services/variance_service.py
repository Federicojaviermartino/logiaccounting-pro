"""Variance analysis service."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, selectinload

from app.budgeting.models.budget import Budget, BudgetVersion
from app.budgeting.models.budget_line import BudgetLine, BudgetPeriod, VarianceType
from app.budgeting.models.variance import VarianceThreshold, VarianceAlert, AlertLevel, AlertStatus
from app.budgeting.schemas.variance import (
    VarianceThresholdCreate, VarianceThresholdUpdate,
    BudgetVsActualReport, BudgetVsActualLine, AlertSummary
)
from app.core.exceptions import NotFoundError, BusinessRuleError


class VarianceService:
    """Service for variance analysis operations."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    # ==========================================
    # VARIANCE ANALYSIS
    # ==========================================

    async def get_budget_vs_actual(
        self,
        budget_id: UUID,
        period_type: str = "ytd",
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> BudgetVsActualReport:
        """Get budget vs actual comparison."""
        budget = await self._get_budget(budget_id)

        if not budget.active_version_id:
            raise BusinessRuleError("Budget has no active version")

        # Get lines for active version with eager loading of periods
        query = select(BudgetLine).where(
            BudgetLine.version_id == budget.active_version_id
        ).options(selectinload(BudgetLine.periods)).order_by(BudgetLine.account_code)

        result = self.db.execute(query)
        lines = result.scalars().all()

        revenue_lines = []
        expense_lines = []

        total_revenue_budget = Decimal(0)
        total_revenue_actual = Decimal(0)
        total_expense_budget = Decimal(0)
        total_expense_actual = Decimal(0)

        current_year = year or datetime.now().year
        current_month = month or datetime.now().month

        for line in lines:
            budgeted, actual = await self._get_line_totals(
                line, period_type, current_year, current_month
            )

            variance = actual - budgeted
            variance_percent = (variance / budgeted * 100) if budgeted != 0 else Decimal(0)

            # Determine variance type
            if line.account_type in ('revenue', 'income'):
                variance_type = "favorable" if variance >= 0 else "unfavorable"
                total_revenue_budget += budgeted
                total_revenue_actual += actual
            else:
                variance_type = "favorable" if variance <= 0 else "unfavorable"
                total_expense_budget += budgeted
                total_expense_actual += actual

            if abs(variance) < Decimal("0.01"):
                variance_type = "on_target"

            line_data = BudgetVsActualLine(
                account_id=line.account_id,
                account_code=line.account_code,
                account_name=line.account_name,
                account_type=line.account_type,
                budgeted=budgeted,
                actual=actual,
                variance=variance,
                variance_percent=variance_percent,
                variance_type=variance_type,
            )

            if line.account_type in ('revenue', 'income'):
                revenue_lines.append(line_data)
            else:
                expense_lines.append(line_data)

        return BudgetVsActualReport(
            budget_id=budget.id,
            budget_name=budget.name,
            period_type=period_type,
            period_year=current_year,
            period_month=current_month if period_type == "monthly" else None,
            total_revenue_budget=total_revenue_budget,
            total_revenue_actual=total_revenue_actual,
            total_revenue_variance=total_revenue_actual - total_revenue_budget,
            total_expense_budget=total_expense_budget,
            total_expense_actual=total_expense_actual,
            total_expense_variance=total_expense_actual - total_expense_budget,
            net_income_budget=total_revenue_budget - total_expense_budget,
            net_income_actual=total_revenue_actual - total_expense_actual,
            net_income_variance=(total_revenue_actual - total_expense_actual) - (total_revenue_budget - total_expense_budget),
            revenue_lines=revenue_lines,
            expense_lines=expense_lines,
        )

    async def _get_line_totals(
        self,
        line: BudgetLine,
        period_type: str,
        year: int,
        month: int
    ) -> Tuple[Decimal, Decimal]:
        """Get budgeted and actual totals for a line based on period type."""
        budgeted = Decimal(0)
        actual = Decimal(0)

        for period in line.periods:
            include = False

            if period_type == "monthly":
                include = period.period_year == year and period.period_month == month
            elif period_type == "quarterly":
                quarter = (month - 1) // 3 + 1
                period_quarter = (period.period_month - 1) // 3 + 1
                include = period.period_year == year and period_quarter == quarter
            elif period_type == "ytd":
                include = period.period_year == year and period.period_month <= month
            elif period_type == "annual":
                include = period.period_year == year

            if include:
                budgeted += period.budgeted_amount
                actual += period.actual_amount

        return budgeted, actual

    async def update_actuals_from_gl(
        self,
        budget_id: UUID,
        year: int,
        month: int
    ) -> int:
        """Update budget periods with actual amounts from GL."""
        budget = await self._get_budget(budget_id)

        if not budget.active_version_id:
            raise BusinessRuleError("Budget has no active version")

        # Get all lines for active version with eager loading of periods
        query = select(BudgetLine).where(
            BudgetLine.version_id == budget.active_version_id
        ).options(selectinload(BudgetLine.periods))
        result = self.db.execute(query)
        lines = result.scalars().all()

        updated_count = 0

        for line in lines:
            # Find the period for this month
            period = next(
                (p for p in line.periods if p.period_year == year and p.period_month == month),
                None
            )

            if not period:
                continue

            # Get actual from GL (simplified - would need real GL integration)
            actual = await self._get_gl_actual(
                line.account_id,
                year,
                month,
                line.department_id,
                line.cost_center_id
            )

            # Update period
            period.actual_amount = actual
            period.variance_amount = actual - period.budgeted_amount

            if period.budgeted_amount != 0:
                period.variance_percent = (period.variance_amount / period.budgeted_amount) * 100

            # Determine variance type
            if line.account_type in ('revenue', 'income'):
                if period.variance_amount > 0:
                    period.variance_type = VarianceType.FAVORABLE
                elif period.variance_amount < 0:
                    period.variance_type = VarianceType.UNFAVORABLE
                else:
                    period.variance_type = VarianceType.ON_TARGET
            else:
                if period.variance_amount < 0:
                    period.variance_type = VarianceType.FAVORABLE
                elif period.variance_amount > 0:
                    period.variance_type = VarianceType.UNFAVORABLE
                else:
                    period.variance_type = VarianceType.ON_TARGET

            updated_count += 1

            # Check for variance alerts
            await self._check_variance_alerts(budget, line, period)

        self.db.commit()
        return updated_count

    async def _get_gl_actual(
        self,
        account_id: UUID,
        year: int,
        month: int,
        department_id: Optional[UUID] = None,
        cost_center_id: Optional[UUID] = None
    ) -> Decimal:
        """Get actual amount from GL for a period."""
        # This would integrate with journal entries module
        # Simplified implementation - returns 0 for now
        return Decimal(0)

    # ==========================================
    # VARIANCE THRESHOLDS
    # ==========================================

    async def create_threshold(self, data: VarianceThresholdCreate) -> VarianceThreshold:
        """Create variance threshold."""
        threshold = VarianceThreshold(
            customer_id=self.customer_id,
            **data.model_dump()
        )
        self.db.add(threshold)
        self.db.commit()
        self.db.refresh(threshold)
        return threshold

    async def update_threshold(self, threshold_id: UUID, data: VarianceThresholdUpdate) -> VarianceThreshold:
        """Update variance threshold."""
        threshold = await self._get_threshold(threshold_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(threshold, key, value)

        self.db.commit()
        self.db.refresh(threshold)
        return threshold

    async def delete_threshold(self, threshold_id: UUID) -> None:
        """Delete variance threshold."""
        threshold = await self._get_threshold(threshold_id)
        self.db.delete(threshold)
        self.db.commit()

    async def get_thresholds(
        self,
        budget_id: Optional[UUID] = None,
        active_only: bool = True
    ) -> List[VarianceThreshold]:
        """Get variance thresholds."""
        query = select(VarianceThreshold).where(
            VarianceThreshold.customer_id == self.customer_id
        )

        if budget_id:
            query = query.where(
                (VarianceThreshold.budget_id == budget_id) |
                (VarianceThreshold.budget_id.is_(None))
            )

        if active_only:
            query = query.where(VarianceThreshold.is_active == True)

        result = self.db.execute(query)
        return result.scalars().all()

    async def _get_threshold(self, threshold_id: UUID) -> VarianceThreshold:
        """Get threshold by ID."""
        threshold = self.db.get(VarianceThreshold, threshold_id)
        if not threshold or threshold.customer_id != self.customer_id:
            raise NotFoundError(f"Threshold not found: {threshold_id}")
        return threshold

    # ==========================================
    # VARIANCE ALERTS
    # ==========================================

    async def _check_variance_alerts(
        self,
        budget: Budget,
        line: BudgetLine,
        period: BudgetPeriod
    ) -> Optional[VarianceAlert]:
        """Check if variance exceeds thresholds and create alert."""
        if period.budgeted_amount == 0:
            return None

        variance_percent = abs(period.variance_percent)

        # Find applicable threshold (most specific wins)
        threshold = await self._get_applicable_threshold(
            budget.id,
            line.account_id,
            line.account_type,
            line.department_id
        )

        if not threshold:
            return None

        # Determine alert level
        alert_level = None
        threshold_used = None

        if variance_percent >= threshold.critical_percent:
            alert_level = AlertLevel.CRITICAL
            threshold_used = threshold.critical_percent
        elif variance_percent >= threshold.warning_percent:
            alert_level = AlertLevel.WARNING
            threshold_used = threshold.warning_percent

        if not alert_level:
            return None

        # Check if alert already exists for this period
        existing = self.db.execute(
            select(VarianceAlert).where(
                VarianceAlert.budget_period_id == period.id,
                VarianceAlert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED])
            )
        ).scalar_one_or_none()

        if existing:
            # Update existing alert
            existing.variance_amount = period.variance_amount
            existing.variance_percent = period.variance_percent
            existing.alert_level = alert_level
            existing.threshold_used = threshold_used
            return existing

        # Create new alert
        alert = VarianceAlert(
            customer_id=self.customer_id,
            budget_id=budget.id,
            budget_period_id=period.id,
            account_id=line.account_id,
            threshold_id=threshold.id,
            account_code=line.account_code,
            account_name=line.account_name,
            budget_name=budget.name,
            period_year=period.period_year,
            period_month=period.period_month,
            budgeted_amount=period.budgeted_amount,
            actual_amount=period.actual_amount,
            variance_amount=period.variance_amount,
            variance_percent=period.variance_percent,
            variance_type=period.variance_type.value if period.variance_type else "unfavorable",
            alert_level=alert_level,
            threshold_used=threshold_used,
        )

        self.db.add(alert)
        return alert

    async def _get_applicable_threshold(
        self,
        budget_id: UUID,
        account_id: UUID,
        account_type: str,
        department_id: Optional[UUID]
    ) -> Optional[VarianceThreshold]:
        """Get most specific applicable threshold."""
        thresholds = await self.get_thresholds(budget_id)

        # Priority: specific account > budget+type > account type > global
        best_match = None
        best_score = -1

        for t in thresholds:
            score = 0

            # Check if applicable
            if t.account_id and t.account_id != account_id:
                continue
            if t.budget_id and t.budget_id != budget_id:
                continue
            if t.account_type and t.account_type != account_type:
                continue
            if t.department_id and t.department_id != department_id:
                continue

            # Calculate specificity score
            if t.account_id:
                score += 100
            if t.budget_id:
                score += 10
            if t.account_type:
                score += 5
            if t.department_id:
                score += 2

            if score > best_score:
                best_score = score
                best_match = t

        return best_match

    async def get_alerts(
        self,
        budget_id: Optional[UUID] = None,
        status: Optional[AlertStatus] = None,
        level: Optional[AlertLevel] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[VarianceAlert], int]:
        """Get variance alerts with filtering."""
        query = select(VarianceAlert).where(
            VarianceAlert.customer_id == self.customer_id
        )

        if budget_id:
            query = query.where(VarianceAlert.budget_id == budget_id)
        if status:
            query = query.where(VarianceAlert.status == status)
        if level:
            query = query.where(VarianceAlert.alert_level == level)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        query = query.order_by(VarianceAlert.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        alerts = result.scalars().all()

        return alerts, total

    async def get_alert_summary(self, budget_id: Optional[UUID] = None) -> AlertSummary:
        """Get alert counts summary."""
        base_filter = VarianceAlert.customer_id == self.customer_id
        if budget_id:
            base_filter = and_(base_filter, VarianceAlert.budget_id == budget_id)

        total = self.db.execute(
            select(func.count(VarianceAlert.id)).where(base_filter)
        ).scalar() or 0

        new_count = self.db.execute(
            select(func.count(VarianceAlert.id)).where(
                base_filter,
                VarianceAlert.status == AlertStatus.NEW
            )
        ).scalar() or 0

        ack_count = self.db.execute(
            select(func.count(VarianceAlert.id)).where(
                base_filter,
                VarianceAlert.status == AlertStatus.ACKNOWLEDGED
            )
        ).scalar() or 0

        critical = self.db.execute(
            select(func.count(VarianceAlert.id)).where(
                base_filter,
                VarianceAlert.alert_level == AlertLevel.CRITICAL,
                VarianceAlert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED])
            )
        ).scalar() or 0

        warning = self.db.execute(
            select(func.count(VarianceAlert.id)).where(
                base_filter,
                VarianceAlert.alert_level == AlertLevel.WARNING,
                VarianceAlert.status.in_([AlertStatus.NEW, AlertStatus.ACKNOWLEDGED])
            )
        ).scalar() or 0

        return AlertSummary(
            total=total,
            new=new_count,
            acknowledged=ack_count,
            critical=critical,
            warning=warning,
        )

    async def acknowledge_alert(self, alert_id: UUID, user_id: UUID, notes: Optional[str] = None) -> VarianceAlert:
        """Acknowledge an alert."""
        alert = await self._get_alert(alert_id)

        if alert.status != AlertStatus.NEW:
            raise BusinessRuleError("Only new alerts can be acknowledged")

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(alert)
        return alert

    async def resolve_alert(self, alert_id: UUID, user_id: UUID, notes: str) -> VarianceAlert:
        """Resolve an alert."""
        alert = await self._get_alert(alert_id)

        if alert.status == AlertStatus.RESOLVED:
            raise BusinessRuleError("Alert is already resolved")

        alert.status = AlertStatus.RESOLVED
        alert.resolved_by = user_id
        alert.resolved_at = datetime.utcnow()
        alert.resolution_notes = notes

        self.db.commit()
        self.db.refresh(alert)
        return alert

    async def dismiss_alert(self, alert_id: UUID) -> VarianceAlert:
        """Dismiss an alert."""
        alert = await self._get_alert(alert_id)
        alert.status = AlertStatus.DISMISSED
        self.db.commit()
        self.db.refresh(alert)
        return alert

    async def _get_alert(self, alert_id: UUID) -> VarianceAlert:
        """Get alert by ID."""
        alert = self.db.get(VarianceAlert, alert_id)
        if not alert or alert.customer_id != self.customer_id:
            raise NotFoundError(f"Alert not found: {alert_id}")
        return alert

    async def _get_budget(self, budget_id: UUID) -> Budget:
        """Get budget by ID."""
        budget = self.db.get(Budget, budget_id)
        if not budget or budget.customer_id != self.customer_id:
            raise NotFoundError(f"Budget not found: {budget_id}")
        return budget
