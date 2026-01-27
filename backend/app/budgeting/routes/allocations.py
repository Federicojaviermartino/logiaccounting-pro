"""API routes for budget allocation."""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_permissions
from app.auth.models import User
from app.budgeting.services.allocation_service import AllocationService
from app.budgeting.schemas.budget_line import (
    BudgetLineCreate, BudgetLineUpdate, BudgetLineResponse,
    BudgetPeriodResponse
)

router = APIRouter(tags=["Budget Allocations"])


@router.get("/versions/{version_id}/lines", response_model=List[BudgetLineResponse])
async def get_budget_lines(
    version_id: UUID,
    account_type: Optional[str] = None,
    department_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get budget lines for a version."""
    service = AllocationService(db, current_user.customer_id)
    return await service.get_lines(version_id, account_type, department_id)


@router.post("/versions/{version_id}/lines", response_model=BudgetLineResponse, status_code=status.HTTP_201_CREATED)
async def create_budget_line(
    version_id: UUID,
    data: BudgetLineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Create budget line."""
    service = AllocationService(db, current_user.customer_id)
    return await service.create_budget_line(version_id, data)


@router.put("/lines/{line_id}", response_model=BudgetLineResponse)
async def update_budget_line(
    line_id: UUID,
    data: BudgetLineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Update budget line."""
    service = AllocationService(db, current_user.customer_id)
    return await service.update_budget_line(line_id, data)


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget_line(
    line_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Delete budget line."""
    service = AllocationService(db, current_user.customer_id)
    await service.delete_budget_line(line_id)


@router.get("/lines/{line_id}/periods", response_model=List[BudgetPeriodResponse])
async def get_line_periods(
    line_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get periods for a budget line."""
    service = AllocationService(db, current_user.customer_id)
    return await service.get_line_periods(line_id)


@router.put("/periods/{period_id}", response_model=BudgetPeriodResponse)
async def update_period(
    period_id: UUID,
    amount: Decimal = Query(..., ge=0),
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Update single period amount."""
    service = AllocationService(db, current_user.customer_id)
    return await service.update_period(period_id, amount, notes)


@router.post("/lines/{line_id}/distribute", response_model=BudgetLineResponse)
async def distribute_line(
    line_id: UUID,
    method: str = Query("equal", pattern="^(equal|seasonal|manual)$"),
    pattern_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Redistribute budget line across periods."""
    service = AllocationService(db, current_user.customer_id)
    return await service.redistribute_line(line_id, method, pattern_id)
