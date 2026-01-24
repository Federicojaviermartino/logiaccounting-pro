"""
Action Base Classes and Registry
Foundation for workflow actions
"""

from typing import Dict, Any, List, Optional, Callable, Type
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ActionCategory(str, Enum):
    COMMUNICATION = "communication"
    DATA = "data"
    INTEGRATION = "integration"
    FLOW_CONTROL = "flow_control"
    UTILITY = "utility"


class ActionInput:
    """Describes an action input field."""

    def __init__(self, name: str, label: str, field_type: str, required: bool = False, default: Any = None, description: str = "", options: List[Dict] = None, placeholder: str = ""):
        self.name = name
        self.label = label
        self.field_type = field_type  # string, number, boolean, select, textarea, email, template
        self.required = required
        self.default = default
        self.description = description
        self.options = options  # For select type
        self.placeholder = placeholder

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.field_type,
            "required": self.required,
            "default": self.default,
            "description": self.description,
            "options": self.options,
            "placeholder": self.placeholder,
        }


class ActionOutput:
    """Describes an action output."""

    def __init__(self, name: str, label: str, output_type: str, description: str = ""):
        self.name = name
        self.label = label
        self.output_type = output_type
        self.description = description

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.output_type,
            "description": self.description,
        }


class BaseAction(ABC):
    """Abstract base class for all workflow actions."""

    # Action metadata (override in subclasses)
    ACTION_ID: str = ""
    ACTION_NAME: str = ""
    DESCRIPTION: str = ""
    CATEGORY: ActionCategory = ActionCategory.UTILITY
    ICON: str = "⚡"

    # Input/output definitions
    INPUTS: List[ActionInput] = []
    OUTPUTS: List[ActionOutput] = []

    def __init__(self):
        self._execution_count = 0
        self._last_execution = None

    def get_metadata(self) -> Dict:
        """Get action metadata."""
        return {
            "id": self.ACTION_ID,
            "name": self.ACTION_NAME,
            "description": self.DESCRIPTION,
            "category": self.CATEGORY.value,
            "icon": self.ICON,
            "inputs": [i.to_dict() for i in self.INPUTS],
            "outputs": [o.to_dict() for o in self.OUTPUTS],
        }

    def validate_inputs(self, config: Dict) -> List[str]:
        """Validate input configuration."""
        errors = []

        for input_def in self.INPUTS:
            if input_def.required and input_def.name not in config:
                errors.append(f"Missing required input: {input_def.name}")

        return errors

    @abstractmethod
    async def execute(self, config: Dict, context: Dict) -> Dict:
        """Execute the action."""
        pass

    def _log_execution(self, config: Dict, result: Dict, error: str = None):
        """Log action execution."""
        self._execution_count += 1
        self._last_execution = datetime.utcnow()

        if error:
            logger.error(f"[{self.ACTION_ID}] Execution failed: {error}")
        else:
            logger.info(f"[{self.ACTION_ID}] Executed successfully")


class ActionRegistry:
    """Registry for all workflow actions."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._actions: Dict[str, BaseAction] = {}
        return cls._instance

    def register(self, action: BaseAction):
        """Register an action."""
        self._actions[action.ACTION_ID] = action
        logger.info(f"Registered action: {action.ACTION_ID}")

    def get(self, action_id: str) -> Optional[BaseAction]:
        """Get action by ID."""
        return self._actions.get(action_id)

    def list_all(self) -> List[Dict]:
        """List all registered actions."""
        return [action.get_metadata() for action in self._actions.values()]

    def list_by_category(self, category: ActionCategory) -> List[Dict]:
        """List actions by category."""
        return [
            action.get_metadata()
            for action in self._actions.values()
            if action.CATEGORY == category
        ]

    def get_categories(self) -> List[Dict]:
        """Get all categories with their actions."""
        categories = {}

        for action in self._actions.values():
            cat = action.CATEGORY.value
            if cat not in categories:
                categories[cat] = {
                    "id": cat,
                    "name": cat.replace("_", " ").title(),
                    "actions": [],
                }
            categories[cat]["actions"].append(action.get_metadata())

        return list(categories.values())


# Global registry instance
action_registry = ActionRegistry()


def register_action(cls: Type[BaseAction]) -> Type[BaseAction]:
    """Decorator to register an action."""
    action_registry.register(cls())
    return cls
