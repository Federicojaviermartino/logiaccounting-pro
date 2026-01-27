"""
Manual workflow trigger.
Allows users to manually trigger workflows with parameters.
"""
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import logging

from app.workflows.models.workflow import Workflow
from app.workflows.models.execution import ExecutionContext
from app.workflows.models.store import workflow_store
from app.workflows.config import TriggerType, WorkflowStatus

if TYPE_CHECKING:
    from app.workflows.engine.core import WorkflowEngine


logger = logging.getLogger(__name__)


class ManualTrigger:
    """
    Handles manual workflow triggers.
    Validates parameters and permissions before triggering.
    """

    def __init__(self, engine: "WorkflowEngine"):
        self.engine = engine

    async def trigger(
        self,
        workflow_id: str,
        parameters: Dict[str, Any],
        user_id: str,
        user_role: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Manually trigger a workflow.

        Args:
            workflow_id: ID of workflow to trigger
            parameters: Input parameters
            user_id: ID of user triggering
            user_role: Role of user
            tenant_id: Tenant ID

        Returns:
            Execution info
        """
        workflow = workflow_store.get_workflow(workflow_id)

        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        if workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow is not active")

        if workflow.tenant_id != tenant_id:
            raise ValueError(f"Access denied to workflow")

        if workflow.trigger.type != TriggerType.MANUAL:
            raise ValueError(f"Workflow does not support manual trigger")

        allowed_roles = workflow.trigger.allowed_roles
        if allowed_roles and user_role not in allowed_roles:
            raise ValueError(f"User role '{user_role}' not allowed to trigger this workflow")

        self._validate_parameters(workflow, parameters)

        context = ExecutionContext(
            trigger_type=TriggerType.MANUAL.value,
            trigger_data={
                "parameters": parameters,
                "triggered_by": user_id
            },
            user_id=user_id,
            tenant_id=tenant_id
        )

        execution = await self.engine.trigger_workflow(
            workflow_id=workflow_id,
            context=context,
            run_async=True
        )

        logger.info(f"Manual trigger of workflow {workflow_id} by user {user_id}")

        return {
            "execution_id": execution.id,
            "workflow_id": workflow.id,
            "status": execution.status.value
        }

    def _validate_parameters(
        self,
        workflow: Workflow,
        parameters: Dict[str, Any]
    ):
        """Validate input parameters against workflow definition."""
        expected_params = workflow.trigger.parameters

        for param in expected_params:
            param_name = param.get("name")
            required = param.get("required", False)
            param_type = param.get("type", "string")

            if required and param_name not in parameters:
                raise ValueError(f"Missing required parameter: {param_name}")

            if param_name in parameters:
                value = parameters[param_name]

                if param_type == "number" and not isinstance(value, (int, float)):
                    raise ValueError(f"Parameter '{param_name}' must be a number")
                elif param_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"Parameter '{param_name}' must be a boolean")
                elif param_type == "array" and not isinstance(value, list):
                    raise ValueError(f"Parameter '{param_name}' must be an array")
