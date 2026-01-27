"""Audit log API routes."""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.audit.services.audit_service import AuditService
from app.audit.schemas.audit import (
    AuditLogResponse, AuditLogDetail, AuditLogFilter, AuditSummary,
    DataChangeResponse, EntitySnapshotResponse
)

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=dict)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    severity: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit logs with filtering and pagination."""
    service = AuditService(db)
    
    filters = AuditLogFilter(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        action=action,
        severity=severity,
        resource_type=resource_type,
        resource_id=resource_id,
        search=search
    )
    
    logs, total = await service.get_logs(
        customer_id=current_user.customer_id,
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    return {
        "items": [AuditLogResponse.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/logs/{log_id}", response_model=AuditLogDetail)
async def get_audit_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific audit log entry with full details."""
    service = AuditService(db)
    log = await service.get_log_by_id(current_user.customer_id, log_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return AuditLogDetail.model_validate(log)


@router.get("/entity/{resource_type}/{resource_id}/history", response_model=List[AuditLogResponse])
async def get_entity_history(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete audit history for an entity."""
    service = AuditService(db)
    logs = await service.get_entity_history(
        customer_id=current_user.customer_id,
        resource_type=resource_type,
        resource_id=resource_id
    )
    
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/user/{user_id}/activity", response_model=List[AuditLogResponse])
async def get_user_activity(
    user_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user activity for the specified period."""
    service = AuditService(db)
    logs = await service.get_user_activity(
        customer_id=current_user.customer_id,
        user_id=user_id,
        days=days
    )
    
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/summary", response_model=AuditSummary)
async def get_audit_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit summary for a period."""
    service = AuditService(db)
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    return await service.get_summary(
        customer_id=current_user.customer_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/actions", response_model=List[str])
async def get_available_actions():
    """Get list of available audit actions."""
    from app.audit.models.audit_log import AuditAction
    return [action.value for action in AuditAction]


@router.get("/resource-types", response_model=List[str])
async def get_resource_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of resource types that have audit logs."""
    from sqlalchemy import select, distinct
    from app.audit.models.audit_log import AuditLog
    
    query = select(distinct(AuditLog.resource_type)).where(
        AuditLog.customer_id == current_user.customer_id
    ).order_by(AuditLog.resource_type)
    
    result = db.execute(query)
    return [row[0] for row in result]
