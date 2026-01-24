"""
Workflow Triggers
Event and schedule trigger system
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import logging
import asyncio

from app.workflows.models import Workflow, TriggerType

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Available event types for triggers."""

    # Invoice events
    INVOICE_CREATED = "invoice.created"
    INVOICE_SENT = "invoice.sent"
    INVOICE_VIEWED = "invoice.viewed"
    INVOICE_PAID = "invoice.paid"
    INVOICE_OVERDUE = "invoice.overdue"
    INVOICE_CANCELLED = "invoice.cancelled"

    # Payment events
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"

    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"

    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_STARTED = "project.started"
    PROJECT_STATUS_CHANGED = "project.status_changed"
    PROJECT_COMPLETED = "project.completed"
    PROJECT_OVERDUE = "project.overdue"

    # Ticket events
    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"
    TICKET_ASSIGNED = "ticket.assigned"
    TICKET_ESCALATED = "ticket.escalated"
    TICKET_RESOLVED = "ticket.resolved"
    TICKET_CLOSED = "ticket.closed"

    # Quote events
    QUOTE_CREATED = "quote.created"
    QUOTE_SENT = "quote.sent"
    QUOTE_ACCEPTED = "quote.accepted"
    QUOTE_REJECTED = "quote.rejected"
    QUOTE_EXPIRED = "quote.expired"

    # User events
    USER_SIGNED_UP = "user.signed_up"
    USER_LOGGED_IN = "user.logged_in"


EVENT_METADATA = {
    EventType.INVOICE_CREATED: {
        "name": "Invoice Created",
        "description": "Triggered when a new invoice is created",
        "category": "invoices",
        "payload_schema": {
            "invoice_id": "string",
            "invoice_number": "string",
            "customer_id": "string",
            "amount": "number",
            "currency": "string",
            "due_date": "date",
        },
    },
    EventType.INVOICE_PAID: {
        "name": "Invoice Paid",
        "description": "Triggered when an invoice is paid",
        "category": "invoices",
        "payload_schema": {
            "invoice_id": "string",
            "invoice_number": "string",
            "customer_id": "string",
            "amount": "number",
            "paid_at": "datetime",
        },
    },
    EventType.INVOICE_OVERDUE: {
        "name": "Invoice Overdue",
        "description": "Triggered when an invoice becomes overdue",
        "category": "invoices",
        "payload_schema": {
            "invoice_id": "string",
            "days_overdue": "number",
            "amount": "number",
        },
    },
    EventType.PAYMENT_RECEIVED: {
        "name": "Payment Received",
        "description": "Triggered when a payment is received",
        "category": "payments",
        "payload_schema": {
            "payment_id": "string",
            "invoice_id": "string",
            "amount": "number",
            "method": "string",
        },
    },
    EventType.CUSTOMER_CREATED: {
        "name": "Customer Created",
        "description": "Triggered when a new customer is added",
        "category": "customers",
        "payload_schema": {
            "customer_id": "string",
            "name": "string",
            "email": "string",
            "company": "string",
        },
    },
    EventType.PROJECT_STATUS_CHANGED: {
        "name": "Project Status Changed",
        "description": "Triggered when a project status is updated",
        "category": "projects",
        "payload_schema": {
            "project_id": "string",
            "old_status": "string",
            "new_status": "string",
        },
    },
    EventType.TICKET_CREATED: {
        "name": "Ticket Created",
        "description": "Triggered when a support ticket is created",
        "category": "tickets",
        "payload_schema": {
            "ticket_id": "string",
            "subject": "string",
            "priority": "string",
            "customer_id": "string",
        },
    },
    EventType.TICKET_ESCALATED: {
        "name": "Ticket Escalated",
        "description": "Triggered when a ticket is escalated",
        "category": "tickets",
        "payload_schema": {
            "ticket_id": "string",
            "old_priority": "string",
            "new_priority": "string",
            "reason": "string",
        },
    },
}


class TriggerRegistry:
    """Registry for workflow triggers."""

    def __init__(self):
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._workflow_triggers: Dict[str, List[str]] = {}  # event -> [workflow_ids]
        self._scheduled_workflows: Dict[str, Dict] = {}  # workflow_id -> schedule_info

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register a handler for an event type."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.info(f"Registered handler for event: {event_type}")

    def subscribe_workflow(self, workflow_id: str, event_type: str):
        """Subscribe a workflow to an event."""
        if event_type not in self._workflow_triggers:
            self._workflow_triggers[event_type] = []
        if workflow_id not in self._workflow_triggers[event_type]:
            self._workflow_triggers[event_type].append(workflow_id)
            logger.info(f"Workflow {workflow_id} subscribed to {event_type}")

    def unsubscribe_workflow(self, workflow_id: str, event_type: str = None):
        """Unsubscribe a workflow from events."""
        if event_type:
            if event_type in self._workflow_triggers:
                self._workflow_triggers[event_type] = [
                    wf for wf in self._workflow_triggers[event_type]
                    if wf != workflow_id
                ]
        else:
            # Unsubscribe from all events
            for event in self._workflow_triggers:
                self._workflow_triggers[event] = [
                    wf for wf in self._workflow_triggers[event]
                    if wf != workflow_id
                ]

    def get_subscribed_workflows(self, event_type: str) -> List[str]:
        """Get workflows subscribed to an event."""
        return self._workflow_triggers.get(event_type, [])

    async def emit_event(self, event_type: str, payload: Dict[str, Any], customer_id: str = None):
        """Emit an event to trigger workflows."""
        logger.info(f"Event emitted: {event_type}")

        # Get subscribed workflows
        workflow_ids = self.get_subscribed_workflows(event_type)

        # Call registered handlers
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, payload, workflow_ids)
                else:
                    handler(event_type, payload, workflow_ids)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

        return workflow_ids

    def schedule_workflow(self, workflow_id: str, schedule_info: Dict):
        """Register a workflow for scheduled execution."""
        self._scheduled_workflows[workflow_id] = schedule_info
        logger.info(f"Workflow {workflow_id} scheduled: {schedule_info}")

    def unschedule_workflow(self, workflow_id: str):
        """Remove workflow from schedule."""
        if workflow_id in self._scheduled_workflows:
            del self._scheduled_workflows[workflow_id]

    def get_scheduled_workflows(self) -> Dict[str, Dict]:
        """Get all scheduled workflows."""
        return self._scheduled_workflows.copy()

    @staticmethod
    def get_available_events() -> List[Dict]:
        """Get list of available event types."""
        events = []
        for event_type in EventType:
            metadata = EVENT_METADATA.get(event_type, {})
            events.append({
                "type": event_type.value,
                "name": metadata.get("name", event_type.value),
                "description": metadata.get("description", ""),
                "category": metadata.get("category", "other"),
                "payload_schema": metadata.get("payload_schema", {}),
            })
        return events

    @staticmethod
    def get_events_by_category() -> Dict[str, List[Dict]]:
        """Get events grouped by category."""
        categories = {}
        for event in TriggerRegistry.get_available_events():
            cat = event["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(event)
        return categories


# Global trigger registry
trigger_registry = TriggerRegistry()


def init_trigger_handlers():
    """Initialize default trigger handlers."""
    from app.workflows.engine import workflow_engine
    from app.workflows.triggers import trigger_registry

    async def default_event_handler(event_type: str, payload: Dict, workflow_ids: List[str]):
        """Default handler that triggers workflows."""
        from app.services.workflow_service import workflow_service

        for workflow_id in workflow_ids:
            workflow = workflow_service.get_workflow(workflow_id)
            if workflow and workflow.status.value == "active":
                trigger_data = {
                    "event": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    **payload,
                }
                asyncio.create_task(
                    workflow_engine.execute(workflow, trigger_data=trigger_data)
                )

    # Register default handler for all events
    for event_type in EventType:
        trigger_registry.register_event_handler(event_type.value, default_event_handler)
