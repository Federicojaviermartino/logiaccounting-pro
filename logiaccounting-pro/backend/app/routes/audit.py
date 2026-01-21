"""
Audit & Compliance Routes - Phase 15
Enterprise Audit Trail, Compliance & Regulatory Framework
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse

from app.utils.auth import require_roles
from app.services.audit import (
    AuditService, audit_service, log_audit,
    AlertService, ReportService,
    EVENT_REGISTRY, get_event_type, EventCategory
)
from app.models.audit_store import audit_db
from app.schemas.audit_schemas import (
    AuditLogListResponse, AuditLogDetailResponse,
    ChangeHistoryListResponse, VersionDiffResponse,
    AlertListResponse, AlertResolveRequest,
    AlertRuleCreate, AlertRuleUpdate, AlertRuleListResponse,
    IntegrityStatusResponse, IntegrityVerifyRequest, IntegrityVerifyResponse,
    ReportListResponse, ReportGenerateRequest, ReportResponse,
    AuditStatisticsResponse, ExportRequest,
    RetentionPolicyCreate, RetentionPolicyUpdate, RetentionPolicyListResponse
)

router = APIRouter()


# ==================== Audit Logs ====================

@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    event_type: Optional[str] = None,
    event_category: Optional[str] = None,
    severity: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    compliance_tag: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """
    List audit logs with filtering and pagination.
    Requires admin or auditor role.
    """
    org_id = current_user.get("organization_id", "default")

    filters = {"organization_id": org_id}

    if event_type:
        filters["event_type"] = event_type
    if event_category:
        filters["event_category"] = event_category
    if severity:
        filters["severity"] = severity
    if entity_type:
        filters["entity_type"] = entity_type
    if entity_id:
        filters["entity_id"] = entity_id
    if user_id:
        filters["user_id"] = user_id
    if action:
        filters["action"] = action
    if from_date:
        filters["from_date"] = from_date
    if to_date:
        filters["to_date"] = to_date

    logs = audit_db.audit_logs.find_all(filters, limit=limit, offset=offset)
    total = audit_db.audit_logs.count(filters)

    # Filter by compliance tag if specified
    if compliance_tag:
        logs = [
            log for log in logs
            if compliance_tag in (log.get("compliance_tags") or [])
        ]

    return {
        "success": True,
        "logs": logs,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    }


@router.get("/logs/{log_id}", response_model=AuditLogDetailResponse)
async def get_audit_log(
    log_id: str,
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Get a specific audit log entry by ID"""
    log = audit_db.audit_logs.find_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return {"success": True, "log": log}


@router.get("/logs/entity/{entity_type}/{entity_id}")
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: str,
    limit: int = Query(default=100, le=500),
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Get complete audit trail for a specific entity"""
    org_id = current_user.get("organization_id", "default")

    filters = {
        "organization_id": org_id,
        "entity_type": entity_type,
        "entity_id": entity_id
    }

    logs = audit_db.audit_logs.find_all(filters, limit=limit)

    return {
        "success": True,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "audit_trail": logs
    }


@router.get("/logs/user/{user_id}")
async def get_user_audit_trail(
    user_id: str,
    days: int = Query(default=30, le=365),
    limit: int = Query(default=200, le=1000),
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Get audit trail for a specific user"""
    org_id = current_user.get("organization_id", "default")
    from_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

    filters = {
        "organization_id": org_id,
        "user_id": user_id,
        "from_date": from_date
    }

    logs = audit_db.audit_logs.find_all(filters, limit=limit)

    return {
        "success": True,
        "user_id": user_id,
        "period_days": days,
        "activity": logs
    }


# ==================== Change History ====================

@router.get("/changes/{entity_type}/{entity_id}", response_model=ChangeHistoryListResponse)
async def get_change_history(
    entity_type: str,
    entity_id: str,
    limit: int = Query(default=50, le=200),
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Get version history for an entity"""
    versions = audit_db.change_history.find_entity_history(
        entity_type, entity_id, limit=limit
    )

    return {
        "success": True,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "versions": versions
    }


@router.get("/changes/{entity_type}/{entity_id}/diff", response_model=VersionDiffResponse)
async def get_version_diff(
    entity_type: str,
    entity_id: str,
    v1: int = Query(..., description="First version number"),
    v2: int = Query(..., description="Second version number"),
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Compare two versions of an entity"""
    diff = audit_db.change_history.get_version_diff(entity_type, entity_id, v1, v2)

    if not diff:
        raise HTTPException(status_code=404, detail="Versions not found")

    return {
        "success": True,
        "v1": v1,
        "v2": v2,
        "diff": diff
    }


@router.get("/changes/{entity_type}/{entity_id}/version/{version}")
async def get_specific_version(
    entity_type: str,
    entity_id: str,
    version: int,
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Get a specific version snapshot of an entity"""
    versions = audit_db.change_history.find_entity_history(entity_type, entity_id)

    for v in versions:
        if v.get("version_number") == version:
            return {"success": True, "version": v}

    raise HTTPException(status_code=404, detail="Version not found")


# ==================== Integrity Verification ====================

@router.get("/integrity/status", response_model=IntegrityStatusResponse)
async def get_integrity_status(
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Get current integrity status of audit log chain"""
    org_id = current_user.get("organization_id", "default")
    status = audit_db.audit_logs.get_integrity_status(org_id)
    return {"success": True, "status": status}


@router.post("/integrity/verify", response_model=IntegrityVerifyResponse)
async def verify_integrity(
    request: IntegrityVerifyRequest,
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Verify integrity of audit log chain within a range"""
    org_id = current_user.get("organization_id", "default")

    result = audit_db.audit_logs.verify_chain_integrity(
        org_id,
        start_sequence=request.start_sequence,
        end_sequence=request.end_sequence
    )

    return {
        "success": True,
        "is_valid": result["is_valid"],
        "issues_count": len(result.get("issues", [])),
        "issues": result.get("issues", [])
    }


# ==================== Alerts ====================

@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """List security and compliance alerts"""
    org_id = current_user.get("organization_id", "default")

    filters = {"organization_id": org_id}
    if status:
        filters["status"] = status
    if severity:
        filters["severity"] = severity
    if alert_type:
        filters["alert_type"] = alert_type

    alerts = audit_db.alerts.find_all(filters, limit=limit)

    return {"success": True, "alerts": alerts}


@router.get("/alerts/{alert_id}")
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Get specific alert details"""
    alert = audit_db.alerts.find_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"success": True, "alert": alert}


@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Acknowledge an alert"""
    org_id = current_user.get("organization_id", "default")
    alert_service = AlertService(org_id)

    result = alert_service.acknowledge_alert(
        alert_id,
        current_user.get("id")
    )

    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"success": True, "alert": result}


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: AlertResolveRequest,
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Resolve an alert with notes"""
    org_id = current_user.get("organization_id", "default")
    alert_service = AlertService(org_id)

    result = alert_service.resolve_alert(
        alert_id,
        current_user.get("id"),
        request.notes
    )

    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"success": True, "alert": result}


@router.put("/alerts/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: str,
    request: AlertResolveRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Dismiss an alert (admin only)"""
    org_id = current_user.get("organization_id", "default")
    alert_service = AlertService(org_id)

    result = alert_service.dismiss_alert(
        alert_id,
        current_user.get("id"),
        request.notes
    )

    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"success": True, "alert": result}


# ==================== Alert Rules ====================

@router.get("/alert-rules", response_model=AlertRuleListResponse)
async def list_alert_rules(
    is_active: Optional[bool] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """List alert rules"""
    org_id = current_user.get("organization_id", "default")

    filters = {"organization_id": org_id}
    if is_active is not None:
        filters["is_active"] = is_active

    rules = audit_db.alert_rules.find_all(filters)

    return {"success": True, "rules": rules}


@router.post("/alert-rules")
async def create_alert_rule(
    rule: AlertRuleCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new alert rule"""
    org_id = current_user.get("organization_id", "default")
    alert_service = AlertService(org_id)

    new_rule = alert_service.create_rule(rule.model_dump())

    log_audit(
        event_type="alert_rule.created",
        entity_type="alert_rule",
        entity_id=new_rule["id"],
        action="create",
        user_id=current_user.get("id"),
        organization_id=org_id
    )

    return {"success": True, "rule": new_rule}


@router.put("/alert-rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    rule: AlertRuleUpdate,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update an alert rule"""
    existing = audit_db.alert_rules.find_by_id(rule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Rule not found")

    updates = {k: v for k, v in rule.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.utcnow().isoformat()

    updated = audit_db.alert_rules.update(rule_id, updates)

    log_audit(
        event_type="alert_rule.updated",
        entity_type="alert_rule",
        entity_id=rule_id,
        action="update",
        user_id=current_user.get("id"),
        organization_id=current_user.get("organization_id", "default"),
        changes=updates
    )

    return {"success": True, "rule": updated}


@router.delete("/alert-rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete an alert rule"""
    existing = audit_db.alert_rules.find_by_id(rule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Rule not found")

    audit_db.alert_rules.delete(rule_id)

    log_audit(
        event_type="alert_rule.deleted",
        entity_type="alert_rule",
        entity_id=rule_id,
        action="delete",
        user_id=current_user.get("id"),
        organization_id=current_user.get("organization_id", "default")
    )

    return {"success": True, "message": "Rule deleted"}


# ==================== Statistics ====================

@router.get("/statistics", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    days: int = Query(default=30, le=365),
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Get audit log statistics"""
    org_id = current_user.get("organization_id", "default")
    service = AuditService(org_id, current_user.get("id"))

    stats = service.get_statistics(days)

    return {
        "success": True,
        "period_days": days,
        "statistics": stats
    }


# ==================== Export ====================

@router.post("/export")
async def export_audit_logs(
    request: ExportRequest,
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Export audit logs to CSV, Excel, or JSON"""
    org_id = current_user.get("organization_id", "default")
    service = AuditService(org_id, current_user.get("id"))

    filters = request.filters or {}
    filters["organization_id"] = org_id

    if request.format == "csv":
        content = service.export_to_csv(filters)
        return StreamingResponse(
            content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
        )
    elif request.format == "excel":
        content = service.export_to_excel(filters)
        return StreamingResponse(
            content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=audit_logs.xlsx"}
        )
    else:
        data = service.export_to_json(filters)
        return {"success": True, "data": data}


# ==================== Reports ====================

@router.get("/reports", response_model=ReportListResponse)
async def list_available_reports(
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """List available report types"""
    reports = ReportService.get_available_reports()
    return {"success": True, "reports": reports}


@router.post("/reports/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerateRequest,
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """Generate an audit or compliance report"""
    org_id = current_user.get("organization_id", "default")
    report_service = ReportService(org_id)

    params = request.parameters or {}

    if request.report_type == "compliance_summary":
        framework = params.get("framework", "sox")
        report = report_service.generate_compliance_report(framework)
    elif request.report_type == "activity_summary":
        start = datetime.fromisoformat(params.get("start_date", (datetime.utcnow() - timedelta(days=30)).isoformat()))
        end = datetime.fromisoformat(params.get("end_date", datetime.utcnow().isoformat()))
        report = report_service.generate_activity_report(start, end)
    elif request.report_type == "access_review":
        start = datetime.fromisoformat(params.get("start_date", (datetime.utcnow() - timedelta(days=30)).isoformat()))
        end = datetime.fromisoformat(params.get("end_date", datetime.utcnow().isoformat()))
        report = report_service.generate_access_report(start, end)
    elif request.report_type == "change_report":
        entity_type = params.get("entity_type", "transaction")
        entity_id = params.get("entity_id")
        report = report_service.generate_change_report(entity_type, entity_id)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {request.report_type}")

    # Return in requested format
    if request.format == "pdf":
        pdf_buffer = report_service.generate_pdf_report(report)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={request.report_type}.pdf"}
        )
    elif request.format == "excel":
        excel_buffer = report_service.generate_excel_report(report)
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={request.report_type}.xlsx"}
        )

    return {"success": True, "report": report}


# ==================== Retention Policies ====================

@router.get("/retention-policies", response_model=RetentionPolicyListResponse)
async def list_retention_policies(
    current_user: dict = Depends(require_roles("admin"))
):
    """List data retention policies"""
    org_id = current_user.get("organization_id", "default")

    policies = audit_db.retention_policies.find_all({"organization_id": org_id})

    return {"success": True, "policies": policies}


@router.post("/retention-policies")
async def create_retention_policy(
    policy: RetentionPolicyCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a data retention policy"""
    org_id = current_user.get("organization_id", "default")

    now = datetime.utcnow().isoformat()
    policy_data = policy.model_dump()
    policy_data["organization_id"] = org_id
    policy_data["created_at"] = now
    policy_data["updated_at"] = now

    new_policy = audit_db.retention_policies.create(policy_data)

    log_audit(
        event_type="retention_policy.created",
        entity_type="retention_policy",
        entity_id=new_policy["id"],
        action="create",
        user_id=current_user.get("id"),
        organization_id=org_id
    )

    return {"success": True, "policy": new_policy}


@router.put("/retention-policies/{policy_id}")
async def update_retention_policy(
    policy_id: str,
    policy: RetentionPolicyUpdate,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a retention policy"""
    existing = audit_db.retention_policies.find_by_id(policy_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Policy not found")

    updates = {k: v for k, v in policy.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.utcnow().isoformat()

    updated = audit_db.retention_policies.update(policy_id, updates)

    return {"success": True, "policy": updated}


@router.delete("/retention-policies/{policy_id}")
async def delete_retention_policy(
    policy_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a retention policy"""
    existing = audit_db.retention_policies.find_by_id(policy_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Policy not found")

    if existing.get("legal_hold"):
        raise HTTPException(
            status_code=400,
            detail="Cannot delete policy with legal hold active"
        )

    audit_db.retention_policies.delete(policy_id)

    return {"success": True, "message": "Policy deleted"}


# ==================== Event Types ====================

@router.get("/event-types")
async def list_event_types(
    category: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "auditor"))
):
    """List available audit event types"""
    from app.services.audit.event_types import get_all_event_types, get_event_types_by_category

    if category:
        try:
            cat = EventCategory(category)
            events = get_event_types_by_category(cat)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    else:
        events = get_all_event_types()

    return {
        "success": True,
        "event_types": [
            {
                "name": et.name,
                "category": et.category.value,
                "severity": et.default_severity.value,
                "description": et.description,
                "compliance_tags": et.compliance_tags
            }
            for et in events
        ]
    }


# ==================== Legacy Compatibility ====================
# Keep backward compatibility with Phase 7 audit endpoints

@router.get("/actions")
async def get_action_types():
    """Get available action types (legacy)"""
    from app.services.audit.event_types import Action
    return {"actions": [a.value for a in Action]}


@router.get("/entities")
async def get_entity_types():
    """Get available entity types (legacy)"""
    return {
        "entities": [
            "transaction", "invoice", "payment", "user", "project",
            "inventory", "document", "report", "integration", "settings"
        ]
    }


@router.get("")
async def search_logs_legacy(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    ip_address: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: dict = Depends(require_roles("admin"))
):
    """Search audit logs (legacy endpoint)"""
    return await list_audit_logs(
        event_type=None,
        event_category=None,
        severity=None,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        action=action,
        compliance_tag=None,
        from_date=date_from,
        to_date=date_to,
        limit=limit,
        offset=offset,
        current_user=current_user
    )
