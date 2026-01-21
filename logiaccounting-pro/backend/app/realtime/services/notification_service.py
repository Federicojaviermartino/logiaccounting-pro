"""
Notification Service
Create and deliver notifications
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid

from app.realtime.server import get_socketio
from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)

notifications_db: Dict[str, Dict[str, Dict]] = {}
unread_counts: Dict[str, int] = {}


NOTIFICATION_TYPES = {
    'payment_received': {'priority': 'high', 'channels': ['websocket', 'push', 'email']},
    'invoice_overdue': {'priority': 'high', 'channels': ['websocket', 'push', 'email']},
    'invoice_paid': {'priority': 'normal', 'channels': ['websocket', 'push']},
    'project_update': {'priority': 'normal', 'channels': ['websocket']},
    'task_assigned': {'priority': 'normal', 'channels': ['websocket', 'push']},
    'mention': {'priority': 'high', 'channels': ['websocket', 'push']},
    'comment': {'priority': 'normal', 'channels': ['websocket']},
    'document_shared': {'priority': 'normal', 'channels': ['websocket', 'push']},
    'low_stock': {'priority': 'high', 'channels': ['websocket', 'push']},
    'system': {'priority': 'normal', 'channels': ['websocket']},
}


class NotificationService:
    """Service for creating and delivering notifications"""

    @staticmethod
    async def create_notification(
        user_id: str,
        tenant_id: str,
        notification_type: str,
        title: str,
        message: str = None,
        source_type: str = None,
        source_id: str = None,
        action_url: str = None,
        action_label: str = None,
        priority: str = None,
        expires_in_days: int = 30,
    ) -> Dict[str, Any]:
        """Create and deliver a notification"""
        config = NOTIFICATION_TYPES.get(notification_type, {'priority': 'normal', 'channels': ['websocket']})

        if priority is None:
            priority = config['priority']

        notification = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'tenant_id': tenant_id,
            'type': notification_type,
            'title': title,
            'message': message,
            'source_type': source_type,
            'source_id': source_id,
            'action_url': action_url,
            'action_label': action_label,
            'priority': priority,
            'is_read': False,
            'read_at': None,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat(),
        }

        if user_id not in notifications_db:
            notifications_db[user_id] = {}
        notifications_db[user_id][notification['id']] = notification

        if user_id not in unread_counts:
            unread_counts[user_id] = 0
        unread_counts[user_id] += 1

        channels = config['channels']

        if 'websocket' in channels:
            await NotificationService._deliver_websocket(notification)

        logger.info(f"Notification created: {notification['id']} for user {user_id}")

        return notification

    @staticmethod
    async def _deliver_websocket(notification: Dict[str, Any]):
        """Deliver notification via WebSocket"""
        try:
            sio = get_socketio()
            if not sio:
                logger.warning("Socket.IO not initialized")
                return

            conn_manager = get_connection_manager()
            user_sids = conn_manager.get_user_sids(notification['user_id'])

            if user_sids:
                for sid in user_sids:
                    await sio.emit(
                        MessageType.NOTIFICATION.value,
                        notification,
                        room=sid,
                    )

                logger.debug(f"Notification {notification['id']} delivered via WebSocket")
        except Exception as e:
            logger.error(f"WebSocket delivery failed: {e}")

    @staticmethod
    def get_notifications(
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user"""
        user_notifications = notifications_db.get(user_id, {})

        notifs = list(user_notifications.values())

        now = datetime.utcnow().isoformat()
        notifs = [n for n in notifs if n.get('expires_at', now) >= now]

        if unread_only:
            notifs = [n for n in notifs if not n.get('is_read')]

        notifs.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        return notifs[offset:offset + limit]

    @staticmethod
    def get_unread_count(user_id: str) -> int:
        """Get unread notification count"""
        return unread_counts.get(user_id, 0)

    @staticmethod
    async def mark_read(notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        if user_id not in notifications_db:
            return False

        if notification_id not in notifications_db[user_id]:
            return False

        notification = notifications_db[user_id][notification_id]
        if not notification.get('is_read'):
            notification['is_read'] = True
            notification['read_at'] = datetime.utcnow().isoformat()

            if user_id in unread_counts:
                unread_counts[user_id] = max(0, unread_counts[user_id] - 1)

            sio = get_socketio()
            if sio:
                conn_manager = get_connection_manager()
                for sid in conn_manager.get_user_sids(user_id):
                    await sio.emit(
                        MessageType.NOTIFICATION_COUNT.value,
                        {'count': unread_counts.get(user_id, 0)},
                        room=sid,
                    )

        return True

    @staticmethod
    async def mark_all_read(user_id: str) -> int:
        """Mark all notifications as read"""
        if user_id not in notifications_db:
            return 0

        count = 0
        now = datetime.utcnow().isoformat()

        for notif in notifications_db[user_id].values():
            if not notif.get('is_read'):
                notif['is_read'] = True
                notif['read_at'] = now
                count += 1

        unread_counts[user_id] = 0

        sio = get_socketio()
        if sio:
            conn_manager = get_connection_manager()
            for sid in conn_manager.get_user_sids(user_id):
                await sio.emit(
                    MessageType.NOTIFICATION_COUNT.value,
                    {'count': 0},
                    room=sid,
                )

        return count

    @staticmethod
    def delete_notification(notification_id: str, user_id: str) -> bool:
        """Delete a notification"""
        if user_id not in notifications_db:
            return False

        if notification_id not in notifications_db[user_id]:
            return False

        notification = notifications_db[user_id].pop(notification_id)

        if not notification.get('is_read'):
            if user_id in unread_counts:
                unread_counts[user_id] = max(0, unread_counts[user_id] - 1)

        return True


async def notify_payment_received(
    user_id: str,
    tenant_id: str,
    payment_amount: float,
    invoice_number: str,
    invoice_id: str,
):
    """Send payment received notification"""
    return await NotificationService.create_notification(
        user_id=user_id,
        tenant_id=tenant_id,
        notification_type='payment_received',
        title='Payment Received',
        message=f'Payment of ${payment_amount:,.2f} received for Invoice #{invoice_number}',
        source_type='invoice',
        source_id=invoice_id,
        action_url=f'/invoices/{invoice_id}',
        action_label='View Invoice',
    )


async def notify_invoice_overdue(
    user_id: str,
    tenant_id: str,
    invoice_number: str,
    invoice_id: str,
    days_overdue: int,
):
    """Send invoice overdue notification"""
    return await NotificationService.create_notification(
        user_id=user_id,
        tenant_id=tenant_id,
        notification_type='invoice_overdue',
        title='Invoice Overdue',
        message=f'Invoice #{invoice_number} is {days_overdue} days overdue',
        source_type='invoice',
        source_id=invoice_id,
        action_url=f'/invoices/{invoice_id}',
        action_label='View Invoice',
        priority='high',
    )


async def notify_mention(
    user_id: str,
    tenant_id: str,
    mentioned_by: str,
    context: str,
    entity_type: str,
    entity_id: str,
    entity_url: str,
):
    """Send mention notification"""
    return await NotificationService.create_notification(
        user_id=user_id,
        tenant_id=tenant_id,
        notification_type='mention',
        title=f'{mentioned_by} mentioned you',
        message=context,
        source_type=entity_type,
        source_id=entity_id,
        action_url=entity_url,
        action_label='View',
    )
