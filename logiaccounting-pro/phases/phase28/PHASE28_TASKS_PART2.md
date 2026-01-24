# Phase 28: Mobile API & PWA - Part 2: Backend Routes

## Overview
This part covers the backend API routes for mobile endpoints including home, notifications, devices, and sync.

---

## File 1: Mobile Home Routes
**Path:** `backend/app/routes/mobile/home.py`

```python
"""
Mobile API Home Routes
Aggregated endpoints for mobile home screen
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.services.mobile.aggregator import mobile_aggregator
from app.routes.portal_v2.auth import get_current_portal_user


router = APIRouter()


@router.get("/home")
async def get_home(current_user: dict = Depends(get_current_portal_user)):
    """
    Get aggregated home screen data.
    Returns user info, stats, activity, notifications in single call.
    """
    return mobile_aggregator.get_home_data(
        customer_id=current_user.get("customer_id"),
        contact_id=current_user.get("contact_id"),
        user_info=current_user,
    )


@router.get("/quick-stats")
async def get_quick_stats(current_user: dict = Depends(get_current_portal_user)):
    """Get key metrics only for dashboard widgets."""
    return mobile_aggregator._get_quick_stats(
        customer_id=current_user.get("customer_id"),
    )


@router.get("/activity")
async def get_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_portal_user),
):
    """Get recent activity feed."""
    return mobile_aggregator._get_recent_activity(
        customer_id=current_user.get("customer_id"),
        limit=limit,
    )


@router.get("/quick-actions")
async def get_quick_actions(current_user: dict = Depends(get_current_portal_user)):
    """Get available quick actions for FAB menu."""
    return mobile_aggregator._get_quick_actions(
        customer_id=current_user.get("customer_id"),
    )


@router.get("/offline-data")
async def get_offline_data(current_user: dict = Depends(get_current_portal_user)):
    """
    Get data package for offline use.
    Includes invoices, projects, tickets, contacts.
    """
    return mobile_aggregator.get_offline_data_package(
        customer_id=current_user.get("customer_id"),
        contact_id=current_user.get("contact_id"),
    )


@router.get("/alerts")
async def get_alerts(current_user: dict = Depends(get_current_portal_user)):
    """Get urgent alerts and warnings."""
    return mobile_aggregator._get_alerts(
        customer_id=current_user.get("customer_id"),
    )
```

---

## File 2: Mobile Notifications Routes
**Path:** `backend/app/routes/mobile/notifications.py`

```python
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
```

---

## File 3: Mobile Device Routes
**Path:** `backend/app/routes/mobile/devices.py`

```python
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
```

---

## File 4: Mobile Sync Routes
**Path:** `backend/app/routes/mobile/sync.py`

```python
"""
Mobile Sync Routes
Offline synchronization endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.mobile.sync_service import sync_service
from app.routes.portal_v2.auth import get_current_portal_user


router = APIRouter()


class SyncActionItem(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]
    created_at: str


class SyncRequest(BaseModel):
    last_sync: Optional[str] = None
    pending_actions: List[SyncActionItem] = []


@router.post("")
async def sync_data(
    data: SyncRequest,
    current_user: dict = Depends(get_current_portal_user),
):
    """
    Synchronize offline data with server.
    
    - Processes pending offline actions
    - Returns server updates since last sync
    - Handles conflict resolution
    """
    result = sync_service.process_sync(
        contact_id=current_user.get("contact_id"),
        customer_id=current_user.get("customer_id"),
        last_sync=data.last_sync,
        pending_actions=[action.dict() for action in data.pending_actions],
    )
    
    return result


@router.get("/status")
async def get_sync_status(current_user: dict = Depends(get_current_portal_user)):
    """Get current sync status."""
    return sync_service.get_sync_status(
        contact_id=current_user.get("contact_id"),
    )


@router.post("/full")
async def full_sync(current_user: dict = Depends(get_current_portal_user)):
    """
    Force a full sync.
    Returns all data regardless of last sync time.
    """
    result = sync_service.process_sync(
        contact_id=current_user.get("contact_id"),
        customer_id=current_user.get("customer_id"),
        last_sync=None,  # Force full sync
        pending_actions=[],
    )
    
    return result
```

---

## File 5: Mobile Routes Init
**Path:** `backend/app/routes/mobile/__init__.py`

```python
"""
Mobile API Routes - Router initialization
"""

from fastapi import APIRouter

from app.routes.mobile import home, notifications, devices, sync


router = APIRouter(prefix="/api/mobile/v1", tags=["Mobile API"])

# Include sub-routers
router.include_router(home.router, tags=["Mobile Home"])
router.include_router(notifications.router, prefix="/notifications", tags=["Mobile Notifications"])
router.include_router(devices.router, prefix="/devices", tags=["Mobile Devices"])
router.include_router(sync.router, prefix="/sync", tags=["Mobile Sync"])


def setup_mobile_routes(app):
    """Setup mobile routes on the FastAPI app."""
    app.include_router(router)
```

---

## Summary Part 2

| File | Description | Lines |
|------|-------------|-------|
| `home.py` | Aggregated home endpoints | ~70 |
| `notifications.py` | Push notification routes | ~140 |
| `devices.py` | Device registration routes | ~100 |
| `sync.py` | Sync routes | ~60 |
| `__init__.py` | Routes initialization | ~20 |
| **Total** | | **~390 lines** |
