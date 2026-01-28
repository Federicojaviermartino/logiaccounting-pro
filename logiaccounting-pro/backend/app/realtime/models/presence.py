"""
Presence Model
User presence state
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from app.utils.datetime_utils import utc_now


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
    user_name: str
    tenant_id: str
    status: PresenceStatus
    last_active_at: datetime
    current_page: Optional[str] = None
    current_entity_type: Optional[str] = None
    current_entity_id: Optional[str] = None
    device_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'tenant_id': self.tenant_id,
            'status': self.status.value if isinstance(self.status, PresenceStatus) else self.status,
            'last_active_at': self.last_active_at.isoformat() if isinstance(self.last_active_at, datetime) else self.last_active_at,
            'current_page': self.current_page,
            'current_entity_type': self.current_entity_type,
            'current_entity_id': self.current_entity_id,
            'device_type': self.device_type,
        }

    def update_activity(self, current_page: str = None, entity_type: str = None, entity_id: str = None):
        """Update last activity and location"""
        self.last_active_at = utc_now()
        if self.status == PresenceStatus.AWAY:
            self.status = PresenceStatus.ONLINE
        if current_page:
            self.current_page = current_page
        if entity_type:
            self.current_entity_type = entity_type
        if entity_id:
            self.current_entity_id = entity_id

    def set_away(self):
        """Set user as away"""
        if self.status == PresenceStatus.ONLINE:
            self.status = PresenceStatus.AWAY

    def set_busy(self):
        """Set user as busy"""
        self.status = PresenceStatus.BUSY

    def set_online(self):
        """Set user as online"""
        self.status = PresenceStatus.ONLINE
        self.last_active_at = utc_now()

    def set_offline(self):
        """Set user as offline"""
        self.status = PresenceStatus.OFFLINE
