"""
Cursor Manager
Manages cursor positions for collaborative editing
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
import hashlib

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


CURSOR_COLORS = [
    '#FF6B6B',
    '#4ECDC4',
    '#45B7D1',
    '#96CEB4',
    '#FFEAA7',
    '#DDA0DD',
    '#98D8C8',
    '#F7DC6F',
    '#BB8FCE',
    '#85C1E9',
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
        self.last_update = utc_now()

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

    CURSOR_TTL = 300

    def __init__(self):
        self.cursors: Dict[str, Dict[str, CursorPosition]] = {}

    def get_user_color(self, user_id: str) -> str:
        """Get consistent color for a user"""
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

        if room_id not in self.cursors:
            self.cursors[room_id] = {}

        self.cursors[room_id][user_id] = cursor

        return cursor

    def get_cursor(self, room_id: str, user_id: str) -> Optional[CursorPosition]:
        """Get cursor position for a user"""
        if room_id not in self.cursors:
            return None

        return self.cursors[room_id].get(user_id)

    def get_room_cursors(self, room_id: str) -> List[CursorPosition]:
        """Get all cursors in a room"""
        if room_id not in self.cursors:
            return []

        return list(self.cursors[room_id].values())

    def remove_cursor(self, room_id: str, user_id: str):
        """Remove cursor when user leaves room"""
        if room_id in self.cursors and user_id in self.cursors[room_id]:
            del self.cursors[room_id][user_id]

    def clear_room_cursors(self, room_id: str):
        """Clear all cursors in a room"""
        if room_id in self.cursors:
            del self.cursors[room_id]


_cursor_manager: Optional[CursorManager] = None


def get_cursor_manager() -> CursorManager:
    """Get cursor manager singleton"""
    global _cursor_manager
    if _cursor_manager is None:
        _cursor_manager = CursorManager()
    return _cursor_manager
