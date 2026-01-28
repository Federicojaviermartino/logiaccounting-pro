"""
Activity Logger - Tracks all user actions for audit trail
"""
import logging

logger = logging.getLogger(__name__)

from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps

from app.utils.datetime_utils import utc_now


class ActivityLogger:
    """Centralized activity logging service"""

    _instance = None
    _activities = []
    _counter = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def log(
        self,
        user_id: str,
        user_email: str,
        user_role: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        entity_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """Log an activity"""
        self._counter += 1
        activity = {
            "id": f"ACT-{self._counter:06d}",
            "timestamp": utc_now().isoformat(),
            "user_id": user_id,
            "user_email": user_email,
            "user_role": user_role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        self._activities.insert(0, activity)  # Most recent first

        # Keep last 10000 activities in memory
        if len(self._activities) > 10000:
            self._activities = self._activities[:10000]

        return activity

    def get_activities(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple:
        """Get filtered activities with pagination"""
        filtered = self._activities.copy()

        if user_id:
            filtered = [a for a in filtered if a["user_id"] == user_id]

        if action:
            filtered = [a for a in filtered if a["action"] == action]

        if entity_type:
            filtered = [a for a in filtered if a["entity_type"] == entity_type]

        if date_from:
            filtered = [a for a in filtered if a["timestamp"] >= date_from]

        if date_to:
            filtered = [a for a in filtered if a["timestamp"] <= date_to]

        total = len(filtered)
        paginated = filtered[offset:offset + limit]

        return paginated, total

    def get_stats(self, days: int = 30) -> Dict:
        """Get activity statistics"""
        from datetime import timedelta
        cutoff = (utc_now() - timedelta(days=days)).isoformat()

        recent = [a for a in self._activities if a["timestamp"] >= cutoff]

        # Count by action
        by_action = {}
        for a in recent:
            by_action[a["action"]] = by_action.get(a["action"], 0) + 1

        # Count by entity
        by_entity = {}
        for a in recent:
            by_entity[a["entity_type"]] = by_entity.get(a["entity_type"], 0) + 1

        # Count by user
        by_user = {}
        for a in recent:
            key = a["user_email"]
            by_user[key] = by_user.get(key, 0) + 1

        # Top 5 active users
        top_users = sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "period_days": days,
            "total_activities": len(recent),
            "by_action": by_action,
            "by_entity": by_entity,
            "top_users": [{"email": u[0], "count": u[1]} for u in top_users],
            "daily_average": round(len(recent) / days, 1) if days > 0 else 0
        }

    def clear(self):
        """Clear all activities (for testing)"""
        self._activities = []
        self._counter = 0


# Global instance
activity_logger = ActivityLogger()


def log_activity(action: str, entity_type: str):
    """Decorator to automatically log endpoint activities"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the function first
            result = await func(*args, **kwargs)

            # Try to log the activity
            try:
                current_user = kwargs.get("current_user")
                if current_user:
                    # Extract entity info from result if possible
                    entity_id = None
                    entity_name = None

                    if isinstance(result, dict):
                        for key in ["material", "transaction", "payment", "project", "user"]:
                            if key in result:
                                entity_id = result[key].get("id")
                                entity_name = result[key].get("name") or result[key].get("reference")
                                break

                    activity_logger.log(
                        user_id=current_user["id"],
                        user_email=current_user["email"],
                        user_role=current_user["role"],
                        action=action,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        entity_name=entity_name
                    )
            except Exception as e:
                logger.error("Activity logging failed: %s", e, exc_info=True)

            return result
        return wrapper
    return decorator
