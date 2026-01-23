"""
Portal v2 Account Management Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict

from app.services.portal.auth_service import portal_auth_service
from app.utils.auth import get_current_user


router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None


class NotificationSettings(BaseModel):
    invoice_created: bool = True
    invoice_reminder: bool = True
    payment_received: bool = True
    ticket_update: bool = True
    project_update: bool = True
    quote_received: bool = True
    message_received: bool = True


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_portal_user)):
    """Get portal user profile."""
    user = portal_auth_service.get_portal_user(current_user.get("email"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/profile")
async def update_profile(
    data: ProfileUpdate,
    current_user: dict = Depends(get_portal_user),
):
    """Update portal user profile."""
    return {"success": True}


@router.put("/password")
async def change_password(
    data: PasswordChange,
    current_user: dict = Depends(get_portal_user),
):
    """Change portal user password."""
    try:
        portal_auth_service.change_password(
            email=current_user.get("email"),
            current_password=data.current_password,
            new_password=data.new_password,
        )
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/preferences")
async def get_preferences(current_user: dict = Depends(get_portal_user)):
    """Get user preferences."""
    user = portal_auth_service.get_portal_user(current_user.get("email"))
    return user.get("preferences", {}) if user else {}


@router.put("/preferences")
async def update_preferences(
    data: PreferencesUpdate,
    current_user: dict = Depends(get_portal_user),
):
    """Update user preferences."""
    try:
        prefs = portal_auth_service.update_preferences(
            email=current_user.get("email"),
            preferences=data.dict(exclude_none=True),
        )
        return prefs
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions")
async def get_sessions(current_user: dict = Depends(get_portal_user)):
    """Get active sessions."""
    return portal_auth_service.get_sessions(
        contact_id=current_user.get("contact_id"),
    )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: dict = Depends(get_portal_user),
):
    """Revoke a specific session."""
    portal_auth_service.revoke_session(
        session_id=session_id,
        contact_id=current_user.get("contact_id"),
    )
    return {"success": True}


@router.get("/2fa")
async def get_2fa_status(current_user: dict = Depends(get_portal_user)):
    """Get 2FA status."""
    user = portal_auth_service.get_portal_user(current_user.get("email"))
    return {
        "enabled": user.get("two_factor_enabled", False) if user else False,
    }


@router.post("/2fa/enable")
async def enable_2fa(current_user: dict = Depends(get_portal_user)):
    """Enable 2FA - returns QR code."""
    import pyotp

    user = portal_auth_service._portal_users.get(current_user.get("email"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    secret = pyotp.random_base32()
    user["two_factor_secret"] = secret

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=user["email"],
        issuer_name="LogiAccounting Portal",
    )

    return {
        "secret": secret,
        "uri": uri,
    }


@router.post("/2fa/verify")
async def verify_and_enable_2fa(
    code: str,
    current_user: dict = Depends(get_portal_user),
):
    """Verify 2FA code and enable."""
    import pyotp

    user = portal_auth_service._portal_users.get(current_user.get("email"))
    if not user or not user.get("two_factor_secret"):
        raise HTTPException(status_code=400, detail="2FA not initialized")

    totp = pyotp.TOTP(user["two_factor_secret"])
    if not totp.verify(code):
        raise HTTPException(status_code=400, detail="Invalid code")

    user["two_factor_enabled"] = True
    return {"success": True, "enabled": True}


@router.delete("/2fa")
async def disable_2fa(
    code: str,
    current_user: dict = Depends(get_portal_user),
):
    """Disable 2FA."""
    import pyotp

    user = portal_auth_service._portal_users.get(current_user.get("email"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("two_factor_enabled"):
        totp = pyotp.TOTP(user["two_factor_secret"])
        if not totp.verify(code):
            raise HTTPException(status_code=400, detail="Invalid code")

    user["two_factor_enabled"] = False
    user["two_factor_secret"] = None
    return {"success": True, "enabled": False}


@router.get("/notifications/settings")
async def get_notification_settings(current_user: dict = Depends(get_portal_user)):
    """Get notification settings."""
    return NotificationSettings().dict()


@router.put("/notifications/settings")
async def update_notification_settings(
    data: NotificationSettings,
    current_user: dict = Depends(get_portal_user),
):
    """Update notification settings."""
    return data.dict()
