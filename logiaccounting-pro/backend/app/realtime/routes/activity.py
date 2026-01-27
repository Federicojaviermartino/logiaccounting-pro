"""
Activity Feed API Routes
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from app.realtime.services.activity_service import ActivityService

router = APIRouter(prefix="/api/v1/activity", tags=["Activity"])


def get_current_user():
    """Get current user from token - placeholder"""
    return {
        'user_id': 'current-user',
        'tenant_id': 'default',
    }


@router.get("")
async def get_activity_feed(
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    since: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get activity feed for current tenant"""
    user_id = current_user.get('user_id')
    tenant_id = current_user.get('tenant_id', 'default')

    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError:
            pass

    activities = ActivityService.get_feed(
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
        since=since_dt,
    )

    return {
        'success': True,
        'activities': activities,
    }


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_activity(
    entity_type: str,
    entity_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get activity for specific entity"""
    tenant_id = current_user.get('tenant_id', 'default')

    activities = ActivityService.get_entity_activity(
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )

    return {
        'success': True,
        'activities': activities,
    }


@router.get("/user/{user_id}")
async def get_user_activity(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get activity by a specific user"""
    tenant_id = current_user.get('tenant_id', 'default')

    activities = ActivityService.get_user_activity(
        tenant_id=tenant_id,
        user_id=user_id,
        limit=limit,
    )

    return {
        'success': True,
        'activities': activities,
    }


@router.get("/my")
async def get_my_activity(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's activity"""
    user_id = current_user.get('user_id')
    tenant_id = current_user.get('tenant_id', 'default')

    activities = ActivityService.get_user_activity(
        tenant_id=tenant_id,
        user_id=user_id,
        limit=limit,
    )

    return {
        'success': True,
        'activities': activities,
    }
