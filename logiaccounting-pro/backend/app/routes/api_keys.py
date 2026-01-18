"""
API Key Management routes
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.api_key_service import api_key_service
from app.utils.auth import require_roles

router = APIRouter()


class CreateKeyRequest(BaseModel):
    name: str
    permissions: Dict[str, List[str]]
    expires_days: Optional[int] = 365


class UpdatePermissionsRequest(BaseModel):
    permissions: Dict[str, List[str]]


@router.get("/permissions")
async def get_available_permissions(current_user: dict = Depends(require_roles("admin"))):
    """Get available permissions"""
    return {"permissions": api_key_service.PERMISSIONS}


@router.get("")
async def list_keys(current_user: dict = Depends(require_roles("admin"))):
    """List all API keys"""
    return {"keys": api_key_service.list_keys()}


@router.post("")
async def create_key(
    request: CreateKeyRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new API key"""
    return api_key_service.generate_key(
        name=request.name,
        permissions=request.permissions,
        expires_days=request.expires_days,
        created_by=current_user["id"]
    )


@router.get("/{key_id}")
async def get_key(
    key_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get API key details"""
    key = api_key_service.get_key(key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return key


@router.put("/{key_id}/permissions")
async def update_permissions(
    key_id: str,
    request: UpdatePermissionsRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update key permissions"""
    key = api_key_service.update_permissions(key_id, request.permissions)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return key


@router.post("/{key_id}/revoke")
async def revoke_key(
    key_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Revoke an API key"""
    if api_key_service.revoke_key(key_id):
        return {"message": "Key revoked"}
    raise HTTPException(status_code=404, detail="Key not found")


@router.delete("/{key_id}")
async def delete_key(
    key_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete an API key"""
    if api_key_service.delete_key(key_id):
        return {"message": "Key deleted"}
    raise HTTPException(status_code=404, detail="Key not found")
