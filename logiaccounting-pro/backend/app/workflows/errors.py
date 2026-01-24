"""
Workflow Error Handling
Error types, retry logic, and recovery
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class WorkflowErrorType(str, Enum):
    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"
    ACTION_ERROR = "action_error"
    CONDITION_ERROR = "condition_error"
    TIMEOUT_ERROR = "timeout_error"
    RETRY_EXHAUSTED = "retry_exhausted"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class WorkflowError(Exception):
    """Base workflow exception."""

    def __init__(self, message: str, error_type: WorkflowErrorType = WorkflowErrorType.UNKNOWN, details: Dict = None, node_id: str = None, recoverable: bool = True):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.node_id = node_id
        self.recoverable = recoverable
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

    def to_dict(self) -> Dict:
        return {
            "message": self.message,
            "error_type": self.error_type.value,
            "details": self.details,
            "node_id": self.node_id,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat(),
        }


class ValidationError(WorkflowError):
    """Workflow validation error."""

    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(
            message=message,
            error_type=WorkflowErrorType.VALIDATION_ERROR,
            details={"errors": errors or []},
            recoverable=False,
        )


class ActionError(WorkflowError):
    """Action execution error."""

    def __init__(self, message: str, action: str, node_id: str = None, original_error: Exception = None):
        super().__init__(
            message=message,
            error_type=WorkflowErrorType.ACTION_ERROR,
            details={
                "action": action,
                "original_error": str(original_error) if original_error else None,
            },
            node_id=node_id,
            recoverable=True,
        )


class TimeoutError(WorkflowError):
    """Workflow or action timeout."""

    def __init__(self, message: str, timeout_seconds: int, node_id: str = None):
        super().__init__(
            message=message,
            error_type=WorkflowErrorType.TIMEOUT_ERROR,
            details={"timeout_seconds": timeout_seconds},
            node_id=node_id,
            recoverable=True,
        )


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0, max_delay: float = 60.0, exponential_base: float = 2.0, retry_on: List[WorkflowErrorType] = None):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on = retry_on or [
            WorkflowErrorType.EXECUTION_ERROR,
            WorkflowErrorType.ACTION_ERROR,
            WorkflowErrorType.TIMEOUT_ERROR,
        ]

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)

    def should_retry(self, error: WorkflowError, attempt: int) -> bool:
        """Check if should retry based on error and attempt count."""
        if attempt >= self.max_retries:
            return False
        if not error.recoverable:
            return False
        if error.error_type not in self.retry_on:
            return False
        return True


class RetryHandler:
    """Handles retry logic for workflow actions."""

    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self._retry_counts: Dict[str, int] = {}

    async def execute_with_retry(self, func: Callable, node_id: str, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        attempt = 0
        last_error = None

        while True:
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success - reset retry count
                self._retry_counts[node_id] = 0
                return result

            except WorkflowError as e:
                last_error = e
                attempt += 1

                if self.config.should_retry(e, attempt):
                    delay = self.config.get_delay(attempt)
                    logger.warning(f"Retrying node {node_id} in {delay}s (attempt {attempt}/{self.config.max_retries})")
                    await asyncio.sleep(delay)
                else:
                    break

            except Exception as e:
                # Wrap unknown exceptions
                last_error = WorkflowError(
                    message=str(e),
                    error_type=WorkflowErrorType.UNKNOWN,
                    node_id=node_id,
                )
                attempt += 1

                if attempt < self.config.max_retries:
                    delay = self.config.get_delay(attempt)
                    logger.warning(f"Retrying node {node_id} in {delay}s (attempt {attempt}/{self.config.max_retries})")
                    await asyncio.sleep(delay)
                else:
                    break

        # All retries exhausted
        self._retry_counts[node_id] = attempt
        raise WorkflowError(
            message=f"Retry exhausted after {attempt} attempts: {last_error.message}",
            error_type=WorkflowErrorType.RETRY_EXHAUSTED,
            details={"attempts": attempt, "last_error": last_error.to_dict()},
            node_id=node_id,
            recoverable=False,
        )

    def get_retry_count(self, node_id: str) -> int:
        """Get current retry count for a node."""
        return self._retry_counts.get(node_id, 0)


class ErrorRecovery:
    """Strategies for recovering from workflow errors."""

    @staticmethod
    async def skip_node(workflow, execution, node_id: str):
        """Skip the failed node and continue."""
        logger.info(f"Skipping failed node: {node_id}")
        step = execution.get_step(node_id)
        if step:
            step.output_data["skipped"] = True
        # Continue to next nodes

    @staticmethod
    async def use_fallback(workflow, execution, node_id: str, fallback_value: Any):
        """Use a fallback value for failed node."""
        logger.info(f"Using fallback for node: {node_id}")
        step = execution.get_step(node_id)
        if step:
            step.output_data = {"fallback": True, "value": fallback_value}

    @staticmethod
    async def retry_from_checkpoint(workflow, execution, checkpoint_node_id: str):
        """Retry workflow from a checkpoint node."""
        logger.info(f"Retrying from checkpoint: {checkpoint_node_id}")
        # Clear steps after checkpoint
        checkpoint_found = False
        steps_to_keep = []
        for step in execution.steps:
            if step.node_id == checkpoint_node_id:
                checkpoint_found = True
            if not checkpoint_found:
                steps_to_keep.append(step)
        execution.steps = steps_to_keep

    @staticmethod
    async def notify_and_pause(workflow, execution, error: WorkflowError):
        """Notify admin and pause workflow."""
        logger.warning(f"Pausing workflow due to error: {error.message}")
        execution.status = "waiting"
        # In production: send notification to admin


class WorkflowValidator:
    """Validates workflow definitions."""

    @staticmethod
    def validate(workflow: Dict) -> List[str]:
        """Validate a workflow definition."""
        errors = []

        # Check required fields
        if not workflow.get("name"):
            errors.append("Workflow name is required")

        if not workflow.get("trigger"):
            errors.append("Workflow trigger is required")

        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        if not nodes:
            errors.append("Workflow must have at least one node")

        # Validate nodes
        node_ids = set()
        for node in nodes:
            if not node.get("id"):
                errors.append("All nodes must have an ID")
                continue

            if node["id"] in node_ids:
                errors.append(f"Duplicate node ID: {node['id']}")
            node_ids.add(node["id"])

            node_type = node.get("type")
            if not node_type:
                errors.append(f"Node {node['id']} must have a type")

            # Validate action nodes
            if node_type == "action" and not node.get("action"):
                errors.append(f"Action node {node['id']} must specify an action")

            # Validate condition nodes
            if node_type == "condition" and not node.get("condition"):
                errors.append(f"Condition node {node['id']} must have a condition")

        # Validate edges
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")

            if source != "trigger" and source not in node_ids:
                errors.append(f"Edge source not found: {source}")

            if target not in node_ids:
                errors.append(f"Edge target not found: {target}")

        # Check for orphan nodes
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.get("target"))

        for node_id in node_ids:
            if node_id not in connected_nodes:
                # Check if it's connected as source
                is_source = any(e.get("source") == node_id for e in edges)
                if not is_source:
                    errors.append(f"Orphan node detected: {node_id}")

        # Check trigger configuration
        trigger = workflow.get("trigger", {})
        trigger_type = trigger.get("type")

        if trigger_type == "event" and not trigger.get("event"):
            errors.append("Event trigger must specify an event")

        if trigger_type == "schedule" and not trigger.get("cron") and not trigger.get("interval_seconds"):
            errors.append("Schedule trigger must have cron or interval")

        return errors
