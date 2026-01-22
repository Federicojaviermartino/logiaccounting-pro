"""
Action executor factory and base class.
"""
from typing import Dict, Any, Optional, Type
from abc import ABC, abstractmethod
import logging


logger = logging.getLogger(__name__)


class ActionExecutor(ABC):
    """Base class for action executors."""

    @abstractmethod
    async def execute(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the action.

        Args:
            config: Action configuration
            variables: Current workflow variables

        Returns:
            Action result
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate action configuration."""
        return True


class ActionExecutorFactory:
    """Factory for creating action executors."""

    _executors: Dict[str, Type[ActionExecutor]] = {}

    @classmethod
    def register(cls, action_type: str, executor_class: Type[ActionExecutor]):
        """Register an action executor."""
        cls._executors[action_type] = executor_class

    @classmethod
    def get(cls, action_type: str) -> ActionExecutor:
        """Get an action executor instance."""
        executor_class = cls._executors.get(action_type)
        if not executor_class:
            raise ValueError(f"Unknown action type: {action_type}")
        return executor_class()

    @classmethod
    def list_actions(cls) -> list:
        """List all registered action types."""
        return list(cls._executors.keys())


from app.workflows.actions.email_action import EmailActionExecutor
from app.workflows.actions.notification_action import NotificationActionExecutor
from app.workflows.actions.webhook_action import WebhookActionExecutor
from app.workflows.actions.entity_actions import (
    UpdateEntityExecutor,
    CreateEntityExecutor,
    DeleteEntityExecutor
)
from app.workflows.actions.approval_action import ApprovalActionExecutor
from app.workflows.actions.delay_action import DelayActionExecutor
from app.workflows.actions.script_action import ScriptActionExecutor

ActionExecutorFactory.register("send_email", EmailActionExecutor)
ActionExecutorFactory.register("notification", NotificationActionExecutor)
ActionExecutorFactory.register("webhook", WebhookActionExecutor)
ActionExecutorFactory.register("update_entity", UpdateEntityExecutor)
ActionExecutorFactory.register("create_entity", CreateEntityExecutor)
ActionExecutorFactory.register("delete_entity", DeleteEntityExecutor)
ActionExecutorFactory.register("approval", ApprovalActionExecutor)
ActionExecutorFactory.register("delay", DelayActionExecutor)
ActionExecutorFactory.register("script", ScriptActionExecutor)
