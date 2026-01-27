"""
Webhook management routes
Phase 17 - Enhanced Webhooks with event types, delivery management, signatures
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, HttpUrl
from app.services.webhook_service import webhook_service
from app.utils.auth import require_roles
from app.middleware.tenant_context import TenantContext
from app.models.webhook_store import EVENT_DEFINITIONS

router = APIRouter()


class CreateWebhookRequest(BaseModel):
    url: str = Field(..., min_length=10)
    events: List[str] = Field(..., min_items=1)
    description: Optional[str] = None
    headers: Optional[dict] = None
    is_active: bool = True


class UpdateWebhookRequest(BaseModel):
    url: Optional[str] = Field(None, min_length=10)
    events: Optional[List[str]] = None
    description: Optional[str] = None
    headers: Optional[dict] = None
    is_active: Optional[bool] = None


@router.get("/events")
async def get_available_events(
    category: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get list of available webhook events with descriptions"""
    events = []

    for event_type, event_info in EVENT_DEFINITIONS.items():
        if category and event_info.get("category") != category:
            continue
        events.append({
            "event": event_type,
            "name": event_info.get("name"),
            "description": event_info.get("description"),
            "category": event_info.get("category"),
            "payload_example": event_info.get("payload_example", {})
        })

    # Get unique categories
    categories = list(set(e.get("category") for e in EVENT_DEFINITIONS.values()))

    return {
        "success": True,
        "events": events,
        "categories": sorted(categories),
        "total": len(events)
    }


@router.get("")
async def list_webhooks(
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_roles("admin"))
):
    """List all webhooks with pagination"""
    tenant_id = TenantContext.get_tenant_id()
    result = webhook_service.list_endpoints(
        tenant_id=tenant_id,
        is_active=is_active,
        page=page,
        per_page=per_page
    )

    return {
        "success": True,
        **result
    }


@router.post("")
async def create_webhook(
    request: CreateWebhookRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new webhook endpoint"""
    tenant_id = TenantContext.get_tenant_id()

    # Validate events
    invalid_events = [e for e in request.events if e not in EVENT_DEFINITIONS and e != "*"]
    if invalid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid events: {invalid_events}"
        )

    result = webhook_service.create_endpoint(
        url=request.url,
        events=request.events,
        description=request.description,
        headers=request.headers,
        is_active=request.is_active,
        created_by=current_user.get("id"),
        tenant_id=tenant_id
    )

    return {
        "success": True,
        "message": "Webhook created successfully. Store the signing secret safely.",
        **result
    }


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get a specific webhook"""
    tenant_id = TenantContext.get_tenant_id()
    webhook = webhook_service.get_endpoint(webhook_id, tenant_id=tenant_id)

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {
        "success": True,
        "webhook": webhook
    }


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    request: UpdateWebhookRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a webhook"""
    tenant_id = TenantContext.get_tenant_id()

    # Validate events if provided
    if request.events:
        invalid_events = [e for e in request.events if e not in EVENT_DEFINITIONS and e != "*"]
        if invalid_events:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid events: {invalid_events}"
            )

    webhook = webhook_service.update_endpoint(
        endpoint_id=webhook_id,
        url=request.url,
        events=request.events,
        description=request.description,
        headers=request.headers,
        is_active=request.is_active,
        tenant_id=tenant_id
    )

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {
        "success": True,
        "webhook": webhook
    }


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a webhook"""
    tenant_id = TenantContext.get_tenant_id()

    if webhook_service.delete_endpoint(webhook_id, tenant_id=tenant_id):
        return {
            "success": True,
            "message": "Webhook deleted successfully"
        }

    raise HTTPException(status_code=404, detail="Webhook not found")


@router.post("/{webhook_id}/rotate-secret")
async def rotate_secret(
    webhook_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Rotate webhook signing secret"""
    tenant_id = TenantContext.get_tenant_id()
    result = webhook_service.rotate_secret(webhook_id, tenant_id=tenant_id)

    if not result:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {
        "success": True,
        "message": "Secret rotated successfully. Store the new secret safely.",
        **result
    }


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Send a test event to webhook"""
    tenant_id = TenantContext.get_tenant_id()

    # Verify webhook exists
    webhook = webhook_service.get_endpoint(webhook_id, tenant_id=tenant_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    result = await webhook_service.send_test_event(webhook_id, tenant_id=tenant_id)

    return {
        "success": result.get("success", False),
        "delivery": result
    }


@router.get("/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: str,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get delivery history for a webhook"""
    tenant_id = TenantContext.get_tenant_id()

    # Verify webhook exists
    webhook = webhook_service.get_endpoint(webhook_id, tenant_id=tenant_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    result = webhook_service.list_deliveries(
        endpoint_id=webhook_id,
        status=status,
        page=page,
        per_page=per_page,
        tenant_id=tenant_id
    )

    return {
        "success": True,
        **result
    }


@router.post("/{webhook_id}/deliveries/{delivery_id}/retry")
async def retry_delivery(
    webhook_id: str,
    delivery_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Manually retry a failed delivery"""
    tenant_id = TenantContext.get_tenant_id()

    # Verify webhook exists
    webhook = webhook_service.get_endpoint(webhook_id, tenant_id=tenant_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    result = await webhook_service.retry_delivery(delivery_id, tenant_id=tenant_id)

    if not result:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return {
        "success": result.get("success", False),
        "delivery": result
    }


@router.get("/{webhook_id}/stats")
async def get_webhook_stats(
    webhook_id: str,
    days: int = Query(30, ge=1, le=90),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get webhook delivery statistics"""
    tenant_id = TenantContext.get_tenant_id()

    # Verify webhook exists
    webhook = webhook_service.get_endpoint(webhook_id, tenant_id=tenant_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    stats = webhook_service.get_endpoint_stats(webhook_id, days=days, tenant_id=tenant_id)

    return {
        "success": True,
        "stats": stats
    }


@router.get("/deliveries/all")
async def get_all_deliveries(
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_roles("admin"))
):
    """Get all webhook deliveries across all endpoints"""
    tenant_id = TenantContext.get_tenant_id()

    result = webhook_service.list_deliveries(
        event_type=event_type,
        status=status,
        page=page,
        per_page=per_page,
        tenant_id=tenant_id
    )

    return {
        "success": True,
        **result
    }
