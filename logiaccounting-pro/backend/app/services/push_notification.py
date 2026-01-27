"""
Push Notification Service - Send notifications to mobile devices
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class NotificationType(str, Enum):
    INVOICE_CREATED = "invoice_created"
    INVOICE_PAID = "invoice_paid"
    INVOICE_OVERDUE = "invoice_overdue"
    PAYMENT_RECEIVED = "payment_received"
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_COMPLETED = "approval_completed"
    INVENTORY_LOW = "inventory_low"
    SYSTEM_ALERT = "system_alert"
    REMINDER = "reminder"


class PushToken(BaseModel):
    token: str
    type: str
    device_id: str
    platform: str
    user_id: str
    created_at: datetime
    last_used_at: Optional[datetime] = None


class NotificationPayload(BaseModel):
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    badge: Optional[int] = None
    sound: str = "default"
    channel_id: Optional[str] = None
    priority: str = "high"


class PushNotificationService:
    """Service for sending push notifications to mobile devices."""

    def __init__(self):
        self._tokens: Dict[str, List[PushToken]] = {}
        self._notification_queue: List[Dict] = []

    async def register_token(
        self,
        user_id: str,
        token: str,
        token_type: str,
        device_id: str,
        platform: str,
    ) -> PushToken:
        """Register a push notification token for a user."""
        push_token = PushToken(
            token=token,
            type=token_type,
            device_id=device_id,
            platform=platform,
            user_id=user_id,
            created_at=datetime.utcnow(),
        )

        if user_id not in self._tokens:
            self._tokens[user_id] = []

        existing = next(
            (t for t in self._tokens[user_id] if t.device_id == device_id), None
        )
        if existing:
            self._tokens[user_id].remove(existing)

        self._tokens[user_id].append(push_token)
        return push_token

    async def unregister_token(self, token: str) -> bool:
        """Unregister a push notification token."""
        for user_id, tokens in self._tokens.items():
            for t in tokens:
                if t.token == token:
                    tokens.remove(t)
                    return True
        return False

    async def get_user_tokens(self, user_id: str) -> List[PushToken]:
        """Get all tokens for a user."""
        return self._tokens.get(user_id, [])

    async def send_notification(
        self,
        user_id: str,
        notification: NotificationPayload,
    ) -> Dict[str, Any]:
        """Send a notification to all devices of a user."""
        tokens = await self.get_user_tokens(user_id)

        if not tokens:
            return {"success": False, "error": "No registered devices"}

        results = []
        for token in tokens:
            result = await self._send_expo_notification(token.token, notification)
            results.append(result)

        success_count = sum(1 for r in results if r.get("success"))
        return {
            "success": success_count > 0,
            "sent": success_count,
            "failed": len(results) - success_count,
            "results": results,
        }

    async def send_bulk_notification(
        self,
        user_ids: List[str],
        notification: NotificationPayload,
    ) -> Dict[str, Any]:
        """Send a notification to multiple users."""
        tasks = [self.send_notification(user_id, notification) for user_id in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        return {
            "total_users": len(user_ids),
            "success": success_count,
            "failed": len(user_ids) - success_count,
        }

    async def _send_expo_notification(
        self,
        token: str,
        notification: NotificationPayload,
    ) -> Dict[str, Any]:
        """Send notification via Expo Push Service (mock implementation)."""
        message = {
            "to": token,
            "title": notification.title,
            "body": notification.body,
            "sound": notification.sound,
            "priority": notification.priority,
        }

        if notification.data:
            message["data"] = notification.data

        if notification.badge is not None:
            message["badge"] = notification.badge

        if notification.channel_id:
            message["channelId"] = notification.channel_id

        self._notification_queue.append(message)
        return {"success": True, "ticket_id": f"ticket-{datetime.utcnow().timestamp()}"}

    async def send_invoice_notification(
        self,
        user_id: str,
        invoice_id: str,
        invoice_number: str,
        customer_name: str,
        amount: str,
        notification_type: NotificationType,
    ) -> Dict[str, Any]:
        """Send invoice-related notification."""
        titles = {
            NotificationType.INVOICE_CREATED: "New Invoice Created",
            NotificationType.INVOICE_PAID: "Invoice Paid",
            NotificationType.INVOICE_OVERDUE: "Invoice Overdue",
        }

        bodies = {
            NotificationType.INVOICE_CREATED: f"Invoice {invoice_number} for {customer_name} ({amount})",
            NotificationType.INVOICE_PAID: f"Invoice {invoice_number} has been paid ({amount})",
            NotificationType.INVOICE_OVERDUE: f"Invoice {invoice_number} for {customer_name} is overdue ({amount})",
        }

        notification = NotificationPayload(
            title=titles.get(notification_type, "Invoice Update"),
            body=bodies.get(notification_type, f"Invoice {invoice_number} updated"),
            data={
                "type": notification_type.value,
                "action": "view_invoice",
                "id": invoice_id,
                "invoice_number": invoice_number,
            },
            channel_id="invoices",
        )

        return await self.send_notification(user_id, notification)

    async def send_approval_notification(
        self,
        user_id: str,
        approval_id: str,
        title: str,
        description: str,
        amount: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send approval request notification."""
        notification = NotificationPayload(
            title="Approval Required",
            body=f"{title}: {description}" + (f" ({amount})" if amount else ""),
            data={
                "type": NotificationType.APPROVAL_REQUIRED.value,
                "action": "approve",
                "id": approval_id,
            },
            channel_id="default",
            priority="high",
        )

        return await self.send_notification(user_id, notification)

    async def send_inventory_alert(
        self,
        user_id: str,
        item_id: str,
        item_name: str,
        current_quantity: int,
        reorder_level: int,
    ) -> Dict[str, Any]:
        """Send low inventory alert."""
        notification = NotificationPayload(
            title="Low Inventory Alert",
            body=f"{item_name} is low ({current_quantity} remaining, reorder at {reorder_level})",
            data={
                "type": NotificationType.INVENTORY_LOW.value,
                "action": "view_inventory",
                "id": item_id,
            },
            channel_id="default",
        )

        return await self.send_notification(user_id, notification)


push_notification_service = PushNotificationService()
