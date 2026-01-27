"""
Connection Model
Represents a WebSocket connection
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Set, Dict, Any


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            'sid': self.sid,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'user_name': self.user_name,
            'connected_at': self.connected_at.isoformat(),
            'device_type': self.device_type,
            'browser': self.browser,
        }

    def add_room(self, room: str):
        """Add connection to a room"""
        self.rooms.add(room)

    def remove_room(self, room: str):
        """Remove connection from a room"""
        self.rooms.discard(room)

    def is_in_room(self, room: str) -> bool:
        """Check if connection is in a room"""
        return room in self.rooms
