"""API routes for budget management."""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_permissions
from app.auth.models import User
from app.budgeting.services.budget_service import BudgetService
from app.budgeting.schemas.budget import (
    BudgetCreate, BudgetUpdate, BudgetResponse, BudgetSummary,
    VersionCreate, VersionResponse
)

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("", response_model=dict)
async def get_budgets(
    fiscal_year: Optional[int] = None,
    status: Optional[str] = None,
    department_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get budgets with filtering."""
    service = BudgetService(db, current_user.customer_id)
    budgets, total = await service.get_budgets(
        fiscal_year=fiscal_year, status=status,
        department_id=department_id, skip=skip, limit=limit
    )
    return {
        "items": [BudgetSummary.model_validate(b) for b in budgets],
        "total": total, "skip": skip, "limit": limit
    }


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: UUID,
    include_versions: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get budget by ID."""
    service = BudgetService(db, current_user.customer_id)
    return await service.get_budget_by_id(budget_id, include_versions)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.create"]))
):
    """Create new budget."""
    service = BudgetService(db, current_user.customer_id)
    return await service.create_budget(data, current_user.id)


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Update budget."""
    service = BudgetService(db, current_user.customer_id)
    return await service.update_budget(budget_id, data)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.delete"]))
):
    """Delete draft budget."""
    service = BudgetService(db, current_user.customer_id)
    await service.delete_budget(budget_id)


@router.get("/{budget_id}/versions", response_model=List[VersionResponse])
async def get_versions(
    budget_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all versions for a budget."""
    service = BudgetService(db, current_user.customer_id)
    budget = await service.get_budget_by_id(budget_id, include_versions=True)
    return budget.versions


@router.post("/{budget_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    budget_id: UUID,
    data: VersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Create new budget version."""
    service = BudgetService(db, current_user.customer_id)
    return await service.create_version(budget_id, data, current_user.id)


@router.post("/versions/{version_id}/submit", response_model=VersionResponse)
async def submit_version(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Submit version for approval."""
    service = BudgetService(db, current_user.customer_id)
    return await service.submit_version(version_id, current_user.id)


@router.post("/versions/{version_id}/approve", response_model=VersionResponse)
async def approve_version(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.approve"]))
):
    """Approve submitted version."""
    service = BudgetService(db, current_user.customer_id)
    return await service.approve_version(version_id, current_user.id)


@router.post("/versions/{version_id}/reject", response_model=VersionResponse)
async def reject_version(
    version_id: UUID,
    reason: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.approve"]))
):
    """Reject submitted version."""
    service = BudgetService(db, current_user.customer_id)
    return await service.reject_version(version_id, current_user.id, reason)


@router.post("/versions/{version_id}/activate", response_model=VersionResponse)
async def activate_version(
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.approve"]))
):
    """Set version as active."""
    service = BudgetService(db, current_user.customer_id)
    return await service.activate_version(version_id, current_user.id)
