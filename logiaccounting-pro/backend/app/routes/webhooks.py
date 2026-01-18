"""
Webhook management routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.webhook_service import webhook_service
from app.utils.auth import require_roles

router = APIRouter()


class CreateWebhookRequest(BaseModel):
    url: str
    events: List[str]
    headers: Optional[dict] = None
    secret: Optional[str] = None


class UpdateWebhookRequest(BaseModel):
    url: Optional[str] = None
    events: Optional[List[str]] = None
    headers: Optional[dict] = None
    active: Optional[bool] = None


@router.get("/events")
async def get_available_events(current_user: dict = Depends(require_roles("admin"))):
    """Get list of available webhook events"""
    return {"events": webhook_service.EVENTS}


@router.get("/logs/all")
async def get_all_logs(
    event: Optional[str] = None,
    success: Optional[bool] = None,
    limit: int = 50,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get all webhook delivery logs"""
    return {"logs": webhook_service.get_logs(event=event, success=success, limit=limit)}


@router.get("")
async def list_webhooks(current_user: dict = Depends(require_roles("admin"))):
    """List all webhooks"""
    return {"webhooks": webhook_service.list_webhooks()}


@router.post("")
async def create_webhook(
    request: CreateWebhookRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new webhook"""
    invalid_events = [e for e in request.events if e not in webhook_service.EVENTS]
    if invalid_events:
        raise HTTPException(status_code=400, detail=f"Invalid events: {invalid_events}")

    return webhook_service.create_webhook(
        url=request.url,
        events=request.events,
        headers=request.headers,
        secret=request.secret,
        user_id=current_user["id"]
    )


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get a specific webhook"""
    webhook = webhook_service.get_webhook(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    request: UpdateWebhookRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a webhook"""
    webhook = webhook_service.update_webhook(
        webhook_id,
        url=request.url,
        events=request.events,
        headers=request.headers,
        active=request.active
    )

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return webhook


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a webhook"""
    if webhook_service.delete_webhook(webhook_id):
        return {"message": "Webhook deleted"}
    raise HTTPException(status_code=404, detail="Webhook not found")


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Send a test event to webhook"""
    return await webhook_service.test_webhook(webhook_id)


@router.get("/{webhook_id}/logs")
async def get_webhook_logs(
    webhook_id: str,
    limit: int = 50,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get delivery logs for a webhook"""
    return {"logs": webhook_service.get_logs(webhook_id=webhook_id, limit=limit)}
