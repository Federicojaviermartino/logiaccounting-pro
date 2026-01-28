"""
Sub-Workflow Action Executor
Allows workflows to call other workflows as reusable components
"""

from typing import Dict, Any, Optional, Set
import asyncio
import logging

from app.utils.datetime_utils import utc_now
from app.workflows.actions.base import ActionExecutor, ActionResult
from app.workflows.models.store import workflow_store
from app.workflows.config import WorkflowStatus, ExecutionStatus


logger = logging.getLogger(__name__)

_active_call_stacks: Dict[str, Set[str]] = {}


class SubWorkflowAction(ActionExecutor):
    """Execute another workflow as a sub-workflow."""

    action_type = "subworkflow"
    MAX_DEPTH = 10

    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            workflow_id = config.get("workflow_id")
            parameters = config.get("parameters", {})
            wait_for_completion = config.get("wait_for_completion", True)
            timeout_seconds = config.get("timeout_seconds", 300)

            if not workflow_id:
                return ActionResult(success=False, error="workflow_id is required")

            parent_execution_id = context.get("execution_id")
            current_depth = context.get("subworkflow_depth", 0)

            if current_depth >= self.MAX_DEPTH:
                return ActionResult(success=False, error=f"Max depth ({self.MAX_DEPTH}) exceeded")

            if self._detect_circular(parent_execution_id, workflow_id):
                return ActionResult(success=False, error="Circular reference detected")

            sub_workflow = workflow_store.get_workflow(workflow_id)
            if not sub_workflow or sub_workflow.status != WorkflowStatus.ACTIVE:
                return ActionResult(success=False, error=f"Workflow not found or inactive")

            interpolated_params = {
                k: self.interpolate(v, context) if isinstance(v, str) else v
                for k, v in parameters.items()
            }

            from app.workflows.models.execution import ExecutionContext
            sub_context = ExecutionContext(
                trigger_type="subworkflow",
                trigger_data={"parent_execution_id": parent_execution_id, "parameters": interpolated_params},
                user_id=context.get("user_id"),
                tenant_id=context.get("tenant_id"),
                variables={**context.get("variables", {}), **interpolated_params},
            )

            self._add_to_stack(parent_execution_id, workflow_id)

            try:
                from app.workflows.engine.core import workflow_engine
                execution = await workflow_engine.trigger_workflow(
                    workflow_id=workflow_id,
                    context=sub_context,
                    run_async=not wait_for_completion,
                    subworkflow_depth=current_depth + 1,
                )

                if wait_for_completion:
                    result = await self._wait_completion(execution.id, timeout_seconds)
                    success = result["status"] == ExecutionStatus.COMPLETED
                    return ActionResult(
                        success=success,
                        data={"execution_id": execution.id, "output": result.get("output", {})},
                        error=result.get("error") if not success else None,
                    )
                return ActionResult(success=True, data={"execution_id": execution.id, "status": "started"})
            finally:
                self._remove_from_stack(parent_execution_id, workflow_id)

        except asyncio.TimeoutError:
            return ActionResult(success=False, error="Sub-workflow timed out")
        except Exception as e:
            logger.error(f"Sub-workflow failed: {e}")
            return ActionResult(success=False, error=str(e))

    def _detect_circular(self, exec_id: str, wf_id: str) -> bool:
        return exec_id and wf_id in _active_call_stacks.get(exec_id, set())

    def _add_to_stack(self, exec_id: str, wf_id: str):
        if exec_id:
            _active_call_stacks.setdefault(exec_id, set()).add(wf_id)

    def _remove_from_stack(self, exec_id: str, wf_id: str):
        if exec_id and exec_id in _active_call_stacks:
            _active_call_stacks[exec_id].discard(wf_id)

    async def _wait_completion(self, exec_id: str, timeout: int) -> Dict:
        start = utc_now()
        while True:
            execution = workflow_store.get_execution(exec_id)
            if not execution:
                return {"status": ExecutionStatus.FAILED, "error": "Not found"}
            if execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                return {"status": execution.status, "output": execution.output, "error": execution.error}
            if (utc_now() - start).total_seconds() >= timeout:
                raise asyncio.TimeoutError()
            await asyncio.sleep(0.5)
