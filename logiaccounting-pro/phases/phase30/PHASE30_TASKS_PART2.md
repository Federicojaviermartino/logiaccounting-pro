# Phase 30: Workflow Automation - Part 2: Triggers & Scheduler

## Overview
This part covers the trigger system including event triggers, schedule triggers, and the scheduler service.

---

## File 1: Trigger Definitions
**Path:** `backend/app/workflows/triggers.py`

```python
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
```

---

## File 2: Scheduler Service
**Path:** `backend/app/workflows/scheduler.py`

```python
"""
Workflow Scheduler
Cron and interval-based workflow scheduling
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import asyncio
import logging
from croniter import croniter

logger = logging.getLogger(__name__)


class ScheduledJob:
    """Represents a scheduled workflow job."""
    
    def __init__(self, workflow_id: str, schedule_type: str, schedule_config: Dict):
        self.workflow_id = workflow_id
        self.schedule_type = schedule_type  # "cron", "interval", "daily", "weekly"
        self.schedule_config = schedule_config
        self.enabled = True
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
        
        # Calculate next run time
        self._calculate_next_run()
    
    def _calculate_next_run(self):
        """Calculate the next run time."""
        now = datetime.utcnow()
        
        if self.schedule_type == "cron":
            cron_expr = self.schedule_config.get("cron", "0 * * * *")
            try:
                cron = croniter(cron_expr, now)
                self.next_run = cron.get_next(datetime)
            except Exception as e:
                logger.error(f"Invalid cron expression: {cron_expr} - {e}")
                self.next_run = None
        
        elif self.schedule_type == "interval":
            interval_seconds = self.schedule_config.get("interval_seconds", 3600)
            self.next_run = now + timedelta(seconds=interval_seconds)
        
        elif self.schedule_type == "daily":
            time_str = self.schedule_config.get("time", "09:00")
            hour, minute = map(int, time_str.split(":"))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            self.next_run = next_run
        
        elif self.schedule_type == "weekly":
            day = self.schedule_config.get("day", 0)  # 0 = Monday
            time_str = self.schedule_config.get("time", "09:00")
            hour, minute = map(int, time_str.split(":"))
            
            days_ahead = day - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            self.next_run = next_run
    
    def mark_executed(self, success: bool = True, error: str = None):
        """Mark job as executed and calculate next run."""
        self.last_run = datetime.utcnow()
        self.run_count += 1
        
        if not success:
            self.error_count += 1
            self.last_error = error
        
        self._calculate_next_run()
    
    def is_due(self) -> bool:
        """Check if job is due for execution."""
        if not self.enabled or not self.next_run:
            return False
        return datetime.utcnow() >= self.next_run
    
    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "schedule_type": self.schedule_type,
            "schedule_config": self.schedule_config,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
        }


class WorkflowScheduler:
    """Manages scheduled workflow execution."""
    
    def __init__(self):
        self._jobs: Dict[str, ScheduledJob] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._check_interval = 60  # seconds
        self._on_execute: Optional[Callable] = None
    
    def set_executor(self, executor: Callable):
        """Set the workflow executor callback."""
        self._on_execute = executor
    
    def add_job(self, workflow_id: str, schedule_type: str, schedule_config: Dict) -> ScheduledJob:
        """Add a scheduled job."""
        job = ScheduledJob(workflow_id, schedule_type, schedule_config)
        self._jobs[workflow_id] = job
        logger.info(f"Scheduled job added: {workflow_id} ({schedule_type})")
        return job
    
    def remove_job(self, workflow_id: str) -> bool:
        """Remove a scheduled job."""
        if workflow_id in self._jobs:
            del self._jobs[workflow_id]
            logger.info(f"Scheduled job removed: {workflow_id}")
            return True
        return False
    
    def update_job(self, workflow_id: str, schedule_type: str = None, schedule_config: Dict = None) -> Optional[ScheduledJob]:
        """Update a scheduled job."""
        job = self._jobs.get(workflow_id)
        if not job:
            return None
        
        if schedule_type:
            job.schedule_type = schedule_type
        if schedule_config:
            job.schedule_config = schedule_config
        
        job._calculate_next_run()
        return job
    
    def enable_job(self, workflow_id: str) -> bool:
        """Enable a scheduled job."""
        job = self._jobs.get(workflow_id)
        if job:
            job.enabled = True
            job._calculate_next_run()
            return True
        return False
    
    def disable_job(self, workflow_id: str) -> bool:
        """Disable a scheduled job."""
        job = self._jobs.get(workflow_id)
        if job:
            job.enabled = False
            return True
        return False
    
    def get_job(self, workflow_id: str) -> Optional[ScheduledJob]:
        """Get a scheduled job."""
        return self._jobs.get(workflow_id)
    
    def get_all_jobs(self) -> List[ScheduledJob]:
        """Get all scheduled jobs."""
        return list(self._jobs.values())
    
    def get_due_jobs(self) -> List[ScheduledJob]:
        """Get jobs that are due for execution."""
        return [job for job in self._jobs.values() if job.is_due()]
    
    async def start(self):
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Workflow scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Workflow scheduler stopped")
    
    async def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_execute()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(self._check_interval)
    
    async def _check_and_execute(self):
        """Check for due jobs and execute them."""
        due_jobs = self.get_due_jobs()
        
        for job in due_jobs:
            if self._on_execute:
                try:
                    logger.info(f"Executing scheduled workflow: {job.workflow_id}")
                    await self._on_execute(job.workflow_id, {
                        "trigger_type": "schedule",
                        "schedule_type": job.schedule_type,
                        "scheduled_time": job.next_run.isoformat() if job.next_run else None,
                    })
                    job.mark_executed(success=True)
                except Exception as e:
                    logger.error(f"Scheduled execution failed: {job.workflow_id} - {e}")
                    job.mark_executed(success=False, error=str(e))
    
    async def run_now(self, workflow_id: str) -> bool:
        """Manually trigger a scheduled workflow."""
        job = self._jobs.get(workflow_id)
        if not job or not self._on_execute:
            return False
        
        try:
            await self._on_execute(workflow_id, {
                "trigger_type": "manual",
                "triggered_at": datetime.utcnow().isoformat(),
            })
            return True
        except Exception as e:
            logger.error(f"Manual execution failed: {workflow_id} - {e}")
            return False
    
    def get_schedule_preview(self, schedule_type: str, schedule_config: Dict, count: int = 5) -> List[datetime]:
        """Preview upcoming execution times."""
        times = []
        temp_job = ScheduledJob("preview", schedule_type, schedule_config)
        
        for _ in range(count):
            if temp_job.next_run:
                times.append(temp_job.next_run)
                temp_job.last_run = temp_job.next_run
                temp_job._calculate_next_run()
            else:
                break
        
        return times


# Global scheduler instance
workflow_scheduler = WorkflowScheduler()


class CronExpressionHelper:
    """Helper for building cron expressions."""
    
    PRESETS = {
        "every_minute": "* * * * *",
        "every_5_minutes": "*/5 * * * *",
        "every_15_minutes": "*/15 * * * *",
        "every_30_minutes": "*/30 * * * *",
        "every_hour": "0 * * * *",
        "every_2_hours": "0 */2 * * *",
        "every_6_hours": "0 */6 * * *",
        "every_12_hours": "0 */12 * * *",
        "daily_midnight": "0 0 * * *",
        "daily_9am": "0 9 * * *",
        "daily_6pm": "0 18 * * *",
        "weekly_monday": "0 9 * * 1",
        "weekly_friday": "0 17 * * 5",
        "monthly_first": "0 9 1 * *",
        "monthly_last": "0 9 L * *",
        "quarterly": "0 9 1 1,4,7,10 *",
    }
    
    @classmethod
    def get_preset(cls, name: str) -> Optional[str]:
        """Get a preset cron expression."""
        return cls.PRESETS.get(name)
    
    @classmethod
    def list_presets(cls) -> List[Dict]:
        """List available presets."""
        return [
            {"name": name, "cron": cron, "description": cls._describe(cron)}
            for name, cron in cls.PRESETS.items()
        ]
    
    @classmethod
    def _describe(cls, cron: str) -> str:
        """Generate human-readable description."""
        descriptions = {
            "* * * * *": "Every minute",
            "*/5 * * * *": "Every 5 minutes",
            "*/15 * * * *": "Every 15 minutes",
            "*/30 * * * *": "Every 30 minutes",
            "0 * * * *": "Every hour",
            "0 */2 * * *": "Every 2 hours",
            "0 */6 * * *": "Every 6 hours",
            "0 */12 * * *": "Every 12 hours",
            "0 0 * * *": "Daily at midnight",
            "0 9 * * *": "Daily at 9:00 AM",
            "0 18 * * *": "Daily at 6:00 PM",
            "0 9 * * 1": "Weekly on Monday at 9:00 AM",
            "0 17 * * 5": "Weekly on Friday at 5:00 PM",
            "0 9 1 * *": "Monthly on the 1st at 9:00 AM",
            "0 9 L * *": "Monthly on the last day at 9:00 AM",
            "0 9 1 1,4,7,10 *": "Quarterly on the 1st at 9:00 AM",
        }
        return descriptions.get(cron, cron)
    
    @classmethod
    def build(cls, minute: str = "*", hour: str = "*", day: str = "*", month: str = "*", weekday: str = "*") -> str:
        """Build a cron expression from components."""
        return f"{minute} {hour} {day} {month} {weekday}"
    
    @classmethod
    def validate(cls, cron: str) -> tuple[bool, str]:
        """Validate a cron expression."""
        try:
            croniter(cron)
            return True, "Valid cron expression"
        except Exception as e:
            return False, str(e)
    
    @classmethod
    def get_next_runs(cls, cron: str, count: int = 5) -> List[datetime]:
        """Get next N run times for a cron expression."""
        try:
            now = datetime.utcnow()
            cron_iter = croniter(cron, now)
            return [cron_iter.get_next(datetime) for _ in range(count)]
        except Exception:
            return []
```

---

## File 3: Event Emitter
**Path:** `backend/app/workflows/events.py`

```python
"""
Workflow Event Emitter
Centralized event emission for workflow triggers
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
import asyncio

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
            "timestamp": datetime.utcnow().isoformat(),
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
                "paid_at": payment.get("paid_at") or datetime.utcnow().isoformat(),
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
                "received_at": payment.get("paid_at") or datetime.utcnow().isoformat(),
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
```

---

## File 4: Webhook Trigger Handler
**Path:** `backend/app/workflows/webhook_trigger.py`

```python
"""
Webhook Trigger Handler
Handles incoming webhooks that trigger workflows
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


class WebhookTrigger:
    """Represents a webhook trigger configuration."""
    
    def __init__(self, workflow_id: str, path: str = None):
        self.id = f"wht_{uuid4().hex[:12]}"
        self.workflow_id = workflow_id
        self.path = path or f"/webhooks/trigger/{self.id}"
        self.secret = uuid4().hex
        self.enabled = True
        self.created_at = datetime.utcnow()
        self.last_triggered_at: Optional[datetime] = None
        self.trigger_count = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "path": self.path,
            "url": f"https://api.logiaccounting.com{self.path}",
            "secret": self.secret,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "trigger_count": self.trigger_count,
        }


class WebhookTriggerHandler:
    """Manages webhook triggers for workflows."""
    
    def __init__(self):
        self._triggers: Dict[str, WebhookTrigger] = {}  # id -> trigger
        self._path_map: Dict[str, str] = {}  # path -> trigger_id
    
    def create_trigger(self, workflow_id: str, custom_path: str = None) -> WebhookTrigger:
        """Create a webhook trigger for a workflow."""
        trigger = WebhookTrigger(workflow_id, custom_path)
        self._triggers[trigger.id] = trigger
        self._path_map[trigger.path] = trigger.id
        
        logger.info(f"Created webhook trigger {trigger.id} for workflow {workflow_id}")
        return trigger
    
    def get_trigger(self, trigger_id: str) -> Optional[WebhookTrigger]:
        """Get trigger by ID."""
        return self._triggers.get(trigger_id)
    
    def get_trigger_by_path(self, path: str) -> Optional[WebhookTrigger]:
        """Get trigger by path."""
        trigger_id = self._path_map.get(path)
        if trigger_id:
            return self._triggers.get(trigger_id)
        return None
    
    def get_workflow_triggers(self, workflow_id: str) -> List[WebhookTrigger]:
        """Get all triggers for a workflow."""
        return [t for t in self._triggers.values() if t.workflow_id == workflow_id]
    
    def delete_trigger(self, trigger_id: str) -> bool:
        """Delete a webhook trigger."""
        trigger = self._triggers.get(trigger_id)
        if trigger:
            del self._triggers[trigger_id]
            if trigger.path in self._path_map:
                del self._path_map[trigger.path]
            logger.info(f"Deleted webhook trigger {trigger_id}")
            return True
        return False
    
    def regenerate_secret(self, trigger_id: str) -> Optional[str]:
        """Regenerate webhook secret."""
        trigger = self._triggers.get(trigger_id)
        if trigger:
            trigger.secret = uuid4().hex
            return trigger.secret
        return None
    
    def verify_signature(self, trigger_id: str, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""
        trigger = self._triggers.get(trigger_id)
        if not trigger:
            return False
        
        expected = hmac.new(
            trigger.secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        
        # Handle different signature formats
        if signature.startswith("sha256="):
            signature = signature[7:]
        
        return hmac.compare_digest(expected, signature)
    
    async def handle_webhook(self, path: str, payload: Dict, headers: Dict) -> Dict:
        """Handle incoming webhook."""
        trigger = self.get_trigger_by_path(path)
        
        if not trigger:
            logger.warning(f"Webhook trigger not found for path: {path}")
            return {"success": False, "error": "Trigger not found"}
        
        if not trigger.enabled:
            return {"success": False, "error": "Trigger is disabled"}
        
        # Update trigger stats
        trigger.last_triggered_at = datetime.utcnow()
        trigger.trigger_count += 1
        
        # Prepare trigger data
        trigger_data = {
            "trigger_type": "webhook",
            "webhook_id": trigger.id,
            "payload": payload,
            "headers": {k: v for k, v in headers.items() if k.lower() not in ["authorization", "cookie"]},
            "received_at": datetime.utcnow().isoformat(),
        }
        
        # Execute workflow
        from app.workflows.engine import workflow_engine
        from app.services.workflow_service import workflow_service
        
        workflow = workflow_service.get_workflow(trigger.workflow_id)
        if not workflow:
            return {"success": False, "error": "Workflow not found"}
        
        try:
            execution = await workflow_engine.execute(
                workflow,
                input_data=payload,
                trigger_data=trigger_data,
            )
            
            return {
                "success": True,
                "execution_id": execution.id,
                "status": execution.status.value,
            }
            
        except Exception as e:
            logger.error(f"Webhook execution failed: {e}")
            return {"success": False, "error": str(e)}


# Global webhook trigger handler
webhook_trigger_handler = WebhookTriggerHandler()
```

---

## File 5: Trigger Init
**Path:** `backend/app/workflows/triggers_init.py`

```python
"""
Trigger System Initialization
Sets up all trigger handlers and registers them with the engine
"""

from typing import Dict, Any
import logging
import asyncio

from app.workflows.triggers import trigger_registry, EventType
from app.workflows.scheduler import workflow_scheduler
from app.workflows.events import event_emitter
from app.workflows.webhook_trigger import webhook_trigger_handler

logger = logging.getLogger(__name__)


async def initialize_trigger_system():
    """Initialize the complete trigger system."""
    logger.info("Initializing workflow trigger system...")
    
    # Set up scheduler executor
    async def execute_scheduled_workflow(workflow_id: str, trigger_data: Dict):
        from app.workflows.engine import workflow_engine
        from app.services.workflow_service import workflow_service
        
        workflow = workflow_service.get_workflow(workflow_id)
        if workflow:
            await workflow_engine.execute(workflow, trigger_data=trigger_data)
    
    workflow_scheduler.set_executor(execute_scheduled_workflow)
    
    # Start scheduler
    await workflow_scheduler.start()
    
    # Register event handlers
    _register_event_handlers()
    
    logger.info("Workflow trigger system initialized")


def _register_event_handlers():
    """Register default event handlers."""
    
    async def workflow_trigger_handler(event_type: str, payload: Dict, workflow_ids: list):
        """Handler that triggers workflows for events."""
        from app.workflows.engine import workflow_engine
        from app.services.workflow_service import workflow_service
        
        for workflow_id in workflow_ids:
            try:
                workflow = workflow_service.get_workflow(workflow_id)
                if workflow and workflow.status.value == "active":
                    trigger_data = {
                        "trigger_type": "event",
                        "event": event_type,
                        "timestamp": payload.get("timestamp"),
                    }
                    
                    # Merge payload into context
                    input_data = {**payload}
                    
                    asyncio.create_task(
                        workflow_engine.execute(
                            workflow,
                            input_data=input_data,
                            trigger_data=trigger_data,
                        )
                    )
            except Exception as e:
                logger.error(f"Failed to trigger workflow {workflow_id}: {e}")
    
    # Register handler for all event types
    for event_type in EventType:
        trigger_registry.register_event_handler(event_type.value, workflow_trigger_handler)


def register_workflow_triggers(workflow):
    """Register triggers for a workflow."""
    if not workflow.trigger:
        return
    
    trigger = workflow.trigger
    
    if trigger.type.value == "event":
        # Subscribe to event
        if trigger.event:
            trigger_registry.subscribe_workflow(workflow.id, trigger.event)
            logger.info(f"Workflow {workflow.id} subscribed to event: {trigger.event}")
    
    elif trigger.type.value == "schedule":
        # Add to scheduler
        schedule_type = "cron" if trigger.cron else "interval"
        schedule_config = {}
        
        if trigger.cron:
            schedule_config["cron"] = trigger.cron
        elif trigger.interval_seconds:
            schedule_config["interval_seconds"] = trigger.interval_seconds
        
        workflow_scheduler.add_job(workflow.id, schedule_type, schedule_config)
        logger.info(f"Workflow {workflow.id} scheduled: {schedule_type}")
    
    elif trigger.type.value == "webhook":
        # Create webhook trigger
        webhook_trigger_handler.create_trigger(workflow.id, trigger.webhook_path)
        logger.info(f"Workflow {workflow.id} webhook trigger created")


def unregister_workflow_triggers(workflow):
    """Unregister triggers for a workflow."""
    # Unsubscribe from events
    trigger_registry.unsubscribe_workflow(workflow.id)
    
    # Remove from scheduler
    workflow_scheduler.remove_job(workflow.id)
    
    # Remove webhook triggers
    for wh_trigger in webhook_trigger_handler.get_workflow_triggers(workflow.id):
        webhook_trigger_handler.delete_trigger(wh_trigger.id)
    
    logger.info(f"Workflow {workflow.id} triggers unregistered")


async def shutdown_trigger_system():
    """Shutdown the trigger system."""
    logger.info("Shutting down workflow trigger system...")
    await workflow_scheduler.stop()
    logger.info("Workflow trigger system shutdown complete")
```

---

## Summary Part 2

| File | Description | Lines |
|------|-------------|-------|
| `triggers.py` | Trigger definitions & registry | ~280 |
| `scheduler.py` | Cron & interval scheduler | ~320 |
| `events.py` | Event emitter service | ~220 |
| `webhook_trigger.py` | Webhook trigger handler | ~200 |
| `triggers_init.py` | Trigger system initialization | ~150 |
| **Total** | | **~1,170 lines** |
