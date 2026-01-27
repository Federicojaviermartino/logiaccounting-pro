"""
Portal Dashboard Service
Aggregates data for customer portal dashboard
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.models.store import db
from app.models.crm_store import crm_store


logger = logging.getLogger(__name__)


class PortalDashboardService:
    """Provides dashboard data for portal customers."""

    def get_dashboard(self, customer_id: str, contact_id: str, tenant_id: str) -> Dict[str, Any]:
        """Get complete dashboard data for a customer."""
        return {
            "welcome": self._get_welcome_data(customer_id, contact_id),
            "stats": self._get_stats(customer_id, tenant_id),
            "recent_activity": self._get_recent_activity(customer_id, tenant_id),
            "quick_actions": self._get_quick_actions(customer_id),
            "open_tickets": self._get_open_tickets(customer_id),
            "pending_invoices": self._get_pending_invoices(customer_id),
            "active_projects": self._get_active_projects(customer_id),
            "pending_quotes": self._get_pending_quotes(customer_id),
            "unread_messages": self._get_unread_message_count(customer_id),
            "announcements": self._get_announcements(tenant_id),
        }

    def _get_welcome_data(self, customer_id: str, contact_id: str) -> Dict:
        """Get welcome message data."""
        contact = crm_store.get_contact(contact_id)
        company = crm_store.get_company(customer_id)

        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        return {
            "greeting": greeting,
            "name": contact.get("first_name", "there") if contact else "there",
            "company_name": company.get("name") if company else None,
        }

    def _get_stats(self, customer_id: str, tenant_id: str) -> Dict:
        """Get summary statistics."""
        invoices = [i for i in db.invoices.find_all() if i.get("client_id") == customer_id]

        total_invoiced = sum(i.get("total", 0) for i in invoices)
        total_paid = sum(i.get("total", 0) for i in invoices if i.get("status") == "paid")
        total_pending = sum(i.get("total", 0) for i in invoices if i.get("status") == "pending")
        total_overdue = sum(i.get("total", 0) for i in invoices if i.get("status") == "overdue")

        projects = [p for p in db.projects.find_all() if p.get("client_id") == customer_id]
        active_projects = len([p for p in projects if p.get("status") == "active"])

        payments = [p for p in db.payments.find_all() if p.get("client_id") == customer_id]
        this_month = datetime.utcnow().replace(day=1)
        payments_this_month = sum(
            p.get("amount", 0) for p in payments
            if p.get("status") == "completed" and
            datetime.fromisoformat(p.get("paid_at", "2000-01-01")) >= this_month
        )

        return {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "total_overdue": total_overdue,
            "active_projects": active_projects,
            "payments_this_month": payments_this_month,
        }

    def _get_recent_activity(self, customer_id: str, tenant_id: str, limit: int = 10) -> List[Dict]:
        """Get recent activity feed."""
        activities = []

        invoices = [i for i in db.invoices.find_all() if i.get("client_id") == customer_id]
        for inv in sorted(invoices, key=lambda x: x.get("created_at", ""), reverse=True)[:3]:
            activities.append({
                "type": "invoice",
                "action": "created" if inv.get("status") == "draft" else inv.get("status"),
                "title": f"Invoice #{inv.get('invoice_number', inv['id'][:8])}",
                "description": f"Amount: ${inv.get('total', 0):,.2f}",
                "timestamp": inv.get("created_at"),
                "icon": "file-text",
            })

        payments = [p for p in db.payments.find_all() if p.get("client_id") == customer_id]
        for pay in sorted(payments, key=lambda x: x.get("created_at", ""), reverse=True)[:3]:
            activities.append({
                "type": "payment",
                "action": pay.get("status"),
                "title": "Payment Received" if pay.get("status") == "completed" else "Payment Processing",
                "description": f"Amount: ${pay.get('amount', 0):,.2f}",
                "timestamp": pay.get("paid_at") or pay.get("created_at"),
                "icon": "credit-card",
            })

        projects = [p for p in db.projects.find_all() if p.get("client_id") == customer_id]
        for proj in sorted(projects, key=lambda x: x.get("updated_at", ""), reverse=True)[:2]:
            activities.append({
                "type": "project",
                "action": "updated",
                "title": proj.get("name", "Project"),
                "description": f"Status: {proj.get('status', 'active')}",
                "timestamp": proj.get("updated_at"),
                "icon": "folder",
            })

        activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return activities[:limit]

    def _get_quick_actions(self, customer_id: str) -> List[Dict]:
        """Get available quick actions."""
        actions = [
            {"id": "new_ticket", "label": "Create Support Ticket", "icon": "help-circle", "url": "/portal/support/new"},
            {"id": "pay_invoice", "label": "Pay Invoice", "icon": "credit-card", "url": "/portal/payments"},
            {"id": "send_message", "label": "Send Message", "icon": "message-circle", "url": "/portal/messages"},
            {"id": "view_documents", "label": "View Documents", "icon": "file", "url": "/portal/documents"},
        ]

        quotes = crm_store.list_quotes_for_company(customer_id)
        pending_quotes = [q for q in quotes if q.get("status") == "sent"]
        if pending_quotes:
            actions.insert(0, {
                "id": "review_quotes",
                "label": f"Review Quotes ({len(pending_quotes)})",
                "icon": "file-check",
                "url": "/portal/quotes",
                "badge": len(pending_quotes),
            })

        return actions

    def _get_open_tickets(self, customer_id: str, limit: int = 5) -> List[Dict]:
        """Get open support tickets."""
        return []

    def _get_pending_invoices(self, customer_id: str, limit: int = 5) -> List[Dict]:
        """Get pending invoices."""
        invoices = [
            i for i in db.invoices.find_all()
            if i.get("client_id") == customer_id and i.get("status") in ["pending", "overdue"]
        ]

        invoices.sort(key=lambda x: x.get("due_date", ""), reverse=False)

        return [
            {
                "id": inv["id"],
                "invoice_number": inv.get("invoice_number", inv["id"][:8]),
                "amount": inv.get("total", 0),
                "due_date": inv.get("due_date"),
                "status": inv.get("status"),
                "is_overdue": inv.get("status") == "overdue",
            }
            for inv in invoices[:limit]
        ]

    def _get_active_projects(self, customer_id: str, limit: int = 5) -> List[Dict]:
        """Get active projects."""
        projects = [
            p for p in db.projects.find_all()
            if p.get("client_id") == customer_id and p.get("status") == "active"
        ]

        return [
            {
                "id": proj["id"],
                "name": proj.get("name"),
                "progress": proj.get("progress", 0),
                "status": proj.get("status"),
                "due_date": proj.get("end_date"),
            }
            for proj in projects[:limit]
        ]

    def _get_pending_quotes(self, customer_id: str, limit: int = 5) -> List[Dict]:
        """Get quotes awaiting response."""
        quotes = crm_store.list_quotes_for_company(customer_id)
        pending = [q for q in quotes if q.get("status") == "sent"]

        return [
            {
                "id": q["id"],
                "quote_number": q.get("quote_number"),
                "total": q.get("total", 0),
                "valid_until": q.get("valid_until"),
                "expires_soon": self._is_expiring_soon(q.get("valid_until")),
            }
            for q in pending[:limit]
        ]

    def _get_unread_message_count(self, customer_id: str) -> int:
        """Get unread message count."""
        return 0

    def _get_announcements(self, tenant_id: str, limit: int = 3) -> List[Dict]:
        """Get portal announcements."""
        return []

    def _is_expiring_soon(self, date_str: str, days: int = 7) -> bool:
        """Check if date is within N days."""
        if not date_str:
            return False
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date <= datetime.utcnow() + timedelta(days=days)
        except:
            return False


portal_dashboard_service = PortalDashboardService()
