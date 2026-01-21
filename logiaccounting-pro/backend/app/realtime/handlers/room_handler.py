"""
Room Handler
Handle room-related WebSocket events
"""

import logging

from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.managers.room_manager import get_room_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


def register_room_handlers(sio):
    """Register room event handlers"""

    @sio.on(MessageType.ROOM_JOIN.value)
    async def handle_room_join(sid, data):
        """Handle room join request"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if not connection:
            await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
            return

        entity_type = data.get('entity_type')
        entity_id = data.get('entity_id')

        if not entity_type or not entity_id:
            await sio.emit('error', {'message': 'entity_type and entity_id required'}, room=sid)
            return

        room_id = f"{entity_type}:{entity_id}"

        room_manager = get_room_manager()
        room = room_manager.join_room(
            room_id=room_id,
            user_id=connection.user_id,
            user_name=connection.user_name,
            sid=sid,
            tenant_id=connection.tenant_id,
        )

        if room:
            await sio.enter_room(sid, room_id)
            conn_manager.add_to_room(sid, room_id)

            await sio.emit(
                MessageType.ROOM_USER_JOINED.value,
                {
                    'user_id': connection.user_id,
                    'user_name': connection.user_name,
                    'room_id': room_id,
                },
                room=room_id,
                skip_sid=sid,
            )

            await sio.emit(
                MessageType.ROOM_USERS.value,
                {
                    'room_id': room_id,
                    'users': room.get_users(),
                },
                room=sid,
            )

            logger.info(f"User {connection.user_id} joined room {room_id}")

    @sio.on(MessageType.ROOM_LEAVE.value)
    async def handle_room_leave(sid, data):
        """Handle room leave request"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if not connection:
            return

        room_id = data.get('room_id')

        if not room_id:
            return

        room_manager = get_room_manager()
        room = room_manager.leave_room(room_id, connection.user_id)

        await sio.leave_room(sid, room_id)
        conn_manager.remove_from_room(sid, room_id)

        if room:
            await sio.emit(
                MessageType.ROOM_USER_LEFT.value,
                {
                    'user_id': connection.user_id,
                    'user_name': connection.user_name,
                    'room_id': room_id,
                },
                room=room_id,
            )

        logger.info(f"User {connection.user_id} left room {room_id}")

    @sio.on(MessageType.ROOM_USERS.value)
    async def handle_room_users_request(sid, data):
        """Handle request for room users list"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if not connection:
            await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
            return

        room_id = data.get('room_id')

        if not room_id:
            await sio.emit('error', {'message': 'room_id required'}, room=sid)
            return

        room_manager = get_room_manager()
        users = room_manager.get_room_users(room_id)

        await sio.emit(
            MessageType.ROOM_USERS.value,
            {
                'room_id': room_id,
                'users': users,
            },
            room=sid,
        )
