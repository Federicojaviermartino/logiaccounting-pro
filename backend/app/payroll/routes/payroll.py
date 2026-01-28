"""API routes for payroll processing."""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_permissions
from app.auth.models import User
from app.payroll.services.payroll_service import PayrollService
from app.payroll.schemas.payroll import (
    PayPeriodCreate, PayPeriodResponse,
    PayrollRunCreate, PayrollRunResponse, PayrollRunWithLines
)

router = APIRouter(prefix="/payroll", tags=["Payroll"])


# ==========================================
# PAY PERIODS
# ==========================================

@router.get("/periods", response_model=List[PayPeriodResponse])
def get_pay_periods(
    year: Optional[int] = None,
    frequency: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pay periods."""
    service = PayrollService(db, current_user.customer_id)
    return service.get_pay_periods(year, frequency, status)


@router.post("/periods", response_model=PayPeriodResponse, status_code=status.HTTP_201_CREATED)
def create_pay_period(
    data: PayPeriodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["payroll.manage"]))
):
    """Create pay period."""
    service = PayrollService(db, current_user.customer_id)
    return service.create_pay_period(
        data.frequency, data.start_date, data.end_date, data.pay_date
    )


# ==========================================
# PAYROLL RUNS
# ==========================================

@router.get("/runs", response_model=dict)
def get_payroll_runs(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payroll runs."""
    service = PayrollService(db, current_user.customer_id)
    runs, total = service.get_payroll_runs(status, skip, limit)
    return {
        "items": [PayrollRunResponse.model_validate(r) for r in runs],
        "total": total, "skip": skip, "limit": limit
    }


@router.get("/runs/{run_id}", response_model=PayrollRunWithLines)
def get_payroll_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get payroll run with employee lines."""
    service = PayrollService(db, current_user.customer_id)
    return service.get_payroll_run_details(run_id)


@router.post("/runs", response_model=PayrollRunResponse, status_code=status.HTTP_201_CREATED)
def create_payroll_run(
    data: PayrollRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["payroll.run"]))
):
    """Create payroll run."""
    service = PayrollService(db, current_user.customer_id)
    return service.create_payroll_run(data.pay_period_id, data.run_type, current_user.id)


@router.post("/runs/{run_id}/calculate", response_model=PayrollRunResponse)
def calculate_payroll(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["payroll.run"]))
):
    """Calculate payroll for all employees."""
    service = PayrollService(db, current_user.customer_id)
    return service.calculate_payroll(run_id)


@router.post("/runs/{run_id}/approve", response_model=PayrollRunResponse)
def approve_payroll(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["payroll.approve"]))
):
    """Approve payroll run."""
    service = PayrollService(db, current_user.customer_id)
    return service.approve_payroll(run_id, current_user.id)


@router.post("/runs/{run_id}/process", response_model=PayrollRunResponse)
def process_payments(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["payroll.process"]))
):
    """Process payments for approved payroll."""
    service = PayrollService(db, current_user.customer_id)
    return service.process_payments(run_id)
