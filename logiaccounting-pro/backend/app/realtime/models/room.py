"""
Room Model
Collaboration room
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any


@dataclass
class Room:
    """Represents a collaboration room"""
    room_id: str
    entity_type: str
    entity_id: str
    tenant_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    users: Dict[str, Dict[str, Any]] = field(default_factory=dict)

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

    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users in room"""
        return list(self.users.values())

    def is_empty(self) -> bool:
        """Check if room is empty"""
        return len(self.users) == 0

    def has_user(self, user_id: str) -> bool:
        """Check if user is in room"""
        return user_id in self.users

    def get_user_count(self) -> int:
        """Get number of users in room"""
        return len(self.users)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'room_id': self.room_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'users': self.get_users(),
            'user_count': self.get_user_count(),
            'created_at': self.created_at.isoformat(),
        }
