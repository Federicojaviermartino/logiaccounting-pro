# Phase 28: Mobile API & PWA - Part 1: Backend Services

## Overview
This part covers the backend services for mobile API including data aggregation, push notifications, offline sync, and device management.

---

## File 1: Mobile Aggregator Service
**Path:** `backend/app/services/mobile/aggregator.py`

```python
"""
Mobile Aggregator Service
Provides aggregated data for mobile home screen in single API call
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MobileAggregatorService:
    """Aggregates data from multiple sources for mobile API."""
    
    def __init__(self):
        self._notifications: Dict[str, List[Dict]] = {}
    
    def get_home_data(self, customer_id: str, contact_id: str, user_info: Dict) -> Dict[str, Any]:
        """Get aggregated home screen data."""
        return {
            "user": self._get_user_summary(user_info),
            "stats": self._get_quick_stats(customer_id),
            "recent_activity": self._get_recent_activity(customer_id, limit=5),
            "quick_actions": self._get_quick_actions(customer_id),
            "notifications": self._get_notifications_summary(contact_id),
            "alerts": self._get_alerts(customer_id),
        }
    
    def _get_user_summary(self, user_info: Dict) -> Dict:
        """Get user summary for header."""
        return {
            "name": user_info.get("name", "User"),
            "first_name": user_info.get("name", "User").split()[0],
            "email": user_info.get("email"),
            "avatar_url": user_info.get("avatar_url"),
            "company": user_info.get("company_name", ""),
        }
    
    def _get_quick_stats(self, customer_id: str) -> Dict:
        """Get key statistics for mobile dashboard."""
        # In production, fetch from database
        return {
            "pending_invoices": 3,
            "pending_amount": 12500.00,
            "overdue_count": 1,
            "overdue_amount": 2500.00,
            "active_projects": 2,
            "open_tickets": 1,
            "unread_messages": 3,
            "pending_quotes": 2,
        }
    
    def _get_recent_activity(self, customer_id: str, limit: int = 5) -> List[Dict]:
        """Get recent activity for mobile feed."""
        activities = [
            {
                "id": "act_001",
                "type": "invoice",
                "icon": "file-text",
                "title": "New Invoice",
                "description": "Invoice #INV-2024-0042 for $5,250",
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "action_url": "/portal/payments/inv_001",
            },
            {
                "id": "act_002",
                "type": "payment",
                "icon": "credit-card",
                "title": "Payment Received",
                "description": "Payment of $3,500 confirmed",
                "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "action_url": "/portal/payments",
            },
            {
                "id": "act_003",
                "type": "project",
                "icon": "folder",
                "title": "Project Update",
                "description": "Website Redesign reached 65%",
                "timestamp": (datetime.utcnow() - timedelta(days=1, hours=5)).isoformat(),
                "action_url": "/portal/projects/proj_001",
            },
            {
                "id": "act_004",
                "type": "ticket",
                "icon": "message-circle",
                "title": "Support Reply",
                "description": "New reply on ticket #TKT-0015",
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "action_url": "/portal/support/tkt_001",
            },
            {
                "id": "act_005",
                "type": "quote",
                "icon": "file",
                "title": "Quote Sent",
                "description": "Quote #QT-2024-0012 for $12,500",
                "timestamp": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                "action_url": "/portal/quotes/qt_001",
            },
        ]
        return activities[:limit]
    
    def _get_quick_actions(self, customer_id: str) -> List[Dict]:
        """Get quick actions for mobile FAB menu."""
        return [
            {
                "id": "pay_invoice",
                "label": "Pay Invoice",
                "icon": "credit-card",
                "color": "#10b981",
                "url": "/portal/payments",
                "badge": 3,
            },
            {
                "id": "new_ticket",
                "label": "New Ticket",
                "icon": "plus-circle",
                "color": "#3b82f6",
                "url": "/portal/support/new",
            },
            {
                "id": "send_message",
                "label": "Message",
                "icon": "message-circle",
                "color": "#8b5cf6",
                "url": "/portal/messages/new",
            },
            {
                "id": "view_projects",
                "label": "Projects",
                "icon": "folder",
                "color": "#f59e0b",
                "url": "/portal/projects",
            },
        ]
    
    def _get_notifications_summary(self, contact_id: str) -> Dict:
        """Get notifications summary."""
        notifications = self._get_user_notifications(contact_id, limit=5)
        unread = [n for n in notifications if not n.get("read")]
        
        return {
            "unread_count": len(unread),
            "items": notifications,
        }
    
    def _get_user_notifications(self, contact_id: str, limit: int = 10) -> List[Dict]:
        """Get user notifications."""
        if contact_id not in self._notifications:
            self._notifications[contact_id] = [
                {
                    "id": "notif_001",
                    "type": "invoice_due",
                    "title": "Invoice Due Soon",
                    "body": "Invoice #INV-2024-0042 is due in 3 days",
                    "read": False,
                    "action_url": "/portal/payments/inv_001",
                    "created_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                },
                {
                    "id": "notif_002",
                    "type": "ticket_reply",
                    "title": "Support Reply",
                    "body": "Your ticket received a response",
                    "read": False,
                    "action_url": "/portal/support/tkt_001",
                    "created_at": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                },
                {
                    "id": "notif_003",
                    "type": "quote_expiring",
                    "title": "Quote Expiring",
                    "body": "Quote #QT-2024-0012 expires in 2 days",
                    "read": False,
                    "action_url": "/portal/quotes/qt_001",
                    "created_at": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                },
                {
                    "id": "notif_004",
                    "type": "project_update",
                    "title": "Milestone Completed",
                    "body": "Design phase completed for Website Redesign",
                    "read": True,
                    "action_url": "/portal/projects/proj_001",
                    "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                },
                {
                    "id": "notif_005",
                    "type": "payment_received",
                    "title": "Payment Confirmed",
                    "body": "Your payment of $3,500 has been received",
                    "read": True,
                    "action_url": "/portal/payments",
                    "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                },
            ]
        
        return self._notifications[contact_id][:limit]
    
    def _get_alerts(self, customer_id: str) -> List[Dict]:
        """Get urgent alerts."""
        alerts = []
        
        # Check for overdue invoices
        stats = self._get_quick_stats(customer_id)
        if stats["overdue_count"] > 0:
            alerts.append({
                "id": "alert_overdue",
                "type": "warning",
                "title": "Overdue Invoice",
                "message": f"You have {stats['overdue_count']} overdue invoice(s) totaling ${stats['overdue_amount']:,.2f}",
                "action": {"label": "Pay Now", "url": "/portal/payments?status=overdue"},
            })
        
        return alerts
    
    def get_offline_data_package(self, customer_id: str, contact_id: str) -> Dict[str, Any]:
        """Get data package for offline use."""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "data": {
                "stats": self._get_quick_stats(customer_id),
                "invoices": self._get_offline_invoices(customer_id),
                "projects": self._get_offline_projects(customer_id),
                "tickets": self._get_offline_tickets(customer_id),
                "contacts": self._get_offline_contacts(customer_id),
            },
        }
    
    def _get_offline_invoices(self, customer_id: str, limit: int = 20) -> List[Dict]:
        """Get invoices for offline cache."""
        return [
            {"id": "inv_001", "number": "INV-2024-0042", "amount": 5250.00, "status": "pending", "due_date": "2024-02-15"},
            {"id": "inv_002", "number": "INV-2024-0039", "amount": 3200.00, "status": "pending", "due_date": "2024-02-10"},
            {"id": "inv_003", "number": "INV-2024-0036", "amount": 1850.00, "status": "overdue", "due_date": "2024-01-20"},
        ]
    
    def _get_offline_projects(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """Get projects for offline cache."""
        return [
            {"id": "proj_001", "name": "Website Redesign", "progress": 65, "status": "active"},
            {"id": "proj_002", "name": "Mobile App Development", "progress": 40, "status": "active"},
        ]
    
    def _get_offline_tickets(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """Get tickets for offline cache."""
        return [
            {"id": "tkt_001", "number": "TKT-0015", "subject": "Integration Question", "status": "in_progress"},
        ]
    
    def _get_offline_contacts(self, customer_id: str) -> List[Dict]:
        """Get support contacts for offline."""
        return [
            {"name": "Support Team", "email": "support@company.com", "phone": "+1-800-SUPPORT"},
        ]
    
    def mark_notification_read(self, contact_id: str, notification_id: str) -> bool:
        """Mark a notification as read."""
        if contact_id in self._notifications:
            for notif in self._notifications[contact_id]:
                if notif["id"] == notification_id:
                    notif["read"] = True
                    return True
        return False
    
    def mark_all_notifications_read(self, contact_id: str) -> int:
        """Mark all notifications as read."""
        count = 0
        if contact_id in self._notifications:
            for notif in self._notifications[contact_id]:
                if not notif["read"]:
                    notif["read"] = True
                    count += 1
        return count


# Service instance
mobile_aggregator = MobileAggregatorService()
```

---

## File 2: Push Notification Service
**Path:** `backend/app/services/mobile/push_service.py`

```python
"""
Push Notification Service
Manages web push notifications using VAPID
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import json
import logging

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
        self.created_at = datetime.utcnow()
        self.last_used_at = datetime.utcnow()


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
        self.created_at = datetime.utcnow()
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
                subscription.last_used_at = datetime.utcnow()
            except Exception as e:
                logger.error(f"Failed to send notification to {subscription.id}: {e}")
                notification.error = str(e)
        
        notification.status = "sent" if sent_ids else "failed"
        notification.sent_at = datetime.utcnow()
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
```

---

## File 3: Offline Sync Service
**Path:** `backend/app/services/mobile/sync_service.py`

```python
"""
Offline Sync Service
Handles synchronization of offline data and actions
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SyncActionType(str, Enum):
    CREATE_TICKET = "create_ticket"
    REPLY_TICKET = "reply_ticket"
    CLOSE_TICKET = "close_ticket"
    ADD_NOTE = "add_note"
    UPDATE_PREFERENCES = "update_preferences"
    MARK_NOTIFICATION_READ = "mark_notification_read"


class SyncAction:
    """Represents an offline action to be synced."""
    
    def __init__(self, offline_id: str, action_type: str, data: Dict, created_at: str):
        self.offline_id = offline_id
        self.action_type = action_type
        self.data = data
        self.created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        self.server_id = None
        self.status = "pending"
        self.error = None
        self.processed_at = None


class SyncResult:
    """Result of processing a sync action."""
    
    def __init__(self, offline_id: str, status: str, server_id: str = None, error: str = None):
        self.offline_id = offline_id
        self.status = status
        self.server_id = server_id
        self.error = error


class OfflineSyncService:
    """Manages offline data synchronization."""
    
    def __init__(self):
        self._sync_tokens: Dict[str, Dict] = {}
        self._processed_actions: List[SyncAction] = []
    
    def process_sync(self, contact_id: str, customer_id: str, last_sync: Optional[str], pending_actions: List[Dict]) -> Dict[str, Any]:
        """Process sync request from mobile client."""
        sync_token = f"sync_{uuid4().hex[:16]}"
        server_time = datetime.utcnow()
        
        # Process pending offline actions
        results = []
        for action_data in pending_actions:
            action = SyncAction(
                offline_id=action_data["id"],
                action_type=action_data["type"],
                data=action_data.get("data", {}),
                created_at=action_data["created_at"],
            )
            
            result = self._process_action(action, contact_id, customer_id)
            results.append({
                "offline_id": result.offline_id,
                "server_id": result.server_id,
                "status": result.status,
                "error": result.error,
            })
        
        # Get updates since last sync
        updates = self._get_updates_since(customer_id, contact_id, last_sync)
        
        # Store sync state
        self._sync_tokens[contact_id] = {
            "token": sync_token,
            "timestamp": server_time,
        }
        
        return {
            "sync_token": sync_token,
            "server_time": server_time.isoformat() + "Z",
            "processed": results,
            "updates": updates,
            "conflicts": [],
        }
    
    def _process_action(self, action: SyncAction, contact_id: str, customer_id: str) -> SyncResult:
        """Process a single offline action."""
        try:
            handler = self._get_action_handler(action.action_type)
            if not handler:
                return SyncResult(
                    offline_id=action.offline_id,
                    status="error",
                    error=f"Unknown action type: {action.action_type}",
                )
            
            server_id = handler(action, contact_id, customer_id)
            
            action.server_id = server_id
            action.status = "success"
            action.processed_at = datetime.utcnow()
            self._processed_actions.append(action)
            
            return SyncResult(
                offline_id=action.offline_id,
                status="success",
                server_id=server_id,
            )
            
        except Exception as e:
            logger.error(f"Failed to process action {action.offline_id}: {e}")
            return SyncResult(
                offline_id=action.offline_id,
                status="error",
                error=str(e),
            )
    
    def _get_action_handler(self, action_type: str):
        """Get handler for action type."""
        handlers = {
            SyncActionType.CREATE_TICKET.value: self._handle_create_ticket,
            SyncActionType.REPLY_TICKET.value: self._handle_reply_ticket,
            SyncActionType.CLOSE_TICKET.value: self._handle_close_ticket,
            SyncActionType.ADD_NOTE.value: self._handle_add_note,
            SyncActionType.UPDATE_PREFERENCES.value: self._handle_update_preferences,
            SyncActionType.MARK_NOTIFICATION_READ.value: self._handle_mark_notification_read,
        }
        return handlers.get(action_type)
    
    def _handle_create_ticket(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        server_id = f"tkt_{uuid4().hex[:12]}"
        logger.info(f"Created ticket {server_id} from offline action {action.offline_id}")
        return server_id
    
    def _handle_reply_ticket(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        server_id = f"msg_{uuid4().hex[:12]}"
        logger.info(f"Added reply {server_id} from offline action {action.offline_id}")
        return server_id
    
    def _handle_close_ticket(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        ticket_id = action.data.get("ticket_id")
        logger.info(f"Closed ticket {ticket_id} from offline action {action.offline_id}")
        return ticket_id
    
    def _handle_add_note(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        server_id = f"note_{uuid4().hex[:12]}"
        logger.info(f"Added note {server_id} from offline action {action.offline_id}")
        return server_id
    
    def _handle_update_preferences(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        logger.info(f"Updated preferences from offline action {action.offline_id}")
        return "preferences_updated"
    
    def _handle_mark_notification_read(self, action: SyncAction, contact_id: str, customer_id: str) -> str:
        notification_id = action.data.get("notification_id")
        logger.info(f"Marked notification {notification_id} as read")
        return notification_id
    
    def _get_updates_since(self, customer_id: str, contact_id: str, last_sync: Optional[str]) -> Dict[str, List]:
        """Get data updates since last sync."""
        if not last_sync:
            return {
                "invoices": self._get_invoice_updates(customer_id, None),
                "projects": self._get_project_updates(customer_id, None),
                "tickets": self._get_ticket_updates(customer_id, None),
                "notifications": self._get_notification_updates(contact_id, None),
            }
        
        sync_time = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
        
        return {
            "invoices": self._get_invoice_updates(customer_id, sync_time),
            "projects": self._get_project_updates(customer_id, sync_time),
            "tickets": self._get_ticket_updates(customer_id, sync_time),
            "notifications": self._get_notification_updates(contact_id, sync_time),
        }
    
    def _get_invoice_updates(self, customer_id: str, since: Optional[datetime]) -> List[Dict]:
        return [
            {"id": "inv_001", "number": "INV-2024-0042", "amount": 5250.00, "status": "pending", "due_date": "2024-02-15", "_action": "update"},
        ]
    
    def _get_project_updates(self, customer_id: str, since: Optional[datetime]) -> List[Dict]:
        return [
            {"id": "proj_001", "name": "Website Redesign", "progress": 68, "status": "active", "_action": "update"},
        ]
    
    def _get_ticket_updates(self, customer_id: str, since: Optional[datetime]) -> List[Dict]:
        return []
    
    def _get_notification_updates(self, contact_id: str, since: Optional[datetime]) -> List[Dict]:
        return []
    
    def get_sync_status(self, contact_id: str) -> Dict:
        """Get current sync status for a contact."""
        sync_state = self._sync_tokens.get(contact_id)
        
        if not sync_state:
            return {"status": "never_synced", "last_sync": None}
        
        return {
            "status": "synced",
            "last_sync": sync_state["timestamp"].isoformat() + "Z",
            "sync_token": sync_state["token"],
        }


# Service instance
sync_service = OfflineSyncService()
```

---

## File 4: Device Registration Service
**Path:** `backend/app/services/mobile/device_service.py`

```python
"""
Device Registration Service
Manages mobile device registration and tokens
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class Device:
    """Represents a registered device."""
    
    def __init__(self, contact_id: str, platform: str, device_token: str):
        self.id = f"dev_{uuid4().hex[:12]}"
        self.contact_id = contact_id
        self.platform = platform  # 'web', 'ios', 'android'
        self.device_token = device_token
        self.device_name = None
        self.device_model = None
        self.os_version = None
        self.app_version = None
        self.push_enabled = True
        self.is_active = True
        self.last_active_at = datetime.utcnow()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class DeviceService:
    """Manages device registration."""
    
    def __init__(self):
        self._devices: Dict[str, Device] = {}
    
    def register_device(self, contact_id: str, data: Dict) -> Device:
        """Register or update a device."""
        # Check if device already exists by token
        existing = self._find_by_token(data.get("token"))
        
        if existing:
            # Update existing device
            existing.contact_id = contact_id
            existing.last_active_at = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            existing.is_active = True
            
            if "device_name" in data:
                existing.device_name = data["device_name"]
            if "device_model" in data:
                existing.device_model = data["device_model"]
            if "os_version" in data:
                existing.os_version = data["os_version"]
            if "app_version" in data:
                existing.app_version = data["app_version"]
            
            logger.info(f"Updated device {existing.id} for contact {contact_id}")
            return existing
        
        # Create new device
        device = Device(
            contact_id=contact_id,
            platform=data.get("platform", "web"),
            device_token=data.get("token"),
        )
        device.device_name = data.get("device_name")
        device.device_model = data.get("device_model")
        device.os_version = data.get("os_version")
        device.app_version = data.get("app_version")
        
        self._devices[device.id] = device
        logger.info(f"Registered new device {device.id} for contact {contact_id}")
        
        return device
    
    def _find_by_token(self, token: str) -> Optional[Device]:
        """Find device by token."""
        if not token:
            return None
        for device in self._devices.values():
            if device.device_token == token:
                return device
        return None
    
    def unregister_device(self, device_id: str, contact_id: str) -> bool:
        """Unregister a device."""
        device = self._devices.get(device_id)
        if device and device.contact_id == contact_id:
            device.is_active = False
            device.updated_at = datetime.utcnow()
            logger.info(f"Unregistered device {device_id}")
            return True
        return False
    
    def get_devices(self, contact_id: str) -> List[Dict]:
        """Get all active devices for a contact."""
        devices = [
            d for d in self._devices.values()
            if d.contact_id == contact_id and d.is_active
        ]
        return [self._device_to_dict(d) for d in devices]
    
    def get_device(self, device_id: str, contact_id: str) -> Optional[Dict]:
        """Get a specific device."""
        device = self._devices.get(device_id)
        if device and device.contact_id == contact_id:
            return self._device_to_dict(device)
        return None
    
    def update_device(self, device_id: str, contact_id: str, data: Dict) -> Optional[Dict]:
        """Update device settings."""
        device = self._devices.get(device_id)
        if not device or device.contact_id != contact_id:
            return None
        
        if "device_name" in data:
            device.device_name = data["device_name"]
        if "push_enabled" in data:
            device.push_enabled = data["push_enabled"]
        
        device.updated_at = datetime.utcnow()
        return self._device_to_dict(device)
    
    def update_activity(self, device_id: str) -> bool:
        """Update device last activity timestamp."""
        device = self._devices.get(device_id)
        if device:
            device.last_active_at = datetime.utcnow()
            return True
        return False
    
    def get_push_tokens(self, contact_id: str) -> List[str]:
        """Get all push tokens for a contact's active devices."""
        devices = [
            d for d in self._devices.values()
            if d.contact_id == contact_id and d.is_active and d.push_enabled and d.device_token
        ]
        return [d.device_token for d in devices]
    
    def cleanup_inactive_devices(self, days: int = 90):
        """Remove devices inactive for specified days."""
        threshold = datetime.utcnow() - timedelta(days=days)
        removed = 0
        
        for device_id, device in list(self._devices.items()):
            if device.last_active_at < threshold:
                device.is_active = False
                removed += 1
        
        logger.info(f"Deactivated {removed} inactive devices")
        return removed
    
    def _device_to_dict(self, device: Device) -> Dict:
        """Convert device to dictionary."""
        return {
            "id": device.id,
            "platform": device.platform,
            "device_name": device.device_name,
            "device_model": device.device_model,
            "os_version": device.os_version,
            "app_version": device.app_version,
            "push_enabled": device.push_enabled,
            "last_active_at": device.last_active_at.isoformat(),
            "created_at": device.created_at.isoformat(),
        }


# Service instance
device_service = DeviceService()
```

---

## File 5: Services Init
**Path:** `backend/app/services/mobile/__init__.py`

```python
"""
Mobile Services - Service initialization
"""

from app.services.mobile.aggregator import mobile_aggregator
from app.services.mobile.push_service import push_service
from app.services.mobile.sync_service import sync_service
from app.services.mobile.device_service import device_service


__all__ = [
    'mobile_aggregator',
    'push_service',
    'sync_service',
    'device_service',
]
```

---

## Summary Part 1

| File | Description | Lines |
|------|-------------|-------|
| `aggregator.py` | Mobile data aggregation service | ~250 |
| `push_service.py` | Push notification service (VAPID) | ~280 |
| `sync_service.py` | Offline sync service | ~200 |
| `device_service.py` | Device registration service | ~180 |
| `__init__.py` | Services initialization | ~15 |
| **Total** | | **~925 lines** |
