"""
Portal v2 Dashboard Routes
"""

from fastapi import APIRouter, Depends, HTTPException

from app.services.portal.dashboard_service import portal_dashboard_service
from app.utils.auth import get_current_user


router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    """Ensure user is a portal customer."""
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("")
async def get_dashboard(current_user: dict = Depends(get_portal_user)):
    """Get customer dashboard data."""
    return portal_dashboard_service.get_dashboard(
        customer_id=current_user.get("customer_id"),
        contact_id=current_user.get("contact_id"),
        tenant_id=current_user.get("tenant_id"),
    )


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_portal_user)):
    """Get dashboard statistics."""
    return portal_dashboard_service._get_stats(
        customer_id=current_user.get("customer_id"),
        tenant_id=current_user.get("tenant_id"),
    )


@router.get("/activity")
async def get_activity(
    limit: int = 20,
    current_user: dict = Depends(get_portal_user),
):
    """Get recent activity feed."""
    return portal_dashboard_service._get_recent_activity(
        customer_id=current_user.get("customer_id"),
        tenant_id=current_user.get("tenant_id"),
        limit=limit,
    )


@router.get("/quick-actions")
async def get_quick_actions(current_user: dict = Depends(get_portal_user)):
    """Get available quick actions."""
    return portal_dashboard_service._get_quick_actions(
        customer_id=current_user.get("customer_id"),
    )
