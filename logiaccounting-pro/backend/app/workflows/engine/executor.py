"""
Workflow executor - handles step-by-step execution.
"""
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime, timedelta
import asyncio
import logging

from app.utils.datetime_utils import utc_now

from app.workflows.models.workflow import Workflow, WorkflowNode
from app.workflows.models.execution import (
    WorkflowExecution, ExecutionStep, ExecutionLog
)
from app.workflows.models.store import workflow_store
from app.workflows.config import StepStatus, NodeType, ExecutionStatus

if TYPE_CHECKING:
    from app.workflows.engine.core import WorkflowEngine


logger = logging.getLogger(__name__)


class WaitingException(Exception):
    """Exception raised when execution needs to wait."""
    pass


class WorkflowExecutor:
    """
    Executes a workflow step by step.
    Handles branching, parallel execution, delays, and errors.
    """

    def __init__(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        engine: "WorkflowEngine"
    ):
        self.workflow = workflow
        self.execution = execution
        self.engine = engine
        self.evaluator = None

        self.nodes: Dict[str, WorkflowNode] = {
            node.id: node for node in workflow.nodes
        }

        self.variables: Dict[str, Any] = {
            **execution.context.trigger_data,
            "execution_id": execution.id,
            "workflow_id": workflow.id,
            "tenant_id": workflow.tenant_id
        }

    def _get_evaluator(self):
        """Lazy load evaluator to avoid circular imports."""
        if self.evaluator is None:
            from app.workflows.rules.evaluator import ExpressionEvaluator
            self.evaluator = ExpressionEvaluator()
        return self.evaluator

    async def execute(self) -> Dict[str, Any]:
        """Execute the workflow from start."""
        start_node = self._find_start_node()

        if not start_node:
            raise ValueError("No start node found in workflow")

        result = await self._execute_node(start_node)

        self.execution.variables = self.variables

        return result

    def _find_start_node(self) -> Optional[WorkflowNode]:
        """Find the workflow start node."""
        for node in self.workflow.nodes:
            if node.type == NodeType.TRIGGER:
                return self.nodes.get(node.next)

        for node in self.workflow.nodes:
            if node.type != NodeType.TRIGGER:
                return node

        return None

    async def _execute_node(self, node: WorkflowNode) -> Dict[str, Any]:
        """Execute a single node and continue to next."""
        step = ExecutionStep(
            node_id=node.id,
            node_type=node.type.value,
            node_name=node.name,
            status=StepStatus.RUNNING,
            started_at=utc_now(),
            input_data=self._get_node_inputs(node)
        )

        self.execution.steps.append(step)
        self.execution.current_node_id = node.id
        workflow_store.save_execution(self.execution)

        try:
            handler = self._get_node_handler(node.type)

            result = await handler(node)

            step.status = StepStatus.COMPLETED
            step.completed_at = utc_now()
            step.duration_ms = int(
                (step.completed_at - step.started_at).total_seconds() * 1000
            )
            step.output_data = result

            if "output_variable" in node.config:
                self.variables[node.config["output_variable"]] = result

            self._log("info", f"Node '{node.name}' completed", {
                "node_id": node.id,
                "duration_ms": step.duration_ms
            })

            next_node_id = self._get_next_node_id(node, result)

            if next_node_id:
                next_node = self.nodes.get(next_node_id)
                if next_node:
                    return await self._execute_node(next_node)

            return result

        except WaitingException:
            raise
        except Exception as e:
            step.status = StepStatus.FAILED
            step.completed_at = utc_now()
            step.error = str(e)

            self.execution.error_node_id = node.id

            self._log("error", f"Node '{node.name}' failed: {str(e)}", {
                "node_id": node.id
            })

            raise

    def _get_node_handler(self, node_type: NodeType):
        """Get the appropriate handler for a node type."""
        handlers = {
            NodeType.ACTION: self._handle_action,
            NodeType.CONDITION: self._handle_condition,
            NodeType.PARALLEL: self._handle_parallel,
            NodeType.DELAY: self._handle_delay,
            NodeType.END: self._handle_end,
        }
        return handlers.get(node_type, self._handle_action)

    async def _handle_action(self, node: WorkflowNode) -> Dict[str, Any]:
        """Execute an action node."""
        from app.workflows.actions import ActionExecutorFactory

        action_type = node.config.get("action_type")
        if not action_type:
            raise ValueError(f"Action type not specified in node {node.id}")

        config = self._interpolate(node.config)

        executor = ActionExecutorFactory.get(action_type)

        result = await executor.execute(config, self.variables)

        return result

    async def _handle_condition(self, node: WorkflowNode) -> Dict[str, Any]:
        """Evaluate conditions and determine branch."""
        evaluator = self._get_evaluator()
        conditions = node.config.get("conditions", [])

        for condition in conditions:
            expression = condition.get("expression")

            result = evaluator.evaluate(expression, self.variables)

            if result:
                return {
                    "branch": condition.get("id"),
                    "next": condition.get("next"),
                    "matched": True
                }

        default_next = node.config.get("default")
        if default_next:
            return {
                "branch": "default",
                "next": default_next,
                "matched": True
            }

        raise ValueError(f"No matching condition in node {node.id}")

    async def _handle_parallel(self, node: WorkflowNode) -> Dict[str, Any]:
        """Execute parallel branches."""
        branches = node.config.get("branches", [])
        wait_all = node.config.get("wait_all", True)

        tasks = []
        for branch in branches:
            start_node_id = branch.get("start_node")
            start_node = self.nodes.get(start_node_id)

            if start_node:
                task = asyncio.create_task(self._execute_node(start_node))
                tasks.append((branch.get("id"), task))

        if wait_all:
            results = {}
            for branch_id, task in tasks:
                try:
                    results[branch_id] = await task
                except Exception as e:
                    results[branch_id] = {"error": str(e)}
        else:
            done, pending = await asyncio.wait(
                [t for _, t in tasks],
                return_when=asyncio.FIRST_COMPLETED
            )

            results = {"first_completed": list(done)[0].result()}

            for task in pending:
                task.cancel()

        return {"parallel_results": results}

    async def _handle_delay(self, node: WorkflowNode) -> Dict[str, Any]:
        """Handle delay/wait node."""
        duration = node.config.get("duration", 0)
        unit = node.config.get("unit", "seconds")

        multipliers = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400
        }

        wait_seconds = duration * multipliers.get(unit, 1)

        if wait_seconds > 300:
            resume_at = utc_now() + timedelta(seconds=wait_seconds)

            self.execution.status = ExecutionStatus.WAITING
            self.execution.waiting_for = "delay"
            self.execution.resume_at = resume_at
            workflow_store.save_execution(self.execution)

            self._log("info", f"Execution paused for {duration} {unit}", {
                "resume_at": resume_at.isoformat()
            })

            raise WaitingException("Waiting for delay")

        await asyncio.sleep(wait_seconds)

        return {"delayed": True, "seconds": wait_seconds}

    async def _handle_end(self, node: WorkflowNode) -> Dict[str, Any]:
        """Handle end node."""
        return {"completed": True, "node": node.id}

    def _get_next_node_id(
        self,
        node: WorkflowNode,
        result: Dict[str, Any]
    ) -> Optional[str]:
        """Determine the next node ID based on result."""
        if node.type == NodeType.CONDITION:
            return result.get("next")

        return node.next

    def _get_node_inputs(self, node: WorkflowNode) -> Dict[str, Any]:
        """Get inputs for a node."""
        inputs = {}

        for key in node.config.get("input_fields", []):
            if key in self.variables:
                inputs[key] = self.variables[key]

        return inputs

    def _interpolate(self, obj: Any) -> Any:
        """Interpolate variables in object."""
        evaluator = self._get_evaluator()
        if isinstance(obj, str):
            return evaluator.interpolate(obj, self.variables)
        elif isinstance(obj, dict):
            return {k: self._interpolate(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._interpolate(item) for item in obj]
        return obj

    def _log(self, level: str, message: str, data: Dict[str, Any] = None):
        """Add log entry."""
        log = ExecutionLog(
            execution_id=self.execution.id,
            step_id=self.execution.steps[-1].id if self.execution.steps else None,
            level=level,
            message=message,
            data=data or {}
        )
        workflow_store.add_log(log)
