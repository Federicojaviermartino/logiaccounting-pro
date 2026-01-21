# LogiAccounting Pro - Phase 18 Tasks Part 1

## WEBSOCKET SERVER & PRESENCE SYSTEM

---

## TASK 1: WEBSOCKET SERVER SETUP

### 1.1 Socket.IO Server Configuration

**File:** `backend/app/realtime/server.py`

```python
"""
WebSocket Server
Socket.IO server with Redis adapter for horizontal scaling
"""

import os
import logging
from flask import Flask
from flask_socketio import SocketIO
import redis

logger = logging.getLogger(__name__)

# Socket.IO instance
socketio = SocketIO()


def init_socketio(app: Flask):
    """Initialize Socket.IO with Flask app"""
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    socketio.init_app(
        app,
        cors_allowed_origins=os.getenv('CORS_ORIGINS', '*').split(','),
        async_mode='eventlet',
        message_queue=redis_url,
        logger=True,
        engineio_logger=True,
        ping_timeout=30,
        ping_interval=25,
        max_http_buffer_size=1024 * 1024,  # 1MB
    )
    
    # Register event handlers
    from app.realtime.handlers import register_handlers
    register_handlers(socketio)
    
    logger.info("Socket.IO server initialized")
    
    return socketio


def get_socketio():
    """Get Socket.IO instance"""
    return socketio
```

### 1.2 Message Types Definition

**File:** `backend/app/realtime/utils/message_types.py`

```python
"""
WebSocket Message Types
Defines all message types and their schemas
"""

from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime


class MessageType(str, Enum):
    """WebSocket message types"""
    
    # Connection
    CONNECT = 'connect'
    DISCONNECT = 'disconnect'
    ERROR = 'error'
    
    # Presence
    PRESENCE_UPDATE = 'presence:update'
    PRESENCE_LIST = 'presence:list'
    PRESENCE_USER_JOINED = 'presence:user_joined'
    PRESENCE_USER_LEFT = 'presence:user_left'
    
    # Rooms
    ROOM_JOIN = 'room:join'
    ROOM_LEAVE = 'room:leave'
    ROOM_USERS = 'room:users'
    ROOM_USER_JOINED = 'room:user_joined'
    ROOM_USER_LEFT = 'room:user_left'
    
    # Cursors
    CURSOR_MOVE = 'cursor:move'
    CURSOR_SYNC = 'cursor:sync'
    CURSOR_REMOVE = 'cursor:remove'
    
    # Documents/Collaboration
    DOC_EDIT = 'doc:edit'
    DOC_SYNC = 'doc:sync'
    DOC_LOCK = 'doc:lock'
    DOC_UNLOCK = 'doc:unlock'
    DOC_LOCK_STATUS = 'doc:lock_status'
    
    # Notifications
    NOTIFICATION = 'notification'
    NOTIFICATION_READ = 'notification:read'
    NOTIFICATION_COUNT = 'notification:count'
    
    # Activity
    ACTIVITY = 'activity'
    ACTIVITY_FEED = 'activity:feed'
    
    # Typing
    TYPING_START = 'typing:start'
    TYPING_STOP = 'typing:stop'
    TYPING_USERS = 'typing:users'


class PresenceStatus(str, Enum):
    """User presence status"""
    ONLINE = 'online'
    AWAY = 'away'
    BUSY = 'busy'
    OFFLINE = 'offline'


@dataclass
class PresenceData:
    """User presence data structure"""
    user_id: str
    status: PresenceStatus
    last_active_at: str
    current_page: Optional[str] = None
    current_entity_type: Optional[str] = None
    current_entity_id: Optional[str] = None
    device_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CursorPosition:
    """Cursor position data"""
    user_id: str
    user_name: str
    color: str
    line: int
    column: int
    selection_start: Optional[Dict[str, int]] = None
    selection_end: Optional[Dict[str, int]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationMessage:
    """Notification message structure"""
    id: str
    type: str
    title: str
    message: Optional[str]
    priority: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    action_url: Optional[str] = None
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ActivityItem:
    """Activity feed item"""
    id: str
    user_id: str
    user_name: str
    action: str
    entity_type: str
    entity_id: str
    entity_name: str
    details: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RoomInfo:
    """Room information"""
    room_id: str
    entity_type: str
    entity_id: str
    users: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
```

---

## TASK 2: CONNECTION MANAGER

### 2.1 Connection Manager Implementation

**File:** `backend/app/realtime/managers/connection_manager.py`

```python
"""
Connection Manager
Manages WebSocket connections and authentication
"""

import logging
from typing import Dict, Optional, Set, List
from datetime import datetime
from dataclasses import dataclass, field
import redis
import json

from flask_socketio import SocketIO
from flask_jwt_extended import decode_token

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """Represents a WebSocket connection"""
    sid: str
    user_id: str
    tenant_id: str
    user_name: str
    user_email: str
    connected_at: datetime
    device_type: str = 'desktop'
    browser: str = 'unknown'
    ip_address: str = ''
    rooms: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> dict:
        return {
            'sid': self.sid,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'user_name': self.user_name,
            'connected_at': self.connected_at.isoformat(),
            'device_type': self.device_type,
            'browser': self.browser,
        }


class ConnectionManager:
    """Manages all WebSocket connections"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.local_connections: Dict[str, Connection] = {}
        
        # Redis keys
        self.CONNECTIONS_KEY = 'ws:connections'
        self.USER_CONNECTIONS_KEY = 'ws:user:{user_id}:connections'
        self.TENANT_CONNECTIONS_KEY = 'ws:tenant:{tenant_id}:connections'
    
    def authenticate(self, token: str) -> Optional[dict]:
        """
        Authenticate WebSocket connection using JWT token
        
        Args:
            token: JWT token from client
            
        Returns:
            User data if valid, None otherwise
        """
        try:
            if not token:
                return None
            
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decode JWT token
            decoded = decode_token(token)
            
            return {
                'user_id': decoded.get('sub'),
                'tenant_id': decoded.get('tenant_id'),
                'user_name': decoded.get('name', 'Unknown'),
                'user_email': decoded.get('email', ''),
                'role': decoded.get('role', 'user'),
            }
            
        except Exception as e:
            logger.warning(f"WebSocket auth failed: {e}")
            return None
    
    def add_connection(
        self,
        sid: str,
        user_data: dict,
        device_type: str = 'desktop',
        browser: str = 'unknown',
        ip_address: str = ''
    ) -> Connection:
        """Add a new connection"""
        connection = Connection(
            sid=sid,
            user_id=user_data['user_id'],
            tenant_id=user_data['tenant_id'],
            user_name=user_data['user_name'],
            user_email=user_data.get('user_email', ''),
            connected_at=datetime.utcnow(),
            device_type=device_type,
            browser=browser,
            ip_address=ip_address,
        )
        
        # Store locally
        self.local_connections[sid] = connection
        
        # Store in Redis for cross-server access
        self._store_connection_redis(connection)
        
        logger.info(f"Connection added: {sid} for user {connection.user_id}")
        
        return connection
    
    def remove_connection(self, sid: str) -> Optional[Connection]:
        """Remove a connection"""
        connection = self.local_connections.pop(sid, None)
        
        if connection:
            self._remove_connection_redis(connection)
            logger.info(f"Connection removed: {sid}")
        
        return connection
    
    def get_connection(self, sid: str) -> Optional[Connection]:
        """Get connection by SID"""
        return self.local_connections.get(sid)
    
    def get_user_connections(self, user_id: str) -> List[Connection]:
        """Get all connections for a user"""
        return [
            conn for conn in self.local_connections.values()
            if conn.user_id == user_id
        ]
    
    def get_user_sids(self, user_id: str) -> List[str]:
        """Get all SIDs for a user (including from other servers)"""
        key = self.USER_CONNECTIONS_KEY.format(user_id=user_id)
        sids = self.redis.smembers(key)
        return [sid.decode() if isinstance(sid, bytes) else sid for sid in sids]
    
    def get_tenant_connections(self, tenant_id: str) -> List[Connection]:
        """Get all connections for a tenant"""
        return [
            conn for conn in self.local_connections.values()
            if conn.tenant_id == tenant_id
        ]
    
    def get_tenant_sids(self, tenant_id: str) -> List[str]:
        """Get all SIDs for a tenant (including from other servers)"""
        key = self.TENANT_CONNECTIONS_KEY.format(tenant_id=tenant_id)
        sids = self.redis.smembers(key)
        return [sid.decode() if isinstance(sid, bytes) else sid for sid in sids]
    
    def get_online_user_ids(self, tenant_id: str) -> Set[str]:
        """Get unique online user IDs for a tenant"""
        connections = self.get_tenant_connections(tenant_id)
        return {conn.user_id for conn in connections}
    
    def add_to_room(self, sid: str, room: str):
        """Add connection to a room"""
        connection = self.local_connections.get(sid)
        if connection:
            connection.rooms.add(room)
    
    def remove_from_room(self, sid: str, room: str):
        """Remove connection from a room"""
        connection = self.local_connections.get(sid)
        if connection and room in connection.rooms:
            connection.rooms.discard(room)
    
    def get_connection_count(self) -> int:
        """Get total connection count"""
        return len(self.local_connections)
    
    def _store_connection_redis(self, connection: Connection):
        """Store connection in Redis"""
        pipe = self.redis.pipeline()
        
        # Add to user's connections
        user_key = self.USER_CONNECTIONS_KEY.format(user_id=connection.user_id)
        pipe.sadd(user_key, connection.sid)
        pipe.expire(user_key, 86400)  # 24 hour TTL
        
        # Add to tenant's connections
        tenant_key = self.TENANT_CONNECTIONS_KEY.format(tenant_id=connection.tenant_id)
        pipe.sadd(tenant_key, connection.sid)
        pipe.expire(tenant_key, 86400)
        
        # Store connection details
        conn_key = f"ws:conn:{connection.sid}"
        pipe.hset(conn_key, mapping={
            'user_id': connection.user_id,
            'tenant_id': connection.tenant_id,
            'user_name': connection.user_name,
            'connected_at': connection.connected_at.isoformat(),
        })
        pipe.expire(conn_key, 86400)
        
        pipe.execute()
    
    def _remove_connection_redis(self, connection: Connection):
        """Remove connection from Redis"""
        pipe = self.redis.pipeline()
        
        # Remove from user's connections
        user_key = self.USER_CONNECTIONS_KEY.format(user_id=connection.user_id)
        pipe.srem(user_key, connection.sid)
        
        # Remove from tenant's connections
        tenant_key = self.TENANT_CONNECTIONS_KEY.format(tenant_id=connection.tenant_id)
        pipe.srem(tenant_key, connection.sid)
        
        # Remove connection details
        pipe.delete(f"ws:conn:{connection.sid}")
        
        pipe.execute()


# Singleton instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get connection manager singleton"""
    global _connection_manager
    if _connection_manager is None:
        redis_client = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True
        )
        _connection_manager = ConnectionManager(redis_client)
    return _connection_manager


import os
```

---

## TASK 3: PRESENCE MANAGER

### 3.1 Presence Manager Implementation

**File:** `backend/app/realtime/managers/presence_manager.py`

```python
"""
Presence Manager
Manages user presence state using Redis
"""

import logging
from typing import Dict, Optional, List, Set
from datetime import datetime, timedelta
import redis
import json

from app.realtime.utils.message_types import PresenceStatus, PresenceData

logger = logging.getLogger(__name__)


class PresenceManager:
    """Manages user presence state"""
    
    # Timeouts
    AWAY_TIMEOUT_SECONDS = 300  # 5 minutes
    OFFLINE_TIMEOUT_SECONDS = 60  # 1 minute after disconnect
    
    # Redis keys
    PRESENCE_KEY = 'presence:{tenant_id}:{user_id}'
    TENANT_ONLINE_KEY = 'presence:online:{tenant_id}'
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def set_online(
        self,
        user_id: str,
        tenant_id: str,
        user_name: str,
        device_type: str = 'desktop',
        current_page: str = None
    ) -> PresenceData:
        """Set user as online"""
        presence = PresenceData(
            user_id=user_id,
            status=PresenceStatus.ONLINE,
            last_active_at=datetime.utcnow().isoformat(),
            current_page=current_page,
            device_type=device_type,
        )
        
        self._store_presence(tenant_id, presence, user_name)
        
        logger.debug(f"User {user_id} is now online")
        
        return presence
    
    def set_away(self, user_id: str, tenant_id: str) -> Optional[PresenceData]:
        """Set user as away"""
        presence = self.get_presence(user_id, tenant_id)
        
        if presence and presence.status == PresenceStatus.ONLINE:
            presence.status = PresenceStatus.AWAY
            self._update_presence_status(tenant_id, user_id, PresenceStatus.AWAY)
            logger.debug(f"User {user_id} is now away")
            return presence
        
        return presence
    
    def set_busy(self, user_id: str, tenant_id: str) -> Optional[PresenceData]:
        """Set user as busy (Do Not Disturb)"""
        presence = self.get_presence(user_id, tenant_id)
        
        if presence:
            presence.status = PresenceStatus.BUSY
            self._update_presence_status(tenant_id, user_id, PresenceStatus.BUSY)
            logger.debug(f"User {user_id} is now busy")
            return presence
        
        return presence
    
    def set_offline(self, user_id: str, tenant_id: str) -> Optional[PresenceData]:
        """Set user as offline"""
        presence = self.get_presence(user_id, tenant_id)
        
        if presence:
            presence.status = PresenceStatus.OFFLINE
            self._remove_presence(tenant_id, user_id)
            logger.debug(f"User {user_id} is now offline")
            return presence
        
        return None
    
    def update_activity(
        self,
        user_id: str,
        tenant_id: str,
        current_page: str = None,
        current_entity_type: str = None,
        current_entity_id: str = None
    ) -> Optional[PresenceData]:
        """Update user's last activity and location"""
        key = self.PRESENCE_KEY.format(tenant_id=tenant_id, user_id=user_id)
        
        updates = {
            'last_active_at': datetime.utcnow().isoformat(),
            'status': PresenceStatus.ONLINE.value,  # Reset to online on activity
        }
        
        if current_page:
            updates['current_page'] = current_page
        if current_entity_type:
            updates['current_entity_type'] = current_entity_type
        if current_entity_id:
            updates['current_entity_id'] = current_entity_id
        
        self.redis.hset(key, mapping=updates)
        
        return self.get_presence(user_id, tenant_id)
    
    def get_presence(self, user_id: str, tenant_id: str) -> Optional[PresenceData]:
        """Get user's presence data"""
        key = self.PRESENCE_KEY.format(tenant_id=tenant_id, user_id=user_id)
        data = self.redis.hgetall(key)
        
        if not data:
            return None
        
        return PresenceData(
            user_id=user_id,
            status=PresenceStatus(data.get('status', 'offline')),
            last_active_at=data.get('last_active_at', ''),
            current_page=data.get('current_page'),
            current_entity_type=data.get('current_entity_type'),
            current_entity_id=data.get('current_entity_id'),
            device_type=data.get('device_type'),
        )
    
    def get_online_users(self, tenant_id: str) -> List[Dict]:
        """Get all online users for a tenant"""
        key = self.TENANT_ONLINE_KEY.format(tenant_id=tenant_id)
        user_ids = self.redis.smembers(key)
        
        users = []
        for user_id in user_ids:
            presence = self.get_presence(user_id, tenant_id)
            if presence and presence.status != PresenceStatus.OFFLINE:
                # Get user name from stored data
                name_key = f"presence:name:{tenant_id}:{user_id}"
                user_name = self.redis.get(name_key) or 'Unknown'
                
                users.append({
                    'user_id': user_id,
                    'user_name': user_name,
                    'status': presence.status.value,
                    'current_page': presence.current_page,
                    'last_active_at': presence.last_active_at,
                })
        
        return users
    
    def get_users_viewing_entity(
        self,
        tenant_id: str,
        entity_type: str,
        entity_id: str
    ) -> List[Dict]:
        """Get users currently viewing a specific entity"""
        online_users = self.get_online_users(tenant_id)
        
        return [
            user for user in online_users
            if self._is_viewing_entity(user['user_id'], tenant_id, entity_type, entity_id)
        ]
    
    def check_inactive_users(self, tenant_id: str) -> List[str]:
        """Check for users that should be marked as away"""
        cutoff = datetime.utcnow() - timedelta(seconds=self.AWAY_TIMEOUT_SECONDS)
        cutoff_str = cutoff.isoformat()
        
        online_users = self.get_online_users(tenant_id)
        away_users = []
        
        for user in online_users:
            if user['status'] == PresenceStatus.ONLINE.value:
                if user['last_active_at'] < cutoff_str:
                    self.set_away(user['user_id'], tenant_id)
                    away_users.append(user['user_id'])
        
        return away_users
    
    def _store_presence(self, tenant_id: str, presence: PresenceData, user_name: str):
        """Store presence data in Redis"""
        key = self.PRESENCE_KEY.format(tenant_id=tenant_id, user_id=presence.user_id)
        
        pipe = self.redis.pipeline()
        
        # Store presence data
        pipe.hset(key, mapping={
            'status': presence.status.value,
            'last_active_at': presence.last_active_at,
            'current_page': presence.current_page or '',
            'current_entity_type': presence.current_entity_type or '',
            'current_entity_id': presence.current_entity_id or '',
            'device_type': presence.device_type or '',
        })
        pipe.expire(key, 86400)  # 24 hour TTL
        
        # Add to online users set
        online_key = self.TENANT_ONLINE_KEY.format(tenant_id=tenant_id)
        pipe.sadd(online_key, presence.user_id)
        pipe.expire(online_key, 86400)
        
        # Store user name
        name_key = f"presence:name:{tenant_id}:{presence.user_id}"
        pipe.set(name_key, user_name, ex=86400)
        
        pipe.execute()
    
    def _update_presence_status(self, tenant_id: str, user_id: str, status: PresenceStatus):
        """Update just the status field"""
        key = self.PRESENCE_KEY.format(tenant_id=tenant_id, user_id=user_id)
        self.redis.hset(key, 'status', status.value)
    
    def _remove_presence(self, tenant_id: str, user_id: str):
        """Remove presence data"""
        pipe = self.redis.pipeline()
        
        # Remove from online set
        online_key = self.TENANT_ONLINE_KEY.format(tenant_id=tenant_id)
        pipe.srem(online_key, user_id)
        
        # Delete presence data
        key = self.PRESENCE_KEY.format(tenant_id=tenant_id, user_id=user_id)
        pipe.delete(key)
        
        pipe.execute()
    
    def _is_viewing_entity(
        self,
        user_id: str,
        tenant_id: str,
        entity_type: str,
        entity_id: str
    ) -> bool:
        """Check if user is viewing specific entity"""
        key = self.PRESENCE_KEY.format(tenant_id=tenant_id, user_id=user_id)
        data = self.redis.hmget(key, 'current_entity_type', 'current_entity_id')
        
        return data[0] == entity_type and data[1] == entity_id


# Singleton
_presence_manager: Optional[PresenceManager] = None


def get_presence_manager() -> PresenceManager:
    """Get presence manager singleton"""
    global _presence_manager
    if _presence_manager is None:
        import os
        redis_client = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True
        )
        _presence_manager = PresenceManager(redis_client)
    return _presence_manager
```

---

## TASK 4: EVENT HANDLERS

### 4.1 Handler Registration

**File:** `backend/app/realtime/handlers/__init__.py`

```python
"""
WebSocket Event Handlers
Register all event handlers
"""

from flask_socketio import SocketIO

from .connection_handler import register_connection_handlers
from .presence_handler import register_presence_handlers
from .room_handler import register_room_handlers
from .cursor_handler import register_cursor_handlers
from .notification_handler import register_notification_handlers


def register_handlers(socketio: SocketIO):
    """Register all WebSocket event handlers"""
    register_connection_handlers(socketio)
    register_presence_handlers(socketio)
    register_room_handlers(socketio)
    register_cursor_handlers(socketio)
    register_notification_handlers(socketio)
```

### 4.2 Connection Handler

**File:** `backend/app/realtime/handlers/connection_handler.py`

```python
"""
Connection Handler
Handle WebSocket connect/disconnect events
"""

import logging
from flask import request
from flask_socketio import SocketIO, emit, disconnect

from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.managers.presence_manager import get_presence_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


def register_connection_handlers(socketio: SocketIO):
    """Register connection event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Handle new WebSocket connection"""
        sid = request.sid
        
        # Get auth token
        token = None
        if auth:
            token = auth.get('token')
        
        if not token:
            # Try from query string
            token = request.args.get('token')
        
        if not token:
            logger.warning(f"Connection rejected: No token provided (sid={sid})")
            disconnect()
            return False
        
        # Authenticate
        conn_manager = get_connection_manager()
        user_data = conn_manager.authenticate(token)
        
        if not user_data:
            logger.warning(f"Connection rejected: Invalid token (sid={sid})")
            disconnect()
            return False
        
        # Parse client info
        user_agent = request.headers.get('User-Agent', '')
        device_type = _parse_device_type(user_agent)
        browser = _parse_browser(user_agent)
        ip_address = request.remote_addr
        
        # Add connection
        connection = conn_manager.add_connection(
            sid=sid,
            user_data=user_data,
            device_type=device_type,
            browser=browser,
            ip_address=ip_address,
        )
        
        # Set user as online
        presence_manager = get_presence_manager()
        presence = presence_manager.set_online(
            user_id=user_data['user_id'],
            tenant_id=user_data['tenant_id'],
            user_name=user_data['user_name'],
            device_type=device_type,
        )
        
        # Join tenant room
        from flask_socketio import join_room
        tenant_room = f"tenant:{user_data['tenant_id']}"
        join_room(tenant_room)
        
        # Broadcast user came online to tenant
        socketio.emit(
            MessageType.PRESENCE_USER_JOINED.value,
            {
                'user_id': user_data['user_id'],
                'user_name': user_data['user_name'],
                'status': presence.status.value,
            },
            room=tenant_room,
            skip_sid=sid,
        )
        
        # Send current online users to the new connection
        online_users = presence_manager.get_online_users(user_data['tenant_id'])
        emit(MessageType.PRESENCE_LIST.value, {'users': online_users})
        
        logger.info(f"User {user_data['user_id']} connected (sid={sid})")
        
        return True
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnection"""
        sid = request.sid
        
        conn_manager = get_connection_manager()
        connection = conn_manager.remove_connection(sid)
        
        if connection:
            # Check if user has other connections
            user_connections = conn_manager.get_user_sids(connection.user_id)
            
            if not user_connections:
                # No more connections, set offline
                presence_manager = get_presence_manager()
                presence_manager.set_offline(connection.user_id, connection.tenant_id)
                
                # Broadcast user went offline
                tenant_room = f"tenant:{connection.tenant_id}"
                socketio.emit(
                    MessageType.PRESENCE_USER_LEFT.value,
                    {
                        'user_id': connection.user_id,
                        'user_name': connection.user_name,
                    },
                    room=tenant_room,
                )
            
            logger.info(f"User {connection.user_id} disconnected (sid={sid})")
    
    @socketio.on_error_default
    def handle_error(e):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {e}")


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
```

### 4.3 Presence Handler

**File:** `backend/app/realtime/handlers/presence_handler.py`

```python
"""
Presence Handler
Handle presence-related WebSocket events
"""

import logging
from flask import request
from flask_socketio import SocketIO, emit

from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.managers.presence_manager import get_presence_manager
from app.realtime.utils.message_types import MessageType, PresenceStatus

logger = logging.getLogger(__name__)


def register_presence_handlers(socketio: SocketIO):
    """Register presence event handlers"""
    
    @socketio.on(MessageType.PRESENCE_UPDATE.value)
    def handle_presence_update(data):
        """Handle presence status update"""
        sid = request.sid
        
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)
        
        if not connection:
            emit('error', {'message': 'Not authenticated'})
            return
        
        presence_manager = get_presence_manager()
        
        # Get new status
        new_status = data.get('status')
        current_page = data.get('current_page')
        entity_type = data.get('entity_type')
        entity_id = data.get('entity_id')
        
        # Update presence
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
            # Just update activity
            presence = presence_manager.update_activity(
                user_id=connection.user_id,
                tenant_id=connection.tenant_id,
                current_page=current_page,
                current_entity_type=entity_type,
                current_entity_id=entity_id,
            )
        
        if presence:
            # Broadcast to tenant
            tenant_room = f"tenant:{connection.tenant_id}"
            socketio.emit(
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
    
    @socketio.on(MessageType.PRESENCE_LIST.value)
    def handle_presence_list_request():
        """Handle request for online users list"""
        sid = request.sid
        
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)
        
        if not connection:
            emit('error', {'message': 'Not authenticated'})
            return
        
        presence_manager = get_presence_manager()
        online_users = presence_manager.get_online_users(connection.tenant_id)
        
        emit(MessageType.PRESENCE_LIST.value, {'users': online_users})
    
    @socketio.on('heartbeat')
    def handle_heartbeat():
        """Handle heartbeat to keep connection alive and update activity"""
        sid = request.sid
        
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)
        
        if connection:
            presence_manager = get_presence_manager()
            presence_manager.update_activity(
                user_id=connection.user_id,
                tenant_id=connection.tenant_id,
            )
        
        emit('heartbeat_ack', {'timestamp': request.sid})
```

---

## TASK 5: ROOM MANAGER

### 5.1 Room Manager Implementation

**File:** `backend/app/realtime/managers/room_manager.py`

```python
"""
Room Manager
Manages collaboration rooms
"""

import logging
from typing import Dict, Optional, List, Set
from datetime import datetime
import redis
import json

logger = logging.getLogger(__name__)


class Room:
    """Represents a collaboration room"""
    
    def __init__(
        self,
        room_id: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str
    ):
        self.room_id = room_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.tenant_id = tenant_id
        self.users: Dict[str, dict] = {}  # user_id -> user_info
        self.created_at = datetime.utcnow()
    
    def add_user(self, user_id: str, user_name: str, sid: str):
        """Add user to room"""
        self.users[user_id] = {
            'user_id': user_id,
            'user_name': user_name,
            'sid': sid,
            'joined_at': datetime.utcnow().isoformat(),
        }
    
    def remove_user(self, user_id: str):
        """Remove user from room"""
        self.users.pop(user_id, None)
    
    def get_users(self) -> List[dict]:
        """Get all users in room"""
        return list(self.users.values())
    
    def is_empty(self) -> bool:
        """Check if room is empty"""
        return len(self.users) == 0
    
    def to_dict(self) -> dict:
        return {
            'room_id': self.room_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'users': self.get_users(),
            'user_count': len(self.users),
        }


class RoomManager:
    """Manages collaboration rooms"""
    
    ROOM_KEY = 'room:{room_id}'
    ROOM_USERS_KEY = 'room:{room_id}:users'
    ENTITY_ROOM_KEY = 'entity_room:{entity_type}:{entity_id}'
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.local_rooms: Dict[str, Room] = {}
    
    def create_room(
        self,
        entity_type: str,
        entity_id: str,
        tenant_id: str
    ) -> Room:
        """Create or get a room for an entity"""
        room_id = f"{entity_type}:{entity_id}"
        
        if room_id in self.local_rooms:
            return self.local_rooms[room_id]
        
        room = Room(
            room_id=room_id,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
        )
        
        self.local_rooms[room_id] = room
        
        # Store in Redis
        self._store_room_redis(room)
        
        logger.info(f"Created room: {room_id}")
        
        return room
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID"""
        return self.local_rooms.get(room_id)
    
    def get_room_for_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> Optional[Room]:
        """Get room for an entity"""
        room_id = f"{entity_type}:{entity_id}"
        return self.local_rooms.get(room_id)
    
    def join_room(
        self,
        room_id: str,
        user_id: str,
        user_name: str,
        sid: str,
        tenant_id: str
    ) -> Optional[Room]:
        """Join a user to a room"""
        # Parse room_id to get entity info
        parts = room_id.split(':', 1)
        if len(parts) != 2:
            logger.warning(f"Invalid room_id format: {room_id}")
            return None
        
        entity_type, entity_id = parts
        
        # Create or get room
        room = self.create_room(entity_type, entity_id, tenant_id)
        
        # Add user
        room.add_user(user_id, user_name, sid)
        
        # Update Redis
        self._add_user_to_room_redis(room_id, user_id, user_name, sid)
        
        logger.info(f"User {user_id} joined room {room_id}")
        
        return room
    
    def leave_room(
        self,
        room_id: str,
        user_id: str
    ) -> Optional[Room]:
        """Remove a user from a room"""
        room = self.local_rooms.get(room_id)
        
        if not room:
            return None
        
        room.remove_user(user_id)
        
        # Update Redis
        self._remove_user_from_room_redis(room_id, user_id)
        
        logger.info(f"User {user_id} left room {room_id}")
        
        # Clean up empty room
        if room.is_empty():
            self._cleanup_room(room_id)
        
        return room
    
    def leave_all_rooms(self, user_id: str, sid: str) -> List[str]:
        """Remove user from all rooms (on disconnect)"""
        left_rooms = []
        
        for room_id, room in list(self.local_rooms.items()):
            if user_id in room.users:
                # Verify it's the same session
                if room.users[user_id].get('sid') == sid:
                    room.remove_user(user_id)
                    self._remove_user_from_room_redis(room_id, user_id)
                    left_rooms.append(room_id)
                    
                    if room.is_empty():
                        self._cleanup_room(room_id)
        
        return left_rooms
    
    def get_room_users(self, room_id: str) -> List[dict]:
        """Get users in a room"""
        room = self.local_rooms.get(room_id)
        return room.get_users() if room else []
    
    def get_rooms_for_user(self, user_id: str) -> List[str]:
        """Get all rooms a user is in"""
        rooms = []
        for room_id, room in self.local_rooms.items():
            if user_id in room.users:
                rooms.append(room_id)
        return rooms
    
    def _store_room_redis(self, room: Room):
        """Store room in Redis"""
        key = self.ROOM_KEY.format(room_id=room.room_id)
        
        self.redis.hset(key, mapping={
            'entity_type': room.entity_type,
            'entity_id': room.entity_id,
            'tenant_id': room.tenant_id,
            'created_at': room.created_at.isoformat(),
        })
        self.redis.expire(key, 86400)  # 24 hour TTL
        
        # Map entity to room
        entity_key = self.ENTITY_ROOM_KEY.format(
            entity_type=room.entity_type,
            entity_id=room.entity_id
        )
        self.redis.set(entity_key, room.room_id, ex=86400)
    
    def _add_user_to_room_redis(
        self,
        room_id: str,
        user_id: str,
        user_name: str,
        sid: str
    ):
        """Add user to room in Redis"""
        key = self.ROOM_USERS_KEY.format(room_id=room_id)
        
        self.redis.hset(key, user_id, json.dumps({
            'user_name': user_name,
            'sid': sid,
            'joined_at': datetime.utcnow().isoformat(),
        }))
        self.redis.expire(key, 86400)
    
    def _remove_user_from_room_redis(self, room_id: str, user_id: str):
        """Remove user from room in Redis"""
        key = self.ROOM_USERS_KEY.format(room_id=room_id)
        self.redis.hdel(key, user_id)
    
    def _cleanup_room(self, room_id: str):
        """Clean up empty room"""
        room = self.local_rooms.pop(room_id, None)
        
        if room:
            # Clean up Redis
            self.redis.delete(self.ROOM_KEY.format(room_id=room_id))
            self.redis.delete(self.ROOM_USERS_KEY.format(room_id=room_id))
            
            entity_key = self.ENTITY_ROOM_KEY.format(
                entity_type=room.entity_type,
                entity_id=room.entity_id
            )
            self.redis.delete(entity_key)
            
            logger.info(f"Cleaned up empty room: {room_id}")


# Singleton
_room_manager: Optional[RoomManager] = None


def get_room_manager() -> RoomManager:
    """Get room manager singleton"""
    global _room_manager
    if _room_manager is None:
        import os
        redis_client = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True
        )
        _room_manager = RoomManager(redis_client)
    return _room_manager
```

### 5.2 Room Handler

**File:** `backend/app/realtime/handlers/room_handler.py`

```python
"""
Room Handler
Handle room-related WebSocket events
"""

import logging
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

from app.realtime.managers.connection_manager import get_connection_manager
from app.realtime.managers.room_manager import get_room_manager
from app.realtime.utils.message_types import MessageType

logger = logging.getLogger(__name__)


def register_room_handlers(socketio: SocketIO):
    """Register room event handlers"""
    
    @socketio.on(MessageType.ROOM_JOIN.value)
    def handle_room_join(data):
        """Handle room join request"""
        sid = request.sid
        
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)
        
        if not connection:
            emit('error', {'message': 'Not authenticated'})
            return
        
        entity_type = data.get('entity_type')
        entity_id = data.get('entity_id')
        
        if not entity_type or not entity_id:
            emit('error', {'message': 'entity_type and entity_id required'})
            return
        
        room_id = f"{entity_type}:{entity_id}"
        
        # Join room
        room_manager = get_room_manager()
        room = room_manager.join_room(
            room_id=room_id,
            user_id=connection.user_id,
            user_name=connection.user_name,
            sid=sid,
            tenant_id=connection.tenant_id,
        )
        
        if room:
            # Join Socket.IO room
            join_room(room_id)
            conn_manager.add_to_room(sid, room_id)
            
            # Notify others in room
            socketio.emit(
                MessageType.ROOM_USER_JOINED.value,
                {
                    'user_id': connection.user_id,
                    'user_name': connection.user_name,
                    'room_id': room_id,
                },
                room=room_id,
                skip_sid=sid,
            )
            
            # Send current room users to joiner
            emit(MessageType.ROOM_USERS.value, {
                'room_id': room_id,
                'users': room.get_users(),
            })
            
            logger.info(f"User {connection.user_id} joined room {room_id}")
    
    @socketio.on(MessageType.ROOM_LEAVE.value)
    def handle_room_leave(data):
        """Handle room leave request"""
        sid = request.sid
        
        conn_manager = get_connection_manager()
        connection = conn_manager.get_connection(sid)
        
        if not connection:
            return
        
        room_id = data.get('room_id')
        
        if not room_id:
            return
        
        # Leave room
        room_manager = get_room_manager()
        room = room_manager.leave_room(room_id, connection.user_id)
        
        # Leave Socket.IO room
        leave_room(room_id)
        conn_manager.remove_from_room(sid, room_id)
        
        # Notify others
        if room:
            socketio.emit(
                MessageType.ROOM_USER_LEFT.value,
                {
                    'user_id': connection.user_id,
                    'user_name': connection.user_name,
                    'room_id': room_id,
                },
                room=room_id,
            )
        
        logger.info(f"User {connection.user_id} left room {room_id}")
    
    @socketio.on(MessageType.ROOM_USERS.value)
    def handle_room_users_request(data):
        """Handle request for room users list"""
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
        
        room_manager = get_room_manager()
        users = room_manager.get_room_users(room_id)
        
        emit(MessageType.ROOM_USERS.value, {
            'room_id': room_id,
            'users': users,
        })
```

---

## Continue to Part 2 for Cursor Sync, Notifications & Activity Feed

---

*Phase 18 Tasks Part 1 - LogiAccounting Pro*
*WebSocket Server & Presence System*
