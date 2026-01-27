"""API routes for variance analysis."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_permissions
from app.auth.models import User
from app.budgeting.services.variance_service import VarianceService
from app.budgeting.schemas.variance import (
    VarianceThresholdCreate, VarianceThresholdUpdate, VarianceThresholdResponse,
    VarianceAlertResponse, AlertAcknowledge, AlertResolve, AlertSummary,
    BudgetVsActualReport
)

router = APIRouter(prefix="/variance", tags=["Variance Analysis"])


# ==========================================
# BUDGET VS ACTUAL
# ==========================================

@router.get("/budgets/{budget_id}/comparison", response_model=BudgetVsActualReport)
async def get_budget_vs_actual(
    budget_id: UUID,
    period_type: str = Query("ytd", pattern="^(monthly|quarterly|ytd|annual)$"),
    year: Optional[int] = None,
    month: Optional[int] = Query(None, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get budget vs actual comparison."""
    service = VarianceService(db, current_user.customer_id)
    return await service.get_budget_vs_actual(budget_id, period_type, year, month)


@router.post("/budgets/{budget_id}/update-actuals")
async def update_actuals_from_gl(
    budget_id: UUID,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Update budget periods with actuals from GL."""
    service = VarianceService(db, current_user.customer_id)
    updated = await service.update_actuals_from_gl(budget_id, year, month)
    return {"updated_periods": updated}


# ==========================================
# THRESHOLDS
# ==========================================

@router.get("/thresholds", response_model=list[VarianceThresholdResponse])
async def get_thresholds(
    budget_id: Optional[UUID] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get variance thresholds."""
    service = VarianceService(db, current_user.customer_id)
    return await service.get_thresholds(budget_id, active_only)


@router.post("/thresholds", response_model=VarianceThresholdResponse, status_code=status.HTTP_201_CREATED)
async def create_threshold(
    data: VarianceThresholdCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Create variance threshold."""
    service = VarianceService(db, current_user.customer_id)
    return await service.create_threshold(data)


@router.put("/thresholds/{threshold_id}", response_model=VarianceThresholdResponse)
async def update_threshold(
    threshold_id: UUID,
    data: VarianceThresholdUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Update variance threshold."""
    service = VarianceService(db, current_user.customer_id)
    return await service.update_threshold(threshold_id, data)


@router.delete("/thresholds/{threshold_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_threshold(
    threshold_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Delete variance threshold."""
    service = VarianceService(db, current_user.customer_id)
    await service.delete_threshold(threshold_id)


# ==========================================
# ALERTS
# ==========================================

@router.get("/alerts", response_model=dict)
async def get_alerts(
    budget_id: Optional[UUID] = None,
    status: Optional[str] = None,
    level: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get variance alerts."""
    service = VarianceService(db, current_user.customer_id)
    alerts, total = await service.get_alerts(
        budget_id=budget_id, status=status, level=level,
        skip=skip, limit=limit
    )
    return {
        "items": [VarianceAlertResponse.model_validate(a) for a in alerts],
        "total": total, "skip": skip, "limit": limit
    }


@router.get("/alerts/summary", response_model=AlertSummary)
async def get_alert_summary(
    budget_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get alert counts summary."""
    service = VarianceService(db, current_user.customer_id)
    return await service.get_alert_summary(budget_id)


@router.post("/alerts/{alert_id}/acknowledge", response_model=VarianceAlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    data: AlertAcknowledge = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert."""
    service = VarianceService(db, current_user.customer_id)
    notes = data.notes if data else None
    return await service.acknowledge_alert(alert_id, current_user.id, notes)


@router.post("/alerts/{alert_id}/resolve", response_model=VarianceAlertResponse)
async def resolve_alert(
    alert_id: UUID,
    data: AlertResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve an alert."""
    service = VarianceService(db, current_user.customer_id)
    return await service.resolve_alert(alert_id, current_user.id, data.resolution_notes)


@router.post("/alerts/{alert_id}/dismiss", response_model=VarianceAlertResponse)
async def dismiss_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["budgets.edit"]))
):
    """Dismiss an alert."""
    service = VarianceService(db, current_user.customer_id)
    return await service.dismiss_alert(alert_id)
