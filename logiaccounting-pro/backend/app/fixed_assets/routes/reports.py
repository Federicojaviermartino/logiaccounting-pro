"""
API routes for fixed asset reports.
"""
from typing import Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.fixed_assets.models.asset import FixedAsset, AssetStatus
from app.fixed_assets.models.category import AssetCategory

router = APIRouter(prefix="/reports", tags=["Asset Reports"])


@router.get("/asset-register")
async def get_asset_register_report(
    as_of_date: date,
    category_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    status: Optional[str] = None,
    format: str = Query("json", pattern="^(json|xlsx|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate asset register report."""
    query = select(FixedAsset).where(
        FixedAsset.customer_id == current_user.customer_id,
        FixedAsset.acquisition_date <= as_of_date
    )

    if category_id:
        query = query.where(FixedAsset.category_id == category_id)

    if status:
        query = query.where(FixedAsset.status == status)

    result = db.execute(query)
    assets = result.scalars().all()

    if format == "json":
        return {
            "report_date": as_of_date,
            "total_assets": len(assets),
            "items": [
                {
                    "asset_number": a.asset_number,
                    "name": a.name,
                    "category_id": a.category_id,
                    "acquisition_date": a.acquisition_date,
                    "total_cost": a.total_cost,
                    "accumulated_depreciation": a.accumulated_depreciation,
                    "book_value": a.book_value,
                    "status": a.status.value
                }
                for a in assets
            ]
        }

    return {"message": f"Export to {format} not implemented"}


@router.get("/depreciation-schedule")
async def get_depreciation_schedule_report(
    year: int,
    category_id: Optional[UUID] = None,
    asset_id: Optional[UUID] = None,
    format: str = Query("json", pattern="^(json|xlsx|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate depreciation schedule report."""
    from app.fixed_assets.models.depreciation import DepreciationSchedule

    query = select(DepreciationSchedule).join(FixedAsset).where(
        FixedAsset.customer_id == current_user.customer_id,
        DepreciationSchedule.period_year == year
    )

    if category_id:
        query = query.where(FixedAsset.category_id == category_id)

    if asset_id:
        query = query.where(DepreciationSchedule.asset_id == asset_id)

    result = db.execute(query)
    schedules = result.scalars().all()

    return {
        "year": year,
        "total_entries": len(schedules),
        "items": [
            {
                "asset_id": s.asset_id,
                "period_month": s.period_month,
                "depreciation_amount": s.depreciation_amount,
                "accumulated_depreciation": s.accumulated_depreciation,
                "closing_book_value": s.closing_book_value
            }
            for s in schedules
        ]
    }


@router.get("/depreciation-summary")
async def get_depreciation_summary(
    start_date: date,
    end_date: date,
    group_by: str = Query("category", pattern="^(category|location|department)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get depreciation summary for period."""
    from app.fixed_assets.models.depreciation import DepreciationEntry

    query = select(
        DepreciationEntry.category_name,
        func.count(DepreciationEntry.id).label("entry_count"),
        func.sum(DepreciationEntry.depreciation_amount).label("total_depreciation")
    ).where(
        DepreciationEntry.customer_id == current_user.customer_id,
        DepreciationEntry.entry_date >= start_date,
        DepreciationEntry.entry_date <= end_date
    ).group_by(DepreciationEntry.category_name)

    result = db.execute(query)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "group_by": group_by,
        "summary": [
            {
                "category": row.category_name,
                "entry_count": row.entry_count,
                "total_depreciation": row.total_depreciation
            }
            for row in result
        ]
    }


@router.get("/movement-history")
async def get_movement_history_report(
    start_date: date,
    end_date: date,
    asset_id: Optional[UUID] = None,
    movement_type: Optional[str] = None,
    format: str = Query("json", pattern="^(json|xlsx|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate movement history report."""
    from app.fixed_assets.models.transaction import AssetTransaction

    query = select(AssetTransaction).where(
        AssetTransaction.customer_id == current_user.customer_id,
        AssetTransaction.transaction_date >= start_date,
        AssetTransaction.transaction_date <= end_date
    )

    if asset_id:
        query = query.where(AssetTransaction.asset_id == asset_id)

    if movement_type:
        query = query.where(AssetTransaction.transaction_type == movement_type)

    result = db.execute(query)
    movements = result.scalars().all()

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_movements": len(movements),
        "items": [
            {
                "transaction_number": m.transaction_number,
                "transaction_type": m.transaction_type.value,
                "transaction_date": m.transaction_date,
                "asset_id": m.asset_id,
                "amount": m.amount
            }
            for m in movements
        ]
    }


@router.get("/disposal-report")
async def get_disposal_report(
    start_date: date,
    end_date: date,
    disposal_type: Optional[str] = None,
    format: str = Query("json", pattern="^(json|xlsx|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate disposal report with gain/loss analysis."""
    from app.fixed_assets.models.transaction import AssetTransaction, TransactionType

    query = select(AssetTransaction).where(
        AssetTransaction.customer_id == current_user.customer_id,
        AssetTransaction.transaction_type == TransactionType.DISPOSAL,
        AssetTransaction.transaction_date >= start_date,
        AssetTransaction.transaction_date <= end_date
    )

    if disposal_type:
        query = query.where(AssetTransaction.disposal_type == disposal_type)

    result = db.execute(query)
    disposals = result.scalars().all()

    total_proceeds = sum(d.proceeds or 0 for d in disposals)
    total_gain_loss = sum(d.gain_loss or 0 for d in disposals)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_disposals": len(disposals),
        "total_proceeds": total_proceeds,
        "total_gain_loss": total_gain_loss,
        "items": [
            {
                "transaction_number": d.transaction_number,
                "disposal_type": d.disposal_type,
                "disposal_date": d.transaction_date,
                "proceeds": d.proceeds,
                "book_value": d.book_value_at_disposal,
                "gain_loss": d.gain_loss
            }
            for d in disposals
        ]
    }


@router.get("/fully-depreciated")
async def get_fully_depreciated_assets(
    as_of_date: Optional[date] = None,
    category_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of fully depreciated assets."""
    query = select(FixedAsset).where(
        FixedAsset.customer_id == current_user.customer_id,
        FixedAsset.is_fully_depreciated == True
    )

    if category_id:
        query = query.where(FixedAsset.category_id == category_id)

    result = db.execute(query)
    assets = result.scalars().all()

    return {
        "total_count": len(assets),
        "items": [
            {
                "asset_number": a.asset_number,
                "name": a.name,
                "total_cost": a.total_cost,
                "fully_depreciated_date": a.fully_depreciated_date,
                "status": a.status.value
            }
            for a in assets
        ]
    }


@router.get("/insurance-expiry")
async def get_insurance_expiry_report(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assets with expiring insurance."""
    from datetime import timedelta

    expiry_date = date.today() + timedelta(days=days_ahead)

    query = select(FixedAsset).where(
        FixedAsset.customer_id == current_user.customer_id,
        FixedAsset.insurance_expiry_date != None,
        FixedAsset.insurance_expiry_date <= expiry_date,
        FixedAsset.status == AssetStatus.ACTIVE
    )

    result = db.execute(query)
    assets = result.scalars().all()

    return {
        "days_ahead": days_ahead,
        "expiry_cutoff": expiry_date,
        "total_count": len(assets),
        "items": [
            {
                "asset_number": a.asset_number,
                "name": a.name,
                "insurance_policy": a.insurance_policy,
                "insurance_expiry_date": a.insurance_expiry_date
            }
            for a in assets
        ]
    }


@router.get("/warranty-expiry")
async def get_warranty_expiry_report(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get assets with expiring warranty."""
    from datetime import timedelta

    expiry_date = date.today() + timedelta(days=days_ahead)

    query = select(FixedAsset).where(
        FixedAsset.customer_id == current_user.customer_id,
        FixedAsset.warranty_expiry_date != None,
        FixedAsset.warranty_expiry_date <= expiry_date,
        FixedAsset.status == AssetStatus.ACTIVE
    )

    result = db.execute(query)
    assets = result.scalars().all()

    return {
        "days_ahead": days_ahead,
        "expiry_cutoff": expiry_date,
        "total_count": len(assets),
        "items": [
            {
                "asset_number": a.asset_number,
                "name": a.name,
                "warranty_provider": a.warranty_provider,
                "warranty_expiry_date": a.warranty_expiry_date
            }
            for a in assets
        ]
    }


@router.get("/category-summary")
async def get_category_summary(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset summary by category."""
    query = select(
        AssetCategory.name,
        func.count(FixedAsset.id).label("asset_count"),
        func.sum(FixedAsset.total_cost).label("total_cost"),
        func.sum(FixedAsset.book_value).label("book_value"),
        func.sum(FixedAsset.accumulated_depreciation).label("accumulated_depreciation")
    ).join(FixedAsset).where(
        FixedAsset.customer_id == current_user.customer_id,
        FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED])
    ).group_by(AssetCategory.name)

    result = db.execute(query)

    return {
        "as_of_date": as_of_date or date.today(),
        "summary": [
            {
                "category": row.name,
                "asset_count": row.asset_count,
                "total_cost": row.total_cost,
                "book_value": row.book_value,
                "accumulated_depreciation": row.accumulated_depreciation
            }
            for row in result
        ]
    }
