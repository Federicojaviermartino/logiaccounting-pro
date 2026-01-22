"""
Entity event trigger handler.
Triggers workflows when entity events occur.
"""
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import asyncio
import logging

from app.workflows.models.workflow import Workflow, TriggerCondition
from app.workflows.models.execution import ExecutionContext
from app.workflows.models.store import workflow_store
from app.workflows.config import TriggerType

if TYPE_CHECKING:
    from app.workflows.engine.core import WorkflowEngine


logger = logging.getLogger(__name__)


class EventTrigger:
    """
    Handles entity event triggers.
    Listens for entity events and triggers matching workflows.
    """

    def __init__(self, engine: "WorkflowEngine"):
        self.engine = engine
        self._running = False

    async def start(self):
        """Start the event trigger."""
        self._running = True
        logger.info("Event trigger started")

    async def stop(self):
        """Stop the event trigger."""
        self._running = False
        logger.info("Event trigger stopped")

    async def handle_event(
        self,
        entity: str,
        event: str,
        data: Dict[str, Any],
        tenant_id: str,
        user_id: Optional[str] = None
    ):
        """
        Handle an entity event.

        Args:
            entity: Entity type (invoice, payment, project, etc.)
            event: Event type (created, updated, deleted, etc.)
            data: Entity data
            tenant_id: Tenant ID
            user_id: User who triggered the event
        """
        if not self._running:
            return

        logger.debug(f"Handling event: {entity}.{event}")

        workflows = workflow_store.get_active_workflows_by_trigger(
            trigger_type=TriggerType.ENTITY_EVENT.value,
            entity=entity,
            event=event
        )

        workflows = [w for w in workflows if w.tenant_id == tenant_id]

        if not workflows:
            return

        logger.info(f"Found {len(workflows)} workflows for {entity}.{event}")

        for workflow in workflows:
            try:
                if not self._check_conditions(workflow.trigger.conditions, data):
                    logger.debug(f"Workflow {workflow.id} conditions not met")
                    continue

                context = ExecutionContext(
                    trigger_type=TriggerType.ENTITY_EVENT.value,
                    trigger_data={
                        entity: data,
                        "event": event
                    },
                    entity=entity,
                    entity_id=data.get("id"),
                    user_id=user_id,
                    tenant_id=tenant_id
                )

                await self.engine.trigger_workflow(
                    workflow_id=workflow.id,
                    context=context,
                    run_async=True
                )

                logger.info(f"Triggered workflow {workflow.id} for {entity}.{event}")

            except Exception as e:
                logger.error(f"Error triggering workflow {workflow.id}: {e}")

    def _check_conditions(
        self,
        conditions: List[TriggerCondition],
        data: Dict[str, Any]
    ) -> bool:
        """Check if all trigger conditions are met."""
        if not conditions:
            return True

        for condition in conditions:
            field_value = self._get_field_value(data, condition.field)

            if not self._evaluate_condition(
                field_value,
                condition.operator,
                condition.value
            ):
                return False

        return True

    def _get_field_value(self, data: Dict[str, Any], field: str) -> Any:
        """Get a field value from nested data."""
        parts = field.split(".")
        value = data

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def _evaluate_condition(
        self,
        actual: Any,
        operator: str,
        expected: Any
    ) -> bool:
        """Evaluate a single condition."""
        operators = {
            "equals": lambda a, e: a == e,
            "not_equals": lambda a, e: a != e,
            "greater_than": lambda a, e: float(a) > float(e) if a is not None else False,
            "less_than": lambda a, e: float(a) < float(e) if a is not None else False,
            "contains": lambda a, e: e in a if a else False,
            "in": lambda a, e: a in e if e else False,
            "is_empty": lambda a, _: not a,
            "is_not_empty": lambda a, _: bool(a),
        }

        op_func = operators.get(operator)
        if not op_func:
            logger.warning(f"Unknown operator: {operator}")
            return False

        try:
            return op_func(actual, expected)
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
