"""
API Key Management routes
Phase 17 - Enhanced API Gateway with scopes, rate limits, IP restrictions
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from app.services.api_key_service import api_key_service
from app.utils.auth import require_roles
from app.middleware.tenant_context import TenantContext

router = APIRouter()


class CreateKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    environment: str = "production"
    expires_days: Optional[int] = Field(None, ge=1, le=365)
    allowed_ips: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1)
    rate_limit_per_day: Optional[int] = Field(None, ge=1)


class UpdateKeyRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    allowed_ips: Optional[List[str]] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


@router.get("/scopes")
async def get_available_scopes(current_user: dict = Depends(require_roles("admin"))):
    """Get available API key scopes with descriptions"""
    return {
        "success": True,
        "scopes": api_key_service.get_available_scopes()
    }


@router.get("/rate-limits")
async def get_rate_limit_tiers(current_user: dict = Depends(require_roles("admin"))):
    """Get rate limit configuration by tier"""
    return {
        "success": True,
        "tiers": api_key_service.RATE_LIMITS
    }


@router.get("")
async def list_keys(
    is_active: Optional[bool] = None,
    environment: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_roles("admin"))
):
    """List all API keys with pagination and filtering"""
    tenant_id = TenantContext.get_tenant_id()
    result = api_key_service.list_keys(
        tenant_id=tenant_id,
        is_active=is_active,
        environment=environment,
        page=page,
        per_page=per_page
    )
    return {
        "success": True,
        **result
    }


@router.post("")
async def create_key(
    request: CreateKeyRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new API key with scopes and rate limits"""
    tenant_id = TenantContext.get_tenant_id()

    try:
        result = api_key_service.create_api_key(
            name=request.name,
            description=request.description,
            scopes=request.scopes,
            environment=request.environment,
            expires_days=request.expires_days,
            allowed_ips=request.allowed_ips,
            rate_limit_per_minute=request.rate_limit_per_minute,
            rate_limit_per_hour=request.rate_limit_per_hour,
            rate_limit_per_day=request.rate_limit_per_day,
            created_by=current_user.get("id"),
            tenant_id=tenant_id
        )
        return {
            "success": True,
            "message": "API key created successfully. Store the key safely - it won't be shown again.",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{key_id}")
async def get_key(
    key_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get API key details"""
    tenant_id = TenantContext.get_tenant_id()
    key = api_key_service.get_key(key_id, tenant_id=tenant_id)

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    return {
        "success": True,
        "api_key": key
    }


@router.put("/{key_id}")
async def update_key(
    key_id: str,
    request: UpdateKeyRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update an API key"""
    tenant_id = TenantContext.get_tenant_id()

    try:
        key = api_key_service.update_key(
            key_id=key_id,
            name=request.name,
            description=request.description,
            scopes=request.scopes,
            allowed_ips=request.allowed_ips,
            rate_limit_per_minute=request.rate_limit_per_minute,
            is_active=request.is_active,
            tenant_id=tenant_id
        )

        if not key:
            raise HTTPException(status_code=404, detail="API key not found")

        return {
            "success": True,
            "api_key": key
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{key_id}/regenerate")
async def regenerate_key(
    key_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Regenerate API key value (keeps settings, new key)"""
    tenant_id = TenantContext.get_tenant_id()
    result = api_key_service.regenerate_key(key_id, tenant_id=tenant_id)

    if not result:
        raise HTTPException(status_code=404, detail="API key not found")

    return {
        "success": True,
        "message": "API key regenerated. Store the new key safely - it won't be shown again.",
        **result
    }


@router.post("/{key_id}/revoke")
async def revoke_key(
    key_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Revoke (deactivate) an API key"""
    tenant_id = TenantContext.get_tenant_id()

    if api_key_service.revoke_key(key_id, tenant_id=tenant_id):
        return {
            "success": True,
            "message": "API key revoked successfully"
        }

    raise HTTPException(status_code=404, detail="API key not found")


@router.delete("/{key_id}")
async def delete_key(
    key_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Permanently delete an API key"""
    tenant_id = TenantContext.get_tenant_id()

    if api_key_service.delete_key(key_id, tenant_id=tenant_id):
        return {
            "success": True,
            "message": "API key deleted successfully"
        }

    raise HTTPException(status_code=404, detail="API key not found")


@router.get("/{key_id}/usage")
async def get_key_usage(
    key_id: str,
    days: int = Query(30, ge=1, le=90),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get usage statistics for an API key"""
    tenant_id = TenantContext.get_tenant_id()
    stats = api_key_service.get_usage_stats(key_id, days=days, tenant_id=tenant_id)

    if not stats:
        raise HTTPException(status_code=404, detail="API key not found")

    return {
        "success": True,
        "usage": stats
    }
