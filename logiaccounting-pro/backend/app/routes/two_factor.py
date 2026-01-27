"""
Two-Factor Authentication routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.two_factor import two_factor_service
from app.utils.auth import get_current_user

router = APIRouter()


class VerifyCodeRequest(BaseModel):
    code: str


@router.get("/status")
async def get_2fa_status(current_user: dict = Depends(get_current_user)):
    """Get current user's 2FA status"""
    return two_factor_service.get_2fa_status(current_user["id"])


@router.post("/setup")
async def setup_2fa(current_user: dict = Depends(get_current_user)):
    """Initialize 2FA setup - returns QR code and backup codes"""
    if two_factor_service.is_2fa_enabled(current_user["id"]):
        raise HTTPException(status_code=400, detail="2FA is already enabled")

    result = two_factor_service.setup_2fa(
        current_user["id"],
        current_user["email"]
    )

    return {
        "qr_code": f"data:image/png;base64,{result['qr_code']}",
        "secret": result["secret"],
        "backup_codes": result["backup_codes"],
        "message": "Scan the QR code with your authenticator app"
    }


@router.post("/verify-setup")
async def verify_2fa_setup(
    request: VerifyCodeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Verify 2FA setup with code from authenticator"""
    if two_factor_service.verify_setup(current_user["id"], request.code):
        return {"success": True, "message": "2FA enabled successfully"}

    raise HTTPException(status_code=400, detail="Invalid verification code")


@router.post("/disable")
async def disable_2fa(
    request: VerifyCodeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Disable 2FA (requires current code)"""
    if not two_factor_service.is_2fa_enabled(current_user["id"]):
        raise HTTPException(status_code=400, detail="2FA is not enabled")

    if not two_factor_service.verify_login(current_user["id"], request.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    two_factor_service.disable_2fa(current_user["id"])
    return {"success": True, "message": "2FA disabled"}
