"""
Broadcast Manager
Manages message broadcasting to rooms and users
"""

import logging
from typing import Optional, List

from app.realtime.server import get_socketio
from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


class BroadcastManager:
    """Manages message broadcasting"""

    async def emit_to_user(self, user_id: str, event: str, data: dict):
        """Emit event to all connections of a specific user"""
        sio = get_socketio()
        if not sio:
            logger.warning("Socket.IO not initialized")
            return

        conn_manager = get_connection_manager()
        sids = conn_manager.get_user_sids(user_id)

        for sid in sids:
            try:
                await sio.emit(event, data, room=sid)
            except Exception as e:
                logger.error(f"Failed to emit to user {user_id}: {e}")

    async def emit_to_tenant(self, tenant_id: str, event: str, data: dict, skip_sid: str = None):
        """Emit event to all users in a tenant"""
        sio = get_socketio()
        if not sio:
            logger.warning("Socket.IO not initialized")
            return

        tenant_room = f"tenant:{tenant_id}"

        try:
            await sio.emit(event, data, room=tenant_room, skip_sid=skip_sid)
        except Exception as e:
            logger.error(f"Failed to emit to tenant {tenant_id}: {e}")

    async def emit_to_room(self, room_id: str, event: str, data: dict, skip_sid: str = None):
        """Emit event to all users in a room"""
        sio = get_socketio()
        if not sio:
            logger.warning("Socket.IO not initialized")
            return

        try:
            await sio.emit(event, data, room=room_id, skip_sid=skip_sid)
        except Exception as e:
            logger.error(f"Failed to emit to room {room_id}: {e}")

    async def broadcast_presence_update(self, tenant_id: str, presence_data: dict, skip_sid: str = None):
        """Broadcast presence update to tenant"""
        await self.emit_to_tenant(
            tenant_id,
            MessageType.PRESENCE_UPDATE.value,
            presence_data,
            skip_sid=skip_sid
        )

    async def broadcast_user_joined(self, tenant_id: str, user_data: dict, skip_sid: str = None):
        """Broadcast user joined event"""
        await self.emit_to_tenant(
            tenant_id,
            MessageType.PRESENCE_USER_JOINED.value,
            user_data,
            skip_sid=skip_sid
        )

    async def broadcast_user_left(self, tenant_id: str, user_data: dict):
        """Broadcast user left event"""
        await self.emit_to_tenant(
            tenant_id,
            MessageType.PRESENCE_USER_LEFT.value,
            user_data
        )

    async def broadcast_room_user_joined(self, room_id: str, user_data: dict, skip_sid: str = None):
        """Broadcast user joined room"""
        await self.emit_to_room(
            room_id,
            MessageType.ROOM_USER_JOINED.value,
            user_data,
            skip_sid=skip_sid
        )

    async def broadcast_room_user_left(self, room_id: str, user_data: dict):
        """Broadcast user left room"""
        await self.emit_to_room(
            room_id,
            MessageType.ROOM_USER_LEFT.value,
            user_data
        )

    async def broadcast_cursor_move(self, room_id: str, cursor_data: dict, skip_sid: str = None):
        """Broadcast cursor move to room"""
        await self.emit_to_room(
            room_id,
            MessageType.CURSOR_MOVE.value,
            cursor_data,
            skip_sid=skip_sid
        )

    async def broadcast_cursor_remove(self, room_id: str, user_id: str, skip_sid: str = None):
        """Broadcast cursor removal"""
        await self.emit_to_room(
            room_id,
            MessageType.CURSOR_REMOVE.value,
            {'user_id': user_id},
            skip_sid=skip_sid
        )

    async def send_notification(self, user_id: str, notification: dict):
        """Send notification to user"""
        await self.emit_to_user(user_id, MessageType.NOTIFICATION.value, notification)

    async def send_notification_count(self, user_id: str, count: int):
        """Send notification count update"""
        await self.emit_to_user(user_id, MessageType.NOTIFICATION_COUNT.value, {'count': count})

    async def broadcast_activity(self, tenant_id: str, activity: dict):
        """Broadcast activity to tenant"""
        await self.emit_to_tenant(tenant_id, MessageType.ACTIVITY.value, activity)


_broadcast_manager: Optional[BroadcastManager] = None


def get_broadcast_manager() -> BroadcastManager:
    """Get broadcast manager singleton"""
    global _broadcast_manager
    if _broadcast_manager is None:
        _broadcast_manager = BroadcastManager()
    return _broadcast_manager
