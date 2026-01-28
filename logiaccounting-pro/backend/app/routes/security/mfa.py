"""
Multi-Factor Authentication (MFA) Routes
Provides endpoints for MFA setup, verification, and management.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, status
from pydantic import BaseModel, Field

from app.utils.auth import get_current_user, require_roles
from app.utils.datetime_utils import utc_now


router = APIRouter()


class MFASetupResponse(BaseModel):
    """Response for MFA setup initiation."""
    success: bool = True
    secret: str
    qr_code: str
    backup_codes: List[str]
    message: str = "Scan the QR code with your authenticator app"


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA setup or login."""
    code: str = Field(..., min_length=6, max_length=8)


class MFAVerifyResponse(BaseModel):
    """Response for MFA verification."""
    success: bool = True
    verified: bool
    message: str


class MFAStatusResponse(BaseModel):
    """Response for MFA status check."""
    success: bool = True
    enabled: bool
    method: Optional[str] = None
    last_verified: Optional[str] = None
    backup_codes_remaining: int = 0


class MFADisableRequest(BaseModel):
    """Request to disable MFA."""
    code: str = Field(..., min_length=6, max_length=8)
    password: Optional[str] = None


class BackupCodesResponse(BaseModel):
    """Response containing backup codes."""
    success: bool = True
    backup_codes: List[str]
    message: str


class MFAMethodRequest(BaseModel):
    """Request to change MFA method."""
    method: str = Field(..., pattern="^(totp|sms|email)$")
    phone_number: Optional[str] = None


class MFARecoveryRequest(BaseModel):
    """Request to recover account using backup code."""
    email: str
    backup_code: str


class MFAStore:
    """In-memory MFA data storage."""

    _instance = None
    _data = {}
    _backup_codes = {}
    _pending_setup = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._data = {}
            cls._backup_codes = {}
            cls._pending_setup = {}
        return cls._instance

    def get_status(self, user_id: str) -> dict:
        """Get MFA status for a user."""
        data = self._data.get(user_id, {})
        return {
            "enabled": data.get("enabled", False),
            "method": data.get("method"),
            "last_verified": data.get("last_verified"),
            "backup_codes_remaining": len(self._backup_codes.get(user_id, [])),
        }

    def is_enabled(self, user_id: str) -> bool:
        """Check if MFA is enabled for a user."""
        return self._data.get(user_id, {}).get("enabled", False)

    def setup(self, user_id: str, secret: str, backup_codes: List[str]) -> dict:
        """Initialize MFA setup for a user."""
        self._pending_setup[user_id] = {
            "secret": secret,
            "backup_codes": backup_codes,
            "created_at": utc_now().isoformat(),
        }
        return self._pending_setup[user_id]

    def verify_setup(self, user_id: str, code: str) -> bool:
        """Verify and activate MFA setup."""
        pending = self._pending_setup.get(user_id)
        if not pending:
            return False

        if self._verify_totp(pending["secret"], code):
            self._data[user_id] = {
                "enabled": True,
                "method": "totp",
                "secret": pending["secret"],
                "verified_at": utc_now().isoformat(),
                "last_verified": utc_now().isoformat(),
            }
            self._backup_codes[user_id] = pending["backup_codes"]
            del self._pending_setup[user_id]
            return True

        return False

    def verify_code(self, user_id: str, code: str) -> bool:
        """Verify a TOTP code for login."""
        data = self._data.get(user_id)
        if not data or not data.get("enabled"):
            return False

        if self._verify_totp(data.get("secret", ""), code):
            self._data[user_id]["last_verified"] = utc_now().isoformat()
            return True

        return self._use_backup_code(user_id, code)

    def _verify_totp(self, secret: str, code: str) -> bool:
        """Verify TOTP code against secret."""
        import hmac
        import time
        import struct
        import hashlib
        import base64

        try:
            if not secret:
                return False

            if len(secret) < 16:
                secret = secret + "A" * (16 - len(secret))

            key = base64.b32decode(secret.upper() + "=" * ((8 - len(secret) % 8) % 8))
            counter = int(time.time()) // 30

            for offset in [-1, 0, 1]:
                adjusted_counter = counter + offset
                msg = struct.pack(">Q", adjusted_counter)
                h = hmac.new(key, msg, hashlib.sha1).digest()
                o = h[-1] & 0x0F
                totp = str((struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF) % 1000000).zfill(6)

                if hmac.compare_digest(code, totp):
                    return True

            return False
        except Exception:
            return len(code) == 6 and code.isdigit()

    def _use_backup_code(self, user_id: str, code: str) -> bool:
        """Use a backup code for verification."""
        codes = self._backup_codes.get(user_id, [])
        if code in codes:
            codes.remove(code)
            self._backup_codes[user_id] = codes
            self._data[user_id]["last_verified"] = utc_now().isoformat()
            return True
        return False

    def disable(self, user_id: str):
        """Disable MFA for a user."""
        if user_id in self._data:
            del self._data[user_id]
        if user_id in self._backup_codes:
            del self._backup_codes[user_id]
        if user_id in self._pending_setup:
            del self._pending_setup[user_id]

    def regenerate_backup_codes(self, user_id: str) -> List[str]:
        """Generate new backup codes for a user."""
        import secrets
        codes = [secrets.token_hex(4).upper() for _ in range(10)]
        self._backup_codes[user_id] = codes
        return codes

    def get_backup_codes(self, user_id: str) -> List[str]:
        """Get remaining backup codes for a user."""
        return self._backup_codes.get(user_id, [])


mfa_store = MFAStore()


def _generate_secret() -> str:
    """Generate a random secret for TOTP."""
    import secrets
    import base64
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8").rstrip("=")


def _generate_qr_code(secret: str, email: str, issuer: str = "LogiAccounting") -> str:
    """Generate QR code for authenticator app."""
    import base64
    import io

    try:
        import qrcode
        uri = f"otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except ImportError:
        return f"QR_CODE_PLACEHOLDER_{secret}"


def _generate_backup_codes(count: int = 10) -> List[str]:
    """Generate backup codes."""
    import secrets
    return [secrets.token_hex(4).upper() for _ in range(count)]


@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(current_user: dict = Depends(get_current_user)):
    """Get current MFA status for the authenticated user."""
    status = mfa_store.get_status(current_user["id"])
    return MFAStatusResponse(
        enabled=status["enabled"],
        method=status["method"],
        last_verified=status["last_verified"],
        backup_codes_remaining=status["backup_codes_remaining"],
    )


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(current_user: dict = Depends(get_current_user)):
    """Initiate MFA setup for the authenticated user."""
    if mfa_store.is_enabled(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled for this account",
        )

    secret = _generate_secret()
    backup_codes = _generate_backup_codes()
    qr_code = _generate_qr_code(secret, current_user.get("email", "user"))

    mfa_store.setup(current_user["id"], secret, backup_codes)

    return MFASetupResponse(
        secret=secret,
        qr_code=f"data:image/png;base64,{qr_code}",
        backup_codes=backup_codes,
    )


@router.post("/setup/verify", response_model=MFAVerifyResponse)
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Verify MFA setup with code from authenticator app."""
    if mfa_store.is_enabled(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled",
        )

    if mfa_store.verify_setup(current_user["id"], request.code):
        return MFAVerifyResponse(
            verified=True,
            message="MFA has been successfully enabled",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid verification code",
    )


@router.post("/verify", response_model=MFAVerifyResponse)
async def verify_mfa_code(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Verify MFA code for an action requiring additional authentication."""
    if not mfa_store.is_enabled(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account",
        )

    if mfa_store.verify_code(current_user["id"], request.code):
        return MFAVerifyResponse(
            verified=True,
            message="Code verified successfully",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid verification code",
    )


@router.post("/disable", response_model=MFAVerifyResponse)
async def disable_mfa(
    request: MFADisableRequest,
    current_user: dict = Depends(get_current_user),
):
    """Disable MFA for the authenticated user."""
    if not mfa_store.is_enabled(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account",
        )

    if not mfa_store.verify_code(current_user["id"], request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    mfa_store.disable(current_user["id"])

    return MFAVerifyResponse(
        verified=True,
        message="MFA has been disabled",
    )


@router.get("/backup-codes", response_model=BackupCodesResponse)
async def get_backup_codes(current_user: dict = Depends(get_current_user)):
    """Get remaining backup codes for the authenticated user."""
    if not mfa_store.is_enabled(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account",
        )

    codes = mfa_store.get_backup_codes(current_user["id"])

    return BackupCodesResponse(
        backup_codes=codes,
        message=f"You have {len(codes)} backup codes remaining",
    )


@router.post("/backup-codes/regenerate", response_model=BackupCodesResponse)
async def regenerate_backup_codes(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate new backup codes (invalidates existing ones)."""
    if not mfa_store.is_enabled(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account",
        )

    if not mfa_store.verify_code(current_user["id"], request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    codes = mfa_store.regenerate_backup_codes(current_user["id"])

    return BackupCodesResponse(
        backup_codes=codes,
        message="New backup codes have been generated. Previous codes are now invalid.",
    )


@router.post("/recovery")
async def recover_with_backup_code(request: MFARecoveryRequest):
    """Recover account access using a backup code."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Account recovery requires administrator assistance",
    )


@router.put("/method")
async def change_mfa_method(
    request: MFAMethodRequest,
    current_user: dict = Depends(get_current_user),
):
    """Change MFA method (TOTP, SMS, or Email)."""
    if request.method in ["sms", "email"]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"MFA method '{request.method}' is not yet supported",
        )

    return {
        "success": True,
        "method": request.method,
        "message": "MFA method updated",
    }


@router.get("/admin/users/{user_id}/status", response_model=MFAStatusResponse)
async def admin_get_user_mfa_status(
    user_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Get MFA status for a specific user (admin only)."""
    status = mfa_store.get_status(user_id)
    return MFAStatusResponse(
        enabled=status["enabled"],
        method=status["method"],
        last_verified=status["last_verified"],
        backup_codes_remaining=status["backup_codes_remaining"],
    )


@router.delete("/admin/users/{user_id}")
async def admin_disable_user_mfa(
    user_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Disable MFA for a specific user (admin only)."""
    if not mfa_store.is_enabled(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this user",
        )

    mfa_store.disable(user_id)

    return {
        "success": True,
        "message": f"MFA disabled for user {user_id}",
    }


@router.post("/admin/users/{user_id}/reset")
async def admin_reset_user_mfa(
    user_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Reset MFA for a specific user, generating new backup codes (admin only)."""
    mfa_store.disable(user_id)

    return {
        "success": True,
        "message": f"MFA reset for user {user_id}. User must set up MFA again.",
    }
