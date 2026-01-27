"""
Fixed asset management service.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.fixed_assets.models.asset import FixedAsset, AssetAttachment, AssetStatus
from app.fixed_assets.models.category import AssetCategory
from app.fixed_assets.schemas.asset import (
    AssetCreate, AssetUpdate, AssetFilter
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


class AssetService:
    """Service for fixed asset operations."""

    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id

    # ==================== Number Generation ====================

    async def _generate_asset_number(self, category: AssetCategory) -> str:
        """Generate unique asset number."""
        year = datetime.now().year % 100
        prefix = category.code[:3].upper()

        # Get count for this category/year
        count_query = select(func.count(FixedAsset.id)).where(
            FixedAsset.customer_id == self.customer_id,
            FixedAsset.asset_number.like(f"{prefix}-{year}-%")
        )
        count = self.db.execute(count_query).scalar() or 0

        return f"{prefix}-{year}-{(count + 1):05d}"

    # ==================== Asset CRUD ====================

    async def create_asset(
        self,
        data: AssetCreate,
        created_by: Optional[UUID] = None
    ) -> FixedAsset:
        """Create a new fixed asset."""
        # Get category for defaults
        category = await self._get_category(data.category_id)

        # Apply category defaults if not specified
        depreciation_method = data.depreciation_method or category.default_depreciation_method
        useful_life_months = data.useful_life_months or category.default_useful_life_months

        # Calculate salvage value
        total_cost = (
            data.acquisition_cost +
            data.installation_cost +
            data.shipping_cost +
            data.other_costs
        )

        if data.salvage_value is not None:
            salvage_value = data.salvage_value
        elif data.salvage_percent is not None:
            salvage_value = total_cost * data.salvage_percent / 100
        else:
            salvage_value = total_cost * category.default_salvage_percent / 100

        # Generate asset number
        asset_number = await self._generate_asset_number(category)

        # Determine in-service date
        in_service_date = data.in_service_date or data.acquisition_date

        # Create asset
        asset = FixedAsset(
            customer_id=self.customer_id,
            asset_number=asset_number,
            name=data.name,
            description=data.description,
            category_id=data.category_id,

            # Location
            location=data.location,
            department_id=data.department_id,
            responsible_person_id=data.responsible_person_id,

            # Physical
            serial_number=data.serial_number,
            model=data.model,
            manufacturer=data.manufacturer,
            barcode=data.barcode,

            # Acquisition
            acquisition_type=data.acquisition_type,
            acquisition_date=data.acquisition_date,
            in_service_date=in_service_date,
            supplier_id=data.supplier_id,
            purchase_order_id=data.purchase_order_id,
            invoice_reference=data.invoice_reference,

            # Costs
            acquisition_cost=data.acquisition_cost,
            installation_cost=data.installation_cost,
            shipping_cost=data.shipping_cost,
            other_costs=data.other_costs,
            total_cost=total_cost,

            # Depreciation
            depreciation_method=depreciation_method,
            useful_life_months=useful_life_months,
            salvage_value=salvage_value,
            salvage_percent=data.salvage_percent or category.default_salvage_percent,
            depreciation_start_date=in_service_date,

            # For units of production
            total_estimated_units=data.total_estimated_units,
            unit_of_measure=data.unit_of_measure,

            # Initial values
            accumulated_depreciation=Decimal(0),
            book_value=total_cost,

            # Insurance
            insured_value=data.insured_value,
            insurance_policy=data.insurance_policy,
            insurance_expiry_date=data.insurance_expiry_date,

            # Warranty
            warranty_expiry_date=data.warranty_expiry_date,
            warranty_provider=data.warranty_provider,

            notes=data.notes,
            status=AssetStatus.ACTIVE,
            created_by=created_by,
        )

        self.db.add(asset)

        try:
            self.db.commit()
            self.db.refresh(asset)
        except IntegrityError as e:
            self.db.rollback()
            raise ValidationError(f"Asset creation failed: {str(e)}")

        # Generate depreciation schedule
        await self._generate_depreciation_schedule(asset)

        return asset

    async def update_asset(
        self,
        asset_id: UUID,
        data: AssetUpdate
    ) -> FixedAsset:
        """Update fixed asset."""
        asset = await self.get_asset_by_id(asset_id)

        # Prevent updates to disposed assets
        if asset.status == AssetStatus.DISPOSED:
            raise BusinessRuleError("Cannot update disposed asset")

        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if hasattr(asset, key):
                setattr(asset, key, value)

        self.db.commit()
        self.db.refresh(asset)

        return asset

    async def get_asset_by_id(
        self,
        asset_id: UUID,
        include_details: bool = True
    ) -> FixedAsset:
        """Get asset by ID."""
        query = select(FixedAsset).where(
            FixedAsset.id == asset_id,
            FixedAsset.customer_id == self.customer_id
        )

        if include_details:
            query = query.options(
                selectinload(FixedAsset.category),
                selectinload(FixedAsset.attachments),
                selectinload(FixedAsset.depreciation_schedule)
            )

        result = self.db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            raise NotFoundError(f"Asset not found: {asset_id}")

        return asset

    async def get_asset_by_barcode(self, barcode: str) -> FixedAsset:
        """Get asset by barcode or serial number."""
        query = select(FixedAsset).where(
            FixedAsset.customer_id == self.customer_id,
            or_(
                FixedAsset.barcode == barcode,
                FixedAsset.serial_number == barcode
            )
        ).options(selectinload(FixedAsset.category))

        result = self.db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            raise NotFoundError(f"Asset not found with barcode: {barcode}")

        return asset

    async def get_assets(
        self,
        filters: AssetFilter,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[FixedAsset], int]:
        """Get assets with filtering."""
        query = select(FixedAsset).where(
            FixedAsset.customer_id == self.customer_id
        )

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    FixedAsset.asset_number.ilike(search_term),
                    FixedAsset.name.ilike(search_term),
                    FixedAsset.serial_number.ilike(search_term),
                    FixedAsset.barcode.ilike(search_term)
                )
            )

        if filters.category_id:
            query = query.where(FixedAsset.category_id == filters.category_id)

        if filters.department_id:
            query = query.where(FixedAsset.department_id == filters.department_id)

        if filters.status:
            query = query.where(FixedAsset.status == filters.status)

        if filters.acquisition_date_from:
            query = query.where(FixedAsset.acquisition_date >= filters.acquisition_date_from)

        if filters.acquisition_date_to:
            query = query.where(FixedAsset.acquisition_date <= filters.acquisition_date_to)

        if filters.is_fully_depreciated is not None:
            query = query.where(FixedAsset.is_fully_depreciated == filters.is_fully_depreciated)

        if filters.fully_depreciated is not None:
            query = query.where(FixedAsset.is_fully_depreciated == filters.fully_depreciated)

        if filters.location:
            query = query.where(FixedAsset.location.ilike(f"%{filters.location}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()

        # Apply pagination
        query = query.options(selectinload(FixedAsset.category))
        query = query.order_by(FixedAsset.asset_number)
        query = query.offset(skip).limit(limit)

        result = self.db.execute(query)
        assets = result.scalars().all()

        return assets, total

    async def delete_asset(self, asset_id: UUID) -> None:
        """Delete draft asset."""
        asset = await self.get_asset_by_id(asset_id)

        if asset.status != AssetStatus.DRAFT:
            raise BusinessRuleError("Only draft assets can be deleted")

        self.db.delete(asset)
        self.db.commit()

    # ==================== Asset Status ====================

    async def activate_asset(
        self,
        asset_id: UUID,
        depreciation_start_date: Optional[date] = None
    ) -> FixedAsset:
        """Activate asset and start depreciation."""
        asset = await self.get_asset_by_id(asset_id)

        if asset.status != AssetStatus.DRAFT:
            raise BusinessRuleError("Only draft assets can be activated")

        asset.status = AssetStatus.ACTIVE
        if depreciation_start_date:
            asset.depreciation_start_date = depreciation_start_date

        self.db.commit()
        self.db.refresh(asset)

        return asset

    async def suspend_depreciation(
        self,
        asset_id: UUID,
        reason: str
    ) -> FixedAsset:
        """Suspend depreciation for an asset."""
        asset = await self.get_asset_by_id(asset_id)

        if asset.status != AssetStatus.ACTIVE:
            raise BusinessRuleError("Only active assets can have depreciation suspended")

        asset.depreciation_suspended = True
        asset.suspension_reason = reason
        asset.status = AssetStatus.UNDER_MAINTENANCE

        self.db.commit()
        self.db.refresh(asset)

        return asset

    async def resume_depreciation(self, asset_id: UUID) -> FixedAsset:
        """Resume depreciation for an asset."""
        asset = await self.get_asset_by_id(asset_id)

        if not asset.depreciation_suspended:
            raise BusinessRuleError("Asset depreciation is not suspended")

        asset.depreciation_suspended = False
        asset.suspension_reason = None
        asset.status = AssetStatus.ACTIVE

        self.db.commit()
        self.db.refresh(asset)

        return asset

    # ==================== Depreciation Schedule ====================

    async def _generate_depreciation_schedule(self, asset: FixedAsset) -> None:
        """Generate depreciation schedule for asset."""
        from app.fixed_assets.models.depreciation import DepreciationSchedule

        # Get schedule from engine
        schedule = DepreciationCalculator.generate_schedule(asset)

        # Create schedule records
        for item in schedule:
            schedule_record = DepreciationSchedule(
                asset_id=asset.id,
                period_number=item.period_number,
                period_year=item.period_year,
                period_month=item.period_month,
                period_start=item.period_start,
                period_end=item.period_end,
                opening_book_value=item.opening_book_value,
                depreciation_amount=item.depreciation_amount,
                accumulated_depreciation=item.accumulated_depreciation,
                closing_book_value=item.closing_book_value,
            )
            self.db.add(schedule_record)

        self.db.commit()

    async def get_depreciation_schedule(self, asset_id: UUID) -> List:
        """Get depreciation schedule for asset."""
        from app.fixed_assets.models.depreciation import DepreciationSchedule

        query = select(DepreciationSchedule).where(
            DepreciationSchedule.asset_id == asset_id
        ).order_by(DepreciationSchedule.period_number)

        result = self.db.execute(query)
        return result.scalars().all()

    async def regenerate_schedule(self, asset_id: UUID) -> List:
        """Regenerate depreciation schedule."""
        from app.fixed_assets.models.depreciation import DepreciationSchedule

        asset = await self.get_asset_by_id(asset_id)

        # Delete unposted schedule entries
        self.db.execute(
            DepreciationSchedule.__table__.delete().where(
                DepreciationSchedule.asset_id == asset_id,
                DepreciationSchedule.is_posted == False
            )
        )

        # Regenerate
        await self._generate_depreciation_schedule(asset)

        return await self.get_depreciation_schedule(asset_id)

    # ==================== Helpers ====================

    async def _get_category(self, category_id: UUID) -> AssetCategory:
        """Get category by ID."""
        query = select(AssetCategory).where(
            AssetCategory.id == category_id,
            AssetCategory.customer_id == self.customer_id
        )
        result = self.db.execute(query)
        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundError(f"Category not found: {category_id}")

        return category

    # ==================== Statistics ====================

    async def get_asset_statistics(self) -> dict:
        """Get asset statistics."""
        # Total counts by status
        status_query = select(
            FixedAsset.status,
            func.count(FixedAsset.id).label("count"),
            func.sum(FixedAsset.total_cost).label("total_cost"),
            func.sum(FixedAsset.book_value).label("book_value")
        ).where(
            FixedAsset.customer_id == self.customer_id
        ).group_by(FixedAsset.status)

        status_result = self.db.execute(status_query)

        by_status = {}
        total_count = 0
        total_cost = Decimal(0)
        total_book_value = Decimal(0)

        for row in status_result:
            by_status[row.status.value] = {
                "count": row.count,
                "total_cost": row.total_cost or Decimal(0),
                "book_value": row.book_value or Decimal(0)
            }
            total_count += row.count
            total_cost += row.total_cost or Decimal(0)
            total_book_value += row.book_value or Decimal(0)

        # By category
        category_query = select(
            AssetCategory.name,
            func.count(FixedAsset.id).label("count"),
            func.sum(FixedAsset.book_value).label("book_value")
        ).join(FixedAsset).where(
            FixedAsset.customer_id == self.customer_id,
            FixedAsset.status == AssetStatus.ACTIVE
        ).group_by(AssetCategory.name)

        category_result = self.db.execute(category_query)
        by_category = [
            {"category": row.name, "count": row.count, "book_value": row.book_value}
            for row in category_result
        ]

        return {
            "total_assets": total_count,
            "total_cost": total_cost,
            "total_book_value": total_book_value,
            "total_depreciation": total_cost - total_book_value,
            "by_status": by_status,
            "by_category": by_category
        }

    # ==================== Import/Export ====================

    async def import_assets(self, file, created_by: UUID) -> dict:
        """Import assets from Excel/CSV."""
        # Implementation would parse the file and create assets
        return {"status": "not_implemented"}

    async def export_assets(
        self,
        format: str,
        category_id: Optional[UUID] = None,
        status: Optional[str] = None
    ):
        """Export assets to Excel/CSV."""
        # Implementation would generate the export file
        return {"status": "not_implemented"}
