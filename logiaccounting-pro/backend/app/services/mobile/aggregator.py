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
