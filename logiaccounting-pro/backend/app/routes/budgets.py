"""
Budget Management routes
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.budget_service import budget_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class CreateBudgetRequest(BaseModel):
    name: str
    amount: float
    period: str
    start_date: str
    category_id: Optional[str] = None
    project_id: Optional[str] = None
    alerts: Optional[List[dict]] = None


class UpdateBudgetRequest(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    period: Optional[str] = None
    start_date: Optional[str] = None
    category_id: Optional[str] = None
    project_id: Optional[str] = None
    active: Optional[bool] = None


@router.get("")
async def list_budgets(
    active_only: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """List all budgets"""
    return {"budgets": budget_service.list_budgets(active_only)}


@router.get("/summary")
async def get_summary(current_user: dict = Depends(get_current_user)):
    """Get budget summary"""
    return budget_service.get_budget_summary()


@router.post("")
async def create_budget(
    request: CreateBudgetRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new budget"""
    return budget_service.create_budget(
        name=request.name,
        amount=request.amount,
        period=request.period,
        start_date=request.start_date,
        category_id=request.category_id,
        project_id=request.project_id,
        alerts=request.alerts,
        created_by=current_user["id"]
    )


@router.get("/{budget_id}")
async def get_budget(
    budget_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific budget"""
    budget = budget_service.get_budget(budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget


@router.put("/{budget_id}")
async def update_budget(
    budget_id: str,
    request: UpdateBudgetRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a budget"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    budget = budget_service.update_budget(budget_id, updates)

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    return budget


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a budget"""
    if budget_service.delete_budget(budget_id):
        return {"message": "Budget deleted"}
    raise HTTPException(status_code=404, detail="Budget not found")


@router.get("/{budget_id}/variance")
async def get_variance(
    budget_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get variance report for a budget"""
    return budget_service.get_variance_report(budget_id)
