"""
Realtime Service
Core service for real-time operations
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.realtime.server import get_socketio
from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.managers.presence_manager import get_presence_manager
from app.realtime.managers.room_manager import get_room_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


class RealtimeService:
    """Core service for real-time operations"""

    @staticmethod
    async def broadcast_to_tenant(tenant_id: str, event: str, data: dict):
        """Broadcast event to all users in a tenant"""
        sio = get_socketio()
        if not sio:
            logger.warning("Socket.IO not initialized")
            return

        tenant_room = f"tenant:{tenant_id}"
        await sio.emit(event, data, room=tenant_room)

    @staticmethod
    async def broadcast_to_room(room_id: str, event: str, data: dict, skip_sid: str = None):
        """Broadcast event to all users in a room"""
        sio = get_socketio()
        if not sio:
            logger.warning("Socket.IO not initialized")
            return

        await sio.emit(event, data, room=room_id, skip_sid=skip_sid)

    @staticmethod
    async def send_to_user(user_id: str, event: str, data: dict):
        """Send event to specific user"""
        sio = get_socketio()
        if not sio:
            logger.warning("Socket.IO not initialized")
            return

        conn_manager = get_connection_manager()
        sids = conn_manager.get_user_sids(user_id)

        for sid in sids:
            await sio.emit(event, data, room=sid)

    @staticmethod
    def get_online_users(tenant_id: str) -> List[Dict]:
        """Get online users for a tenant"""
        presence_manager = get_presence_manager()
        return presence_manager.get_online_users(tenant_id)

    @staticmethod
    def get_room_users(entity_type: str, entity_id: str) -> List[Dict]:
        """Get users in a room"""
        room_id = f"{entity_type}:{entity_id}"
        room_manager = get_room_manager()
        return room_manager.get_room_users(room_id)

    @staticmethod
    def is_user_online(user_id: str) -> bool:
        """Check if user is online"""
        conn_manager = get_connection_manager()
        return conn_manager.is_user_online(user_id)

    @staticmethod
    async def notify_entity_update(
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        data: Dict[str, Any]
    ):
        """Notify about entity update to relevant room and tenant"""
        room_id = f"{entity_type}:{entity_id}"

        await RealtimeService.broadcast_to_room(
            room_id,
            f"{entity_type}:{action}",
            {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'action': action,
                'data': data,
                'timestamp': datetime.utcnow().isoformat(),
            }
        )

    @staticmethod
    async def notify_data_change(
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        change_type: str,
        changed_by: str
    ):
        """Notify about data change"""
        await RealtimeService.broadcast_to_tenant(
            tenant_id,
            'data:change',
            {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'change_type': change_type,
                'changed_by': changed_by,
                'timestamp': datetime.utcnow().isoformat(),
            }
        )
