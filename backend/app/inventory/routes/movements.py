"""Movement API Routes"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.inventory.movements import (
    MovementService, get_movement_service,
    ReceiptCreate, IssueCreate, TransferCreate, AdjustmentCreate, MovementFilter
)

router = APIRouter(prefix="/movements", tags=["Inventory - Movements"])


@router.get("")
def list_movements(
    product_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    movement_type: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_movement_service(db)
    filters = MovementFilter(
        product_id=product_id, warehouse_id=warehouse_id,
        movement_type=movement_type, status=status,
        date_from=date_from, date_to=date_to
    )
    movements, total = service.get_movements(user.customer_id, filters, page, page_size)
    return {
        "movements": [m.to_dict() for m in movements],
        "total": total,
    }


@router.post("/receipt")
def create_receipt(
    data: ReceiptCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_movement_service(db)
    try:
        movement = service.create_receipt(user.customer_id, data, user.id)
        return movement.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/issue")
def create_issue(
    data: IssueCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_movement_service(db)
    try:
        movement = service.create_issue(user.customer_id, data, user.id)
        return movement.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/transfer")
def create_transfer(
    data: TransferCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_movement_service(db)
    try:
        movement = service.create_transfer(user.customer_id, data, user.id)
        return movement.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/adjustment")
def create_adjustment(
    data: AdjustmentCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_movement_service(db)
    try:
        movement = service.create_adjustment(user.customer_id, data, user.id)
        return movement.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{movement_id}/confirm")
def confirm_movement(
    movement_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_movement_service(db)
    try:
        movement = service.confirm_movement(movement_id, user.id)
        return movement.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{movement_id}/cancel")
def cancel_movement(
    movement_id: UUID,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_movement_service(db)
    try:
        movement = service.cancel_movement(movement_id, reason)
        return movement.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))
