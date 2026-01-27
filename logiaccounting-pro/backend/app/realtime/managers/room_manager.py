"""
Room Manager
Manages collaboration rooms
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime

from app.realtime.models.room import Room

logger = logging.getLogger(__name__)


class RoomManager:
    """Manages collaboration rooms"""

    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    def create_room(
        self,
        entity_type: str,
        entity_id: str,
        tenant_id: str
    ) -> Room:
        """Create or get a room for an entity"""
        room_id = f"{entity_type}:{entity_id}"

        if room_id in self.rooms:
            return self.rooms[room_id]

        room = Room(
            room_id=room_id,
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
        )

        self.rooms[room_id] = room

        logger.info(f"Created room: {room_id}")

        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID"""
        return self.rooms.get(room_id)

    def get_room_for_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> Optional[Room]:
        """Get room for an entity"""
        room_id = f"{entity_type}:{entity_id}"
        return self.rooms.get(room_id)

    def join_room(
        self,
        room_id: str,
        user_id: str,
        user_name: str,
        sid: str,
        tenant_id: str
    ) -> Optional[Room]:
        """Join a user to a room"""
        parts = room_id.split(':', 1)
        if len(parts) != 2:
            logger.warning(f"Invalid room_id format: {room_id}")
            return None

        entity_type, entity_id = parts

        room = self.create_room(entity_type, entity_id, tenant_id)

        room.add_user(user_id, user_name, sid)

        logger.info(f"User {user_id} joined room {room_id}")

        return room

    def leave_room(
        self,
        room_id: str,
        user_id: str
    ) -> Optional[Room]:
        """Remove a user from a room"""
        room = self.rooms.get(room_id)

        if not room:
            return None

        room.remove_user(user_id)

        logger.info(f"User {user_id} left room {room_id}")

        if room.is_empty():
            self._cleanup_room(room_id)

        return room

    def leave_all_rooms(self, user_id: str, sid: str) -> List[str]:
        """Remove user from all rooms (on disconnect)"""
        left_rooms = []

        for room_id, room in list(self.rooms.items()):
            if room.has_user(user_id):
                user_info = room.users.get(user_id, {})
                if user_info.get('sid') == sid:
                    room.remove_user(user_id)
                    left_rooms.append(room_id)

                    if room.is_empty():
                        self._cleanup_room(room_id)

        return left_rooms

    def get_room_users(self, room_id: str) -> List[dict]:
        """Get users in a room"""
        room = self.rooms.get(room_id)
        return room.get_users() if room else []

    def get_rooms_for_user(self, user_id: str) -> List[str]:
        """Get all rooms a user is in"""
        rooms = []
        for room_id, room in self.rooms.items():
            if room.has_user(user_id):
                rooms.append(room_id)
        return rooms

    def _cleanup_room(self, room_id: str):
        """Clean up empty room"""
        room = self.rooms.pop(room_id, None)

        if room:
            logger.info(f"Cleaned up empty room: {room_id}")


_room_manager: Optional[RoomManager] = None


def get_room_manager() -> RoomManager:
    """Get room manager singleton"""
    global _room_manager
    if _room_manager is None:
        _room_manager = RoomManager()
    return _room_manager
