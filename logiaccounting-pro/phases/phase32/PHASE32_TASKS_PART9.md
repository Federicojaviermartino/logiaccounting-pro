# Phase 32: Advanced Security - Part 9: Security API Routes

## Overview
This part covers the API routes for all security features.

---

## File 1: Security Routes
**Path:** `backend/app/routes/security.py`

```python
"""
Security API Routes
Endpoints for security features
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from pydantic import BaseModel, EmailStr
import logging

from app.auth.dependencies import get_current_user, require_admin
from app.security.auth.mfa_service import MFAService
from app.security.auth.oauth import oauth_manager, OAuthProvider
from app.security.auth.sessions import session_manager
from app.security.auth.tokens import token_manager, TokenType
from app.security.rbac.engine import rbac_engine
from app.security.audit.logger import audit_logger
from app.security.audit.events import AuditEventType, AuditOutcome
from app.security.protection.rate_limiter import rate_limiter
from app.security.protection.ip_filter import ip_filter
from app.security.config import get_security_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["Security"])


# ============== Request Models ==============

class MFASetupRequest(BaseModel):
    method: str  # 'totp', 'sms', 'email'
    phone_number: Optional[str] = None


class MFAVerifyRequest(BaseModel):
    code: str


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str
    redirect_uri: str


class RoleAssignmentRequest(BaseModel):
    user_id: str
    role_name: str
    customer_id: Optional[str] = None
    expires_at: Optional[datetime] = None


class IPBlockRequest(BaseModel):
    ip_address: str
    reason: str
    duration_seconds: Optional[int] = 3600
    permanent: bool = False


class SecurityConfigUpdate(BaseModel):
    mfa_required: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    max_login_attempts: Optional[int] = None
    password_min_length: Optional[int] = None


# ============== MFA Endpoints ==============

@router.post("/mfa/setup")
async def setup_mfa(
    request: MFASetupRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """Setup MFA for current user."""
    mfa_service = MFAService(db)
    
    result = await mfa_service.setup_mfa(
        user_id=str(current_user.id),
        method=request.method,
        email=current_user.email,
        phone=request.phone_number,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    # Log audit event
    audit_logger.log_auth_event(
        AuditEventType.AUTH_MFA_ENABLED,
        user_id=str(current_user.id),
        success=True,
        details={"method": request.method},
    )
    
    return result


@router.post("/mfa/verify")
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """Verify MFA setup with code."""
    mfa_service = MFAService(db)
    
    result = await mfa_service.verify_setup(
        user_id=str(current_user.id),
        code=request.code,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    audit_logger.log_auth_event(
        AuditEventType.AUTH_MFA_VERIFIED,
        user_id=str(current_user.id),
        success=True,
    )
    
    return result


@router.post("/mfa/disable")
async def disable_mfa(
    request: MFAVerifyRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """Disable MFA (requires verification)."""
    mfa_service = MFAService(db)
    
    result = await mfa_service.disable_mfa(
        user_id=str(current_user.id),
        code=request.code,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    audit_logger.log_auth_event(
        AuditEventType.AUTH_MFA_DISABLED,
        user_id=str(current_user.id),
        success=True,
    )
    
    return result


@router.get("/mfa/status")
async def get_mfa_status(
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """Get MFA status for current user."""
    mfa_service = MFAService(db)
    return mfa_service.get_mfa_status(str(current_user.id))


@router.post("/mfa/backup-codes")
async def regenerate_backup_codes(
    request: MFAVerifyRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db),
):
    """Regenerate backup codes (requires verification)."""
    mfa_service = MFAService(db)
    
    result = await mfa_service.regenerate_backup_codes(
        user_id=str(current_user.id),
        code=request.code,
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


# ============== OAuth Endpoints ==============

@router.get("/oauth/providers")
async def get_oauth_providers():
    """Get available OAuth providers."""
    return {
        "providers": oauth_manager.get_available_providers(),
    }


@router.get("/oauth/{provider}/authorize")
async def oauth_authorize(
    provider: str,
    redirect_uri: str,
):
    """Get OAuth authorization URL."""
    try:
        result = oauth_manager.get_authorization_url(
            provider=provider,
            redirect_uri=redirect_uri,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: OAuthCallbackRequest,
):
    """Handle OAuth callback."""
    try:
        # Exchange code for tokens
        tokens = await oauth_manager.exchange_code(
            provider=provider,
            code=request.code,
            redirect_uri=request.redirect_uri,
            state=request.state,
        )
        
        # Get user info
        user_info = await oauth_manager.get_user_info(
            provider=provider,
            access_token=tokens.access_token,
        )
        
        # TODO: Create or update user, create session
        
        return {
            "user": {
                "email": user_info.email,
                "name": user_info.name,
                "provider": user_info.provider.value,
            },
            "tokens": {
                "access_token": tokens.access_token,
                "expires_in": tokens.expires_in,
            },
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Session Endpoints ==============

@router.get("/sessions")
async def get_sessions(
    current_user = Depends(get_current_user),
    request: Request = None,
):
    """Get active sessions for current user."""
    # Get current session ID from token
    current_session_id = getattr(request.state, "session_id", None)
    
    sessions = session_manager.get_user_sessions(
        user_id=str(current_user.id),
        current_session_id=current_session_id,
    )
    
    return {
        "sessions": [s.to_dict() for s in sessions],
    }


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user = Depends(get_current_user),
):
    """Revoke a specific session."""
    session = session_manager.get_session(session_id)
    
    if not session or session.user_id != str(current_user.id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_manager.revoke_session(session_id)
    
    audit_logger.log_auth_event(
        AuditEventType.AUTH_SESSION_REVOKED,
        user_id=str(current_user.id),
        success=True,
        details={"session_id": session_id},
    )
    
    return {"message": "Session revoked"}


@router.delete("/sessions")
async def revoke_all_sessions(
    current_user = Depends(get_current_user),
    request: Request = None,
):
    """Revoke all sessions except current."""
    current_session_id = getattr(request.state, "session_id", None)
    
    count = session_manager.revoke_all_sessions(
        user_id=str(current_user.id),
        except_session_id=current_session_id,
    )
    
    return {"message": f"Revoked {count} sessions"}


# ============== RBAC Endpoints ==============

@router.get("/rbac/roles")
async def list_roles(
    current_user = Depends(require_admin),
):
    """List all available roles."""
    from app.security.rbac.roles import role_manager
    
    roles = role_manager.get_all_roles()
    return {
        "roles": [r.to_dict() for r in roles],
    }


@router.get("/rbac/permissions")
async def list_permissions(
    current_user = Depends(require_admin),
):
    """List all available permissions."""
    from app.security.rbac.permissions import permission_registry
    
    permissions = permission_registry.get_all_permissions()
    return {
        "permissions": [str(p) for p in permissions],
    }


@router.post("/rbac/assign")
async def assign_role(
    request: RoleAssignmentRequest,
    current_user = Depends(require_admin),
):
    """Assign role to user."""
    try:
        assignment = rbac_engine.assign_role(
            user_id=request.user_id,
            role_name=request.role_name,
            customer_id=request.customer_id,
            granted_by=str(current_user.id),
            expires_at=request.expires_at,
        )
        
        audit_logger.log_auth_event(
            AuditEventType.AUTHZ_ROLE_ASSIGNED,
            user_id=str(current_user.id),
            success=True,
            details={
                "target_user": request.user_id,
                "role": request.role_name,
            },
        )
        
        return {"message": "Role assigned", "assignment": assignment}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rbac/assign")
async def revoke_role(
    user_id: str,
    role_name: str,
    customer_id: Optional[str] = None,
    current_user = Depends(require_admin),
):
    """Revoke role from user."""
    success = rbac_engine.revoke_role(
        user_id=user_id,
        role_name=role_name,
        customer_id=customer_id,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    
    audit_logger.log_auth_event(
        AuditEventType.AUTHZ_ROLE_REVOKED,
        user_id=str(current_user.id),
        success=True,
        details={
            "target_user": user_id,
            "role": role_name,
        },
    )
    
    return {"message": "Role revoked"}


@router.get("/rbac/user/{user_id}")
async def get_user_roles(
    user_id: str,
    current_user = Depends(require_admin),
):
    """Get roles and permissions for a user."""
    roles = rbac_engine.get_user_roles(user_id)
    permissions = rbac_engine.get_user_permissions(user_id)
    
    return {
        "user_id": user_id,
        "roles": [r.to_dict() for r in roles],
        "permissions": list(permissions),
    }


@router.get("/rbac/check")
async def check_permission(
    permission: str,
    current_user = Depends(get_current_user),
):
    """Check if current user has a permission."""
    result = rbac_engine.check_permission(
        user_id=str(current_user.id),
        permission=permission,
    )
    
    return {
        "allowed": result.allowed,
        "reason": result.reason,
    }


# ============== Audit Endpoints ==============

@router.get("/audit/logs")
async def query_audit_logs(
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    current_user = Depends(require_admin),
):
    """Query audit logs."""
    event_type_enum = AuditEventType(event_type) if event_type else None
    
    events = audit_logger.query(
        event_type=event_type_enum,
        user_id=user_id,
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    
    return {
        "logs": [e.to_dict() for e in events],
        "total": len(events),
    }


@router.get("/audit/summary")
async def get_audit_summary(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user = Depends(require_admin),
):
    """Get audit log summary."""
    return audit_logger.get_summary(start_time, end_time)


@router.post("/audit/export")
async def export_audit_logs(
    format: str = Query("json", regex="^(json|csv)$"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user = Depends(require_admin),
):
    """Export audit logs."""
    from fastapi.responses import Response
    
    content = audit_logger.export(
        start_time=start_time,
        end_time=end_time,
        format=format,
    )
    
    media_type = "application/json" if format == "json" else "text/csv"
    filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d')}.{format}"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ============== IP & Rate Limit Endpoints ==============

@router.get("/ip/blocked")
async def get_blocked_ips(
    current_user = Depends(require_admin),
):
    """Get list of blocked IPs."""
    return {
        "blocked_ips": ip_filter.get_blocked_ips(),
    }


@router.post("/ip/block")
async def block_ip(
    request: IPBlockRequest,
    current_user = Depends(require_admin),
):
    """Block an IP address."""
    if request.permanent:
        ip_filter.add_blacklist(
            request.ip_address,
            reason=request.reason,
            permanent=True,
        )
    else:
        ip_filter.temporary_block(
            request.ip_address,
            duration_seconds=request.duration_seconds,
        )
    
    audit_logger.log_security_event(
        AuditEventType.SECURITY_IP_BLOCKED,
        severity="warning",
        description=f"IP blocked: {request.ip_address}",
        details={"reason": request.reason},
    )
    
    return {"message": f"IP {request.ip_address} blocked"}


@router.delete("/ip/block/{ip_address}")
async def unblock_ip(
    ip_address: str,
    current_user = Depends(require_admin),
):
    """Unblock an IP address."""
    ip_filter.unblock(ip_address)
    return {"message": f"IP {ip_address} unblocked"}


@router.get("/rate-limits/{key}")
async def get_rate_limit_status(
    key: str,
    current_user = Depends(require_admin),
):
    """Get rate limit status for a key."""
    return rate_limiter.get_status(key)


# ============== Security Config Endpoints ==============

@router.get("/config")
async def get_security_config_endpoint(
    current_user = Depends(require_admin),
):
    """Get current security configuration."""
    config = get_security_config()
    
    return {
        "mfa": {
            "required": config.mfa_policy.required,
            "required_for_admins": config.mfa_policy.required_for_admins,
            "allowed_methods": config.mfa_policy.allowed_methods,
        },
        "session": {
            "timeout_minutes": config.session_policy.session_timeout_minutes,
            "max_concurrent": config.session_policy.max_concurrent_sessions,
        },
        "password": {
            "min_length": config.password_policy.min_length,
            "require_special": config.password_policy.require_special,
            "max_age_days": config.password_policy.max_age_days,
        },
        "rate_limiting": {
            "enabled": config.rate_limit_policy.enabled,
            "requests_per_minute": config.rate_limit_policy.default_requests_per_minute,
        },
    }


@router.get("/status")
async def get_security_status(
    current_user = Depends(require_admin),
):
    """Get overall security status."""
    config = get_security_config()
    
    # Get recent security events
    from datetime import timedelta
    recent_events = audit_logger.query(
        event_type=AuditEventType.SECURITY_ALERT,
        start_time=datetime.utcnow() - timedelta(hours=24),
        limit=10,
    )
    
    return {
        "status": "healthy",
        "encryption_available": True,
        "mfa_enforcement": config.mfa_policy.required,
        "blocked_ips_count": len(ip_filter.get_blocked_ips()),
        "recent_security_events": len(recent_events),
        "warnings": config.validate(),
    }
```

---

## File 2: Auth Routes Update
**Path:** `backend/app/routes/auth_security.py`

```python
"""
Auth Routes with Security Integration
Enhanced authentication with MFA and security features
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
import logging

from app.security.auth.mfa_service import MFAService
from app.security.auth.sessions import session_manager
from app.security.auth.tokens import token_manager
from app.security.protection.rate_limiter import rate_limiter
from app.security.protection.ip_filter import ip_filter
from app.security.audit.logger import audit_logger
from app.security.audit.events import AuditEventType
from app.security.config import get_security_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    mfa_required: bool = False
    mfa_token: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class MFALoginRequest(BaseModel):
    mfa_token: str
    code: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_request: LoginRequest,
    db = Depends(get_db),
):
    """Login with email and password."""
    client_ip = request.client.host
    
    # Check IP filter
    ip_result = ip_filter.check(client_ip)
    if not ip_result.allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {ip_result.reason}",
        )
    
    # Check rate limit
    rate_result = rate_limiter.check(client_ip, "auth")
    if not rate_result.allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts",
            headers=rate_result.to_headers(),
        )
    
    # Verify credentials (integrate with existing auth)
    user = await verify_credentials(db, login_request.email, login_request.password)
    
    if not user:
        # Record failed attempt
        ip_filter.record_failed_attempt(client_ip)
        
        audit_logger.log_auth_event(
            AuditEventType.AUTH_LOGIN_FAILED,
            success=False,
            ip_address=client_ip,
            details={"email": login_request.email},
        )
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Clear failed attempts on success
    ip_filter.clear_failed_attempts(client_ip)
    
    # Check if MFA is enabled
    mfa_service = MFAService(db)
    mfa_status = mfa_service.get_mfa_status(str(user.id))
    
    if mfa_status["enabled"]:
        # If MFA code provided, verify it
        if login_request.mfa_code:
            mfa_result = await mfa_service.verify_code(
                user_id=str(user.id),
                code=login_request.mfa_code,
            )
            
            if not mfa_result["success"]:
                raise HTTPException(status_code=401, detail=mfa_result.get("error"))
        else:
            # Return MFA token for second step
            mfa_token = token_manager.create_mfa_token(str(user.id))
            
            # Send verification code if SMS/email
            if mfa_status["method"] in ["sms", "email"]:
                await mfa_service.send_verification_code(str(user.id))
            
            return LoginResponse(
                access_token="",
                refresh_token="",
                expires_in=0,
                mfa_required=True,
                mfa_token=mfa_token,
            )
    
    # Create session
    session_token, session = session_manager.create_session(
        user_id=str(user.id),
        user_agent=request.headers.get("user-agent", ""),
        ip_address=client_ip,
    )
    
    # Create tokens
    access_token, refresh_token = token_manager.create_token_pair(
        user_id=str(user.id),
        customer_id=str(user.customer_id) if user.customer_id else None,
        roles=[r.name for r in user.roles] if hasattr(user, "roles") else [],
        session_id=session.id,
    )
    
    audit_logger.log_auth_event(
        AuditEventType.AUTH_LOGIN,
        user_id=str(user.id),
        success=True,
        ip_address=client_ip,
    )
    
    config = get_security_config()
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=config.access_token_expire_minutes * 60,
    )


@router.post("/mfa-verify", response_model=LoginResponse)
async def verify_mfa_login(
    request: Request,
    mfa_request: MFALoginRequest,
    db = Depends(get_db),
):
    """Complete MFA verification step."""
    client_ip = request.client.host
    
    # Verify MFA token
    try:
        payload = token_manager.verify_token(mfa_request.mfa_token, TokenType.MFA)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired MFA token")
    
    user_id = payload["sub"]
    
    # Verify MFA code
    mfa_service = MFAService(db)
    mfa_result = await mfa_service.verify_code(
        user_id=user_id,
        code=mfa_request.code,
    )
    
    if not mfa_result["success"]:
        raise HTTPException(status_code=401, detail=mfa_result.get("error"))
    
    # Get user
    user = await get_user_by_id(db, user_id)
    
    # Create session
    session_token, session = session_manager.create_session(
        user_id=user_id,
        user_agent=request.headers.get("user-agent", ""),
        ip_address=client_ip,
    )
    
    # Create tokens
    access_token, refresh_token = token_manager.create_token_pair(
        user_id=user_id,
        customer_id=str(user.customer_id) if user.customer_id else None,
        roles=[r.name for r in user.roles] if hasattr(user, "roles") else [],
        session_id=session.id,
    )
    
    audit_logger.log_auth_event(
        AuditEventType.AUTH_MFA_VERIFIED,
        user_id=user_id,
        success=True,
        ip_address=client_ip,
    )
    
    config = get_security_config()
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=config.access_token_expire_minutes * 60,
    )


@router.post("/refresh")
async def refresh_tokens(
    request: Request,
    refresh_request: RefreshRequest,
):
    """Refresh access token."""
    try:
        access_token, refresh_token = token_manager.refresh_access_token(
            refresh_request.refresh_token
        )
        
        config = get_security_config()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": config.access_token_expire_minutes * 60,
        }
        
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout(
    request: Request,
    current_user = Depends(get_current_user),
):
    """Logout and revoke session."""
    session_id = getattr(request.state, "session_id", None)
    
    if session_id:
        session_manager.revoke_session(session_id)
    
    # Revoke tokens
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        token_manager.revoke_token(token)
    
    audit_logger.log_auth_event(
        AuditEventType.AUTH_LOGOUT,
        user_id=str(current_user.id),
        success=True,
    )
    
    return {"message": "Logged out successfully"}


# Helper functions (integrate with existing auth)
async def verify_credentials(db, email: str, password: str):
    """Verify user credentials."""
    # TODO: Integrate with existing user model
    pass


async def get_user_by_id(db, user_id: str):
    """Get user by ID."""
    # TODO: Integrate with existing user model
    pass
```

---

## Summary Part 9

| File | Description | Lines |
|------|-------------|-------|
| `routes/security.py` | Security API routes | ~480 |
| `routes/auth_security.py` | Auth with security | ~250 |
| **Total** | | **~730 lines** |
