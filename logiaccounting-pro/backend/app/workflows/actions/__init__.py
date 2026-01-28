"""
Workflow Actions Module
Registers all available actions
"""
import logging

logger = logging.getLogger(__name__)

from app.workflows.actions.base import (
    BaseAction,
    ActionCategory,
    ActionInput,
    ActionOutput,
    action_registry,
    register_action,
)

# Import action modules to register them
from app.workflows.actions import communication
from app.workflows.actions import data
from app.workflows.actions import integration
from app.workflows.actions import flow


__all__ = [
    'BaseAction',
    'ActionCategory',
    'ActionInput',
    'ActionOutput',
    'action_registry',
    'register_action',
]


def register_default_actions(engine):
    """Register action handlers with the workflow engine."""
    for action_id, action in action_registry._actions.items():
        async def handler(config, context, action=action):
            return await action.execute(config, context)

        engine.register_action(action_id, handler)

    logger.info("Registered %d workflow actions", len(action_registry._actions))


def get_action(action_id: str) -> BaseAction:
    """Get action by ID."""
    return action_registry.get(action_id)


def list_actions() -> list:
    """List all registered actions."""
    return action_registry.list_all()
