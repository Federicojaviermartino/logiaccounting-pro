"""
Notifications API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from app.realtime.services.notification_service import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


def get_current_user():
    """Get current user from token - placeholder"""
    return {
        'user_id': 'current-user',
        'tenant_id': 'default',
    }


class CreateNotificationRequest(BaseModel):
    notification_type: str
    title: str
    message: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    priority: Optional[str] = None


@router.get("")
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for current user"""
    user_id = current_user.get('user_id')

    notifications = NotificationService.get_notifications(
        user_id=user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )

    return {
        'success': True,
        'notifications': notifications,
    }


@router.get("/unread/count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get unread notification count"""
    user_id = current_user.get('user_id')

    count = NotificationService.get_unread_count(user_id)

    return {
        'success': True,
        'count': count,
    }


@router.put("/{notification_id}/read")
async def mark_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark notification as read"""
    user_id = current_user.get('user_id')

    success = await NotificationService.mark_read(notification_id, user_id)

    if success:
        return {'success': True}

    raise HTTPException(status_code=404, detail='Notification not found')


@router.put("/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    user_id = current_user.get('user_id')

    count = await NotificationService.mark_all_read(user_id)

    return {
        'success': True,
        'marked_count': count,
    }


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a notification"""
    user_id = current_user.get('user_id')

    success = NotificationService.delete_notification(notification_id, user_id)

    if success:
        return {'success': True}

    raise HTTPException(status_code=404, detail='Notification not found')


@router.post("")
async def create_notification(
    request: CreateNotificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a notification (admin only)"""
    user_id = current_user.get('user_id')
    tenant_id = current_user.get('tenant_id', 'default')

    notification = await NotificationService.create_notification(
        user_id=user_id,
        tenant_id=tenant_id,
        notification_type=request.notification_type,
        title=request.title,
        message=request.message,
        source_type=request.source_type,
        source_id=request.source_id,
        action_url=request.action_url,
        action_label=request.action_label,
        priority=request.priority,
    )

    return {
        'success': True,
        'notification': notification,
    }
