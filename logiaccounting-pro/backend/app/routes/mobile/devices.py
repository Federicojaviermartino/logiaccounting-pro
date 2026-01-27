"""
Mobile Device Routes
Device registration and management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.mobile.device_service import device_service
from app.routes.portal_v2.auth import get_current_portal_user


router = APIRouter()


class RegisterDeviceRequest(BaseModel):
    token: str
    platform: str = "web"
    device_name: Optional[str] = None
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None


class UpdateDeviceRequest(BaseModel):
    device_name: Optional[str] = None
    push_enabled: Optional[bool] = None


@router.get("")
async def get_devices(current_user: dict = Depends(get_current_portal_user)):
    """Get all registered devices for current user."""
    return device_service.get_devices(
        contact_id=current_user.get("contact_id"),
    )


@router.post("")
async def register_device(
    data: RegisterDeviceRequest,
    current_user: dict = Depends(get_current_portal_user),
):
    """Register a new device for push notifications."""
    device = device_service.register_device(
        contact_id=current_user.get("contact_id"),
        data={
            "token": data.token,
            "platform": data.platform,
            "device_name": data.device_name,
            "device_model": data.device_model,
            "os_version": data.os_version,
            "app_version": data.app_version,
        },
    )

    return {
        "id": device.id,
        "platform": device.platform,
        "device_name": device.device_name,
        "created_at": device.created_at.isoformat(),
    }


@router.get("/{device_id}")
async def get_device(
    device_id: str,
    current_user: dict = Depends(get_current_portal_user),
):
    """Get a specific device."""
    device = device_service.get_device(
        device_id=device_id,
        contact_id=current_user.get("contact_id"),
    )

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@router.put("/{device_id}")
async def update_device(
    device_id: str,
    data: UpdateDeviceRequest,
    current_user: dict = Depends(get_current_portal_user),
):
    """Update device settings."""
    update_data = {}

    if data.device_name is not None:
        update_data["device_name"] = data.device_name
    if data.push_enabled is not None:
        update_data["push_enabled"] = data.push_enabled

    device = device_service.update_device(
        device_id=device_id,
        contact_id=current_user.get("contact_id"),
        data=update_data,
    )

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@router.delete("/{device_id}")
async def unregister_device(
    device_id: str,
    current_user: dict = Depends(get_current_portal_user),
):
    """Unregister a device."""
    success = device_service.unregister_device(
        device_id=device_id,
        contact_id=current_user.get("contact_id"),
    )

    if not success:
        raise HTTPException(status_code=404, detail="Device not found")

    return {"success": True}


@router.post("/{device_id}/ping")
async def ping_device(
    device_id: str,
    current_user: dict = Depends(get_current_portal_user),
):
    """Update device last activity (heartbeat)."""
    success = device_service.update_activity(device_id)

    if not success:
        raise HTTPException(status_code=404, detail="Device not found")

    return {"success": True}
