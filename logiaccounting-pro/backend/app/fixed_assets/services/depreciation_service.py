"""
Depreciation processing service.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID
import json

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.fixed_assets.models.asset import FixedAsset, AssetStatus
from app.fixed_assets.models.category import AssetCategory
from app.fixed_assets.models.depreciation import (
    DepreciationRun, DepreciationEntry, DepreciationSchedule,
    DepreciationRunStatus, DepreciationEntryStatus
)
from app.fixed_assets.services.depreciation_engine import DepreciationCalculator


class NotFoundError(Exception):
    """Resource not found."""
    pass


class ValidationError(Exception):
    """Validation error."""
    pass


class BusinessRuleError(Exception):
    """Business rule violation."""
    pass


class DepreciationService:
    """Service for depreciation processing."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    # ==================== Depreciation Runs ====================

    async def create_depreciation_run(
        self,
        period_year: int,
        period_month: int,
        category_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None
    ) -> DepreciationRun:
        """Create and calculate a depreciation run."""
        # Check for existing run
        existing = await self._get_existing_run(period_year, period_month)
        if existing and existing.status == DepreciationRunStatus.POSTED:
            raise BusinessRuleError(f"Depreciation already posted for {period_year}-{period_month:02d}")

        # Generate run number
        run_number = await self._generate_run_number(period_year, period_month)

        # Create run
        run = DepreciationRun(
            customer_id=self.customer_id,
            run_number=run_number,
            run_date=date.today(),
            period_year=period_year,
            period_month=period_month,
            category_id=category_id,
            department_id=department_id,
            status=DepreciationRunStatus.DRAFT,
            created_by=created_by,
        )

        self.db.add(run)
        self.db.flush()

        # Calculate depreciation for all eligible assets
        await self._calculate_run_entries(run)

        self.db.commit()
        self.db.refresh(run)

        return run

    async def _calculate_run_entries(self, run: DepreciationRun) -> None:
        """Calculate depreciation entries for all eligible assets."""
        from sqlalchemy.orm import selectinload

        # Get eligible assets
        query = select(FixedAsset).where(
            FixedAsset.customer_id == self.customer_id,
            FixedAsset.status == AssetStatus.ACTIVE,
            FixedAsset.is_fully_depreciated == False,
            FixedAsset.depreciation_suspended == False
        ).options(selectinload(FixedAsset.category))

        if run.category_id:
            query = query.where(FixedAsset.category_id == run.category_id)

        if run.department_id:
            query = query.where(FixedAsset.department_id == run.department_id)

        result = self.db.execute(query)
        assets = result.scalars().all()

        total_depreciation = Decimal(0)
        processed = 0
        skipped = 0
        errors = []

        for asset in assets:
            # Calculate depreciation
            depreciation, skip_reason = DepreciationCalculator.calculate_for_asset(
                asset,
                run.period_year,
                run.period_month
            )

            if skip_reason:
                # Create skipped entry for audit
                entry = DepreciationEntry(
                    customer_id=self.customer_id,
                    depreciation_run_id=run.id,
                    period_year=run.period_year,
                    period_month=run.period_month,
                    entry_date=date(run.period_year, run.period_month, 1),
                    asset_id=asset.id,
                    asset_number=asset.asset_number,
                    asset_name=asset.name,
                    category_id=asset.category_id,
                    category_name=asset.category.name if asset.category else "Unknown",
                    depreciation_method=asset.depreciation_method.value,
                    depreciation_amount=Decimal(0),
                    book_value_before=asset.book_value,
                    book_value_after=asset.book_value,
                    accumulated_before=asset.accumulated_depreciation,
                    accumulated_after=asset.accumulated_depreciation,
                    expense_account_id=asset.category.depreciation_expense_account_id if asset.category and asset.category.depreciation_expense_account_id else asset.id,
                    accumulated_account_id=asset.category.accumulated_depreciation_account_id if asset.category and asset.category.accumulated_depreciation_account_id else asset.id,
                    status=DepreciationEntryStatus.SKIPPED,
                    skip_reason=skip_reason,
                )
                self.db.add(entry)
                skipped += 1
                continue

            if depreciation <= 0:
                skipped += 1
                continue

            # Get accounts from category
            category = asset.category
            if not category or not category.depreciation_expense_account_id or not category.accumulated_depreciation_account_id:
                errors.append(f"Asset {asset.asset_number}: Missing GL accounts in category")
                skipped += 1
                continue

            # Create depreciation entry
            entry = DepreciationEntry(
                customer_id=self.customer_id,
                depreciation_run_id=run.id,
                period_year=run.period_year,
                period_month=run.period_month,
                entry_date=date(run.period_year, run.period_month, 1),
                asset_id=asset.id,
                asset_number=asset.asset_number,
                asset_name=asset.name,
                category_id=asset.category_id,
                category_name=category.name,
                depreciation_method=asset.depreciation_method.value,
                depreciation_amount=depreciation,
                book_value_before=asset.book_value,
                book_value_after=asset.book_value - depreciation,
                accumulated_before=asset.accumulated_depreciation,
                accumulated_after=asset.accumulated_depreciation + depreciation,
                expense_account_id=category.depreciation_expense_account_id,
                accumulated_account_id=category.accumulated_depreciation_account_id,
                status=DepreciationEntryStatus.CALCULATED,
            )

            self.db.add(entry)
            total_depreciation += depreciation
            processed += 1

        # Update run totals
        run.assets_processed = processed
        run.assets_skipped = skipped
        run.total_depreciation = total_depreciation
        run.status = DepreciationRunStatus.CALCULATED

        if errors:
            run.errors = json.dumps(errors)

    async def post_depreciation_run(
        self,
        run_id: UUID,
        user_id: UUID
    ) -> DepreciationRun:
        """Post depreciation run to general ledger."""
        run = await self.get_run_by_id(run_id)

        if run.status != DepreciationRunStatus.CALCULATED:
            raise BusinessRuleError("Run must be in calculated status to post")

        if run.total_depreciation <= 0:
            raise ValidationError("No depreciation to post")

        # Update run
        run.status = DepreciationRunStatus.POSTED
        run.posted_at = datetime.utcnow()
        run.posted_by = user_id

        # Update entries and assets
        for entry in run.entries:
            if entry.status == DepreciationEntryStatus.CALCULATED:
                entry.status = DepreciationEntryStatus.POSTED
                entry.posted_at = datetime.utcnow()
                entry.posted_by = user_id

                # Update asset
                asset = self.db.get(FixedAsset, entry.asset_id)
                if asset:
                    asset.accumulated_depreciation = entry.accumulated_after
                    asset.book_value = entry.book_value_after
                    asset.last_depreciation_date = entry.entry_date
                    asset.last_depreciation_amount = entry.depreciation_amount

                    # Check if fully depreciated
                    if asset.book_value <= asset.salvage_value:
                        asset.is_fully_depreciated = True
                        asset.fully_depreciated_date = entry.entry_date
                        asset.status = AssetStatus.FULLY_DEPRECIATED

        self.db.commit()
        self.db.refresh(run)

        return run

    async def cancel_depreciation_run(self, run_id: UUID) -> DepreciationRun:
        """Cancel a non-posted depreciation run."""
        run = await self.get_run_by_id(run_id)

        if run.status == DepreciationRunStatus.POSTED:
            raise BusinessRuleError("Cannot cancel posted run")

        run.status = DepreciationRunStatus.CANCELLED

        for entry in run.entries:
            entry.status = DepreciationEntryStatus.SKIPPED
            entry.skip_reason = "Run cancelled"

        self.db.commit()
        self.db.refresh(run)

        return run

    async def reverse_depreciation_run(
        self,
        run_id: UUID,
        reason: str,
        user_id: UUID
    ) -> DepreciationRun:
        """Reverse a posted depreciation run."""
        run = await self.get_run_by_id(run_id)

        if run.status != DepreciationRunStatus.POSTED:
            raise BusinessRuleError("Can only reverse posted runs")

        # Reverse entries and update assets
        for entry in run.entries:
            if entry.status == DepreciationEntryStatus.POSTED:
                entry.status = DepreciationEntryStatus.REVERSED

                # Reverse asset values
                asset = self.db.get(FixedAsset, entry.asset_id)
                if asset:
                    asset.accumulated_depreciation = entry.accumulated_before
                    asset.book_value = entry.book_value_before
                    if asset.is_fully_depreciated:
                        asset.is_fully_depreciated = False
                        asset.fully_depreciated_date = None
                        asset.status = AssetStatus.ACTIVE

        run.status = DepreciationRunStatus.CANCELLED

        self.db.commit()
        self.db.refresh(run)

        return run

    # ==================== Queries ====================

    async def get_run_by_id(
        self,
        run_id: UUID,
        include_entries: bool = False
    ) -> DepreciationRun:
        """Get depreciation run by ID."""
        from sqlalchemy.orm import selectinload

        query = select(DepreciationRun).where(
            DepreciationRun.id == run_id,
            DepreciationRun.customer_id == self.customer_id
        )

        if include_entries:
            query = query.options(selectinload(DepreciationRun.entries))

        result = self.db.execute(query)
        run = result.scalar_one_or_none()

        if not run:
            raise NotFoundError(f"Depreciation run not found: {run_id}")

        return run

    async def get_runs(
        self,
        year: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[DepreciationRun], int]:
        """Get depreciation runs."""
        query = select(DepreciationRun).where(
            DepreciationRun.customer_id == self.customer_id
        )

        if year:
            query = query.where(DepreciationRun.period_year == year)

        if status:
            query = query.where(DepreciationRun.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        query = query.order_by(
            DepreciationRun.period_year.desc(),
            DepreciationRun.period_month.desc()
        ).offset(skip).limit(limit)

        result = self.db.execute(query)
        runs = result.scalars().all()

        return runs, total

    async def get_entries(
        self,
        asset_id: Optional[UUID] = None,
        run_id: Optional[UUID] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[DepreciationEntry], int]:
        """Get depreciation entries."""
        query = select(DepreciationEntry).where(
            DepreciationEntry.customer_id == self.customer_id
        )

        if asset_id:
            query = query.where(DepreciationEntry.asset_id == asset_id)

        if run_id:
            query = query.where(DepreciationEntry.depreciation_run_id == run_id)

        if year:
            query = query.where(DepreciationEntry.period_year == year)

        if month:
            query = query.where(DepreciationEntry.period_month == month)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        query = query.order_by(
            DepreciationEntry.period_year.desc(),
            DepreciationEntry.period_month.desc()
        ).offset(skip).limit(limit)

        result = self.db.execute(query)
        entries = result.scalars().all()

        return entries, total

    async def _get_existing_run(
        self,
        period_year: int,
        period_month: int
    ) -> Optional[DepreciationRun]:
        """Check for existing run."""
        query = select(DepreciationRun).where(
            DepreciationRun.customer_id == self.customer_id,
            DepreciationRun.period_year == period_year,
            DepreciationRun.period_month == period_month
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    async def _generate_run_number(self, year: int, month: int) -> str:
        """Generate depreciation run number."""
        return f"DEP-{year}-{month:02d}"

    # ==================== Units of Production ====================

    async def record_units(
        self,
        asset_id: UUID,
        period_year: int,
        period_month: int,
        units: Decimal
    ) -> dict:
        """Record units produced for UOP depreciation."""
        asset = self.db.get(FixedAsset, asset_id)
        if not asset:
            raise NotFoundError(f"Asset not found: {asset_id}")

        asset.units_produced_to_date += units

        self.db.commit()

        return {
            "asset_id": asset_id,
            "units_recorded": units,
            "total_units": asset.units_produced_to_date
        }

    # ==================== Preview ====================

    async def preview_depreciation(
        self,
        period_year: int,
        period_month: int,
        category_id: Optional[UUID] = None
    ) -> List[dict]:
        """Preview depreciation calculations without creating run."""
        from sqlalchemy.orm import selectinload

        query = select(FixedAsset).where(
            FixedAsset.customer_id == self.customer_id,
            FixedAsset.status == AssetStatus.ACTIVE,
            FixedAsset.is_fully_depreciated == False,
            FixedAsset.depreciation_suspended == False
        ).options(selectinload(FixedAsset.category))

        if category_id:
            query = query.where(FixedAsset.category_id == category_id)

        result = self.db.execute(query)
        assets = result.scalars().all()

        preview = []
        for asset in assets:
            depreciation, skip_reason = DepreciationCalculator.calculate_for_asset(
                asset, period_year, period_month
            )

            preview.append({
                "asset_id": asset.id,
                "asset_number": asset.asset_number,
                "asset_name": asset.name,
                "category_name": asset.category.name if asset.category else None,
                "depreciation_amount": depreciation,
                "book_value_before": asset.book_value,
                "book_value_after": asset.book_value - depreciation,
                "skip_reason": skip_reason
            })

        return preview
