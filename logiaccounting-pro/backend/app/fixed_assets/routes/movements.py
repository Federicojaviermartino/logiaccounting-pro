"""
API routes for asset movements and disposals.
"""
from typing import Optional, List
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.fixed_assets.services.disposal_service import DisposalService
from app.fixed_assets.schemas.transaction import (
    TransferCreate, RevaluationCreate, ImprovementCreate,
    MovementResponse, DisposalCreate, DisposalResponse
)

router = APIRouter(tags=["Asset Movements & Disposals"])


# ==================== Movements ====================

@router.get("/movements", response_model=dict)
async def get_movements(
    asset_id: Optional[UUID] = None,
    movement_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset movements."""
    # Implementation would query movements
    return {
        "items": [],
        "total": 0,
        "skip": skip,
        "limit": limit
    }


@router.get("/movements/{movement_id}", response_model=MovementResponse)
async def get_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get movement by ID."""
    raise HTTPException(status_code=404, detail="Movement not found")


@router.post("/transfer", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
async def transfer_asset(
    data: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfer asset to new location/department."""
    service = DisposalService(db, current_user.customer_id)
    try:
        return await service.transfer_asset(data, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/revalue", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
async def revalue_asset(
    data: RevaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revalue an asset."""
    # Implementation for revaluation
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/improve", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
async def add_improvement(
    data: ImprovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add capitalized improvement to asset."""
    # Implementation for improvement
    raise HTTPException(status_code=501, detail="Not implemented")


# ==================== Disposals ====================

@router.get("/disposals", response_model=dict)
async def get_disposals(
    status: Optional[str] = None,
    disposal_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get asset disposals."""
    service = DisposalService(db, current_user.customer_id)
    disposals, total = await service.get_disposals(
        status, disposal_type, date_from, date_to, skip, limit
    )

    return {
        "items": [DisposalResponse.model_validate(d, from_attributes=True) for d in disposals],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/disposals/{disposal_id}", response_model=DisposalResponse)
async def get_disposal(
    disposal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get disposal by ID."""
    service = DisposalService(db, current_user.customer_id)
    try:
        return await service.get_disposal_by_id(disposal_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/disposals", response_model=DisposalResponse, status_code=status.HTTP_201_CREATED)
async def create_disposal(
    data: DisposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create asset disposal."""
    service = DisposalService(db, current_user.customer_id)
    try:
        return await service.create_disposal(data, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disposals/{disposal_id}/approve", response_model=DisposalResponse)
async def approve_disposal(
    disposal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve disposal."""
    service = DisposalService(db, current_user.customer_id)
    try:
        return await service.approve_disposal(disposal_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disposals/{disposal_id}/post", response_model=DisposalResponse)
async def post_disposal(
    disposal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Post disposal to general ledger."""
    service = DisposalService(db, current_user.customer_id)
    try:
        return await service.post_disposal(disposal_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disposals/{disposal_id}/cancel", response_model=DisposalResponse)
async def cancel_disposal(
    disposal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel disposal."""
    service = DisposalService(db, current_user.customer_id)
    try:
        return await service.cancel_disposal(disposal_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
