"""
Notifications routes
"""

from fastapi import APIRouter, Depends, Query
from app.models.store import db
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("")
async def get_notifications(
    unread: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for current user"""
    notifications = db.notifications.find_by_user(current_user["id"], current_user["role"])
    
    if unread:
        notifications = [n for n in notifications if not n.get("read")]
    
    unread_count = db.notifications.get_unread_count(current_user["id"], current_user["role"])
    
    return {
        "notifications": notifications[:50],
        "unread_count": unread_count
    }


@router.get("/count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get unread notification count"""
    count = db.notifications.get_unread_count(current_user["id"], current_user["role"])
    return {"count": count}


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read"""
    db.notifications.mark_as_read(notification_id)
    return {"success": True}


@router.put("/read-all")
async def mark_all_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    db.notifications.mark_all_as_read(current_user["id"], current_user["role"])
    return {"success": True}
