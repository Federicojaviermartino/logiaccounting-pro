"""
Schedule-based workflow trigger.
Uses cron expressions to trigger workflows at specific times.
"""
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
import asyncio
import logging

from app.utils.datetime_utils import utc_now
from app.workflows.models.workflow import Workflow
from app.workflows.models.execution import ExecutionContext
from app.workflows.models.store import workflow_store
from app.workflows.config import TriggerType, workflow_settings

if TYPE_CHECKING:
    from app.workflows.engine.core import WorkflowEngine


logger = logging.getLogger(__name__)


class ScheduleTrigger:
    """
    Handles scheduled workflow triggers.
    Runs workflows based on cron expressions.
    """

    def __init__(self, engine: "WorkflowEngine"):
        self.engine = engine
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._next_runs: Dict[str, datetime] = {}

    async def start(self):
        """Start the schedule trigger."""
        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        logger.info("Schedule trigger started")

    async def stop(self):
        """Stop the schedule trigger."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Schedule trigger stopped")

    async def _run_scheduler(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_schedules()
                await asyncio.sleep(workflow_settings.scheduler_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    async def _check_schedules(self):
        """Check and trigger scheduled workflows."""
        now = utc_now()

        workflows = workflow_store.get_active_workflows_by_trigger(
            trigger_type=TriggerType.SCHEDULE.value
        )

        for workflow in workflows:
            try:
                if self._should_run(workflow, now):
                    await self._trigger_workflow(workflow)
            except Exception as e:
                logger.error(f"Error checking workflow {workflow.id}: {e}")

    def _should_run(self, workflow: Workflow, now: datetime) -> bool:
        """Check if workflow should run now."""
        cron_expr = workflow.trigger.cron
        if not cron_expr:
            return False

        try:
            from croniter import croniter
            cron = croniter(cron_expr, workflow.last_executed or now)
            next_run = cron.get_next(datetime)

            self._next_runs[workflow.id] = next_run

            return next_run <= now

        except ImportError:
            logger.warning("croniter not installed, scheduled workflows disabled")
            return False
        except Exception as e:
            logger.error(f"Invalid cron expression {cron_expr}: {e}")
            return False

    async def _trigger_workflow(self, workflow: Workflow):
        """Trigger a scheduled workflow."""
        context = ExecutionContext(
            trigger_type=TriggerType.SCHEDULE.value,
            trigger_data={
                "scheduled_time": utc_now().isoformat(),
                "cron": workflow.trigger.cron
            },
            tenant_id=workflow.tenant_id
        )

        await self.engine.trigger_workflow(
            workflow_id=workflow.id,
            context=context,
            run_async=True
        )

        logger.info(f"Triggered scheduled workflow {workflow.id}")

    def get_next_run(self, workflow_id: str) -> Optional[datetime]:
        """Get the next scheduled run time for a workflow."""
        return self._next_runs.get(workflow_id)
