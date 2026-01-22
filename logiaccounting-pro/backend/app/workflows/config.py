"""
Workflow Engine Configuration.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class TriggerType(str, Enum):
    ENTITY_EVENT = "entity_event"
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    MANUAL = "manual"
    CASCADE = "cascade"
    CONDITION = "condition"


class ActionType(str, Enum):
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    NOTIFICATION = "notification"
    WEBHOOK = "webhook"
    UPDATE_ENTITY = "update_entity"
    CREATE_ENTITY = "create_entity"
    DELETE_ENTITY = "delete_entity"
    APPROVAL = "approval"
    DELAY = "delay"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
    SCRIPT = "script"
    ASSIGN = "assign"
    LOG = "log"


class NodeType(str, Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    PARALLEL = "parallel"
    DELAY = "delay"
    END = "end"


class WorkflowSettings(BaseSettings):
    """Workflow engine settings."""

    max_execution_time_seconds: int = 3600
    max_concurrent_executions: int = 100
    max_nodes_per_workflow: int = 50
    max_retries: int = 3
    retry_delay_seconds: int = 300

    scheduler_interval_seconds: int = 60
    max_scheduled_workflows: int = 1000

    script_timeout_seconds: int = 30
    script_memory_limit_mb: int = 128

    redis_queue_name: str = "workflow_executions"
    redis_results_ttl_seconds: int = 86400

    class Config:
        env_prefix = "WORKFLOW_"


workflow_settings = WorkflowSettings()
