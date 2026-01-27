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
