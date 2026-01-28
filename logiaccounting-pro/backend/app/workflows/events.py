"""
Workflow Event Emitter
Centralized event emission for workflow triggers
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
import asyncio

from app.utils.datetime_utils import utc_now

from app.workflows.triggers import trigger_registry, EventType

logger = logging.getLogger(__name__)


class WorkflowEventEmitter:
    """Emits events to trigger workflows."""

    def __init__(self):
        self._event_history: list = []
        self._max_history = 1000

    async def emit(self, event_type: str, payload: Dict[str, Any], customer_id: str = None) -> Dict:
        """Emit an event."""
        event = {
            "type": event_type,
            "payload": payload,
            "customer_id": customer_id,
            "timestamp": utc_now().isoformat(),
        }

        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

        # Trigger workflows
        triggered_workflows = await trigger_registry.emit_event(
            event_type, payload, customer_id
        )

        event["triggered_workflows"] = triggered_workflows

        logger.info(f"Event {event_type} emitted, triggered {len(triggered_workflows)} workflows")

        return event

    def get_recent_events(self, limit: int = 50, event_type: str = None) -> list:
        """Get recent events."""
        events = self._event_history

        if event_type:
            events = [e for e in events if e["type"] == event_type]

        return events[-limit:][::-1]  # Most recent first

    # ==================== Convenience Methods ====================

    async def invoice_created(self, invoice: Dict) -> Dict:
        """Emit invoice.created event."""
        return await self.emit(
            EventType.INVOICE_CREATED.value,
            {
                "invoice": invoice,
                "invoice_id": invoice.get("id"),
                "invoice_number": invoice.get("number"),
                "customer_id": invoice.get("customer_id"),
                "customer": invoice.get("customer"),
                "amount": invoice.get("total"),
                "currency": invoice.get("currency"),
                "due_date": invoice.get("due_date"),
            },
            customer_id=invoice.get("customer_id"),
        )

    async def invoice_paid(self, invoice: Dict, payment: Dict) -> Dict:
        """Emit invoice.paid event."""
        return await self.emit(
            EventType.INVOICE_PAID.value,
            {
                "invoice": invoice,
                "payment": payment,
                "invoice_id": invoice.get("id"),
                "invoice_number": invoice.get("number"),
                "customer_id": invoice.get("customer_id"),
                "amount": payment.get("amount"),
                "paid_at": payment.get("paid_at") or utc_now().isoformat(),
            },
            customer_id=invoice.get("customer_id"),
        )

    async def invoice_overdue(self, invoice: Dict, days_overdue: int) -> Dict:
        """Emit invoice.overdue event."""
        return await self.emit(
            EventType.INVOICE_OVERDUE.value,
            {
                "invoice": invoice,
                "invoice_id": invoice.get("id"),
                "invoice_number": invoice.get("number"),
                "customer_id": invoice.get("customer_id"),
                "amount": invoice.get("total"),
                "due_date": invoice.get("due_date"),
                "days_overdue": days_overdue,
            },
            customer_id=invoice.get("customer_id"),
        )

    async def payment_received(self, payment: Dict) -> Dict:
        """Emit payment.received event."""
        return await self.emit(
            EventType.PAYMENT_RECEIVED.value,
            {
                "payment": payment,
                "payment_id": payment.get("id"),
                "invoice_id": payment.get("invoice_id"),
                "customer_id": payment.get("customer_id"),
                "amount": payment.get("amount"),
                "method": payment.get("method"),
                "received_at": payment.get("paid_at") or utc_now().isoformat(),
            },
            customer_id=payment.get("customer_id"),
        )

    async def customer_created(self, customer: Dict) -> Dict:
        """Emit customer.created event."""
        return await self.emit(
            EventType.CUSTOMER_CREATED.value,
            {
                "customer": customer,
                "customer_id": customer.get("id"),
                "name": customer.get("name"),
                "email": customer.get("email"),
                "company": customer.get("company_name"),
            },
            customer_id=customer.get("id"),
        )

    async def project_status_changed(self, project: Dict, old_status: str, new_status: str) -> Dict:
        """Emit project.status_changed event."""
        return await self.emit(
            EventType.PROJECT_STATUS_CHANGED.value,
            {
                "project": project,
                "project_id": project.get("id"),
                "project_name": project.get("name"),
                "customer_id": project.get("customer_id"),
                "old_status": old_status,
                "new_status": new_status,
            },
            customer_id=project.get("customer_id"),
        )

    async def ticket_created(self, ticket: Dict) -> Dict:
        """Emit ticket.created event."""
        return await self.emit(
            EventType.TICKET_CREATED.value,
            {
                "ticket": ticket,
                "ticket_id": ticket.get("id"),
                "ticket_number": ticket.get("number"),
                "subject": ticket.get("subject"),
                "description": ticket.get("description"),
                "priority": ticket.get("priority"),
                "customer_id": ticket.get("customer_id"),
            },
            customer_id=ticket.get("customer_id"),
        )

    async def ticket_escalated(self, ticket: Dict, old_priority: str, new_priority: str, reason: str = None) -> Dict:
        """Emit ticket.escalated event."""
        return await self.emit(
            EventType.TICKET_ESCALATED.value,
            {
                "ticket": ticket,
                "ticket_id": ticket.get("id"),
                "ticket_number": ticket.get("number"),
                "subject": ticket.get("subject"),
                "old_priority": old_priority,
                "new_priority": new_priority,
                "reason": reason,
                "customer_id": ticket.get("customer_id"),
            },
            customer_id=ticket.get("customer_id"),
        )


# Global event emitter instance
event_emitter = WorkflowEventEmitter()
