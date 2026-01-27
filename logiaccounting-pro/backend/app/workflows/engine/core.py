"""
Main workflow engine.
Coordinates workflow execution, triggers, and actions.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging

from app.workflows.models.workflow import Workflow, WorkflowNode
from app.workflows.models.execution import (
    WorkflowExecution, ExecutionStep, ExecutionContext, ExecutionLog
)
from app.workflows.models.store import workflow_store
from app.workflows.config import (
    WorkflowStatus, ExecutionStatus, StepStatus, NodeType, workflow_settings
)
from app.workflows.engine.executor import WorkflowExecutor


logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Main workflow engine.
    Handles workflow registration, triggering, and execution coordination.
    """

    def __init__(self):
        self.event_trigger = None
        self._active_executions: Dict[str, asyncio.Task] = {}

    async def start(self):
        """Start the workflow engine."""
        logger.info("Starting workflow engine")
        from app.workflows.triggers.event_trigger import EventTrigger
        self.event_trigger = EventTrigger(self)
        await self.event_trigger.start()

    async def stop(self):
        """Stop the workflow engine."""
        logger.info("Stopping workflow engine")

        for task in self._active_executions.values():
            task.cancel()

        if self.event_trigger:
            await self.event_trigger.stop()

    async def trigger_workflow(
        self,
        workflow_id: str,
        context: ExecutionContext,
        run_async: bool = True
    ) -> WorkflowExecution:
        """
        Trigger a workflow execution.

        Args:
            workflow_id: ID of the workflow to execute
            context: Execution context with trigger data
            run_async: Whether to run asynchronously

        Returns:
            WorkflowExecution record
        """
        workflow = workflow_store.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        if workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow is not active: {workflow.status}")

        active_count = len([
            e for e in workflow_store.get_executions_by_workflow(
                workflow_id, status=ExecutionStatus.RUNNING
            )
        ])

        if active_count >= workflow_settings.max_concurrent_executions:
            raise ValueError("Maximum concurrent executions reached")

        execution = WorkflowExecution(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            workflow_version=workflow.version,
            tenant_id=workflow.tenant_id,
            context=context,
            status=ExecutionStatus.PENDING
        )

        workflow_store.save_execution(execution)

        self._log(execution.id, "info", f"Workflow execution created", {
            "workflow_id": workflow.id,
            "trigger_type": context.trigger_type
        })

        if run_async:
            task = asyncio.create_task(
                self._execute_workflow(workflow, execution)
            )
            self._active_executions[execution.id] = task
        else:
            await self._execute_workflow(workflow, execution)

        return execution

    async def _execute_workflow(
        self,
        workflow: Workflow,
        execution: WorkflowExecution
    ):
        """Execute a workflow."""
        try:
            execution.status = ExecutionStatus.RUNNING
            workflow_store.save_execution(execution)

            executor = WorkflowExecutor(
                workflow=workflow,
                execution=execution,
                engine=self
            )

            result = await executor.execute()

            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.duration_ms = int(
                (execution.completed_at - execution.started_at).total_seconds() * 1000
            )

            workflow.execution_count += 1
            workflow.last_executed = datetime.utcnow()
            workflow_store.save_workflow(workflow)

            self._log(execution.id, "info", "Workflow completed successfully", {
                "duration_ms": execution.duration_ms
            })

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.completed_at = datetime.utcnow()
            execution.error = str(e)

            logger.error(f"Workflow execution failed: {e}")
            self._log(execution.id, "error", f"Workflow failed: {str(e)}")

            await self._handle_execution_error(workflow, execution, e)

        finally:
            workflow_store.save_execution(execution)

            if execution.id in self._active_executions:
                del self._active_executions[execution.id]

    async def _handle_execution_error(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        error: Exception
    ):
        """Handle workflow execution error."""
        error_handler = workflow.error_handler

        if execution.retry_count < error_handler.retry_count:
            execution.retry_count += 1

            self._log(
                execution.id, "warning",
                f"Scheduling retry {execution.retry_count}/{error_handler.retry_count}",
                {"delay_seconds": error_handler.retry_delay_seconds}
            )

            await asyncio.sleep(error_handler.retry_delay_seconds)

            execution.status = ExecutionStatus.PENDING
            execution.error = None
            await self._execute_workflow(workflow, execution)

        else:
            if error_handler.on_failure:
                await self._execute_failure_handler(
                    workflow, execution, error_handler.on_failure
                )

    async def _execute_failure_handler(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        handler_config: Dict[str, Any]
    ):
        """Execute failure handler actions."""
        from app.workflows.actions import ActionExecutorFactory

        action_type = handler_config.get("action", "notify")

        if action_type == "notify":
            executor = ActionExecutorFactory.get("notification")
            await executor.execute({
                "recipients": handler_config.get("recipients", []),
                "template": handler_config.get("template", "workflow_failure"),
                "variables": {
                    "workflow_name": workflow.name,
                    "execution_id": execution.id,
                    "error": execution.error
                }
            }, {})

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        execution = workflow_store.get_execution(execution_id)
        if not execution:
            return False

        if execution.status not in [ExecutionStatus.RUNNING, ExecutionStatus.WAITING]:
            return False

        if execution_id in self._active_executions:
            self._active_executions[execution_id].cancel()
            del self._active_executions[execution_id]

        execution.status = ExecutionStatus.CANCELLED
        execution.completed_at = datetime.utcnow()
        workflow_store.save_execution(execution)

        self._log(execution_id, "info", "Execution cancelled")
        return True

    async def resume_execution(self, execution_id: str, data: Dict[str, Any] = None):
        """Resume a waiting execution."""
        execution = workflow_store.get_execution(execution_id)
        if not execution or execution.status != ExecutionStatus.WAITING:
            raise ValueError(f"Execution not in waiting state: {execution_id}")

        workflow = workflow_store.get_workflow(execution.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {execution.workflow_id}")

        if data:
            execution.variables.update(data)

        execution.waiting_for = None
        execution.resume_at = None
        execution.status = ExecutionStatus.RUNNING
        workflow_store.save_execution(execution)

        await self._execute_workflow(workflow, execution)

    def on_entity_event(
        self,
        entity: str,
        event: str,
        data: Dict[str, Any],
        tenant_id: str,
        user_id: Optional[str] = None
    ):
        """
        Handle an entity event and trigger matching workflows.
        Called by application event handlers.
        """
        if self.event_trigger:
            asyncio.create_task(
                self.event_trigger.handle_event(
                    entity=entity,
                    event=event,
                    data=data,
                    tenant_id=tenant_id,
                    user_id=user_id
                )
            )

    def _log(
        self,
        execution_id: str,
        level: str,
        message: str,
        data: Dict[str, Any] = None
    ):
        """Add an execution log entry."""
        log = ExecutionLog(
            execution_id=execution_id,
            level=level,
            message=message,
            data=data or {}
        )
        workflow_store.add_log(log)


workflow_engine = WorkflowEngine()
