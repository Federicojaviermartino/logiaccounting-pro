"""
WebSocket Event Handlers
Register all event handlers
"""

from .connection_handler import register_connection_handlers
from .presence_handler import register_presence_handlers
from .room_handler import register_room_handlers
from .cursor_handler import register_cursor_handlers
from .notification_handler import register_notification_handlers


def register_handlers(socketio):
    """Register all WebSocket event handlers"""
    register_connection_handlers(socketio)
    register_presence_handlers(socketio)
    register_room_handlers(socketio)
    register_cursor_handlers(socketio)
    register_notification_handlers(socketio)
