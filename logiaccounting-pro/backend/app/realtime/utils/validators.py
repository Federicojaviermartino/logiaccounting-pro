"""
Real-Time Validators
Message validation utilities
"""

import re
from typing import Optional, Dict, Any


def validate_room_id(room_id: str) -> bool:
    """Validate room ID format (entity_type:entity_id)"""
    if not room_id:
        return False

    pattern = r'^[a-zA-Z_]+:[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, room_id))


def validate_cursor_position(data: Dict[str, Any]) -> bool:
    """Validate cursor position data"""
    required_fields = ['room_id', 'line', 'column']

    for field in required_fields:
        if field not in data:
            return False

    if not isinstance(data.get('line'), int) or data['line'] < 0:
        return False

    if not isinstance(data.get('column'), int) or data['column'] < 0:
        return False

    return True


def validate_presence_update(data: Dict[str, Any]) -> bool:
    """Validate presence update data"""
    valid_statuses = ['online', 'away', 'busy']

    status = data.get('status')
    if status and status not in valid_statuses:
        return False

    return True


def sanitize_string(value: Optional[str], max_length: int = 255) -> Optional[str]:
    """Sanitize string input"""
    if value is None:
        return None

    value = str(value).strip()

    if len(value) > max_length:
        value = value[:max_length]

    return value
