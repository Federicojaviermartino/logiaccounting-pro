"""
API routes for fixed asset management.
"""
from typing import Optional, List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.fixed_assets.services.asset_service import AssetService
from app.fixed_assets.schemas.asset import (
    AssetCreate, AssetUpdate, AssetResponse, AssetSummary, AssetFilter
)

router = APIRouter(prefix="/assets", tags=["Fixed Assets"])


# ==================== Asset CRUD ====================

@router.get("", response_model=dict)
async def get_assets(
    search: Optional[str] = None,
    category_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    status: Optional[str] = None,
    acquisition_date_from: Optional[date] = None,
    acquisition_date_to: Optional[date] = None,
    fully_depreciated: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get fixed assets with filtering and pagination."""
    service = AssetService(db, current_user.customer_id)

    filters = AssetFilter(
        search=search,
        category_id=category_id,
        location_id=location_id,
        department_id=department_id,
        status=status,
        acquisition_date_from=acquisition_date_from,
        acquisition_date_to=acquisition_date_to,
        fully_depreciated=fully_depreciated
    )

    assets, total = await service.get_assets(filters, skip, limit)

    return {
        "items": [AssetSummary.model_validate(a, from_attributes=True) for a in assets],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/summary", response_model=dict)
async def get_assets_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset summary statistics."""
    service = AssetService(db, current_user.customer_id)
    return await service.get_asset_statistics()


@router.get("/barcode/{barcode}", response_model=AssetResponse)
async def get_asset_by_barcode(
    barcode: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset by barcode or serial number."""
    service = AssetService(db, current_user.customer_id)
    try:
        return await service.get_asset_by_barcode(barcode)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    include_schedule: bool = False,
    include_movements: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset by ID with optional details."""
    service = AssetService(db, current_user.customer_id)
    try:
        return await service.get_asset_by_id(asset_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    data: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new fixed asset."""
    service = AssetService(db, current_user.customer_id)
    try:
        return await service.create_asset(data, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update fixed asset."""
    service = AssetService(db, current_user.customer_id)
    try:
        return await service.update_asset(asset_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete draft asset."""
    service = AssetService(db, current_user.customer_id)
    try:
        await service.delete_asset(asset_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Asset Status ====================

@router.post("/{asset_id}/activate", response_model=AssetResponse)
async def activate_asset(
    asset_id: UUID,
    depreciation_start_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate asset and start depreciation."""
    service = AssetService(db, current_user.customer_id)
    try:
        return await service.activate_asset(asset_id, depreciation_start_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{asset_id}/suspend-depreciation", response_model=AssetResponse)
async def suspend_depreciation(
    asset_id: UUID,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Suspend depreciation for an asset."""
    service = AssetService(db, current_user.customer_id)
    try:
        return await service.suspend_depreciation(asset_id, reason)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{asset_id}/resume-depreciation", response_model=AssetResponse)
async def resume_depreciation(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resume depreciation for an asset."""
    service = AssetService(db, current_user.customer_id)
    try:
        return await service.resume_depreciation(asset_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Schedule ====================

@router.get("/{asset_id}/schedule", response_model=List[dict])
async def get_depreciation_schedule(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get depreciation schedule for asset."""
    service = AssetService(db, current_user.customer_id)
    schedule = await service.get_depreciation_schedule(asset_id)
    return [
        {
            "id": s.id,
            "period_number": s.period_number,
            "period_year": s.period_year,
            "period_month": s.period_month,
            "opening_book_value": s.opening_book_value,
            "depreciation_amount": s.depreciation_amount,
            "accumulated_depreciation": s.accumulated_depreciation,
            "closing_book_value": s.closing_book_value,
            "is_posted": s.is_posted
        }
        for s in schedule
    ]


@router.post("/{asset_id}/regenerate-schedule", response_model=List[dict])
async def regenerate_schedule(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate depreciation schedule."""
    service = AssetService(db, current_user.customer_id)
    schedule = await service.regenerate_schedule(asset_id)
    return [
        {
            "id": s.id,
            "period_number": s.period_number,
            "period_year": s.period_year,
            "period_month": s.period_month,
            "depreciation_amount": s.depreciation_amount,
            "closing_book_value": s.closing_book_value,
            "is_posted": s.is_posted
        }
        for s in schedule
    ]


# ==================== Import/Export ====================

@router.post("/import", response_model=dict)
async def import_assets(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import assets from Excel/CSV."""
    service = AssetService(db, current_user.customer_id)
    return await service.import_assets(file, current_user.id)


@router.get("/export")
async def export_assets(
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    category_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export assets to Excel/CSV."""
    service = AssetService(db, current_user.customer_id)
    return await service.export_assets(format, category_id, status)
