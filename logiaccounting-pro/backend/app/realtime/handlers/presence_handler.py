"""
Presence Handler
Handle presence-related WebSocket events
"""

import logging

from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.managers.presence_manager import get_presence_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


def register_presence_handlers(sio):
    """Register presence event handlers"""

    @sio.on(MessageType.PRESENCE_UPDATE.value)
    async def handle_presence_update(sid, data):
        """Handle presence status update"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if not connection:
            await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
            return

        presence_manager = get_presence_manager()

        new_status = data.get('status')
        current_page = data.get('current_page')
        entity_type = data.get('entity_type')
        entity_id = data.get('entity_id')

        if new_status == 'busy':
            presence = presence_manager.set_busy(
                connection.user_id,
                connection.tenant_id
            )
        elif new_status == 'away':
            presence = presence_manager.set_away(
                connection.user_id,
                connection.tenant_id
            )
        elif new_status == 'online':
            presence = presence_manager.update_activity(
                user_id=connection.user_id,
                tenant_id=connection.tenant_id,
                current_page=current_page,
                current_entity_type=entity_type,
                current_entity_id=entity_id,
            )
        else:
            presence = presence_manager.update_activity(
                user_id=connection.user_id,
                tenant_id=connection.tenant_id,
                current_page=current_page,
                current_entity_type=entity_type,
                current_entity_id=entity_id,
            )

        if presence:
            tenant_room = f"tenant:{connection.tenant_id}"
            await sio.emit(
                MessageType.PRESENCE_UPDATE.value,
                {
                    'user_id': connection.user_id,
                    'user_name': connection.user_name,
                    'status': presence.status.value,
                    'current_page': presence.current_page,
                    'current_entity_type': presence.current_entity_type,
                    'current_entity_id': presence.current_entity_id,
                },
                room=tenant_room,
            )

    @sio.on(MessageType.PRESENCE_LIST.value)
    async def handle_presence_list_request(sid, data=None):
        """Handle request for online users list"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if not connection:
            await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
            return

        presence_manager = get_presence_manager()
        online_users = presence_manager.get_online_users(connection.tenant_id)

        await sio.emit(MessageType.PRESENCE_LIST.value, {'users': online_users}, room=sid)
