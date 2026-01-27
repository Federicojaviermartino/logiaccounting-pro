"""
Workflow Automation Module.
Provides workflow engine, business rules, and process automation capabilities.
"""

from app.workflows.models import (
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowTrigger,
    WorkflowExecution,
    StepExecution,
    WorkflowStatus,
    ExecutionStatus,
    NodeType,
    TriggerType,
)

from app.workflows.engine import workflow_engine, WorkflowEngine

from app.workflows.variables import VariableResolver, ExpressionEvaluator

from app.workflows.conditions import ConditionBuilder, DateConditionHelper, ConditionPresets

from app.workflows.errors import (
    WorkflowError,
    WorkflowErrorType,
    ValidationError,
    ActionError,
    TimeoutError,
    RetryConfig,
    RetryHandler,
    ErrorRecovery,
    WorkflowValidator,
)

__all__ = [
    # Models
    'Workflow',
    'WorkflowNode',
    'WorkflowEdge',
    'WorkflowTrigger',
    'WorkflowExecution',
    'StepExecution',
    'WorkflowStatus',
    'ExecutionStatus',
    'NodeType',
    'TriggerType',
    # Engine
    'workflow_engine',
    'WorkflowEngine',
    # Variables
    'VariableResolver',
    'ExpressionEvaluator',
    # Conditions
    'ConditionBuilder',
    'DateConditionHelper',
    'ConditionPresets',
    # Errors
    'WorkflowError',
    'WorkflowErrorType',
    'ValidationError',
    'ActionError',
    'TimeoutError',
    'RetryConfig',
    'RetryHandler',
    'ErrorRecovery',
    'WorkflowValidator',
]
