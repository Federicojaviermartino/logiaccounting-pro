"""
Presence API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.realtime.managers.presence_manager import get_presence_manager
from app.realtime.managers.connection_manager import get_connection_manager

router = APIRouter(prefix="/api/v1/presence", tags=["Presence"])


def get_current_user():
    """Get current user from token - placeholder"""
    return {
        'user_id': 'current-user',
        'tenant_id': 'default',
    }


@router.get("")
async def get_online_users(current_user: dict = Depends(get_current_user)):
    """Get online users for current tenant"""
    tenant_id = current_user.get('tenant_id', 'default')

    presence_manager = get_presence_manager()
    online_users = presence_manager.get_online_users(tenant_id)

    return {
        'success': True,
        'users': online_users,
        'count': len(online_users),
    }


@router.get("/{user_id}")
async def get_user_presence(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific user's presence"""
    tenant_id = current_user.get('tenant_id', 'default')

    presence_manager = get_presence_manager()
    presence = presence_manager.get_presence(user_id, tenant_id)

    if not presence:
        return {
            'success': True,
            'presence': {
                'user_id': user_id,
                'status': 'offline',
            },
        }

    return {
        'success': True,
        'presence': presence.to_dict(),
    }


@router.put("/status")
async def update_status(status: str, current_user: dict = Depends(get_current_user)):
    """Update own presence status"""
    user_id = current_user.get('user_id')
    tenant_id = current_user.get('tenant_id', 'default')

    if status not in ['online', 'away', 'busy']:
        raise HTTPException(status_code=400, detail='Invalid status')

    presence_manager = get_presence_manager()

    if status == 'busy':
        presence = presence_manager.set_busy(user_id, tenant_id)
    elif status == 'away':
        presence = presence_manager.set_away(user_id, tenant_id)
    else:
        presence = presence_manager.update_activity(user_id, tenant_id)

    if presence:
        return {
            'success': True,
            'presence': presence.to_dict(),
        }

    raise HTTPException(status_code=404, detail='Presence not found')


@router.get("/stats/online-count")
async def get_online_count(current_user: dict = Depends(get_current_user)):
    """Get count of online users"""
    tenant_id = current_user.get('tenant_id', 'default')

    presence_manager = get_presence_manager()
    count = presence_manager.get_online_count(tenant_id)

    return {
        'success': True,
        'count': count,
    }


@router.get("/entity/{entity_type}/{entity_id}")
async def get_users_viewing_entity(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get users viewing a specific entity"""
    tenant_id = current_user.get('tenant_id', 'default')

    presence_manager = get_presence_manager()
    users = presence_manager.get_users_viewing_entity(tenant_id, entity_type, entity_id)

    return {
        'success': True,
        'users': users,
        'count': len(users),
    }
