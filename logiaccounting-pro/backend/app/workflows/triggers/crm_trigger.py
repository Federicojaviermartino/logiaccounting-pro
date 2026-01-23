"""
CRM Event Trigger - Triggers from CRM module events
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime
import asyncio
import logging

from app.workflows.models.workflow import Workflow
from app.workflows.models.execution import ExecutionContext
from app.workflows.models.store import workflow_store
from app.workflows.config import TriggerType, WorkflowStatus

if TYPE_CHECKING:
    from app.workflows.engine.core import WorkflowEngine


logger = logging.getLogger(__name__)


class CRMEventType:
    """CRM Event types"""
    LEAD_CREATED = "lead.created"
    LEAD_CONVERTED = "lead.converted"
    LEAD_ASSIGNED = "lead.assigned"
    DEAL_CREATED = "deal.created"
    DEAL_STAGE_CHANGED = "deal.stage_changed"
    DEAL_WON = "deal.won"
    DEAL_LOST = "deal.lost"
    CONTACT_CREATED = "contact.created"
    COMPANY_HEALTH_CHANGED = "company.health_changed"
    ACTIVITY_LOGGED = "activity.logged"
    QUOTE_CREATED = "quote.created"
    QUOTE_SENT = "quote.sent"
    QUOTE_ACCEPTED = "quote.accepted"


CRM_EVENTS = {
    CRMEventType.LEAD_CREATED: {"label": "Lead Created", "entity": "lead", "fields": ["id", "first_name", "email", "source", "score"]},
    CRMEventType.LEAD_CONVERTED: {"label": "Lead Converted", "entity": "lead", "fields": ["id", "contact_id", "opportunity_id"]},
    CRMEventType.DEAL_CREATED: {"label": "Deal Created", "entity": "opportunity", "fields": ["id", "name", "amount", "stage_id"]},
    CRMEventType.DEAL_STAGE_CHANGED: {"label": "Deal Stage Changed", "entity": "opportunity", "fields": ["id", "previous_stage", "new_stage"]},
    CRMEventType.DEAL_WON: {"label": "Deal Won", "entity": "opportunity", "fields": ["id", "name", "amount"]},
    CRMEventType.DEAL_LOST: {"label": "Deal Lost", "entity": "opportunity", "fields": ["id", "lost_reason"]},
    CRMEventType.QUOTE_SENT: {"label": "Quote Sent", "entity": "quote", "fields": ["id", "quote_number", "total"]},
    CRMEventType.QUOTE_ACCEPTED: {"label": "Quote Accepted", "entity": "quote", "fields": ["id", "total", "opportunity_id"]},
}


class CRMTrigger:
    """Handles CRM event triggers."""

    def __init__(self, engine: "WorkflowEngine"):
        self.engine = engine
        self._subscriptions: Dict[str, List[str]] = {}
        self._running = False

    async def start(self):
        self._running = True
        await self._load_subscriptions()
        logger.info("CRM trigger started")

    async def stop(self):
        self._running = False
        logger.info("CRM trigger stopped")

    async def _load_subscriptions(self):
        self._subscriptions.clear()
        workflows = workflow_store.list_workflows(status=WorkflowStatus.ACTIVE)

        for workflow in workflows:
            if workflow.trigger.type == TriggerType.CRM_EVENT:
                event_type = workflow.trigger.crm_event
                if event_type not in self._subscriptions:
                    self._subscriptions[event_type] = []
                self._subscriptions[event_type].append(workflow.id)

        logger.info(f"Loaded {len(self._subscriptions)} CRM subscriptions")

    async def handle_event(self, event_type: str, entity_data: Dict, tenant_id: str, user_id: str = None, metadata: Dict = None):
        """Handle a CRM event and trigger matching workflows."""
        if not self._running:
            return

        workflow_ids = self._subscriptions.get(event_type, [])

        for workflow_id in workflow_ids:
            workflow = workflow_store.get_workflow(workflow_id)

            if not workflow or workflow.tenant_id != tenant_id or workflow.status != WorkflowStatus.ACTIVE:
                continue

            if not await self._check_conditions(workflow, entity_data):
                continue

            context = ExecutionContext(
                trigger_type=TriggerType.CRM_EVENT.value,
                trigger_data={"event_type": event_type, "entity": entity_data, "metadata": metadata or {}},
                entity_type=CRM_EVENTS.get(event_type, {}).get("entity"),
                entity_id=entity_data.get("id"),
                user_id=user_id,
                tenant_id=tenant_id,
            )

            await self.engine.trigger_workflow(workflow_id=workflow_id, context=context, run_async=True)
            logger.info(f"Triggered workflow {workflow_id} for {event_type}")

    async def _check_conditions(self, workflow: Workflow, entity_data: Dict) -> bool:
        conditions = workflow.trigger.conditions
        if not conditions:
            return True
        from app.workflows.rules.evaluator import evaluate_conditions
        return evaluate_conditions(conditions, {"entity": entity_data})

    @staticmethod
    def get_available_events() -> List[Dict]:
        return [{"type": event_type, **event_info} for event_type, event_info in CRM_EVENTS.items()]


class CRMEventEmitter:
    """Helper to emit CRM events to workflow engine."""
    _trigger: Optional[CRMTrigger] = None

    @classmethod
    def set_trigger(cls, trigger: CRMTrigger):
        cls._trigger = trigger

    @classmethod
    async def emit(cls, event_type: str, entity_data: Dict, tenant_id: str, user_id: str = None, metadata: Dict = None):
        if cls._trigger:
            await cls._trigger.handle_event(event_type, entity_data, tenant_id, user_id, metadata)
