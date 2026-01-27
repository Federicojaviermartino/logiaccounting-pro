"""
WebSocket Message Types
Defines all message types and their schemas
"""

from enum import Enum
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
from datetime import datetime


class MessageType(str, Enum):
    """WebSocket message types"""

    CONNECT = 'connect'
    DISCONNECT = 'disconnect'
    ERROR = 'error'

    PRESENCE_UPDATE = 'presence:update'
    PRESENCE_LIST = 'presence:list'
    PRESENCE_USER_JOINED = 'presence:user_joined'
    PRESENCE_USER_LEFT = 'presence:user_left'

    ROOM_JOIN = 'room:join'
    ROOM_LEAVE = 'room:leave'
    ROOM_USERS = 'room:users'
    ROOM_USER_JOINED = 'room:user_joined'
    ROOM_USER_LEFT = 'room:user_left'

    CURSOR_MOVE = 'cursor:move'
    CURSOR_SYNC = 'cursor:sync'
    CURSOR_REMOVE = 'cursor:remove'

    DOC_EDIT = 'doc:edit'
    DOC_SYNC = 'doc:sync'
    DOC_LOCK = 'doc:lock'
    DOC_UNLOCK = 'doc:unlock'
    DOC_LOCK_STATUS = 'doc:lock_status'

    NOTIFICATION = 'notification'
    NOTIFICATION_READ = 'notification:read'
    NOTIFICATION_COUNT = 'notification:count'

    ACTIVITY = 'activity'
    ACTIVITY_FEED = 'activity:feed'

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
    user_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value if isinstance(self.status, PresenceStatus) else self.status
        return result


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
    users: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
