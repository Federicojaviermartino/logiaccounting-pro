"""
Cursor Handler
Handle cursor-related WebSocket events
"""

import logging

from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.managers.cursor_manager import get_cursor_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


def register_cursor_handlers(sio):
    """Register cursor event handlers"""

    @sio.on(MessageType.CURSOR_MOVE.value)
    async def handle_cursor_move(sid, data):
        """Handle cursor position update"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if not connection:
            return

        room_id = data.get('room_id')
        line = data.get('line', 0)
        column = data.get('column', 0)
        selection_start = data.get('selection_start')
        selection_end = data.get('selection_end')

        if not room_id:
            return

        cursor_manager = get_cursor_manager()
        cursor = cursor_manager.update_cursor(
            room_id=room_id,
            user_id=connection.user_id,
            user_name=connection.user_name,
            line=line,
            column=column,
            selection_start=selection_start,
            selection_end=selection_end,
        )

        await sio.emit(
            MessageType.CURSOR_MOVE.value,
            cursor.to_dict(),
            room=room_id,
            skip_sid=sid,
        )

    @sio.on(MessageType.CURSOR_SYNC.value)
    async def handle_cursor_sync_request(sid, data):
        """Handle request for all cursors in room"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if not connection:
            await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
            return

        room_id = data.get('room_id')

        if not room_id:
            await sio.emit('error', {'message': 'room_id required'}, room=sid)
            return

        cursor_manager = get_cursor_manager()
        cursors = cursor_manager.get_room_cursors(room_id)

        other_cursors = [
            c.to_dict() for c in cursors
            if c.user_id != connection.user_id
        ]

        await sio.emit(
            MessageType.CURSOR_SYNC.value,
            {
                'room_id': room_id,
                'cursors': other_cursors,
            },
            room=sid,
        )

    @sio.on(MessageType.CURSOR_REMOVE.value)
    async def handle_cursor_remove(sid, data):
        """Handle cursor removal (user left room)"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if not connection:
            return

        room_id = data.get('room_id')

        if not room_id:
            return

        cursor_manager = get_cursor_manager()
        cursor_manager.remove_cursor(room_id, connection.user_id)

        await sio.emit(
            MessageType.CURSOR_REMOVE.value,
            {'user_id': connection.user_id},
            room=room_id,
            skip_sid=sid,
        )
