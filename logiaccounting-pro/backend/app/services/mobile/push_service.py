"""
Push Notification Service
Manages web push notifications using VAPID
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import json
import logging

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class PushSubscription:
    """Represents a push subscription."""

    def __init__(self, contact_id: str, endpoint: str, keys: Dict, platform: str = "web"):
        self.id = f"push_{uuid4().hex[:12]}"
        self.contact_id = contact_id
        self.endpoint = endpoint
        self.keys = keys  # p256dh and auth keys
        self.platform = platform
        self.device_name = None
        self.is_active = True
        self.preferences = {
            "invoices": True,
            "projects": True,
            "support": True,
            "quotes": True,
            "payments": True,
            "marketing": False,
        }
        self.created_at = utc_now()
        self.last_used_at = utc_now()


class PushNotification:
    """Represents a push notification to be sent."""

    def __init__(self, contact_id: str, notification_type: str, title: str, body: str, data: Dict = None):
        self.id = f"pn_{uuid4().hex[:12]}"
        self.contact_id = contact_id
        self.type = notification_type
        self.title = title
        self.body = body
        self.icon = "/icons/icon-192.png"
        self.badge = "/icons/badge-72.png"
        self.data = data or {}
        self.tag = f"{notification_type}_{uuid4().hex[:8]}"
        self.require_interaction = False
        self.actions = []
        self.status = "pending"
        self.created_at = utc_now()
        self.sent_at = None
        self.error = None


class PushNotificationService:
    """Manages push notifications."""

    # VAPID keys would be loaded from environment in production
    VAPID_PUBLIC_KEY = "BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U"
    VAPID_PRIVATE_KEY = "UUxI4O8-FbRouADVXc-hK5_rSgMr5y9-tZDMqK8xK9E"
    VAPID_CLAIMS = {"sub": "mailto:push@logiaccounting.com"}

    def __init__(self):
        self._subscriptions: Dict[str, PushSubscription] = {}
        self._notifications: List[PushNotification] = []
        self._notification_queue: List[PushNotification] = []

    def get_vapid_public_key(self) -> str:
        """Get VAPID public key for client subscription."""
        return self.VAPID_PUBLIC_KEY

    def subscribe(self, contact_id: str, subscription_data: Dict) -> PushSubscription:
        """Register a push subscription."""
        subscription = PushSubscription(
            contact_id=contact_id,
            endpoint=subscription_data["endpoint"],
            keys=subscription_data.get("keys", {}),
            platform=subscription_data.get("platform", "web"),
        )
        subscription.device_name = subscription_data.get("device_name")

        if "preferences" in subscription_data:
            subscription.preferences.update(subscription_data["preferences"])

        self._subscriptions[subscription.id] = subscription
        logger.info(f"Push subscription registered: {subscription.id} for contact {contact_id}")

        return subscription

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a push subscription."""
        if subscription_id in self._subscriptions:
            self._subscriptions[subscription_id].is_active = False
            logger.info(f"Push subscription deactivated: {subscription_id}")
            return True
        return False

    def get_subscriptions(self, contact_id: str) -> List[Dict]:
        """Get all active subscriptions for a contact."""
        subscriptions = [
            s for s in self._subscriptions.values()
            if s.contact_id == contact_id and s.is_active
        ]
        return [self._subscription_to_dict(s) for s in subscriptions]

    def update_preferences(self, subscription_id: str, preferences: Dict) -> Optional[Dict]:
        """Update notification preferences for a subscription."""
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            return None

        subscription.preferences.update(preferences)
        return subscription.preferences

    def send_notification(self, contact_id: str, notification_type: str, title: str, body: str, data: Dict = None, actions: List[Dict] = None) -> List[str]:
        """Send push notification to all user's devices."""
        notification = PushNotification(
            contact_id=contact_id,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data,
        )

        if actions:
            notification.actions = actions
            notification.require_interaction = True

        # Get active subscriptions that have this notification type enabled
        subscriptions = [
            s for s in self._subscriptions.values()
            if s.contact_id == contact_id and s.is_active and s.preferences.get(notification_type, True)
        ]

        sent_ids = []
        for subscription in subscriptions:
            try:
                self._send_to_subscription(notification, subscription)
                sent_ids.append(subscription.id)
                subscription.last_used_at = utc_now()
            except Exception as e:
                logger.error(f"Failed to send notification to {subscription.id}: {e}")
                notification.error = str(e)

        notification.status = "sent" if sent_ids else "failed"
        notification.sent_at = utc_now()
        self._notifications.append(notification)

        return sent_ids

    def _send_to_subscription(self, notification: PushNotification, subscription: PushSubscription):
        """Send notification to a specific subscription."""
        # In production, use pywebpush library
        payload = json.dumps({
            "title": notification.title,
            "body": notification.body,
            "icon": notification.icon,
            "badge": notification.badge,
            "tag": notification.tag,
            "data": notification.data,
            "actions": notification.actions,
            "requireInteraction": notification.require_interaction,
        })

        logger.info(f"Push notification sent to {subscription.id}: {notification.title}")

    def send_invoice_due_notification(self, contact_id: str, invoice_number: str, amount: float, due_date: str):
        """Send invoice due reminder."""
        return self.send_notification(
            contact_id=contact_id,
            notification_type="invoices",
            title="Invoice Due Soon",
            body=f"Invoice {invoice_number} for ${amount:,.2f} is due on {due_date}",
            data={"type": "invoice_due", "invoice_number": invoice_number, "url": f"/portal/payments"},
            actions=[
                {"action": "pay", "title": "Pay Now"},
                {"action": "view", "title": "View Invoice"},
            ],
        )

    def send_payment_received_notification(self, contact_id: str, amount: float, reference: str):
        """Send payment confirmation."""
        return self.send_notification(
            contact_id=contact_id,
            notification_type="payments",
            title="Payment Received",
            body=f"Your payment of ${amount:,.2f} has been confirmed (Ref: {reference})",
            data={"type": "payment_received", "reference": reference, "url": "/portal/payments"},
        )

    def send_ticket_reply_notification(self, contact_id: str, ticket_number: str, ticket_id: str):
        """Send support ticket reply notification."""
        return self.send_notification(
            contact_id=contact_id,
            notification_type="support",
            title="Support Reply",
            body=f"Your ticket {ticket_number} has received a response",
            data={"type": "ticket_reply", "ticket_id": ticket_id, "url": f"/portal/support/{ticket_id}"},
            actions=[
                {"action": "view", "title": "View Reply"},
                {"action": "reply", "title": "Reply"},
            ],
        )

    def send_project_update_notification(self, contact_id: str, project_name: str, milestone: str, project_id: str):
        """Send project milestone notification."""
        return self.send_notification(
            contact_id=contact_id,
            notification_type="projects",
            title="Project Update",
            body=f"{project_name}: {milestone} completed",
            data={"type": "project_update", "project_id": project_id, "url": f"/portal/projects/{project_id}"},
        )

    def send_quote_expiring_notification(self, contact_id: str, quote_number: str, quote_id: str, days_left: int):
        """Send quote expiring notification."""
        return self.send_notification(
            contact_id=contact_id,
            notification_type="quotes",
            title="Quote Expiring Soon",
            body=f"Quote {quote_number} expires in {days_left} day(s)",
            data={"type": "quote_expiring", "quote_id": quote_id, "url": f"/portal/quotes/{quote_id}"},
            actions=[
                {"action": "accept", "title": "Accept Quote"},
                {"action": "view", "title": "View Quote"},
            ],
        )

    def get_notification_history(self, contact_id: str, limit: int = 50) -> List[Dict]:
        """Get notification history for a contact."""
        notifications = [n for n in self._notifications if n.contact_id == contact_id]
        notifications.sort(key=lambda n: n.created_at, reverse=True)

        return [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "status": n.status,
                "created_at": n.created_at.isoformat(),
                "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            }
            for n in notifications[:limit]
        ]

    def _subscription_to_dict(self, subscription: PushSubscription) -> Dict:
        """Convert subscription to dictionary."""
        return {
            "id": subscription.id,
            "platform": subscription.platform,
            "device_name": subscription.device_name,
            "preferences": subscription.preferences,
            "created_at": subscription.created_at.isoformat(),
            "last_used_at": subscription.last_used_at.isoformat(),
        }


# Service instance
push_service = PushNotificationService()
