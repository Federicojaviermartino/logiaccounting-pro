"""
Support Ticket Service
Manages customer support tickets
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from app.utils.datetime_utils import utc_now
from app.models.crm_store import crm_store


logger = logging.getLogger(__name__)


class Ticket:
    """Support ticket model"""

    def __init__(self, tenant_id: str, customer_id: str, subject: str, description: str, category: str, priority: str = "normal"):
        self.id = f"tkt_{uuid4().hex[:12]}"
        self.tenant_id = tenant_id
        self.customer_id = customer_id
        self.ticket_number = self._generate_ticket_number()
        self.subject = subject
        self.description = description
        self.category = category
        self.priority = priority
        self.status = "open"
        self.assigned_to = None
        self.sla_due_at = self._calculate_sla(priority)
        self.first_response_at = None
        self.resolved_at = None
        self.satisfaction_rating = None
        self.satisfaction_comment = None
        self.tags = []
        self.custom_fields = {}
        self.messages = []
        self.created_at = utc_now()
        self.updated_at = utc_now()

    def _generate_ticket_number(self) -> str:
        import random
        return f"TKT-{random.randint(100000, 999999)}"

    def _calculate_sla(self, priority: str) -> datetime:
        hours = {"urgent": 4, "high": 8, "normal": 24, "low": 48}
        return utc_now() + timedelta(hours=hours.get(priority, 24))


class TicketMessage:
    """Ticket message/reply"""

    def __init__(self, ticket_id: str, sender_type: str, sender_id: str, sender_name: str, message: str, attachments: List = None, is_internal: bool = False):
        self.id = f"msg_{uuid4().hex[:12]}"
        self.ticket_id = ticket_id
        self.sender_type = sender_type
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.message = message
        self.attachments = attachments or []
        self.is_internal = is_internal
        self.created_at = utc_now()


class TicketService:
    """Manages support tickets."""

    CATEGORIES = [
        {"id": "billing", "name": "Billing & Payments", "icon": "credit-card"},
        {"id": "technical", "name": "Technical Support", "icon": "settings"},
        {"id": "general", "name": "General Inquiry", "icon": "help-circle"},
        {"id": "feature_request", "name": "Feature Request", "icon": "lightbulb"},
        {"id": "bug_report", "name": "Bug Report", "icon": "bug"},
        {"id": "account", "name": "Account Management", "icon": "user"},
    ]

    PRIORITIES = [
        {"id": "low", "name": "Low", "sla_hours": 48},
        {"id": "normal", "name": "Normal", "sla_hours": 24},
        {"id": "high", "name": "High", "sla_hours": 8},
        {"id": "urgent", "name": "Urgent", "sla_hours": 4},
    ]

    STATUSES = ["open", "in_progress", "waiting_customer", "resolved", "closed"]

    def __init__(self):
        self._tickets: Dict[str, Ticket] = {}

    def create_ticket(
        self,
        tenant_id: str,
        customer_id: str,
        contact_id: str,
        subject: str,
        description: str,
        category: str,
        priority: str = "normal",
        attachments: List = None,
    ) -> Ticket:
        """Create a new support ticket."""
        ticket = Ticket(
            tenant_id=tenant_id,
            customer_id=customer_id,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
        )

        contact = crm_store.get_contact(contact_id)
        sender_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() if contact else "Customer"

        initial_msg = TicketMessage(
            ticket_id=ticket.id,
            sender_type="customer",
            sender_id=contact_id,
            sender_name=sender_name,
            message=description,
            attachments=attachments or [],
        )
        ticket.messages.append(initial_msg)

        self._tickets[ticket.id] = ticket

        logger.info(f"Ticket created: {ticket.ticket_number}")

        return ticket

    def get_ticket(self, ticket_id: str, customer_id: str = None) -> Optional[Ticket]:
        """Get ticket by ID."""
        ticket = self._tickets.get(ticket_id)
        if ticket and customer_id and ticket.customer_id != customer_id:
            return None
        return ticket

    def get_ticket_by_number(self, ticket_number: str, customer_id: str = None) -> Optional[Ticket]:
        """Get ticket by ticket number."""
        for ticket in self._tickets.values():
            if ticket.ticket_number == ticket_number:
                if customer_id and ticket.customer_id != customer_id:
                    return None
                return ticket
        return None

    def list_tickets(
        self,
        customer_id: str,
        status: str = None,
        category: str = None,
        priority: str = None,
        search: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List tickets for a customer."""
        tickets = [t for t in self._tickets.values() if t.customer_id == customer_id]

        if status:
            if status == "open":
                tickets = [t for t in tickets if t.status in ["open", "in_progress", "waiting_customer"]]
            elif status == "closed":
                tickets = [t for t in tickets if t.status in ["resolved", "closed"]]
            else:
                tickets = [t for t in tickets if t.status == status]

        if category:
            tickets = [t for t in tickets if t.category == category]

        if priority:
            tickets = [t for t in tickets if t.priority == priority]

        if search:
            search_lower = search.lower()
            tickets = [t for t in tickets if search_lower in t.subject.lower() or search_lower in t.ticket_number.lower()]

        tickets.sort(key=lambda t: t.updated_at, reverse=True)

        total = len(tickets)
        skip = (page - 1) * page_size
        tickets = tickets[skip:skip + page_size]

        return {
            "items": [self._ticket_to_dict(t) for t in tickets],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def add_reply(
        self,
        ticket_id: str,
        sender_type: str,
        sender_id: str,
        sender_name: str,
        message: str,
        attachments: List = None,
        is_internal: bool = False,
    ) -> TicketMessage:
        """Add a reply to a ticket."""
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        msg = TicketMessage(
            ticket_id=ticket_id,
            sender_type=sender_type,
            sender_id=sender_id,
            sender_name=sender_name,
            message=message,
            attachments=attachments or [],
            is_internal=is_internal,
        )

        ticket.messages.append(msg)
        ticket.updated_at = utc_now()

        if sender_type == "customer" and ticket.status == "waiting_customer":
            ticket.status = "in_progress"
        elif sender_type == "agent" and ticket.status == "open":
            ticket.status = "in_progress"
            if not ticket.first_response_at:
                ticket.first_response_at = utc_now()

        logger.info(f"Reply added to ticket {ticket.ticket_number}")

        return msg

    def update_status(self, ticket_id: str, status: str, user_id: str = None) -> Ticket:
        """Update ticket status."""
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        if status not in self.STATUSES:
            raise ValueError(f"Invalid status: {status}")

        old_status = ticket.status
        ticket.status = status
        ticket.updated_at = utc_now()

        if status == "resolved":
            ticket.resolved_at = utc_now()

        msg = TicketMessage(
            ticket_id=ticket_id,
            sender_type="system",
            sender_id="system",
            sender_name="System",
            message=f"Status changed from {old_status} to {status}",
            is_internal=True,
        )
        ticket.messages.append(msg)

        logger.info(f"Ticket {ticket.ticket_number} status changed to {status}")

        return ticket

    def close_ticket(self, ticket_id: str, customer_id: str) -> Ticket:
        """Close a ticket (by customer)."""
        ticket = self._tickets.get(ticket_id)
        if not ticket or ticket.customer_id != customer_id:
            raise ValueError("Ticket not found")

        return self.update_status(ticket_id, "closed")

    def reopen_ticket(self, ticket_id: str, customer_id: str, reason: str = None) -> Ticket:
        """Reopen a closed ticket."""
        ticket = self._tickets.get(ticket_id)
        if not ticket or ticket.customer_id != customer_id:
            raise ValueError("Ticket not found")

        if ticket.status not in ["resolved", "closed"]:
            raise ValueError("Ticket is not closed")

        ticket.status = "open"
        ticket.resolved_at = None
        ticket.updated_at = utc_now()

        msg = TicketMessage(
            ticket_id=ticket_id,
            sender_type="customer",
            sender_id=customer_id,
            sender_name="Customer",
            message=f"Ticket reopened. Reason: {reason or 'Not specified'}",
        )
        ticket.messages.append(msg)

        return ticket

    def rate_ticket(self, ticket_id: str, customer_id: str, rating: int, comment: str = None) -> Ticket:
        """Rate ticket satisfaction."""
        ticket = self._tickets.get(ticket_id)
        if not ticket or ticket.customer_id != customer_id:
            raise ValueError("Ticket not found")

        if ticket.status not in ["resolved", "closed"]:
            raise ValueError("Can only rate resolved/closed tickets")

        ticket.satisfaction_rating = max(1, min(5, rating))
        ticket.satisfaction_comment = comment
        ticket.updated_at = utc_now()

        logger.info(f"Ticket {ticket.ticket_number} rated {rating}/5")

        return ticket

    def get_stats(self, customer_id: str) -> Dict[str, Any]:
        """Get ticket statistics for customer."""
        tickets = [t for t in self._tickets.values() if t.customer_id == customer_id]

        open_count = len([t for t in tickets if t.status in ["open", "in_progress", "waiting_customer"]])
        resolved_count = len([t for t in tickets if t.status in ["resolved", "closed"]])

        avg_rating = 0
        rated_tickets = [t for t in tickets if t.satisfaction_rating]
        if rated_tickets:
            avg_rating = sum(t.satisfaction_rating for t in rated_tickets) / len(rated_tickets)

        return {
            "total": len(tickets),
            "open": open_count,
            "resolved": resolved_count,
            "average_rating": round(avg_rating, 1),
        }

    def get_categories(self) -> List[Dict]:
        """Get available ticket categories."""
        return self.CATEGORIES

    def get_priorities(self) -> List[Dict]:
        """Get available priorities."""
        return self.PRIORITIES

    def _ticket_to_dict(self, ticket: Ticket, include_messages: bool = False) -> Dict:
        """Convert ticket to dictionary."""
        result = {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "subject": ticket.subject,
            "description": ticket.description,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": ticket.status,
            "sla_due_at": ticket.sla_due_at.isoformat() if ticket.sla_due_at else None,
            "first_response_at": ticket.first_response_at.isoformat() if ticket.first_response_at else None,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            "satisfaction_rating": ticket.satisfaction_rating,
            "message_count": len(ticket.messages),
            "last_message": ticket.messages[-1].message[:100] if ticket.messages else None,
            "created_at": ticket.created_at.isoformat(),
            "updated_at": ticket.updated_at.isoformat(),
        }

        if include_messages:
            result["messages"] = [
                {
                    "id": m.id,
                    "sender_type": m.sender_type,
                    "sender_name": m.sender_name,
                    "message": m.message,
                    "attachments": m.attachments,
                    "is_internal": m.is_internal,
                    "created_at": m.created_at.isoformat(),
                }
                for m in ticket.messages
                if not m.is_internal
            ]

        return result


ticket_service = TicketService()
