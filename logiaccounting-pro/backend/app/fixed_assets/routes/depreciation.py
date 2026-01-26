"""
API routes for depreciation processing.
"""
from typing import Optional, List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.fixed_assets.services.depreciation_service import DepreciationService
from app.fixed_assets.schemas.depreciation import (
    DepreciationRunCreate, DepreciationRunResponse,
    DepreciationEntryResponse, UnitsUpdateRequest
)

router = APIRouter(prefix="/depreciation", tags=["Asset Depreciation"])


# ==================== Depreciation Runs ====================

@router.get("/runs", response_model=dict)
async def get_depreciation_runs(
    year: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get depreciation runs."""
    service = DepreciationService(db, current_user.customer_id)
    runs, total = await service.get_runs(year, status, skip, limit)

    return {
        "items": [DepreciationRunResponse.model_validate(r, from_attributes=True) for r in runs],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/runs/{run_id}", response_model=DepreciationRunResponse)
async def get_depreciation_run(
    run_id: UUID,
    include_entries: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get depreciation run details."""
    service = DepreciationService(db, current_user.customer_id)
    try:
        return await service.get_run_by_id(run_id, include_entries)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/runs", response_model=DepreciationRunResponse, status_code=status.HTTP_201_CREATED)
async def create_depreciation_run(
    data: DepreciationRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and calculate depreciation run."""
    service = DepreciationService(db, current_user.customer_id)
    try:
        return await service.create_depreciation_run(
            period_year=data.period_year,
            period_month=data.period_month,
            category_id=data.category_id,
            created_by=current_user.id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/post", response_model=DepreciationRunResponse)
async def post_depreciation_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Post depreciation run to general ledger."""
    service = DepreciationService(db, current_user.customer_id)
    try:
        return await service.post_depreciation_run(run_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/cancel", response_model=DepreciationRunResponse)
async def cancel_depreciation_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a non-posted depreciation run."""
    service = DepreciationService(db, current_user.customer_id)
    try:
        return await service.cancel_depreciation_run(run_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/reverse", response_model=DepreciationRunResponse)
async def reverse_depreciation_run(
    run_id: UUID,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reverse a posted depreciation run."""
    service = DepreciationService(db, current_user.customer_id)
    try:
        return await service.reverse_depreciation_run(run_id, reason, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Entries ====================

@router.get("/entries", response_model=dict)
async def get_depreciation_entries(
    asset_id: Optional[UUID] = None,
    run_id: Optional[UUID] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get depreciation entries."""
    service = DepreciationService(db, current_user.customer_id)
    entries, total = await service.get_entries(asset_id, run_id, year, month, skip, limit)

    return {
        "items": [DepreciationEntryResponse.model_validate(e, from_attributes=True) for e in entries],
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ==================== Units of Production ====================

@router.post("/record-units", response_model=dict)
async def record_units_produced(
    data: UnitsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record units produced for units-of-production depreciation."""
    service = DepreciationService(db, current_user.customer_id)
    try:
        return await service.record_units(data.asset_id, data.period_year, data.period_month, data.units)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Preview ====================

@router.get("/preview")
async def preview_depreciation(
    period_year: int,
    period_month: int,
    category_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview depreciation calculations without creating run."""
    service = DepreciationService(db, current_user.customer_id)
    return await service.preview_depreciation(period_year, period_month, category_id)
