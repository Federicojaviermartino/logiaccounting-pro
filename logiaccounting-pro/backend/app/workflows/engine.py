"""
Workflow Execution Engine
Core engine for running workflows
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from uuid import uuid4
import asyncio
import logging

from app.workflows.models import (
    Workflow, WorkflowNode, WorkflowExecution, StepExecution,
    ExecutionStatus, NodeType
)
from app.workflows.variables import VariableResolver, ExpressionEvaluator

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Executes workflows."""

    def __init__(self):
        self._action_handlers: Dict[str, Callable] = {}
        self._running_executions: Dict[str, WorkflowExecution] = {}
        self._execution_history: Dict[str, List[WorkflowExecution]] = {}

    def register_action(self, action_name: str, handler: Callable):
        """Register an action handler."""
        self._action_handlers[action_name] = handler
        logger.info(f"Registered action: {action_name}")

    async def execute(self, workflow: Workflow, input_data: Dict = None, trigger_data: Dict = None) -> WorkflowExecution:
        """Execute a workflow."""
        # Create execution instance
        execution = WorkflowExecution(
            id=f"exec_{uuid4().hex[:12]}",
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            trigger_data=trigger_data or {},
            input_data=input_data or {},
            context={
                "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                },
                "trigger": trigger_data or {},
                "input": input_data or {},
            },
        )

        # Track execution
        self._running_executions[execution.id] = execution
        if workflow.id not in self._execution_history:
            self._execution_history[workflow.id] = []
        self._execution_history[workflow.id].append(execution)

        # Initialize resolver
        resolver = VariableResolver(execution.context)
        evaluator = ExpressionEvaluator(resolver)

        try:
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.utcnow()

            # Get starting nodes
            start_nodes = workflow.get_start_nodes()
            if not start_nodes:
                raise ValueError("No start nodes found in workflow")

            # Execute from start nodes
            for node_id in start_nodes:
                await self._execute_node(workflow, execution, node_id, resolver, evaluator)

            # Mark as completed
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()

            # Update workflow stats
            workflow.run_count += 1
            workflow.success_count += 1
            workflow.last_run_at = datetime.utcnow()

            logger.info(f"Workflow {workflow.id} completed successfully")

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()

            workflow.run_count += 1
            workflow.failure_count += 1
            workflow.last_run_at = datetime.utcnow()

            logger.error(f"Workflow {workflow.id} failed: {e}")

        finally:
            del self._running_executions[execution.id]

        return execution

    async def _execute_node(self, workflow: Workflow, execution: WorkflowExecution, node_id: str, resolver: VariableResolver, evaluator: ExpressionEvaluator):
        """Execute a single node."""
        node = workflow.get_node(node_id)
        if not node:
            logger.warning(f"Node not found: {node_id}")
            return

        # Create step execution
        step = execution.add_step(node_id)
        step.status = ExecutionStatus.RUNNING
        step.started_at = datetime.utcnow()
        execution.current_node_id = node_id

        try:
            logger.info(f"Executing node: {node_id} ({node.type})")

            if node.type == NodeType.ACTION:
                await self._execute_action(node, step, resolver)

            elif node.type == NodeType.CONDITION:
                branch = await self._execute_condition(node, evaluator)
                step.output_data["branch"] = branch

                # Execute appropriate branch
                next_nodes = node.true_branch if branch else node.false_branch
                for next_id in next_nodes:
                    await self._execute_node(workflow, execution, next_id, resolver, evaluator)

                step.status = ExecutionStatus.COMPLETED
                step.completed_at = datetime.utcnow()
                return  # Don't continue to normal next nodes

            elif node.type == NodeType.LOOP:
                await self._execute_loop(workflow, execution, node, resolver, evaluator)

            elif node.type == NodeType.PARALLEL:
                await self._execute_parallel(workflow, execution, node, resolver, evaluator)

            elif node.type == NodeType.DELAY:
                await self._execute_delay(node, step, resolver)

            elif node.type == NodeType.END:
                pass  # End node, nothing to do

            step.status = ExecutionStatus.COMPLETED
            step.completed_at = datetime.utcnow()

            # Store outputs in context
            for output_name in node.outputs:
                if output_name in step.output_data:
                    resolver.update_context(output_name, step.output_data[output_name])

            # Continue to next nodes
            next_nodes = workflow.get_next_nodes(node_id)
            for next_id in next_nodes:
                await self._execute_node(workflow, execution, next_id, resolver, evaluator)

        except Exception as e:
            step.status = ExecutionStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.utcnow()
            raise

    async def _execute_action(self, node: WorkflowNode, step: StepExecution, resolver: VariableResolver):
        """Execute an action node."""
        action_name = node.action
        if not action_name:
            raise ValueError(f"No action specified for node {node.id}")

        handler = self._action_handlers.get(action_name)
        if not handler:
            raise ValueError(f"Unknown action: {action_name}")

        # Resolve config variables
        config = resolver.resolve(node.config)
        step.input_data = config

        # Execute action
        if asyncio.iscoroutinefunction(handler):
            result = await handler(config, resolver.context)
        else:
            result = handler(config, resolver.context)

        step.output_data = result if isinstance(result, dict) else {"result": result}

    async def _execute_condition(self, node: WorkflowNode, evaluator: ExpressionEvaluator) -> bool:
        """Execute a condition node and return branch result."""
        if not node.condition:
            return True

        return evaluator.evaluate(node.condition)

    async def _execute_loop(self, workflow: Workflow, execution: WorkflowExecution, node: WorkflowNode, resolver: VariableResolver, evaluator: ExpressionEvaluator):
        """Execute a loop node."""
        collection = resolver.resolve(node.collection)

        if not isinstance(collection, list):
            logger.warning(f"Loop collection is not a list: {type(collection)}")
            return

        item_var = node.item_variable or "item"
        index_var = f"{item_var}_index"

        for index, item in enumerate(collection):
            # Set loop variables
            resolver.update_context(item_var, item)
            resolver.update_context(index_var, index)

            # Execute body nodes
            for body_node_id in node.body:
                await self._execute_node(workflow, execution, body_node_id, resolver, evaluator)

    async def _execute_parallel(self, workflow: Workflow, execution: WorkflowExecution, node: WorkflowNode, resolver: VariableResolver, evaluator: ExpressionEvaluator):
        """Execute parallel branches."""
        tasks = []

        for branch in node.branches:
            for branch_node_id in branch:
                # Create a copy of resolver for each branch
                branch_resolver = VariableResolver(dict(resolver.context))
                branch_evaluator = ExpressionEvaluator(branch_resolver)

                task = self._execute_node(workflow, execution, branch_node_id, branch_resolver, branch_evaluator)
                tasks.append(task)

        # Wait for all branches
        await asyncio.gather(*tasks)

    async def _execute_delay(self, node: WorkflowNode, step: StepExecution, resolver: VariableResolver):
        """Execute a delay node."""
        if node.delay_seconds > 0:
            step.output_data["delay_seconds"] = node.delay_seconds
            await asyncio.sleep(node.delay_seconds)
        elif node.delay_until:
            target_time = resolver.resolve(node.delay_until)
            if isinstance(target_time, str):
                target_time = datetime.fromisoformat(target_time)

            now = datetime.utcnow()
            if target_time > now:
                delay = (target_time - now).total_seconds()
                step.output_data["delay_until"] = target_time.isoformat()
                await asyncio.sleep(delay)

    # ==================== Management ====================

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID."""
        # Check running first
        if execution_id in self._running_executions:
            return self._running_executions[execution_id]

        # Check history
        for executions in self._execution_history.values():
            for execution in executions:
                if execution.id == execution_id:
                    return execution

        return None

    def get_workflow_executions(self, workflow_id: str, limit: int = 20) -> List[WorkflowExecution]:
        """Get executions for a workflow."""
        executions = self._execution_history.get(workflow_id, [])
        return sorted(executions, key=lambda e: e.started_at or datetime.min, reverse=True)[:limit]

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        execution = self._running_executions.get(execution_id)
        if execution:
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = datetime.utcnow()
            return True
        return False

    def get_running_executions(self) -> List[WorkflowExecution]:
        """Get all running executions."""
        return list(self._running_executions.values())


# Global engine instance
workflow_engine = WorkflowEngine()
