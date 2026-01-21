# LogiAccounting Pro - Phase 18 Tasks Part 2

## CURSORS, NOTIFICATIONS & ACTIVITY FEED

---

## TASK 6: CURSOR TRACKING

### 6.1 Cursor Manager

**File:** `backend/app/realtime/managers/cursor_manager.py`

```python
"""
Cursor Manager
Manages cursor positions for collaborative editing
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
import redis
import json
import hashlib

logger = logging.getLogger(__name__)


# Predefined colors for cursor assignment
CURSOR_COLORS = [
    '#FF6B6B',  # Red
    '#4ECDC4',  # Teal
    '#45B7D1',  # Blue
    '#96CEB4',  # Green
    '#FFEAA7',  # Yellow
    '#DDA0DD',  # Plum
    '#98D8C8',  # Mint
    '#F7DC6F',  # Gold
    '#BB8FCE',  # Purple
    '#85C1E9',  # Sky Blue
]


class CursorPosition:
    """Represents a cursor position"""
    
    def __init__(
        self,
        user_id: str,
        user_name: str,
        color: str,
        line: int = 0,
        column: int = 0,
        selection_start: dict = None,
        selection_end: dict = None,
    ):
        self.user_id = user_id
        self.user_name = user_name
        self.color = color
        self.line = line
        self.column = column
        self.selection_start = selection_start
        self.selection_end = selection_end
        self.last_update = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'color': self.color,
            'line': self.line,
            'column': self.column,
            'selection_start': self.selection_start,
            'selection_end': self.selection_end,
            'last_update': self.last_update.isoformat(),
        }


class CursorManager:
    """Manages cursor positions for rooms"""
    
    CURSOR_KEY = 'cursor:{room_id}:{user_id}'
    ROOM_CURSORS_KEY = 'cursors:{room_id}'
    CURSOR_TTL = 300  # 5 minutes
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def get_user_color(self, user_id: str) -> str:
        """Get consistent color for a user"""
        # Use hash of user_id to get consistent color
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return CURSOR_COLORS[hash_val % len(CURSOR_COLORS)]
    
    def update_cursor(
        self,
        room_id: str,
        user_id: str,
        user_name: str,
        line: int,
        column: int,
        selection_start: dict = None,
        selection_end: dict = None,
    ) -> CursorPosition:
        """Update cursor position"""
        color = self.get_user_color(user_id)
        
        cursor = CursorPosition(
            user_id=user_id,
            user_name=user_name,
            color=color,
            line=line,
            column=column,
            selection_start=selection_start,
            selection_end=selection_end,
        )
        
        # Store in Redis
        key = self.CURSOR_KEY.format(room_id=room_id, user_id=user_id)
        self.redis.set(key, json.dumps(cursor.to_dict()), ex=self.CURSOR_TTL)
        
        # Add to room's cursor set
        room_key = self.ROOM_CURSORS_KEY.format(room_id=room_id)
        self.redis.sadd(room_key, user_id)
        self.redis.expire(room_key, self.CURSOR_TTL)
        
        return cursor
    
    def get_cursor(self, room_id: str, user_id: str) -> Optional[CursorPosition]:
        """Get cursor position for a user"""
        key = self.CURSOR_KEY.format(room_id=room_id, user_id=user_id)
        data = self.redis.get(key)
        
        if not data:
            return None
        
        cursor_data = json.loads(data)
        
        return CursorPosition(
            user_id=cursor_data['user_id'],
            user_name=cursor_data['user_name'],
            color=cursor_data['color'],
            line=cursor_data['line'],
            column=cursor_data['column'],
            selection_start=cursor_data.get('selection_start'),
            selection_end=cursor_data.get('selection_end'),
        )
    
    def get_room_cursors(self, room_id: str) -> List[CursorPosition]:
        """Get all cursors in a room"""
        room_key = self.ROOM_CURSORS_KEY.format(room_id=room_id)
        user_ids = self.redis.smembers(room_key)
        
        cursors = []
        for user_id in user_ids:
            cursor = self.get_cursor(room_id, user_id)
            if cursor:
                cursors.append(cursor)
        
        return cursors
    
    def remove_cursor(self, room_id: str, user_id: str):
        """Remove cursor when user leaves room"""
        key = self.CURSOR_KEY.format(room_id=room_id, user_id=user_id)
        self.redis.delete(key)
        
        room_key = self.ROOM_CURSORS_KEY.format(room_id=room_id)
        self.redis.srem(room_key, user_id)
    
    def clear_room_cursors(self, room_id: str):
        """Clear all cursors in a room"""
        room_key = self.ROOM_CURSORS_KEY.format(room_id=room_id)
        user_ids = self.redis.smembers(room_key)
        
        pipe = self.redis.pipeline()
        for user_id in user_ids:
            key = self.CURSOR_KEY.format(room_id=room_id, user_id=user_id)
            pipe.delete(key)
        
        pipe.delete(room_key)
        pipe.execute()


# Singleton
_cursor_manager: Optional[CursorManager] = None


def get_cursor_manager() -> CursorManager:
    """Get cursor manager singleton"""
    global _cursor_manager
    if _cursor_manager is None:
        import os
        redis_client = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True
        )
        _cursor_manager = CursorManager(redis_client)
    return _cursor_manager
```

### 6.2 Cursor Handler

**File:** `backend/app/realtime/handlers/cursor_handler.py`

```python
"""
Cursor Handler
Handle cursor-related WebSocket events
"""

import logging
from flask import request
from flask_socketio import SocketIO, emit

from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.managers.cursor_manager import get_cursor_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


def register_cursor_handlers(socketio: SocketIO):
    """Register cursor event handlers"""
    
    @socketio.on(MessageType.CURSOR_MOVE.value)
    def handle_cursor_move(data):
        """Handle cursor position update"""
        sid = request.sid
        
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
        
        # Update cursor in manager
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
        
        # Broadcast to room (except sender)
        socketio.emit(
            MessageType.CURSOR_MOVE.value,
            cursor.to_dict(),
            room=room_id,
            skip_sid=sid,
        )
    
    @socketio.on(MessageType.CURSOR_SYNC.value)
    def handle_cursor_sync_request(data):
        """Handle request for all cursors in room"""
        sid = request.sid
        
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)
        
        if not connection:
            emit('error', {'message': 'Not authenticated'})
            return
        
        room_id = data.get('room_id')
        
        if not room_id:
            emit('error', {'message': 'room_id required'})
            return
        
        # Get all cursors
        cursor_manager = get_cursor_manager()
        cursors = cursor_manager.get_room_cursors(room_id)
        
        # Exclude requester's cursor
        other_cursors = [
            c.to_dict() for c in cursors
            if c.user_id != connection.user_id
        ]
        
        emit(MessageType.CURSOR_SYNC.value, {
            'room_id': room_id,
            'cursors': other_cursors,
        })
    
    @socketio.on(MessageType.CURSOR_REMOVE.value)
    def handle_cursor_remove(data):
        """Handle cursor removal (user left room)"""
        sid = request.sid
        
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)
        
        if not connection:
            return
        
        room_id = data.get('room_id')
        
        if not room_id:
            return
        
        # Remove cursor
        cursor_manager = get_cursor_manager()
        cursor_manager.remove_cursor(room_id, connection.user_id)
        
        # Notify room
        socketio.emit(
            MessageType.CURSOR_REMOVE.value,
            {'user_id': connection.user_id},
            room=room_id,
            skip_sid=sid,
        )
```

---

## TASK 7: NOTIFICATION SYSTEM

### 7.1 Notification Model

**File:** `backend/app/realtime/models/notification.py`

```python
"""
Notification Model
Real-time notifications
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class Notification(db.Model):
    """Real-time notification model"""
    
    __tablename__ = 'realtime_notifications'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Notification Type
    type = Column(String(50), nullable=False)
    
    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text)
    
    # Source
    source_type = Column(String(50))
    source_id = Column(UUID(as_uuid=True))
    
    # Action
    action_url = Column(String(500))
    action_label = Column(String(100))
    
    # Priority
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(db.DateTime)
    
    # Delivery status
    delivered_websocket = Column(Boolean, default=False)
    delivered_push = Column(Boolean, default=False)
    delivered_email = Column(Boolean, default=False)
    
    # Expiration
    expires_at = Column(db.DateTime)
    
    created_at = Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Notification Types
    TYPES = {
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
    
    @property
    def is_expired(self) -> bool:
        """Check if notification has expired"""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.utcnow()
    
    def mark_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'source_type': self.source_type,
            'source_id': str(self.source_id) if self.source_id else None,
            'action_url': self.action_url,
            'action_label': self.action_label,
            'priority': self.priority,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PushSubscription(db.Model):
    """Push notification subscription"""
    
    __tablename__ = 'push_subscriptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Subscription Details
    endpoint = Column(String(500), nullable=False)
    p256dh_key = Column(String(255), nullable=False)
    auth_key = Column(String(255), nullable=False)
    
    # Device Info
    device_type = Column(String(20))
    device_name = Column(String(100))
    browser = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(db.DateTime, default=datetime.utcnow)
    last_used_at = Column(db.DateTime)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'endpoint', name='uq_push_user_endpoint'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'device_type': self.device_type,
            'device_name': self.device_name,
            'browser': self.browser,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
```

### 7.2 Notification Service

**File:** `backend/app/realtime/services/notification_service.py`

```python
"""
Notification Service
Create and deliver notifications
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

from app.extensions import db
from app.realtime.models.notification import Notification, PushSubscription
from app.realtime.server import get_socketio
from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for creating and delivering notifications"""
    
    @staticmethod
    def create_notification(
        user_id: str,
        tenant_id: str,
        type: str,
        title: str,
        message: str = None,
        source_type: str = None,
        source_id: str = None,
        action_url: str = None,
        action_label: str = None,
        priority: str = None,
        expires_in_days: int = 30,
    ) -> Notification:
        """Create and deliver a notification"""
        # Get notification config
        config = Notification.TYPES.get(type, {'priority': 'normal', 'channels': ['websocket']})
        
        if priority is None:
            priority = config['priority']
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            tenant_id=tenant_id,
            type=type,
            title=title,
            message=message,
            source_type=source_type,
            source_id=source_id,
            action_url=action_url,
            action_label=action_label,
            priority=priority,
            expires_at=expires_at,
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Deliver via channels
        channels = config['channels']
        
        if 'websocket' in channels:
            NotificationService._deliver_websocket(notification)
        
        if 'push' in channels:
            NotificationService._deliver_push(notification)
        
        if 'email' in channels and priority in ['high', 'urgent']:
            # Email delivery is async via Celery
            from app.realtime.tasks.notification_tasks import send_notification_email
            send_notification_email.delay(str(notification.id))
        
        logger.info(f"Notification created: {notification.id} for user {user_id}")
        
        return notification
    
    @staticmethod
    def _deliver_websocket(notification: Notification):
        """Deliver notification via WebSocket"""
        try:
            socketio = get_socketio()
            conn_manager = get_connection_manager()
            
            # Get user's active sessions
            user_sids = conn_manager.get_user_sids(str(notification.user_id))
            
            if user_sids:
                # Send to all user's connections
                for sid in user_sids:
                    socketio.emit(
                        MessageType.NOTIFICATION.value,
                        notification.to_dict(),
                        room=sid,
                    )
                
                notification.delivered_websocket = True
                db.session.commit()
                
                logger.debug(f"Notification {notification.id} delivered via WebSocket")
        except Exception as e:
            logger.error(f"WebSocket delivery failed: {e}")
    
    @staticmethod
    def _deliver_push(notification: Notification):
        """Deliver notification via Web Push"""
        try:
            from pywebpush import webpush, WebPushException
            import os
            
            # Get user's push subscriptions
            subscriptions = PushSubscription.query.filter(
                PushSubscription.user_id == notification.user_id,
                PushSubscription.is_active == True,
            ).all()
            
            if not subscriptions:
                return
            
            # Prepare push payload
            payload = json.dumps({
                'title': notification.title,
                'body': notification.message or '',
                'icon': '/static/images/icon-192.png',
                'badge': '/static/images/badge-72.png',
                'data': {
                    'notification_id': str(notification.id),
                    'action_url': notification.action_url,
                },
            })
            
            vapid_private_key = os.getenv('VAPID_PRIVATE_KEY')
            vapid_claims = {
                'sub': f"mailto:{os.getenv('VAPID_CONTACT_EMAIL', 'admin@logiaccounting.com')}"
            }
            
            for subscription in subscriptions:
                try:
                    webpush(
                        subscription_info={
                            'endpoint': subscription.endpoint,
                            'keys': {
                                'p256dh': subscription.p256dh_key,
                                'auth': subscription.auth_key,
                            }
                        },
                        data=payload,
                        vapid_private_key=vapid_private_key,
                        vapid_claims=vapid_claims,
                    )
                    
                    subscription.last_used_at = datetime.utcnow()
                    
                except WebPushException as e:
                    logger.warning(f"Push failed for subscription {subscription.id}: {e}")
                    
                    # Disable invalid subscriptions
                    if e.response and e.response.status_code in [404, 410]:
                        subscription.is_active = False
            
            notification.delivered_push = True
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Push delivery failed: {e}")
    
    @staticmethod
    def get_notifications(
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = Notification.query.filter(
            Notification.user_id == user_id,
            db.or_(
                Notification.expires_at == None,
                Notification.expires_at > datetime.utcnow()
            )
        )
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(
            Notification.created_at.desc()
        ).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_unread_count(user_id: str) -> int:
        """Get unread notification count"""
        return Notification.query.filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            db.or_(
                Notification.expires_at == None,
                Notification.expires_at > datetime.utcnow()
            )
        ).count()
    
    @staticmethod
    def mark_read(notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        notification = Notification.query.filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        ).first()
        
        if notification:
            notification.mark_read()
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def mark_all_read(user_id: str) -> int:
        """Mark all notifications as read"""
        count = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow(),
        })
        
        db.session.commit()
        return count
    
    @staticmethod
    def delete_notification(notification_id: str, user_id: str) -> bool:
        """Delete a notification"""
        notification = Notification.query.filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        ).first()
        
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        
        return False


# Convenience functions for common notification types
def notify_payment_received(
    user_id: str,
    tenant_id: str,
    payment_amount: float,
    invoice_number: str,
    invoice_id: str,
):
    """Send payment received notification"""
    return NotificationService.create_notification(
        user_id=user_id,
        tenant_id=tenant_id,
        type='payment_received',
        title='Payment Received',
        message=f'Payment of ${payment_amount:,.2f} received for Invoice #{invoice_number}',
        source_type='invoice',
        source_id=invoice_id,
        action_url=f'/invoices/{invoice_id}',
        action_label='View Invoice',
    )


def notify_invoice_overdue(
    user_id: str,
    tenant_id: str,
    invoice_number: str,
    invoice_id: str,
    days_overdue: int,
):
    """Send invoice overdue notification"""
    return NotificationService.create_notification(
        user_id=user_id,
        tenant_id=tenant_id,
        type='invoice_overdue',
        title='Invoice Overdue',
        message=f'Invoice #{invoice_number} is {days_overdue} days overdue',
        source_type='invoice',
        source_id=invoice_id,
        action_url=f'/invoices/{invoice_id}',
        action_label='View Invoice',
        priority='high',
    )


def notify_mention(
    user_id: str,
    tenant_id: str,
    mentioned_by: str,
    context: str,
    entity_type: str,
    entity_id: str,
    entity_url: str,
):
    """Send mention notification"""
    return NotificationService.create_notification(
        user_id=user_id,
        tenant_id=tenant_id,
        type='mention',
        title=f'{mentioned_by} mentioned you',
        message=context,
        source_type=entity_type,
        source_id=entity_id,
        action_url=entity_url,
        action_label='View',
    )
```

### 7.3 Notification Handler

**File:** `backend/app/realtime/handlers/notification_handler.py`

```python
"""
Notification Handler
Handle notification-related WebSocket events
"""

import logging
from flask import request
from flask_socketio import SocketIO, emit

from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.services.notification_service import NotificationService
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


def register_notification_handlers(socketio: SocketIO):
    """Register notification event handlers"""
    
    @socketio.on(MessageType.NOTIFICATION_READ.value)
    def handle_notification_read(data):
        """Handle marking notification as read"""
        sid = request.sid
        
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)
        
        if not connection:
            emit('error', {'message': 'Not authenticated'})
            return
        
        notification_id = data.get('notification_id')
        
        if not notification_id:
            emit('error', {'message': 'notification_id required'})
            return
        
        success = NotificationService.mark_read(
            notification_id,
            connection.user_id
        )
        
        if success:
            # Update unread count for all user's connections
            unread_count = NotificationService.get_unread_count(connection.user_id)
            
            user_sids = conn_manager.get_user_sids(connection.user_id)
            for user_sid in user_sids:
                socketio.emit(
                    MessageType.NOTIFICATION_COUNT.value,
                    {'count': unread_count},
                    room=user_sid,
                )
    
    @socketio.on(MessageType.NOTIFICATION_COUNT.value)
    def handle_notification_count_request():
        """Handle request for unread notification count"""
        sid = request.sid
        
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)
        
        if not connection:
            emit('error', {'message': 'Not authenticated'})
            return
        
        unread_count = NotificationService.get_unread_count(connection.user_id)
        
        emit(MessageType.NOTIFICATION_COUNT.value, {'count': unread_count})
```

---

## TASK 8: ACTIVITY FEED

### 8.1 Activity Model

**File:** `backend/app/realtime/models/activity.py`

```python
"""
Activity Feed Model
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.extensions import db
import uuid


class Activity(db.Model):
    """Activity feed item"""
    
    __tablename__ = 'activity_feed'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Actor
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    user_name = Column(String(100))
    
    # Action
    action = Column(String(50), nullable=False)
    # 'created', 'updated', 'deleted', 'commented', 'assigned', 'completed', 'sent', 'paid'
    
    # Target
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_name = Column(String(255))
    
    # Details
    details = Column(JSONB)
    
    # Visibility
    visibility = Column(String(20), default='team')  # 'private', 'team', 'public'
    visible_to = Column(ARRAY(UUID(as_uuid=True)))  # Specific users if private
    
    # Timestamp
    created_at = Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Action display names
    ACTION_LABELS = {
        'created': 'created',
        'updated': 'updated',
        'deleted': 'deleted',
        'commented': 'commented on',
        'assigned': 'assigned',
        'completed': 'completed',
        'sent': 'sent',
        'paid': 'marked as paid',
        'uploaded': 'uploaded',
        'shared': 'shared',
    }
    
    @property
    def action_label(self) -> str:
        """Get human-readable action label"""
        return self.ACTION_LABELS.get(self.action, self.action)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'user_name': self.user_name,
            'action': self.action,
            'action_label': self.action_label,
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id),
            'entity_name': self.entity_name,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
```

### 8.2 Activity Service

**File:** `backend/app/realtime/services/activity_service.py`

```python
"""
Activity Service
Create and retrieve activity feed items
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from app.extensions import db
from app.realtime.models.activity import Activity
from app.realtime.server import get_socketio
from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


class ActivityService:
    """Service for activity feed operations"""
    
    @staticmethod
    def log_activity(
        tenant_id: str,
        user_id: str,
        user_name: str,
        action: str,
        entity_type: str,
        entity_id: str,
        entity_name: str = None,
        details: Dict[str, Any] = None,
        visibility: str = 'team',
        visible_to: List[str] = None,
        broadcast: bool = True,
    ) -> Activity:
        """Log an activity and optionally broadcast it"""
        activity = Activity(
            tenant_id=tenant_id,
            user_id=user_id,
            user_name=user_name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            details=details,
            visibility=visibility,
            visible_to=visible_to,
        )
        
        db.session.add(activity)
        db.session.commit()
        
        if broadcast:
            ActivityService._broadcast_activity(activity)
        
        logger.debug(f"Activity logged: {user_name} {action} {entity_type} {entity_id}")
        
        return activity
    
    @staticmethod
    def _broadcast_activity(activity: Activity):
        """Broadcast activity to relevant users"""
        try:
            socketio = get_socketio()
            
            # Broadcast to tenant room
            tenant_room = f"tenant:{activity.tenant_id}"
            
            socketio.emit(
                MessageType.ACTIVITY.value,
                activity.to_dict(),
                room=tenant_room,
            )
            
        except Exception as e:
            logger.error(f"Activity broadcast failed: {e}")
    
    @staticmethod
    def get_feed(
        tenant_id: str,
        user_id: str = None,
        entity_type: str = None,
        entity_id: str = None,
        limit: int = 50,
        offset: int = 0,
        since: datetime = None,
    ) -> List[Activity]:
        """Get activity feed"""
        query = Activity.query.filter(Activity.tenant_id == tenant_id)
        
        if user_id:
            # Filter by visibility for this user
            query = query.filter(
                db.or_(
                    Activity.visibility == 'team',
                    Activity.visibility == 'public',
                    Activity.user_id == user_id,
                    Activity.visible_to.contains([user_id]),
                )
            )
        
        if entity_type:
            query = query.filter(Activity.entity_type == entity_type)
        
        if entity_id:
            query = query.filter(Activity.entity_id == entity_id)
        
        if since:
            query = query.filter(Activity.created_at > since)
        
        return query.order_by(
            Activity.created_at.desc()
        ).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_entity_activity(
        tenant_id: str,
        entity_type: str,
        entity_id: str,
        limit: int = 20,
    ) -> List[Activity]:
        """Get activity for a specific entity"""
        return Activity.query.filter(
            Activity.tenant_id == tenant_id,
            Activity.entity_type == entity_type,
            Activity.entity_id == entity_id,
        ).order_by(
            Activity.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_user_activity(
        tenant_id: str,
        user_id: str,
        limit: int = 50,
    ) -> List[Activity]:
        """Get activity by a specific user"""
        return Activity.query.filter(
            Activity.tenant_id == tenant_id,
            Activity.user_id == user_id,
        ).order_by(
            Activity.created_at.desc()
        ).limit(limit).all()


# Convenience functions
def log_invoice_created(tenant_id: str, user_id: str, user_name: str, invoice_id: str, invoice_number: str):
    """Log invoice creation activity"""
    return ActivityService.log_activity(
        tenant_id=tenant_id,
        user_id=user_id,
        user_name=user_name,
        action='created',
        entity_type='invoice',
        entity_id=invoice_id,
        entity_name=f'Invoice #{invoice_number}',
    )


def log_payment_received(tenant_id: str, user_id: str, user_name: str, payment_id: str, amount: float, invoice_number: str):
    """Log payment received activity"""
    return ActivityService.log_activity(
        tenant_id=tenant_id,
        user_id=user_id,
        user_name=user_name,
        action='paid',
        entity_type='payment',
        entity_id=payment_id,
        entity_name=f'Payment ${amount:,.2f}',
        details={
            'amount': amount,
            'invoice_number': invoice_number,
        },
    )


def log_project_completed(tenant_id: str, user_id: str, user_name: str, project_id: str, project_name: str):
    """Log project completion activity"""
    return ActivityService.log_activity(
        tenant_id=tenant_id,
        user_id=user_id,
        user_name=user_name,
        action='completed',
        entity_type='project',
        entity_id=project_id,
        entity_name=project_name,
    )
```

---

## TASK 9: API ROUTES

### 9.1 Presence Routes

**File:** `backend/app/realtime/routes/presence.py`

```python
"""
Presence API Routes
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.realtime.managers.presence_manager import get_presence_manager
from app.tenancy.core.tenant_middleware import require_tenant

presence_bp = Blueprint('presence', __name__, url_prefix='/api/v1/presence')


@presence_bp.route('', methods=['GET'])
@jwt_required()
@require_tenant
def get_online_users():
    """Get online users for current tenant"""
    tenant = g.tenant
    
    presence_manager = get_presence_manager()
    online_users = presence_manager.get_online_users(str(tenant.id))
    
    return jsonify({
        'success': True,
        'users': online_users,
        'count': len(online_users),
    })


@presence_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
@require_tenant
def get_user_presence(user_id):
    """Get specific user's presence"""
    tenant = g.tenant
    
    presence_manager = get_presence_manager()
    presence = presence_manager.get_presence(user_id, str(tenant.id))
    
    if not presence:
        return jsonify({
            'success': True,
            'presence': {
                'user_id': user_id,
                'status': 'offline',
            },
        })
    
    return jsonify({
        'success': True,
        'presence': presence.to_dict(),
    })


@presence_bp.route('/status', methods=['PUT'])
@jwt_required()
@require_tenant
def update_status():
    """Update own presence status"""
    user_id = get_jwt_identity()
    tenant = g.tenant
    data = request.get_json()
    
    status = data.get('status')
    
    if status not in ['online', 'away', 'busy']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    presence_manager = get_presence_manager()
    
    if status == 'busy':
        presence = presence_manager.set_busy(user_id, str(tenant.id))
    elif status == 'away':
        presence = presence_manager.set_away(user_id, str(tenant.id))
    else:
        presence = presence_manager.update_activity(user_id, str(tenant.id))
    
    if presence:
        return jsonify({
            'success': True,
            'presence': presence.to_dict(),
        })
    
    return jsonify({'success': False, 'error': 'Presence not found'}), 404
```

### 9.2 Notifications Routes

**File:** `backend/app/realtime/routes/notifications.py`

```python
"""
Notifications API Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.realtime.services.notification_service import NotificationService
from app.realtime.models.notification import PushSubscription
from app.extensions import db

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')


@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications for current user"""
    user_id = get_jwt_identity()
    
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    notifications = NotificationService.get_notifications(
        user_id=user_id,
        unread_only=unread_only,
        limit=min(limit, 100),
        offset=offset,
    )
    
    return jsonify({
        'success': True,
        'notifications': [n.to_dict() for n in notifications],
    })


@notifications_bp.route('/unread/count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get unread notification count"""
    user_id = get_jwt_identity()
    
    count = NotificationService.get_unread_count(user_id)
    
    return jsonify({
        'success': True,
        'count': count,
    })


@notifications_bp.route('/<notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_read(notification_id):
    """Mark notification as read"""
    user_id = get_jwt_identity()
    
    success = NotificationService.mark_read(notification_id, user_id)
    
    if success:
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Notification not found'}), 404


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_read():
    """Mark all notifications as read"""
    user_id = get_jwt_identity()
    
    count = NotificationService.mark_all_read(user_id)
    
    return jsonify({
        'success': True,
        'marked_count': count,
    })


@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Delete a notification"""
    user_id = get_jwt_identity()
    
    success = NotificationService.delete_notification(notification_id, user_id)
    
    if success:
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Notification not found'}), 404


# Push Subscription endpoints
@notifications_bp.route('/push/subscribe', methods=['POST'])
@jwt_required()
def subscribe_push():
    """Subscribe to push notifications"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    endpoint = data.get('endpoint')
    keys = data.get('keys', {})
    
    if not endpoint or not keys.get('p256dh') or not keys.get('auth'):
        return jsonify({'success': False, 'error': 'Invalid subscription data'}), 400
    
    # Check if subscription exists
    existing = PushSubscription.query.filter(
        PushSubscription.user_id == user_id,
        PushSubscription.endpoint == endpoint,
    ).first()
    
    if existing:
        existing.is_active = True
        existing.p256dh_key = keys['p256dh']
        existing.auth_key = keys['auth']
    else:
        subscription = PushSubscription(
            user_id=user_id,
            endpoint=endpoint,
            p256dh_key=keys['p256dh'],
            auth_key=keys['auth'],
            device_type=data.get('device_type'),
            device_name=data.get('device_name'),
            browser=data.get('browser'),
        )
        db.session.add(subscription)
    
    db.session.commit()
    
    return jsonify({'success': True})


@notifications_bp.route('/push/unsubscribe', methods=['DELETE'])
@jwt_required()
def unsubscribe_push():
    """Unsubscribe from push notifications"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    endpoint = data.get('endpoint')
    
    if endpoint:
        # Unsubscribe specific endpoint
        PushSubscription.query.filter(
            PushSubscription.user_id == user_id,
            PushSubscription.endpoint == endpoint,
        ).update({'is_active': False})
    else:
        # Unsubscribe all
        PushSubscription.query.filter(
            PushSubscription.user_id == user_id,
        ).update({'is_active': False})
    
    db.session.commit()
    
    return jsonify({'success': True})
```

### 9.3 Activity Routes

**File:** `backend/app/realtime/routes/activity.py`

```python
"""
Activity Feed API Routes
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.realtime.services.activity_service import ActivityService
from app.tenancy.core.tenant_middleware import require_tenant

activity_bp = Blueprint('activity', __name__, url_prefix='/api/v1/activity')


@activity_bp.route('', methods=['GET'])
@jwt_required()
@require_tenant
def get_activity_feed():
    """Get activity feed for current tenant"""
    user_id = get_jwt_identity()
    tenant = g.tenant
    
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    entity_type = request.args.get('entity_type')
    since = request.args.get('since')
    
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError:
            pass
    
    activities = ActivityService.get_feed(
        tenant_id=str(tenant.id),
        user_id=user_id,
        entity_type=entity_type,
        limit=min(limit, 100),
        offset=offset,
        since=since_dt,
    )
    
    return jsonify({
        'success': True,
        'activities': [a.to_dict() for a in activities],
    })


@activity_bp.route('/entity/<entity_type>/<entity_id>', methods=['GET'])
@jwt_required()
@require_tenant
def get_entity_activity(entity_type, entity_id):
    """Get activity for specific entity"""
    tenant = g.tenant
    
    limit = request.args.get('limit', 20, type=int)
    
    activities = ActivityService.get_entity_activity(
        tenant_id=str(tenant.id),
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )
    
    return jsonify({
        'success': True,
        'activities': [a.to_dict() for a in activities],
    })
```

---

## Continue to Part 3 for Frontend Components

---

*Phase 18 Tasks Part 2 - LogiAccounting Pro*
*Cursors, Notifications & Activity Feed*
