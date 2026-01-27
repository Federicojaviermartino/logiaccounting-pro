"""Compliance management API routes."""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.audit.services.compliance_service import ComplianceService
from app.audit.schemas.compliance import (
    RetentionPolicyCreate, RetentionPolicyResponse,
    ComplianceRuleCreate, ComplianceRuleResponse,
    ComplianceViolationResponse, ViolationResolve,
    AccessLogResponse, ComplianceDashboard, AccessReport
)

router = APIRouter(prefix="/compliance", tags=["Compliance"])


# ==========================================
# DASHBOARD
# ==========================================

@router.get("/dashboard", response_model=ComplianceDashboard)
async def get_compliance_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get compliance dashboard summary."""
    service = ComplianceService(db)
    return await service.get_compliance_dashboard(current_user.customer_id)


# ==========================================
# RETENTION POLICIES
# ==========================================

@router.get("/retention-policies", response_model=List[RetentionPolicyResponse])
async def get_retention_policies(
    include_system: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all retention policies."""
    service = ComplianceService(db)
    policies = await service.get_retention_policies(
        customer_id=current_user.customer_id,
        include_system=include_system
    )
    return [RetentionPolicyResponse.model_validate(p) for p in policies]


@router.post("/retention-policies", response_model=RetentionPolicyResponse)
async def create_retention_policy(
    data: RetentionPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new retention policy."""
    service = ComplianceService(db)
    policy = await service.create_retention_policy(
        customer_id=current_user.customer_id,
        data=data
    )
    return RetentionPolicyResponse.model_validate(policy)


# ==========================================
# COMPLIANCE RULES
# ==========================================

@router.get("/rules", response_model=List[ComplianceRuleResponse])
async def get_compliance_rules(
    standard: Optional[str] = None,
    category: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get compliance rules."""
    service = ComplianceService(db)
    rules = await service.get_compliance_rules(
        customer_id=current_user.customer_id,
        standard=standard,
        category=category,
        active_only=active_only
    )
    return [ComplianceRuleResponse.model_validate(r) for r in rules]


@router.post("/rules", response_model=ComplianceRuleResponse)
async def create_compliance_rule(
    data: ComplianceRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new compliance rule."""
    service = ComplianceService(db)
    rule = await service.create_compliance_rule(
        customer_id=current_user.customer_id,
        data=data
    )
    return ComplianceRuleResponse.model_validate(rule)


# ==========================================
# VIOLATIONS
# ==========================================

@router.get("/violations", response_model=dict)
async def get_violations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    rule_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get compliance violations."""
    service = ComplianceService(db)
    violations, total = await service.get_violations(
        customer_id=current_user.customer_id,
        status=status,
        severity=severity,
        rule_id=rule_id,
        page=page,
        page_size=page_size
    )
    
    return {
        "items": [ComplianceViolationResponse.model_validate(v) for v in violations],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.put("/violations/{violation_id}/resolve", response_model=ComplianceViolationResponse)
async def resolve_violation(
    violation_id: UUID,
    data: ViolationResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve a compliance violation."""
    service = ComplianceService(db)
    violation = await service.resolve_violation(
        customer_id=current_user.customer_id,
        violation_id=violation_id,
        resolved_by=current_user.id,
        status=data.status,
        resolution_notes=data.resolution_notes
    )
    
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    
    return ComplianceViolationResponse.model_validate(violation)


# ==========================================
# ACCESS LOGS
# ==========================================

@router.get("/access-logs", response_model=dict)
async def get_access_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    data_classification: Optional[str] = None,
    contains_pii: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get access logs."""
    from sqlalchemy import select, func, desc
    from app.audit.models.compliance import AccessLog
    
    query = select(AccessLog).where(AccessLog.customer_id == current_user.customer_id)
    
    if user_id:
        query = query.where(AccessLog.user_id == user_id)
    if resource_type:
        query = query.where(AccessLog.resource_type == resource_type)
    if data_classification:
        query = query.where(AccessLog.data_classification == data_classification)
    if contains_pii is not None:
        query = query.where(AccessLog.contains_pii == contains_pii)
    if start_date:
        query = query.where(AccessLog.accessed_at >= start_date)
    if end_date:
        query = query.where(AccessLog.accessed_at <= end_date)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()
    
    query = query.order_by(desc(AccessLog.accessed_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = db.execute(query)
    logs = result.scalars().all()
    
    return {
        "items": [AccessLogResponse.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/access-report", response_model=AccessReport)
async def get_access_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate access report for a period."""
    service = ComplianceService(db)
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    return await service.get_access_report(
        customer_id=current_user.customer_id,
        start_date=start_date,
        end_date=end_date
    )


# ==========================================
# COMPLIANCE STANDARDS
# ==========================================

@router.get("/standards", response_model=List[dict])
async def get_compliance_standards():
    """Get available compliance standards."""
    from app.audit.models.compliance import ComplianceStandard
    return [
        {"code": standard.value, "name": standard.name}
        for standard in ComplianceStandard
    ]
