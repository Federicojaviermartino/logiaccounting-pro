"""
Security Audit Routes
Provides endpoints for security audit log querying and export.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import io

from app.utils.auth import get_current_user, require_roles


router = APIRouter()


class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    id: str
    timestamp: str
    event_type: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    severity: str = "info"
    outcome: str = "success"
    details: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None


class AuditLogListResponse(BaseModel):
    """Response for audit log list."""
    success: bool = True
    logs: List[AuditLogEntry]
    total: int
    limit: int
    offset: int
    has_more: bool


class AuditLogDetailResponse(BaseModel):
    """Response for single audit log."""
    success: bool = True
    log: AuditLogEntry


class AuditStatistics(BaseModel):
    """Audit statistics."""
    total_events: int
    by_event_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_outcome: Dict[str, int]
    by_user: Dict[str, int]
    by_hour: Dict[str, int]
    period_days: int


class AuditStatisticsResponse(BaseModel):
    """Response for audit statistics."""
    success: bool = True
    statistics: AuditStatistics


class ExportRequest(BaseModel):
    """Request for audit log export."""
    format: str = Field(default="json", pattern="^(json|csv|xlsx)$")
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    event_types: Optional[List[str]] = None
    severity: Optional[str] = None
    user_id: Optional[str] = None


class SecurityAuditStore:
    """In-memory security audit log storage."""

    _instance = None
    _logs: List[Dict[str, Any]] = []
    _counter = 0

    EVENT_TYPES = [
        "auth.login",
        "auth.logout",
        "auth.login_failed",
        "auth.password_change",
        "auth.password_reset",
        "mfa.enabled",
        "mfa.disabled",
        "mfa.verified",
        "mfa.failed",
        "session.created",
        "session.revoked",
        "session.expired",
        "access.granted",
        "access.denied",
        "permission.changed",
        "role.assigned",
        "role.removed",
        "api_key.created",
        "api_key.revoked",
        "rate_limit.exceeded",
        "security.threat_detected",
        "security.config_changed",
        "data.exported",
        "data.accessed",
    ]

    SEVERITIES = ["debug", "info", "warning", "error", "critical"]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._logs = []
            cls._counter = 0
        return cls._instance

    def log(
        self,
        event_type: str,
        action: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "info",
        outcome: str = "success",
        details: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a security audit log entry."""
        self._counter += 1

        entry = {
            "id": f"SEC-{self._counter:08d}",
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "user_email": user_email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "severity": severity,
            "outcome": outcome,
            "details": details or {},
            "changes": changes,
        }

        self._logs.append(entry)

        return entry

    def get_log(self, log_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific log entry."""
        for log in self._logs:
            if log["id"] == log_id:
                return log
        return None

    def search(
        self,
        event_type: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        severity: Optional[str] = None,
        outcome: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search audit logs with filters."""
        results = self._logs.copy()

        if event_type:
            results = [l for l in results if l["event_type"] == event_type]
        if action:
            results = [l for l in results if l["action"] == action]
        if entity_type:
            results = [l for l in results if l["entity_type"] == entity_type]
        if entity_id:
            results = [l for l in results if l["entity_id"] == entity_id]
        if user_id:
            results = [l for l in results if l["user_id"] == user_id]
        if user_email:
            results = [l for l in results if l["user_email"] == user_email]
        if ip_address:
            results = [l for l in results if l["ip_address"] == ip_address]
        if severity:
            results = [l for l in results if l["severity"] == severity]
        if outcome:
            results = [l for l in results if l["outcome"] == outcome]
        if date_from:
            results = [l for l in results if l["timestamp"] >= date_from]
        if date_to:
            results = [l for l in results if l["timestamp"] <= date_to]

        results = sorted(results, key=lambda x: x["timestamp"], reverse=True)

        total = len(results)
        paginated = results[offset:offset + limit]

        return {
            "logs": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        }

    def get_user_audit_trail(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a specific user."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        return sorted(
            [l for l in self._logs if l["user_id"] == user_id and l["timestamp"] >= cutoff],
            key=lambda x: x["timestamp"],
            reverse=True,
        )[:limit]

    def get_entity_audit_trail(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a specific entity."""
        return sorted(
            [l for l in self._logs if l["entity_type"] == entity_type and l["entity_id"] == entity_id],
            key=lambda x: x["timestamp"],
            reverse=True,
        )[:limit]

    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get audit statistics."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        recent = [l for l in self._logs if l["timestamp"] >= cutoff]

        by_event_type = {}
        by_severity = {}
        by_outcome = {}
        by_user = {}
        by_hour = {str(i).zfill(2): 0 for i in range(24)}

        for log in recent:
            event = log["event_type"]
            by_event_type[event] = by_event_type.get(event, 0) + 1

            severity = log["severity"]
            by_severity[severity] = by_severity.get(severity, 0) + 1

            outcome = log["outcome"]
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1

            user = log["user_email"] or log["user_id"] or "system"
            by_user[user] = by_user.get(user, 0) + 1

            try:
                hour = log["timestamp"][11:13]
                by_hour[hour] = by_hour.get(hour, 0) + 1
            except (IndexError, KeyError):
                pass

        return {
            "total_events": len(recent),
            "by_event_type": by_event_type,
            "by_severity": by_severity,
            "by_outcome": by_outcome,
            "by_user": dict(sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_hour": by_hour,
            "period_days": days,
        }

    def export_json(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        severity: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Export logs as JSON."""
        results = self._logs.copy()

        if date_from:
            results = [l for l in results if l["timestamp"] >= date_from]
        if date_to:
            results = [l for l in results if l["timestamp"] <= date_to]
        if event_types:
            results = [l for l in results if l["event_type"] in event_types]
        if severity:
            results = [l for l in results if l["severity"] == severity]
        if user_id:
            results = [l for l in results if l["user_id"] == user_id]

        results = sorted(results, key=lambda x: x["timestamp"])

        return json.dumps(results, indent=2)

    def export_csv(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        severity: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Export logs as CSV."""
        results = self._logs.copy()

        if date_from:
            results = [l for l in results if l["timestamp"] >= date_from]
        if date_to:
            results = [l for l in results if l["timestamp"] <= date_to]
        if event_types:
            results = [l for l in results if l["event_type"] in event_types]
        if severity:
            results = [l for l in results if l["severity"] == severity]
        if user_id:
            results = [l for l in results if l["user_id"] == user_id]

        results = sorted(results, key=lambda x: x["timestamp"])

        headers = [
            "id", "timestamp", "event_type", "action", "entity_type",
            "entity_id", "user_id", "user_email", "ip_address", "severity", "outcome"
        ]
        lines = [",".join(headers)]

        for log in results:
            row = [
                str(log.get(h, "") or "") for h in headers
            ]
            lines.append(",".join(f'"{v}"' for v in row))

        return "\n".join(lines)


security_audit_store = SecurityAuditStore()


def log_security_event(
    event_type: str,
    action: str,
    request=None,
    user=None,
    **kwargs
):
    """Helper function to log security events."""
    ip_address = None
    user_agent = None

    if request:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        elif request.client:
            ip_address = request.client.host
        user_agent = request.headers.get("User-Agent")

    user_id = None
    user_email = None
    if user:
        user_id = user.get("id")
        user_email = user.get("email")

    return security_audit_store.log(
        event_type=event_type,
        action=action,
        user_id=user_id,
        user_email=user_email,
        ip_address=ip_address,
        user_agent=user_agent,
        **kwargs,
    )


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    event_type: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    severity: Optional[str] = None,
    outcome: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    current_user: dict = Depends(require_roles("admin", "auditor")),
):
    """List security audit logs with filtering and pagination."""
    result = security_audit_store.search(
        event_type=event_type,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        severity=severity,
        outcome=outcome,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )

    return AuditLogListResponse(
        logs=[AuditLogEntry(**log) for log in result["logs"]],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
        has_more=result["has_more"],
    )


@router.get("/event-types")
async def list_event_types(
    current_user: dict = Depends(require_roles("admin", "auditor")),
):
    """List available security event types."""
    return {
        "success": True,
        "event_types": SecurityAuditStore.EVENT_TYPES,
        "severities": SecurityAuditStore.SEVERITIES,
    }


@router.get("/statistics", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    days: int = Query(default=30, le=365),
    current_user: dict = Depends(require_roles("admin", "auditor")),
):
    """Get security audit statistics."""
    stats = security_audit_store.get_statistics(days)

    return AuditStatisticsResponse(
        statistics=AuditStatistics(**stats),
    )


@router.get("/user/{user_id}")
async def get_user_audit_trail(
    user_id: str,
    days: int = Query(default=30, le=365),
    limit: int = Query(default=200, le=1000),
    current_user: dict = Depends(require_roles("admin", "auditor")),
):
    """Get security audit trail for a specific user."""
    logs = security_audit_store.get_user_audit_trail(user_id, days, limit)

    return {
        "success": True,
        "user_id": user_id,
        "period_days": days,
        "logs": [AuditLogEntry(**log) for log in logs],
        "total": len(logs),
    }


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: str,
    limit: int = Query(default=100, le=500),
    current_user: dict = Depends(require_roles("admin", "auditor")),
):
    """Get security audit trail for a specific entity."""
    logs = security_audit_store.get_entity_audit_trail(entity_type, entity_id, limit)

    return {
        "success": True,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "logs": [AuditLogEntry(**log) for log in logs],
        "total": len(logs),
    }


@router.get("/{log_id}", response_model=AuditLogDetailResponse)
async def get_audit_log(
    log_id: str,
    current_user: dict = Depends(require_roles("admin", "auditor")),
):
    """Get a specific audit log entry."""
    log = security_audit_store.get_log(log_id)

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    return AuditLogDetailResponse(log=AuditLogEntry(**log))


@router.post("/export")
async def export_audit_logs(
    request: ExportRequest,
    current_user: dict = Depends(require_roles("admin", "auditor")),
):
    """Export security audit logs."""
    log_security_event(
        event_type="data.exported",
        action="export_audit_logs",
        user=current_user,
        details={"format": request.format},
    )

    if request.format == "json":
        content = security_audit_store.export_json(
            date_from=request.date_from,
            date_to=request.date_to,
            event_types=request.event_types,
            severity=request.severity,
            user_id=request.user_id,
        )
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=security_audit_logs.json"},
        )

    elif request.format == "csv":
        content = security_audit_store.export_csv(
            date_from=request.date_from,
            date_to=request.date_to,
            event_types=request.event_types,
            severity=request.severity,
            user_id=request.user_id,
        )
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=security_audit_logs.csv"},
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {request.format}",
        )


@router.get("/my-activity")
async def get_my_audit_trail(
    days: int = Query(default=30, le=90),
    limit: int = Query(default=100, le=500),
    current_user: dict = Depends(get_current_user),
):
    """Get security audit trail for the current user."""
    logs = security_audit_store.get_user_audit_trail(
        current_user["id"],
        days,
        limit,
    )

    return {
        "success": True,
        "period_days": days,
        "logs": [AuditLogEntry(**log) for log in logs],
        "total": len(logs),
    }
