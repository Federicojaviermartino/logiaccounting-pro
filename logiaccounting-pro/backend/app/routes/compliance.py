"""
Compliance Routes - Phase 15
Enterprise Compliance Framework (SOX, GDPR, SOC 2, PCI-DSS, HIPAA)
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse

from app.utils.auth import require_roles
from app.services.audit import ComplianceService, ReportService, log_audit
from app.models.audit_store import audit_db
from app.schemas.audit_schemas import (
    ComplianceFrameworkResponse, FrameworkListResponse,
    ComplianceDashboardResponse
)

router = APIRouter()


# ==================== Compliance Frameworks ====================

@router.get("/frameworks", response_model=FrameworkListResponse)
async def list_frameworks(
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """List available compliance frameworks"""
    org_id = current_user.get("organization_id", "default")
    compliance_service = ComplianceService(org_id)

    frameworks = compliance_service.list_frameworks()

    return {"success": True, "frameworks": frameworks}


@router.get("/frameworks/{framework_id}", response_model=ComplianceFrameworkResponse)
async def get_framework_status(
    framework_id: str,
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """Get compliance status for a specific framework"""
    org_id = current_user.get("organization_id", "default")
    compliance_service = ComplianceService(org_id)

    result = compliance_service.run_framework_checks(framework_id)

    if not result.get("controls"):
        raise HTTPException(
            status_code=404,
            detail=f"Framework '{framework_id}' not found or not supported"
        )

    # Log compliance check
    log_audit(
        event_type="compliance.check_run",
        entity_type="compliance_framework",
        entity_id=framework_id,
        action="execute",
        user_id=current_user.get("id"),
        organization_id=org_id,
        metadata={
            "framework": framework_id,
            "overall_score": result["summary"]["overall_score"],
            "status": result["summary"]["status"]
        }
    )

    return {
        "success": True,
        "framework": framework_id,
        "summary": result["summary"],
        "controls": result["controls"]
    }


@router.post("/frameworks/{framework_id}/run")
async def run_compliance_check(
    framework_id: str,
    current_user: dict = Depends(require_roles("admin", "compliance"))
):
    """Run compliance checks for a framework"""
    org_id = current_user.get("organization_id", "default")
    compliance_service = ComplianceService(org_id)

    result = compliance_service.run_framework_checks(framework_id)

    if not result.get("controls"):
        raise HTTPException(
            status_code=404,
            detail=f"Framework '{framework_id}' not found or not supported"
        )

    # Store compliance check result
    check_data = {
        "organization_id": org_id,
        "framework_id": framework_id,
        "checked_at": datetime.utcnow().isoformat(),
        "summary": result["summary"],
        "controls": result["controls"],
        "initiated_by": current_user.get("id")
    }

    audit_db.compliance_checks.create(check_data)

    log_audit(
        event_type="compliance.check_run",
        entity_type="compliance_framework",
        entity_id=framework_id,
        action="execute",
        user_id=current_user.get("id"),
        organization_id=org_id,
        metadata={
            "framework": framework_id,
            "passed": result["summary"]["passed"],
            "failed": result["summary"]["failed"],
            "overall_score": result["summary"]["overall_score"]
        }
    )

    return {
        "success": True,
        "framework": framework_id,
        "summary": result["summary"],
        "controls": result["controls"]
    }


# ==================== Compliance Dashboard ====================

@router.get("/dashboard", response_model=ComplianceDashboardResponse)
async def get_compliance_dashboard(
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """Get compliance dashboard with all frameworks status"""
    org_id = current_user.get("organization_id", "default")
    compliance_service = ComplianceService(org_id)

    dashboard = compliance_service.get_compliance_dashboard()

    return {"success": True, "dashboard": dashboard}


@router.get("/dashboard/summary")
async def get_compliance_summary(
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """Get high-level compliance summary"""
    org_id = current_user.get("organization_id", "default")
    compliance_service = ComplianceService(org_id)

    dashboard = compliance_service.get_compliance_dashboard()

    # Calculate overall statistics
    total_controls = 0
    passed_controls = 0
    failed_controls = 0
    warning_controls = 0

    for fw_data in dashboard.get("frameworks", {}).values():
        summary = fw_data.get("summary", {})
        total_controls += summary.get("total_controls", 0)
        passed_controls += summary.get("passed", 0)
        failed_controls += summary.get("failed", 0)
        warning_controls += summary.get("warnings", 0)

    overall_score = (passed_controls / total_controls * 100) if total_controls > 0 else 0

    return {
        "success": True,
        "summary": {
            "total_frameworks": len(dashboard.get("frameworks", {})),
            "total_controls": total_controls,
            "passed_controls": passed_controls,
            "failed_controls": failed_controls,
            "warning_controls": warning_controls,
            "overall_score": round(overall_score, 1),
            "last_checked": dashboard.get("last_checked")
        }
    }


# ==================== Control Details ====================

@router.get("/controls/{framework_id}/{control_id}")
async def get_control_details(
    framework_id: str,
    control_id: str,
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """Get detailed information about a specific control"""
    org_id = current_user.get("organization_id", "default")
    compliance_service = ComplianceService(org_id)

    result = compliance_service.run_framework_checks(framework_id)

    if not result.get("controls"):
        raise HTTPException(
            status_code=404,
            detail=f"Framework '{framework_id}' not found"
        )

    # Find the specific control
    for control in result["controls"]:
        if control.get("control_id") == control_id:
            return {"success": True, "control": control}

    raise HTTPException(
        status_code=404,
        detail=f"Control '{control_id}' not found in framework '{framework_id}'"
    )


# ==================== Compliance History ====================

@router.get("/history")
async def get_compliance_history(
    framework_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """Get historical compliance check results"""
    org_id = current_user.get("organization_id", "default")

    filters = {"organization_id": org_id}
    if framework_id:
        filters["framework_id"] = framework_id

    checks = audit_db.compliance_checks.find_all(filters, limit=limit)

    return {
        "success": True,
        "history": checks
    }


@router.get("/history/{check_id}")
async def get_compliance_check(
    check_id: str,
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """Get a specific historical compliance check"""
    check = audit_db.compliance_checks.find_by_id(check_id)

    if not check:
        raise HTTPException(status_code=404, detail="Compliance check not found")

    return {"success": True, "check": check}


# ==================== Compliance Reports ====================

@router.get("/reports/{framework_id}")
async def generate_compliance_report(
    framework_id: str,
    format: str = Query(default="json", regex="^(json|pdf|excel)$"),
    include_evidence: bool = True,
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """Generate a compliance report for a framework"""
    org_id = current_user.get("organization_id", "default")
    report_service = ReportService(org_id)

    report = report_service.generate_compliance_report(
        framework_id,
        include_evidence=include_evidence
    )

    if format == "pdf":
        pdf_buffer = report_service.generate_pdf_report(report)
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=compliance_{framework_id}.pdf"
            }
        )
    elif format == "excel":
        excel_buffer = report_service.generate_excel_report(report)
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=compliance_{framework_id}.xlsx"
            }
        )

    return {"success": True, "report": report}


# ==================== Compliance Violations ====================

@router.get("/violations")
async def list_compliance_violations(
    framework_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """List compliance violations/findings"""
    org_id = current_user.get("organization_id", "default")

    # Get violations from audit logs
    filters = {
        "organization_id": org_id,
        "event_type": "compliance.violation"
    }

    logs = audit_db.audit_logs.find_all(filters, limit=limit)

    violations = []
    for log in logs:
        metadata = log.get("metadata", {})
        violation = {
            "id": log.get("id"),
            "framework_id": metadata.get("framework_id"),
            "control_id": metadata.get("control_id"),
            "severity": log.get("severity"),
            "description": metadata.get("description"),
            "detected_at": log.get("occurred_at"),
            "status": metadata.get("status", "open")
        }

        # Apply filters
        if framework_id and violation["framework_id"] != framework_id:
            continue
        if severity and violation["severity"] != severity:
            continue
        if status and violation["status"] != status:
            continue

        violations.append(violation)

    return {"success": True, "violations": violations}


# ==================== Compliance Settings ====================

@router.get("/settings")
async def get_compliance_settings(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get compliance module settings"""
    org_id = current_user.get("organization_id", "default")

    # Get organization compliance settings
    settings = {
        "enabled_frameworks": ["sox", "gdpr", "soc2"],
        "auto_check_interval_hours": 24,
        "alert_on_failure": True,
        "alert_threshold_score": 80,
        "notification_emails": [],
        "data_retention_days": 2555,  # 7 years for SOX
        "require_evidence": True
    }

    return {"success": True, "settings": settings}


@router.put("/settings")
async def update_compliance_settings(
    settings: dict,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update compliance module settings"""
    org_id = current_user.get("organization_id", "default")

    # Validate settings
    allowed_keys = [
        "enabled_frameworks", "auto_check_interval_hours",
        "alert_on_failure", "alert_threshold_score",
        "notification_emails", "data_retention_days", "require_evidence"
    ]

    filtered_settings = {k: v for k, v in settings.items() if k in allowed_keys}

    log_audit(
        event_type="system.config_changed",
        entity_type="compliance_settings",
        entity_id=org_id,
        action="update",
        user_id=current_user.get("id"),
        organization_id=org_id,
        changes=filtered_settings
    )

    return {
        "success": True,
        "message": "Settings updated",
        "settings": filtered_settings
    }


# ==================== Framework-Specific Endpoints ====================

@router.get("/sox/controls")
async def list_sox_controls(
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """List all SOX compliance controls"""
    org_id = current_user.get("organization_id", "default")
    compliance_service = ComplianceService(org_id)

    result = compliance_service.run_framework_checks("sox")

    return {
        "success": True,
        "framework": "sox",
        "framework_name": "Sarbanes-Oxley Act",
        "controls": result.get("controls", [])
    }


@router.get("/gdpr/controls")
async def list_gdpr_controls(
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """List all GDPR compliance controls"""
    org_id = current_user.get("organization_id", "default")
    compliance_service = ComplianceService(org_id)

    result = compliance_service.run_framework_checks("gdpr")

    return {
        "success": True,
        "framework": "gdpr",
        "framework_name": "General Data Protection Regulation",
        "controls": result.get("controls", [])
    }


@router.get("/soc2/controls")
async def list_soc2_controls(
    current_user: dict = Depends(require_roles("admin", "auditor", "compliance"))
):
    """List all SOC 2 compliance controls"""
    org_id = current_user.get("organization_id", "default")
    compliance_service = ComplianceService(org_id)

    result = compliance_service.run_framework_checks("soc2")

    return {
        "success": True,
        "framework": "soc2",
        "framework_name": "SOC 2 Type II",
        "controls": result.get("controls", [])
    }


# ==================== Data Subject Rights (GDPR) ====================

@router.get("/gdpr/data-subjects")
async def list_data_subject_requests(
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    current_user: dict = Depends(require_roles("admin", "compliance"))
):
    """List GDPR data subject requests (access, erasure, portability)"""
    org_id = current_user.get("organization_id", "default")

    # Get DSR logs from audit
    filters = {
        "organization_id": org_id,
        "event_category": "compliance"
    }

    logs = audit_db.audit_logs.find_all(filters, limit=limit)

    dsr_events = [
        "gdpr.access_request", "gdpr.erasure_request",
        "gdpr.portability_request", "gdpr.rectification_request"
    ]

    requests = []
    for log in logs:
        if log.get("event_type") in dsr_events:
            metadata = log.get("metadata", {})
            req = {
                "id": log.get("id"),
                "request_type": log.get("event_type").replace("gdpr.", ""),
                "data_subject_id": metadata.get("data_subject_id"),
                "data_subject_email": metadata.get("data_subject_email"),
                "status": metadata.get("status", "pending"),
                "requested_at": log.get("occurred_at"),
                "completed_at": metadata.get("completed_at")
            }

            if status and req["status"] != status:
                continue
            if request_type and req["request_type"] != request_type:
                continue

            requests.append(req)

    return {"success": True, "requests": requests}


@router.post("/gdpr/data-subjects/{request_id}/complete")
async def complete_data_subject_request(
    request_id: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin", "compliance"))
):
    """Mark a data subject request as completed"""
    org_id = current_user.get("organization_id", "default")

    log_audit(
        event_type="gdpr.request_completed",
        entity_type="data_subject_request",
        entity_id=request_id,
        action="update",
        user_id=current_user.get("id"),
        organization_id=org_id,
        metadata={
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "completed_by": current_user.get("id"),
            "notes": notes
        }
    )

    return {
        "success": True,
        "message": "Data subject request marked as completed",
        "request_id": request_id
    }
