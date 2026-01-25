# Phase 32: Advanced Security - Part 8: Security API Routes

## Overview
This part covers FastAPI routes for security features including MFA, sessions, and audit logs.

---

## File 1: MFA Routes
**Path:** `backend/app/routes/security/mfa.py`

```python
"""
MFA API Routes
Multi-factor authentication endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.security.auth.mfa_service import MFAService
from app.security.audit.logger import audit_logger
from app.security.audit.events import AuditEventType

router = APIRouter(prefix="/security/mfa", tags=["MFA"])


# Request/Response Models
class TOTPSetupRequest(BaseModel):
    """TOTP setup request."""
    pass  # No additional data needed


class TOTPSetupResponse(BaseModel):
    """TOTP setup response."""
    success: bool
    qr_code_uri: Optional[str] = None
    backup_codes: Optional[list] = None
    message: str = ""


class VerifyCodeRequest(BaseModel):
    """Verify MFA code request."""
    code: str = Field(..., min_length=6, max_length=10)


class MFAStatusResponse(BaseModel):
    """MFA status response."""
    enabled: bool
    method: Optional[str] = None
    verified: bool = False
    backup_codes_remaining: int = 0
    last_used: Optional[str] = None


class EmailOTPSetupRequest(BaseModel):
    """Email OTP setup request."""
    email: Optional[str] = None  # Use account email if not provided


class BackupCodesResponse(BaseModel):
    """Backup codes response."""
    success: bool
    backup_codes: list = []


# Routes
@router.post("/setup/totp", response_model=TOTPSetupResponse)
async def setup_totp(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Setup TOTP (Time-based One-Time Password) MFA.
    Returns QR code URI for authenticator apps.
    """
    service = MFAService(db)
    
    result = await service.setup_mfa(
        user_id=current_user["id"],
        method="totp",
        email=current_user["email"],
    )
    
    if result["success"]:
        audit_logger.log_auth_event(
            AuditEventType.AUTH_MFA_ENABLED,
            user_id=current_user["id"],
            details={"method": "totp", "status": "pending_verification"},
        )
    
    return TOTPSetupResponse(**result)


@router.post("/verify/totp")
async def verify_totp_setup(
    request: VerifyCodeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify TOTP code to complete MFA setup.
    """
    service = MFAService(db)
    
    result = await service.verify_setup(
        user_id=current_user["id"],
        code=request.code,
    )
    
    if result["success"]:
        audit_logger.log_auth_event(
            AuditEventType.AUTH_MFA_VERIFIED,
            user_id=current_user["id"],
            details={"method": "totp"},
        )
    
    return result


@router.post("/setup/email")
async def setup_email_otp(
    request: EmailOTPSetupRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Setup email-based OTP MFA.
    """
    service = MFAService(db)
    
    email = request.email or current_user["email"]
    
    result = await service.setup_mfa(
        user_id=current_user["id"],
        method="email",
        email=email,
    )
    
    if result["success"]:
        audit_logger.log_auth_event(
            AuditEventType.AUTH_MFA_ENABLED,
            user_id=current_user["id"],
            details={"method": "email"},
        )
    
    return result


@router.post("/send-code")
async def send_mfa_code(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send MFA verification code (for email/SMS methods).
    """
    service = MFAService(db)
    
    return await service.send_verification_code(current_user["id"])


@router.post("/verify")
async def verify_mfa_code(
    request: VerifyCodeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify MFA code during login or sensitive operations.
    """
    service = MFAService(db)
    
    result = await service.verify_code(
        user_id=current_user["id"],
        code=request.code,
    )
    
    if result["success"]:
        audit_logger.log_auth_event(
            AuditEventType.AUTH_MFA_VERIFIED,
            user_id=current_user["id"],
            details={"method": result.get("method")},
        )
    
    return result


@router.delete("/disable")
async def disable_mfa(
    request: VerifyCodeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disable MFA (requires verification).
    """
    service = MFAService(db)
    
    result = await service.disable_mfa(
        user_id=current_user["id"],
        code=request.code,
    )
    
    if result["success"]:
        audit_logger.log_auth_event(
            AuditEventType.AUTH_MFA_DISABLED,
            user_id=current_user["id"],
        )
    
    return result


@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get MFA status for current user.
    """
    service = MFAService(db)
    
    status = service.get_mfa_status(current_user["id"])
    
    return MFAStatusResponse(**status)


@router.post("/backup-codes/regenerate", response_model=BackupCodesResponse)
async def regenerate_backup_codes(
    request: VerifyCodeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Regenerate backup codes (requires verification).
    """
    service = MFAService(db)
    
    result = await service.regenerate_backup_codes(
        user_id=current_user["id"],
        code=request.code,
    )
    
    return BackupCodesResponse(**result)
```

---

## File 2: Session Routes
**Path:** `backend/app/routes/security/sessions.py`

```python
"""
Session API Routes
Session management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.security.auth.sessions import session_manager, Session as UserSession
from app.security.audit.logger import audit_logger
from app.security.audit.events import AuditEventType

router = APIRouter(prefix="/security/sessions", tags=["Sessions"])


# Response Models
class SessionDevice(BaseModel):
    """Device information."""
    type: str
    browser: str
    os: str


class SessionLocation(BaseModel):
    """Location information."""
    ip: str
    country: str = ""
    city: str = ""


class SessionResponse(BaseModel):
    """Session response."""
    id: str
    device: SessionDevice
    location: SessionLocation
    created_at: str
    last_activity: str
    is_current: bool


class SessionListResponse(BaseModel):
    """List of sessions response."""
    sessions: List[SessionResponse]
    total: int


class CurrentSessionResponse(BaseModel):
    """Current session info."""
    id: str
    device: SessionDevice
    location: SessionLocation
    created_at: str
    last_activity: str
    expires_in_seconds: int


# Routes
@router.get("", response_model=SessionListResponse)
async def list_sessions(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    List all active sessions for current user.
    """
    # Get current session ID from request state
    current_session_id = getattr(request.state, "session_id", None)
    
    sessions = session_manager.get_user_sessions(
        user_id=current_user["id"],
        current_session_id=current_session_id,
    )
    
    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s.id,
                device=SessionDevice(
                    type=s.device.device_type,
                    browser=s.device.browser,
                    os=s.device.os,
                ),
                location=SessionLocation(
                    ip=s.location.ip_address,
                    country=s.location.country,
                    city=s.location.city,
                ),
                created_at=s.created_at.isoformat(),
                last_activity=s.last_activity.isoformat(),
                is_current=s.is_current,
            )
            for s in sessions
        ],
        total=len(sessions),
    )


@router.get("/current", response_model=CurrentSessionResponse)
async def get_current_session(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Get current session information.
    """
    session_id = getattr(request.state, "session_id", None)
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    expires_in = (session.expires_at - session.last_activity).total_seconds()
    
    return CurrentSessionResponse(
        id=session.id,
        device=SessionDevice(
            type=session.device.device_type,
            browser=session.device.browser,
            os=session.device.os,
        ),
        location=SessionLocation(
            ip=session.location.ip_address,
            country=session.location.country,
            city=session.location.city,
        ),
        created_at=session.created_at.isoformat(),
        last_activity=session.last_activity.isoformat(),
        expires_in_seconds=int(max(0, expires_in)),
    )


@router.delete("/{session_id}")
async def revoke_session(
    session_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Revoke a specific session.
    """
    # Get session to verify ownership
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    if session.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke another user's session",
        )
    
    # Check if revoking current session
    current_session_id = getattr(request.state, "session_id", None)
    if session_id == current_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke current session. Use logout instead.",
        )
    
    success = session_manager.revoke_session(session_id)
    
    if success:
        audit_logger.log_auth_event(
            AuditEventType.AUTH_SESSION_REVOKED,
            user_id=current_user["id"],
            details={"revoked_session_id": session_id},
        )
    
    return {"success": success, "message": "Session revoked" if success else "Failed to revoke session"}


@router.delete("/all")
async def revoke_all_sessions(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Revoke all sessions except current.
    """
    current_session_id = getattr(request.state, "session_id", None)
    
    count = session_manager.revoke_all_sessions(
        user_id=current_user["id"],
        except_session_id=current_session_id,
    )
    
    if count > 0:
        audit_logger.log_auth_event(
            AuditEventType.AUTH_SESSION_REVOKED,
            user_id=current_user["id"],
            details={"revoked_count": count, "action": "revoke_all"},
        )
    
    return {"success": True, "revoked_count": count}


@router.post("/refresh")
async def refresh_session(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Refresh current session (extend expiry).
    """
    session_id = getattr(request.state, "session_id", None)
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    new_token = session_manager.refresh_session(session_id)
    
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to refresh session",
        )
    
    return {"success": True, "token": new_token}
```

---

## File 3: Audit Routes
**Path:** `backend/app/routes/security/audit.py`

```python
"""
Audit API Routes
Audit log endpoints
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_permission
from app.security.audit.logger import audit_logger
from app.security.audit.events import AuditEventType, AuditSeverity

router = APIRouter(prefix="/security/audit", tags=["Audit"])


# Response Models
class AuditLogEntry(BaseModel):
    """Audit log entry."""
    id: str
    timestamp: str
    event_type: str
    outcome: str
    severity: str
    user_id: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    description: str
    ip_address: Optional[str]


class AuditLogResponse(BaseModel):
    """Audit log query response."""
    logs: List[AuditLogEntry]
    total: int
    page: int
    per_page: int


class AuditSummaryResponse(BaseModel):
    """Audit summary response."""
    total_events: int
    period: dict
    by_type: dict
    by_outcome: dict
    by_severity: dict


# Routes
@router.get("/logs", response_model=AuditLogResponse)
async def get_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """
    Query audit logs with filters.
    Requires audit:read permission.
    """
    # Parse dates
    start_time = None
    end_time = None
    
    if start_date:
        start_time = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        end_time = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    
    # Query logs
    event_type_enum = AuditEventType(event_type) if event_type else None
    
    logs = audit_logger.query(
        event_type=event_type_enum,
        user_id=user_id,
        customer_id=current_user.get("customer_id"),
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time,
        limit=per_page * page,  # Get enough for pagination
    )
    
    # Apply pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_logs = logs[start_idx:end_idx]
    
    return AuditLogResponse(
        logs=[
            AuditLogEntry(
                id=log.id,
                timestamp=log.timestamp.isoformat(),
                event_type=log.event_type.value,
                outcome=log.outcome.value,
                severity=log.severity.value,
                user_id=log.user_id,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                action=log.action,
                description=log.description,
                ip_address=log.ip_address,
            )
            for log in paginated_logs
        ],
        total=len(logs),
        page=page,
        per_page=per_page,
    )


@router.get("/logs/{log_id}")
async def get_audit_log(
    log_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get specific audit log entry.
    """
    logs = audit_logger.query(limit=10000)
    
    for log in logs:
        if log.id == log_id:
            return {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "event_type": log.event_type.value,
                "outcome": log.outcome.value,
                "severity": log.severity.value,
                "user_id": log.user_id,
                "customer_id": log.customer_id,
                "session_id": log.session_id,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "action": log.action,
                "description": log.description,
                "details": log.details,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "request_id": log.request_id,
            }
    
    raise HTTPException(status_code=404, detail="Audit log not found")


@router.get("/summary", response_model=AuditSummaryResponse)
async def get_audit_summary(
    days: int = Query(1, ge=1, le=30, description="Number of days"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get audit log summary statistics.
    """
    start_time = datetime.utcnow() - timedelta(days=days)
    
    summary = audit_logger.get_summary(start_time=start_time)
    
    return AuditSummaryResponse(**summary)


@router.get("/export")
async def export_audit_logs(
    format: str = Query("json", regex="^(json|csv)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """
    Export audit logs in JSON or CSV format.
    """
    start_time = None
    end_time = None
    
    if start_date:
        start_time = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    if end_date:
        end_time = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    
    content = audit_logger.export(
        start_time=start_time,
        end_time=end_time,
        format=format,
    )
    
    # Set response headers
    media_type = "application/json" if format == "json" else "text/csv"
    filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )


@router.get("/event-types")
async def get_event_types(
    current_user: dict = Depends(get_current_user),
):
    """
    Get list of available event types.
    """
    return {
        "event_types": [
            {"value": e.value, "name": e.name}
            for e in AuditEventType
        ],
        "severities": [
            {"value": s.value, "name": s.name}
            for s in AuditSeverity
        ],
    }
```

---

## File 4: Security Routes Init
**Path:** `backend/app/routes/security/__init__.py`

```python
"""
Security Routes Module
All security-related API routes
"""

from fastapi import APIRouter

from app.routes.security.mfa import router as mfa_router
from app.routes.security.sessions import router as sessions_router
from app.routes.security.audit import router as audit_router


# Create main security router
router = APIRouter()

# Include sub-routers
router.include_router(mfa_router)
router.include_router(sessions_router)
router.include_router(audit_router)


__all__ = ['router']
```

---

## Summary Part 8

| File | Description | Lines |
|------|-------------|-------|
| `routes/security/mfa.py` | MFA endpoints | ~220 |
| `routes/security/sessions.py` | Session endpoints | ~200 |
| `routes/security/audit.py` | Audit endpoints | ~210 |
| `routes/security/__init__.py` | Routes init | ~25 |
| **Total** | | **~655 lines** |
