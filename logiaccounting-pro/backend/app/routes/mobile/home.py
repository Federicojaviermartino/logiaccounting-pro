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
