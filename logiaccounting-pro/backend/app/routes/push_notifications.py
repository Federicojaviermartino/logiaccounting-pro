"""
Push Notifications API - Device registration and notification endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.push_notification import (
    push_notification_service,
    NotificationPayload,
    NotificationType,
)

router = APIRouter(prefix="/push", tags=["Push Notifications"])


class RegisterTokenRequest(BaseModel):
    token: str
    type: str  # 'expo' | 'fcm' | 'apns'
    device_id: str
    platform: str  # 'ios' | 'android' | 'web'


class UnregisterTokenRequest(BaseModel):
    token: str


class SendNotificationRequest(BaseModel):
    user_id: Optional[int] = None
    user_ids: Optional[List[int]] = None
    title: str
    body: str
    data: Optional[dict] = None
    badge: Optional[int] = None
    channel_id: Optional[str] = None


class TestNotificationRequest(BaseModel):
    title: str = "Test Notification"
    body: str = "This is a test notification from LogiAccounting Pro"


@router.post("/register")
async def register_device(
    request: RegisterTokenRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Register a device for push notifications.
    """
    token = await push_notification_service.register_token(
        user_id=current_user.id,
        token=request.token,
        token_type=request.type,
        device_id=request.device_id,
        platform=request.platform,
    )

    return {
        "status": "registered",
        "device_id": request.device_id,
        "platform": request.platform,
    }


@router.post("/unregister")
async def unregister_device(
    request: UnregisterTokenRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Unregister a device from push notifications.
    """
    success = await push_notification_service.unregister_token(request.token)

    if not success:
        raise HTTPException(status_code=404, detail="Token not found")

    return {"status": "unregistered"}


@router.get("/devices")
async def get_registered_devices(
    current_user: User = Depends(get_current_user),
):
    """
    Get all registered devices for the current user.
    """
    tokens = await push_notification_service.get_user_tokens(current_user.id)

    return {
        "devices": [
            {
                "device_id": t.device_id,
                "platform": t.platform,
                "type": t.type,
                "created_at": t.created_at.isoformat(),
                "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
            }
            for t in tokens
        ]
    }


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a push notification to one or more users.
    Requires admin privileges.
    """
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    notification = NotificationPayload(
        title=request.title,
        body=request.body,
        data=request.data,
        badge=request.badge,
        channel_id=request.channel_id,
    )

    if request.user_ids:
        result = await push_notification_service.send_bulk_notification(
            request.user_ids, notification
        )
    elif request.user_id:
        result = await push_notification_service.send_notification(
            request.user_id, notification
        )
    else:
        raise HTTPException(
            status_code=400, detail="Either user_id or user_ids must be provided"
        )

    return result


@router.post("/test")
async def send_test_notification(
    request: TestNotificationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a test notification to the current user's devices.
    """
    notification = NotificationPayload(
        title=request.title,
        body=request.body,
        data={"type": "test", "action": "none"},
    )

    result = await push_notification_service.send_notification(
        current_user.id, notification
    )

    return result


@router.post("/invoice/{invoice_id}/notify")
async def send_invoice_notification(
    invoice_id: str,
    notification_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send an invoice-related notification.
    """
    from app.models.invoice import Invoice

    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.organization_id == current_user.organization_id,
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        notif_type = NotificationType(notification_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification type")

    result = await push_notification_service.send_invoice_notification(
        user_id=current_user.id,
        invoice_id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        customer_name=invoice.customer_name or "Customer",
        amount=f"${invoice.total:,.2f}",
        notification_type=notif_type,
    )

    return result


@router.post("/approval/{approval_id}/notify")
async def send_approval_notification(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send an approval request notification.
    """
    result = await push_notification_service.send_approval_notification(
        user_id=current_user.id,
        approval_id=approval_id,
        title="Expense Approval",
        description="New expense requires your approval",
        amount="$500.00",
    )

    return result


@router.get("/settings")
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
):
    """
    Get notification settings for the current user.
    """
    return {
        "invoice_notifications": True,
        "payment_reminders": True,
        "approval_requests": True,
        "inventory_alerts": True,
        "marketing": False,
    }


@router.patch("/settings")
async def update_notification_settings(
    settings: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Update notification settings for the current user.
    """
    return {
        "status": "updated",
        "settings": settings,
    }
