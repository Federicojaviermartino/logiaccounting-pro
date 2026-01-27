"""API routes for time off management."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_permissions
from app.auth.models import User
from app.payroll.models.time_off import TimeOffRequest, TimeOffBalance, TimeOffStatus, TimeOffType
from app.payroll.schemas.time_off import (
    TimeOffRequestCreate, TimeOffRequestUpdate, TimeOffRequestResponse,
    TimeOffReview, TimeOffBalanceResponse, TimeOffBalanceAdjust
)
from app.core.exceptions import NotFoundError, BusinessRuleError

router = APIRouter(prefix="/time-off", tags=["Time Off"])


# ==========================================
# TIME OFF REQUESTS
# ==========================================

@router.get("/requests", response_model=dict)
async def get_time_off_requests(
    employee_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get time off requests."""
    query = select(TimeOffRequest).where(
        TimeOffRequest.customer_id == current_user.customer_id
    )

    if employee_id:
        query = query.where(TimeOffRequest.employee_id == employee_id)
    if status:
        query = query.where(TimeOffRequest.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    query = query.order_by(TimeOffRequest.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = db.execute(query)
    requests = result.scalars().all()

    return {
        "items": [TimeOffRequestResponse.model_validate(r) for r in requests],
        "total": total, "skip": skip, "limit": limit
    }


@router.get("/requests/{request_id}", response_model=TimeOffRequestResponse)
async def get_time_off_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get time off request by ID."""
    request = db.get(TimeOffRequest, request_id)
    if not request or request.customer_id != current_user.customer_id:
        raise NotFoundError(f"Time off request not found: {request_id}")
    return request


@router.post("/requests", response_model=TimeOffRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_time_off_request(
    employee_id: UUID,
    data: TimeOffRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create time off request."""
    # Generate request number
    count = db.execute(
        select(func.count(TimeOffRequest.id)).where(
            TimeOffRequest.customer_id == current_user.customer_id
        )
    ).scalar() or 0

    request = TimeOffRequest(
        customer_id=current_user.customer_id,
        employee_id=employee_id,
        request_number=f"TO-{datetime.now().year}-{(count + 1):05d}",
        time_off_type=TimeOffType(data.time_off_type),
        start_date=data.start_date,
        end_date=data.end_date,
        hours_requested=data.hours_requested,
        start_time=data.start_time,
        end_time=data.end_time,
        reason=data.reason,
    )

    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.post("/requests/{request_id}/review", response_model=TimeOffRequestResponse)
async def review_time_off_request(
    request_id: UUID,
    data: TimeOffReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["employees.manage_time_off"]))
):
    """Approve or reject time off request."""
    request = db.get(TimeOffRequest, request_id)
    if not request or request.customer_id != current_user.customer_id:
        raise NotFoundError(f"Time off request not found: {request_id}")

    if request.status != TimeOffStatus.PENDING:
        raise BusinessRuleError("Request is not pending")

    request.status = TimeOffStatus.APPROVED if data.action == "approve" else TimeOffStatus.REJECTED
    request.reviewed_by = current_user.id
    request.reviewed_at = datetime.utcnow()
    request.review_notes = data.notes

    # Update balance if approved
    if request.status == TimeOffStatus.APPROVED:
        balance = db.execute(
            select(TimeOffBalance).where(
                TimeOffBalance.employee_id == request.employee_id,
                TimeOffBalance.year == request.start_date.year,
                TimeOffBalance.time_off_type == request.time_off_type
            )
        ).scalar_one_or_none()

        if balance:
            balance.hours_pending += request.hours_requested

    db.commit()
    db.refresh(request)
    return request


@router.post("/requests/{request_id}/cancel", response_model=TimeOffRequestResponse)
async def cancel_time_off_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel time off request."""
    request = db.get(TimeOffRequest, request_id)
    if not request or request.customer_id != current_user.customer_id:
        raise NotFoundError(f"Time off request not found: {request_id}")

    if request.status not in (TimeOffStatus.PENDING, TimeOffStatus.APPROVED):
        raise BusinessRuleError("Cannot cancel this request")

    request.status = TimeOffStatus.CANCELLED
    db.commit()
    db.refresh(request)
    return request


# ==========================================
# TIME OFF BALANCES
# ==========================================

@router.get("/balances/{employee_id}", response_model=List[TimeOffBalanceResponse])
async def get_time_off_balances(
    employee_id: UUID,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employee time off balances."""
    query = select(TimeOffBalance).where(
        TimeOffBalance.employee_id == employee_id
    )

    if year:
        query = query.where(TimeOffBalance.year == year)

    result = db.execute(query)
    return result.scalars().all()


@router.post("/balances/{employee_id}/adjust", response_model=TimeOffBalanceResponse)
async def adjust_time_off_balance(
    employee_id: UUID,
    time_off_type: str,
    year: int,
    data: TimeOffBalanceAdjust,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions(["employees.manage_time_off"]))
):
    """Adjust employee time off balance."""
    balance = db.execute(
        select(TimeOffBalance).where(
            TimeOffBalance.employee_id == employee_id,
            TimeOffBalance.year == year,
            TimeOffBalance.time_off_type == time_off_type
        )
    ).scalar_one_or_none()

    if not balance:
        raise NotFoundError("Time off balance not found")

    balance.adjustments += data.adjustment
    db.commit()
    db.refresh(balance)
    return balance
