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
