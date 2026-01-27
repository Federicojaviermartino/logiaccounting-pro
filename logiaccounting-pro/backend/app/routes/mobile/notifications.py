"""
Mobile Notifications Routes
Push notification management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, List

from app.services.mobile.push_service import push_service
from app.services.mobile.aggregator import mobile_aggregator
from app.routes.portal_v2.auth import get_current_portal_user


router = APIRouter()


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: Dict[str, str]
    platform: Optional[str] = "web"
    device_name: Optional[str] = None
    preferences: Optional[Dict[str, bool]] = None


class UpdatePreferencesRequest(BaseModel):
    invoices: Optional[bool] = None
    projects: Optional[bool] = None
    support: Optional[bool] = None
    quotes: Optional[bool] = None
    payments: Optional[bool] = None
    marketing: Optional[bool] = None


@router.get("/vapid-key")
async def get_vapid_key():
    """Get VAPID public key for push subscription."""
    return {
        "publicKey": push_service.get_vapid_public_key(),
    }


@router.get("")
async def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    current_user: dict = Depends(get_current_portal_user),
):
    """Get user notifications."""
    notifications = mobile_aggregator._get_user_notifications(
        contact_id=current_user.get("contact_id"),
        limit=limit,
    )

    if unread_only:
        notifications = [n for n in notifications if not n.get("read")]

    return {
        "items": notifications,
        "unread_count": len([n for n in notifications if not n.get("read")]),
    }


@router.get("/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_portal_user)):
    """Get unread notification count for badge."""
    notifications = mobile_aggregator._get_user_notifications(
        contact_id=current_user.get("contact_id"),
    )
    unread = len([n for n in notifications if not n.get("read")])
    return {"count": unread}


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_portal_user),
):
    """Mark a notification as read."""
    success = mobile_aggregator.mark_notification_read(
        contact_id=current_user.get("contact_id"),
        notification_id=notification_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"success": True}


@router.post("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_portal_user)):
    """Mark all notifications as read."""
    count = mobile_aggregator.mark_all_notifications_read(
        contact_id=current_user.get("contact_id"),
    )
    return {"marked_read": count}


@router.get("/subscriptions")
async def get_subscriptions(current_user: dict = Depends(get_current_portal_user)):
    """Get all push subscriptions for current user."""
    return push_service.get_subscriptions(
        contact_id=current_user.get("contact_id"),
    )


@router.post("/subscribe")
async def subscribe_push(
    data: PushSubscriptionRequest,
    current_user: dict = Depends(get_current_portal_user),
):
    """Subscribe to push notifications."""
    subscription = push_service.subscribe(
        contact_id=current_user.get("contact_id"),
        subscription_data={
            "endpoint": data.endpoint,
            "keys": data.keys,
            "platform": data.platform,
            "device_name": data.device_name,
            "preferences": data.preferences,
        },
    )

    return {
        "id": subscription.id,
        "message": "Successfully subscribed to push notifications",
    }


@router.delete("/subscriptions/{subscription_id}")
async def unsubscribe_push(
    subscription_id: str,
    current_user: dict = Depends(get_current_portal_user),
):
    """Unsubscribe from push notifications."""
    success = push_service.unsubscribe(subscription_id)

    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {"success": True}


@router.put("/subscriptions/{subscription_id}/preferences")
async def update_preferences(
    subscription_id: str,
    data: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_portal_user),
):
    """Update notification preferences for a subscription."""
    preferences = {}

    if data.invoices is not None:
        preferences["invoices"] = data.invoices
    if data.projects is not None:
        preferences["projects"] = data.projects
    if data.support is not None:
        preferences["support"] = data.support
    if data.quotes is not None:
        preferences["quotes"] = data.quotes
    if data.payments is not None:
        preferences["payments"] = data.payments
    if data.marketing is not None:
        preferences["marketing"] = data.marketing

    result = push_service.update_preferences(subscription_id, preferences)

    if not result:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {"preferences": result}


@router.get("/history")
async def get_notification_history(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_portal_user),
):
    """Get push notification history."""
    return push_service.get_notification_history(
        contact_id=current_user.get("contact_id"),
        limit=limit,
    )
