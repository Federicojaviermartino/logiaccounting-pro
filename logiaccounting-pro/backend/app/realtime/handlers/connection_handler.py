"""
Connection Handler
Handle WebSocket connect/disconnect events
"""

import logging

from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.managers.presence_manager import get_presence_manager
from app.realtime.managers.room_manager import get_room_manager
from app.realtime.managers.cursor_manager import get_cursor_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


def register_connection_handlers(sio):
    """Register connection event handlers"""

    @sio.event
    async def connect(sid, environ, auth):
        """Handle new WebSocket connection"""
        token = None
        if auth:
            token = auth.get('token')

        if not token:
            query_string = environ.get('QUERY_STRING', '')
            for param in query_string.split('&'):
                if param.startswith('token='):
                    token = param[6:]
                    break

        if not token:
            logger.warning(f"Connection rejected: No token provided (sid={sid})")
            return False

        conn_manager = get_connection_manager()
        user_data = conn_manager.authenticate(token)

        if not user_data:
            logger.warning(f"Connection rejected: Invalid token (sid={sid})")
            return False

        user_agent = environ.get('HTTP_USER_AGENT', '')
        device_type = _parse_device_type(user_agent)
        browser = _parse_browser(user_agent)

        forwarded_for = environ.get('HTTP_X_FORWARDED_FOR', '')
        ip_address = forwarded_for.split(',')[0].strip() if forwarded_for else environ.get('REMOTE_ADDR', '')

        connection = conn_manager.add_connection(
            sid=sid,
            user_data=user_data,
            device_type=device_type,
            browser=browser,
            ip_address=ip_address,
        )

        presence_manager = get_presence_manager()
        presence = presence_manager.set_online(
            user_id=user_data['user_id'],
            tenant_id=user_data['tenant_id'],
            user_name=user_data['user_name'],
            device_type=device_type,
        )

        tenant_room = f"tenant:{user_data['tenant_id']}"
        await sio.enter_room(sid, tenant_room)

        await sio.emit(
            MessageType.PRESENCE_USER_JOINED.value,
            {
                'user_id': user_data['user_id'],
                'user_name': user_data['user_name'],
                'status': presence.status.value,
            },
            room=tenant_room,
            skip_sid=sid,
        )

        online_users = presence_manager.get_online_users(user_data['tenant_id'])
        await sio.emit(MessageType.PRESENCE_LIST.value, {'users': online_users}, room=sid)

        logger.info(f"User {user_data['user_id']} connected (sid={sid})")

        return True

    @sio.event
    async def disconnect(sid):
        """Handle WebSocket disconnection"""
        conn_manager = get_connection_manager()
        connection = conn_manager.remove_connection(sid)

        if connection:
            room_manager = get_room_manager()
            left_rooms = room_manager.leave_all_rooms(connection.user_id, sid)

            cursor_manager = get_cursor_manager()
            for room_id in left_rooms:
                cursor_manager.remove_cursor(room_id, connection.user_id)
                await sio.emit(
                    MessageType.CURSOR_REMOVE.value,
                    {'user_id': connection.user_id},
                    room=room_id,
                )
                await sio.emit(
                    MessageType.ROOM_USER_LEFT.value,
                    {
                        'user_id': connection.user_id,
                        'user_name': connection.user_name,
                        'room_id': room_id,
                    },
                    room=room_id,
                )

            user_connections = conn_manager.get_user_sids(connection.user_id)

            if not user_connections:
                presence_manager = get_presence_manager()
                presence_manager.set_offline(connection.user_id, connection.tenant_id)

                tenant_room = f"tenant:{connection.tenant_id}"
                await sio.emit(
                    MessageType.PRESENCE_USER_LEFT.value,
                    {
                        'user_id': connection.user_id,
                        'user_name': connection.user_name,
                    },
                    room=tenant_room,
                )

            logger.info(f"User {connection.user_id} disconnected (sid={sid})")

    @sio.event
    async def heartbeat(sid):
        """Handle heartbeat to keep connection alive"""
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)

        if connection:
            presence_manager = get_presence_manager()
            presence_manager.update_activity(
                user_id=connection.user_id,
                tenant_id=connection.tenant_id,
            )

        await sio.emit('heartbeat_ack', {'sid': sid}, room=sid)


def _parse_device_type(user_agent: str) -> str:
    """Parse device type from user agent"""
    ua_lower = user_agent.lower()

    if 'mobile' in ua_lower or 'android' in ua_lower:
        return 'mobile'
    if 'tablet' in ua_lower or 'ipad' in ua_lower:
        return 'tablet'

    return 'desktop'


def _parse_browser(user_agent: str) -> str:
    """Parse browser from user agent"""
    ua_lower = user_agent.lower()

    if 'chrome' in ua_lower and 'edg' not in ua_lower:
        return 'Chrome'
    if 'firefox' in ua_lower:
        return 'Firefox'
    if 'safari' in ua_lower and 'chrome' not in ua_lower:
        return 'Safari'
    if 'edg' in ua_lower:
        return 'Edge'

    return 'Unknown'
