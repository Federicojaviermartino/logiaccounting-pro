"""
Notification Handler
Handle notification-related WebSocket events
"""

import logging

from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)

notifications_store = {}
notification_counter = {}


def register_notification_handlers(sio):
    """Register notification event handlers"""

    @sio.on(MessageType.NOTIFICATION_READ.value)
    async def handle_notification_read(sid, data):
        """Handle marking notification as read"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if not connection:
            await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
            return

        notification_id = data.get('notification_id')

        if not notification_id:
            await sio.emit('error', {'message': 'notification_id required'}, room=sid)
            return

        user_id = connection.user_id
        if user_id in notifications_store and notification_id in notifications_store[user_id]:
            notifications_store[user_id][notification_id]['is_read'] = True

            if user_id in notification_counter:
                notification_counter[user_id] = max(0, notification_counter[user_id] - 1)

            user_sids = conn_manager.get_user_sids(user_id)
            count = notification_counter.get(user_id, 0)
            for user_sid in user_sids:
                await sio.emit(
                    MessageType.NOTIFICATION_COUNT.value,
                    {'count': count},
                    room=user_sid,
                )

    @sio.on(MessageType.NOTIFICATION_COUNT.value)
    async def handle_notification_count_request(sid, data=None):
        """Handle request for unread notification count"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if not connection:
            await sio.emit('error', {'message': 'Not authenticated'}, room=sid)
            return

        user_id = connection.user_id
        count = notification_counter.get(user_id, 0)

        await sio.emit(MessageType.NOTIFICATION_COUNT.value, {'count': count}, room=sid)


async def send_notification_to_user(sio, user_id: str, notification: dict):
    """Send notification to a user via WebSocket"""
    conn_manager = get_connection_manager()

    if user_id not in notifications_store:
        notifications_store[user_id] = {}
    notifications_store[user_id][notification['id']] = notification

    if user_id not in notification_counter:
        notification_counter[user_id] = 0
    notification_counter[user_id] += 1

    user_sids = conn_manager.get_user_sids(user_id)
    for sid in user_sids:
        await sio.emit(MessageType.NOTIFICATION.value, notification, room=sid)

    logger.debug(f"Notification sent to user {user_id}")
