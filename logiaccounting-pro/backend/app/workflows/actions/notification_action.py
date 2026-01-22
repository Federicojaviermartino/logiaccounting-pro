"""
In-app notification action executor.
Creates notifications for users.
"""
from typing import Dict, Any, List
from datetime import datetime
import logging
import re
import uuid

from app.workflows.actions import ActionExecutor


logger = logging.getLogger(__name__)


class NotificationActionExecutor(ActionExecutor):
    """Executes in-app notification actions."""

    async def execute(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create in-app notifications.

        Config:
            recipients: List of user IDs or role names
            title: Notification title
            message: Notification message
            template: Optional template ID
            priority: Priority level (low, normal, high, urgent)
            link: Optional link URL
            channels: Notification channels (in_app, push, email)
        """
        recipients = self._resolve_recipients(
            config.get("recipients", []),
            variables
        )

        if not recipients:
            return {"created": False, "error": "No recipients"}

        title = self._interpolate(config.get("title", ""), variables)
        message = self._interpolate(config.get("message", ""), variables)

        priority = config.get("priority", "normal")
        link = self._interpolate(config.get("link", ""), variables)
        channels = config.get("channels", ["in_app"])

        notification_ids = []

        for user_id in recipients:
            notification = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": title,
                "message": message,
                "priority": priority,
                "link": link,
                "read": False,
                "created_at": datetime.utcnow().isoformat()
            }

            notification_id = await self._create_notification(notification, channels)
            notification_ids.append(notification_id)

        logger.info(f"Created {len(notification_ids)} notifications")

        return {
            "created": True,
            "count": len(notification_ids),
            "notification_ids": notification_ids
        }

    def _resolve_recipients(
        self,
        recipients: List[str],
        variables: Dict[str, Any]
    ) -> List[str]:
        """Resolve recipient references to user IDs."""
        resolved = []

        for recipient in recipients:
            if recipient.startswith("{{") and recipient.endswith("}}"):
                key = recipient[2:-2].strip()
                value = self._get_nested(variables, key)
                if value:
                    if isinstance(value, list):
                        resolved.extend(value)
                    else:
                        resolved.append(str(value))
            elif recipient.startswith("role:"):
                pass
            else:
                resolved.append(recipient)

        return list(set(resolved))

    def _interpolate(self, text: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables in text."""
        def replace(match):
            key = match.group(1).strip()
            value = self._get_nested(variables, key)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace, text)

    def _get_nested(self, obj: Dict, path: str) -> Any:
        """Get nested value from dict."""
        keys = path.split(".")
        value = obj

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    async def _create_notification(
        self,
        notification: Dict[str, Any],
        channels: List[str]
    ) -> str:
        """Create notification in system."""
        return notification["id"]
