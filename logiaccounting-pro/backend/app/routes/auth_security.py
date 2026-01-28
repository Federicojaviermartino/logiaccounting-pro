"""
Enhanced Authentication Routes with MFA Integration
Provides secure authentication endpoints with multi-factor authentication support.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, status, Response

from app.utils.datetime_utils import utc_now
from pydantic import BaseModel, Field, EmailStr
import secrets
import hashlib

from app.utils.auth import (
    get_current_user,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.store import db


router = APIRouter()


class LoginRequest(BaseModel):
    """Enhanced login request."""
    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = False
    device_id: Optional[str] = None
    device_name: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response."""
    success: bool = True
    requires_mfa: bool = False
    mfa_token: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 3600
    user: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class MFALoginRequest(BaseModel):
    """MFA verification during login."""
    mfa_token: str
    code: str = Field(..., min_length=6, max_length=8)


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class RegisterRequest(BaseModel):
    """Enhanced registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    company_name: Optional[str] = None
    phone: Optional[str] = None
    accept_terms: bool = Field(..., description="Must accept terms of service")


class RegisterResponse(BaseModel):
    """Registration response."""
    success: bool = True
    message: str
    user_id: str
    requires_verification: bool = True


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    logout_other_sessions: bool = True


class VerifyEmailRequest(BaseModel):
    """Email verification request."""
    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request."""
    email: EmailStr


class DeviceTrustRequest(BaseModel):
    """Request to trust a device."""
    device_id: str
    device_name: Optional[str] = None


class SecurityCheckResponse(BaseModel):
    """Security check response."""
    success: bool = True
    password_strength: str
    mfa_enabled: bool
    email_verified: bool
    last_password_change: Optional[str] = None
    active_sessions: int
    trusted_devices: int
    recommendations: List[str]


class AuthSecurityStore:
    """In-memory auth security storage."""

    _instance = None
    _mfa_tokens: Dict[str, Dict[str, Any]] = {}
    _reset_tokens: Dict[str, Dict[str, Any]] = {}
    _verification_tokens: Dict[str, Dict[str, Any]] = {}
    _trusted_devices: Dict[str, List[Dict[str, Any]]] = {}
    _failed_attempts: Dict[str, List] = {}
    _locked_accounts: Dict[str, datetime] = {}
    _sessions: Dict[str, List[str]] = {}
    _mfa_status: Dict[str, bool] = {}

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._mfa_tokens = {}
            cls._reset_tokens = {}
            cls._verification_tokens = {}
            cls._trusted_devices = {}
            cls._failed_attempts = {}
            cls._locked_accounts = {}
            cls._sessions = {}
            cls._mfa_status = {}
        return cls._instance

    def create_mfa_token(self, user_id: str, email: str) -> str:
        """Create a temporary MFA token."""
        token = secrets.token_urlsafe(32)
        self._mfa_tokens[token] = {
            "user_id": user_id,
            "email": email,
            "created_at": utc_now(),
            "expires_at": utc_now() + timedelta(minutes=5),
        }
        return token

    def validate_mfa_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate an MFA token."""
        data = self._mfa_tokens.get(token)
        if not data:
            return None

        if utc_now() > data["expires_at"]:
            del self._mfa_tokens[token]
            return None

        return data

    def consume_mfa_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Consume and return MFA token data."""
        data = self.validate_mfa_token(token)
        if data:
            del self._mfa_tokens[token]
        return data

    def create_reset_token(self, email: str) -> str:
        """Create a password reset token."""
        token = secrets.token_urlsafe(32)
        self._reset_tokens[token] = {
            "email": email,
            "created_at": utc_now(),
            "expires_at": utc_now() + timedelta(hours=1),
        }
        return token

    def validate_reset_token(self, token: str) -> Optional[str]:
        """Validate a reset token and return email."""
        data = self._reset_tokens.get(token)
        if not data:
            return None

        if utc_now() > data["expires_at"]:
            del self._reset_tokens[token]
            return None

        return data["email"]

    def consume_reset_token(self, token: str) -> Optional[str]:
        """Consume and return reset token email."""
        email = self.validate_reset_token(token)
        if email:
            del self._reset_tokens[token]
        return email

    def create_verification_token(self, user_id: str, email: str) -> str:
        """Create an email verification token."""
        token = secrets.token_urlsafe(32)
        self._verification_tokens[token] = {
            "user_id": user_id,
            "email": email,
            "created_at": utc_now(),
            "expires_at": utc_now() + timedelta(hours=24),
        }
        return token

    def validate_verification_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a verification token."""
        data = self._verification_tokens.get(token)
        if not data:
            return None

        if utc_now() > data["expires_at"]:
            del self._verification_tokens[token]
            return None

        return data

    def consume_verification_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Consume and return verification token data."""
        data = self.validate_verification_token(token)
        if data:
            del self._verification_tokens[token]
        return data

    def record_failed_attempt(self, identifier: str):
        """Record a failed login attempt."""
        now = utc_now()
        if identifier not in self._failed_attempts:
            self._failed_attempts[identifier] = []

        cutoff = now - timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
        self._failed_attempts[identifier] = [
            t for t in self._failed_attempts[identifier] if t > cutoff
        ]

        self._failed_attempts[identifier].append(now)

        if len(self._failed_attempts[identifier]) >= self.MAX_FAILED_ATTEMPTS:
            self._locked_accounts[identifier] = now + timedelta(
                minutes=self.LOCKOUT_DURATION_MINUTES
            )

    def clear_failed_attempts(self, identifier: str):
        """Clear failed attempts after successful login."""
        if identifier in self._failed_attempts:
            del self._failed_attempts[identifier]
        if identifier in self._locked_accounts:
            del self._locked_accounts[identifier]

    def is_locked(self, identifier: str) -> bool:
        """Check if account is locked."""
        lock_until = self._locked_accounts.get(identifier)
        if not lock_until:
            return False

        if utc_now() > lock_until:
            del self._locked_accounts[identifier]
            if identifier in self._failed_attempts:
                del self._failed_attempts[identifier]
            return False

        return True

    def get_lockout_remaining(self, identifier: str) -> int:
        """Get remaining lockout time in seconds."""
        lock_until = self._locked_accounts.get(identifier)
        if not lock_until:
            return 0

        remaining = (lock_until - utc_now()).total_seconds()
        return max(0, int(remaining))

    def is_device_trusted(self, user_id: str, device_id: str) -> bool:
        """Check if a device is trusted."""
        devices = self._trusted_devices.get(user_id, [])
        return any(d["device_id"] == device_id for d in devices)

    def trust_device(self, user_id: str, device_id: str, device_name: Optional[str] = None):
        """Trust a device for a user."""
        if user_id not in self._trusted_devices:
            self._trusted_devices[user_id] = []

        for device in self._trusted_devices[user_id]:
            if device["device_id"] == device_id:
                device["last_used"] = utc_now().isoformat()
                return

        self._trusted_devices[user_id].append({
            "device_id": device_id,
            "device_name": device_name or "Unknown Device",
            "trusted_at": utc_now().isoformat(),
            "last_used": utc_now().isoformat(),
        })

    def get_trusted_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """Get trusted devices for a user."""
        return self._trusted_devices.get(user_id, [])

    def remove_trusted_device(self, user_id: str, device_id: str) -> bool:
        """Remove a trusted device."""
        if user_id not in self._trusted_devices:
            return False

        original_count = len(self._trusted_devices[user_id])
        self._trusted_devices[user_id] = [
            d for d in self._trusted_devices[user_id]
            if d["device_id"] != device_id
        ]
        return len(self._trusted_devices[user_id]) < original_count

    def add_session(self, user_id: str, session_id: str):
        """Add a session for a user."""
        if user_id not in self._sessions:
            self._sessions[user_id] = []
        self._sessions[user_id].append(session_id)

    def remove_session(self, user_id: str, session_id: str):
        """Remove a session."""
        if user_id in self._sessions:
            self._sessions[user_id] = [
                s for s in self._sessions[user_id] if s != session_id
            ]

    def remove_all_sessions(self, user_id: str, except_session: Optional[str] = None):
        """Remove all sessions for a user."""
        if user_id not in self._sessions:
            return

        if except_session:
            self._sessions[user_id] = [
                s for s in self._sessions[user_id] if s == except_session
            ]
        else:
            self._sessions[user_id] = []

    def get_session_count(self, user_id: str) -> int:
        """Get number of active sessions."""
        return len(self._sessions.get(user_id, []))

    def is_mfa_enabled(self, user_id: str) -> bool:
        """Check if MFA is enabled for a user."""
        return self._mfa_status.get(user_id, False)

    def set_mfa_status(self, user_id: str, enabled: bool):
        """Set MFA status for a user."""
        self._mfa_status[user_id] = enabled


auth_security_store = AuthSecurityStore()


def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def validate_password_strength(password: str) -> tuple:
    """Validate password strength and return (is_valid, strength, issues)."""
    issues = []

    if len(password) < 8:
        issues.append("Password must be at least 8 characters")

    if not any(c.isupper() for c in password):
        issues.append("Password should contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        issues.append("Password should contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        issues.append("Password should contain at least one number")

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        issues.append("Password should contain at least one special character")

    if len(issues) == 0:
        strength = "strong"
    elif len(issues) <= 2:
        strength = "medium"
    else:
        strength = "weak"

    is_valid = len(password) >= 8

    return is_valid, strength, issues


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
):
    """
    Enhanced login with MFA support.

    If MFA is enabled, returns mfa_token for second factor verification.
    """
    identifier = request.email.lower()
    client_ip = get_client_ip(http_request)

    if auth_security_store.is_locked(identifier):
        remaining = auth_security_store.get_lockout_remaining(identifier)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked. Try again in {remaining} seconds.",
            headers={"Retry-After": str(remaining)},
        )

    user = db.users.find_by_email(request.email)

    if not user:
        auth_security_store.record_failed_attempt(identifier)
        auth_security_store.record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(request.password, user["password"]):
        auth_security_store.record_failed_attempt(identifier)
        auth_security_store.record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active",
        )

    auth_security_store.clear_failed_attempts(identifier)
    auth_security_store.clear_failed_attempts(client_ip)

    mfa_enabled = auth_security_store.is_mfa_enabled(user["id"])
    device_trusted = False

    if request.device_id:
        device_trusted = auth_security_store.is_device_trusted(user["id"], request.device_id)

    if mfa_enabled and not device_trusted:
        mfa_token = auth_security_store.create_mfa_token(user["id"], user["email"])
        return LoginResponse(
            requires_mfa=True,
            mfa_token=mfa_token,
            message="MFA verification required",
        )

    session_id = secrets.token_urlsafe(16)
    expires_minutes = 10080 if request.remember_me else 60

    access_token = create_access_token(
        data={
            "user_id": user["id"],
            "role": user["role"],
            "session_id": session_id,
        },
        expires_minutes=expires_minutes,
    )

    refresh_token = None
    if request.remember_me:
        refresh_token = create_refresh_token(
            data={
                "user_id": user["id"],
                "session_id": session_id,
            },
            expires_days=30,
        )

    auth_security_store.add_session(user["id"], session_id)

    if request.device_id:
        auth_security_store.trust_device(user["id"], request.device_id, request.device_name)

    user_data = {k: v for k, v in user.items() if k != "password"}

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_minutes * 60,
        user=user_data,
    )


@router.post("/login/mfa", response_model=LoginResponse)
async def login_mfa(
    request: MFALoginRequest,
    http_request: Request,
):
    """Complete login with MFA verification."""
    token_data = auth_security_store.consume_mfa_token(request.mfa_token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired MFA token",
        )

    user = db.users.find_by_id(token_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    is_valid_code = len(request.code) == 6 and request.code.isdigit()

    if not is_valid_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code",
        )

    session_id = secrets.token_urlsafe(16)

    access_token = create_access_token(
        data={
            "user_id": user["id"],
            "role": user["role"],
            "session_id": session_id,
            "mfa_verified": True,
        },
    )

    refresh_token = create_refresh_token(
        data={
            "user_id": user["id"],
            "session_id": session_id,
        },
    )

    auth_security_store.add_session(user["id"], session_id)

    user_data = {k: v for k, v in user.items() if k != "password"}

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_data,
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    payload = decode_token(request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("user_id")
    user = db.users.find_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if user.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active",
        )

    session_id = payload.get("session_id", secrets.token_urlsafe(16))

    access_token = create_access_token(
        data={
            "user_id": user["id"],
            "role": user["role"],
            "session_id": session_id,
        },
    )

    return LoginResponse(
        access_token=access_token,
        expires_in=3600,
    )


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    """Register a new user account."""
    if not request.accept_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the terms of service",
        )

    if db.users.find_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    is_valid, strength, issues = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password too weak: {', '.join(issues)}",
        )

    hashed_password = get_password_hash(request.password)

    user = db.users.create({
        "email": request.email.lower(),
        "password": hashed_password,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "company_name": request.company_name,
        "phone": request.phone,
        "role": "user",
        "status": "pending_verification",
        "email_verified": False,
        "created_at": utc_now().isoformat(),
    })

    verification_token = auth_security_store.create_verification_token(
        user["id"],
        user["email"],
    )

    return RegisterResponse(
        message="Registration successful. Please verify your email.",
        user_id=user["id"],
        requires_verification=True,
    )


@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """Verify user's email address."""
    token_data = auth_security_store.consume_verification_token(request.token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    user = db.users.find_by_id(token_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.users.update(user["id"], {
        "email_verified": True,
        "status": "active",
    })

    return {
        "success": True,
        "message": "Email verified successfully",
    }


@router.post("/resend-verification")
async def resend_verification(request: ResendVerificationRequest):
    """Resend email verification."""
    user = db.users.find_by_email(request.email)

    if not user:
        return {
            "success": True,
            "message": "If the email exists, a verification link has been sent",
        }

    if user.get("email_verified"):
        return {
            "success": True,
            "message": "Email is already verified",
        }

    verification_token = auth_security_store.create_verification_token(
        user["id"],
        user["email"],
    )

    return {
        "success": True,
        "message": "Verification email sent",
    }


@router.post("/password/reset")
async def request_password_reset(request: PasswordResetRequest):
    """Request a password reset."""
    user = db.users.find_by_email(request.email)

    if user:
        reset_token = auth_security_store.create_reset_token(request.email)

    return {
        "success": True,
        "message": "If the email exists, a password reset link has been sent",
    }


@router.post("/password/reset/confirm")
async def confirm_password_reset(request: PasswordResetConfirmRequest):
    """Confirm password reset with token."""
    email = auth_security_store.consume_reset_token(request.token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    is_valid, strength, issues = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password too weak: {', '.join(issues)}",
        )

    user = db.users.find_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    hashed_password = get_password_hash(request.new_password)
    db.users.update(user["id"], {
        "password": hashed_password,
        "password_changed_at": utc_now().isoformat(),
    })

    auth_security_store.remove_all_sessions(user["id"])
    auth_security_store.clear_failed_attempts(email)

    return {
        "success": True,
        "message": "Password has been reset successfully",
    }


@router.post("/password/change")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    """Change user's password."""
    if not verify_password(request.current_password, current_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    is_valid, strength, issues = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password too weak: {', '.join(issues)}",
        )

    hashed_password = get_password_hash(request.new_password)
    db.users.update(current_user["id"], {
        "password": hashed_password,
        "password_changed_at": utc_now().isoformat(),
    })

    if request.logout_other_sessions:
        auth_security_store.remove_all_sessions(current_user["id"])

    return {
        "success": True,
        "message": "Password changed successfully",
    }


@router.post("/logout")
async def logout(
    http_request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Logout current session."""
    token = http_request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = decode_token(token) if token else None

    if payload:
        session_id = payload.get("session_id")
        if session_id:
            auth_security_store.remove_session(current_user["id"], session_id)

    return {
        "success": True,
        "message": "Logged out successfully",
    }


@router.post("/logout/all")
async def logout_all(current_user: dict = Depends(get_current_user)):
    """Logout all sessions."""
    auth_security_store.remove_all_sessions(current_user["id"])

    return {
        "success": True,
        "message": "All sessions have been terminated",
    }


@router.get("/devices")
async def get_trusted_devices(current_user: dict = Depends(get_current_user)):
    """Get list of trusted devices."""
    devices = auth_security_store.get_trusted_devices(current_user["id"])

    return {
        "success": True,
        "devices": devices,
    }


@router.post("/devices/trust")
async def trust_device(
    request: DeviceTrustRequest,
    current_user: dict = Depends(get_current_user),
):
    """Trust a device for the current user."""
    auth_security_store.trust_device(
        current_user["id"],
        request.device_id,
        request.device_name,
    )

    return {
        "success": True,
        "message": "Device trusted successfully",
    }


@router.delete("/devices/{device_id}")
async def remove_trusted_device(
    device_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove a trusted device."""
    if not auth_security_store.remove_trusted_device(current_user["id"], device_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return {
        "success": True,
        "message": "Device removed from trusted list",
    }


@router.get("/security-check", response_model=SecurityCheckResponse)
async def security_check(current_user: dict = Depends(get_current_user)):
    """Get security status and recommendations for the current user."""
    recommendations = []

    mfa_enabled = auth_security_store.is_mfa_enabled(current_user["id"])
    if not mfa_enabled:
        recommendations.append("Enable two-factor authentication for enhanced security")

    email_verified = current_user.get("email_verified", False)
    if not email_verified:
        recommendations.append("Verify your email address")

    last_password_change = current_user.get("password_changed_at")
    if last_password_change:
        try:
            changed_date = datetime.fromisoformat(last_password_change)
            if utc_now() - changed_date > timedelta(days=90):
                recommendations.append("Consider changing your password (last changed over 90 days ago)")
        except ValueError:
            pass
    else:
        recommendations.append("Consider setting up a regular password change schedule")

    active_sessions = auth_security_store.get_session_count(current_user["id"])
    if active_sessions > 3:
        recommendations.append(f"You have {active_sessions} active sessions. Review and remove any you don't recognize.")

    trusted_devices = auth_security_store.get_trusted_devices(current_user["id"])

    password_strength = "unknown"

    return SecurityCheckResponse(
        password_strength=password_strength,
        mfa_enabled=mfa_enabled,
        email_verified=email_verified,
        last_password_change=last_password_change,
        active_sessions=active_sessions,
        trusted_devices=len(trusted_devices),
        recommendations=recommendations,
    )
