"""Dashboard and KPI API routes."""
from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.reporting.services.kpi_service import KPIService
from app.reporting.schemas.kpi import KPIValue, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    as_of_date: Optional[date] = Query(None, description="As of date (defaults to today)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get executive dashboard summary with KPIs."""
    service = KPIService(db, current_user.customer_id)
    return await service.get_dashboard_summary(as_of_date)


@router.get("/kpis", response_model=List[KPIValue])
async def get_kpis(
    as_of_date: Optional[date] = Query(None, description="As of date (defaults to today)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all KPIs."""
    service = KPIService(db, current_user.customer_id)
    kpis = await service.calculate_all_kpis(as_of_date or date.today())
    
    if category:
        kpis = [k for k in kpis if k.category == category]
    
    return kpis
