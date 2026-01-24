"""
Workflow Models
Data structures for workflow definitions and executions
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from uuid import uuid4
from dataclasses import dataclass, field


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"
    RETRYING = "retrying"


class NodeType(str, Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    DELAY = "delay"
    END = "end"


class TriggerType(str, Enum):
    EVENT = "event"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    WEBHOOK = "webhook"


@dataclass
class WorkflowNode:
    """Represents a node in the workflow."""

    id: str
    type: NodeType
    name: str = ""
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0})

    # For action nodes
    action: Optional[str] = None

    # For condition nodes
    condition: Optional[Dict] = None
    true_branch: List[str] = field(default_factory=list)
    false_branch: List[str] = field(default_factory=list)

    # For loop nodes
    collection: Optional[str] = None
    item_variable: Optional[str] = None
    body: List[str] = field(default_factory=list)

    # For parallel nodes
    branches: List[List[str]] = field(default_factory=list)

    # For delay nodes
    delay_seconds: int = 0
    delay_until: Optional[str] = None

    # Outputs
    outputs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, NodeType) else self.type,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "position": self.position,
            "action": self.action,
            "condition": self.condition,
            "true_branch": self.true_branch,
            "false_branch": self.false_branch,
            "collection": self.collection,
            "item_variable": self.item_variable,
            "body": self.body,
            "branches": self.branches,
            "delay_seconds": self.delay_seconds,
            "delay_until": self.delay_until,
            "outputs": self.outputs,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowNode":
        node_type = data.get("type")
        if isinstance(node_type, str):
            node_type = NodeType(node_type)

        return cls(
            id=data["id"],
            type=node_type,
            name=data.get("name", ""),
            description=data.get("description", ""),
            config=data.get("config", {}),
            position=data.get("position", {"x": 0, "y": 0}),
            action=data.get("action"),
            condition=data.get("condition"),
            true_branch=data.get("true_branch", []),
            false_branch=data.get("false_branch", []),
            collection=data.get("collection"),
            item_variable=data.get("item_variable"),
            body=data.get("body", []),
            branches=data.get("branches", []),
            delay_seconds=data.get("delay_seconds", 0),
            delay_until=data.get("delay_until"),
            outputs=data.get("outputs", []),
        )


@dataclass
class WorkflowEdge:
    """Represents a connection between nodes."""

    id: str
    source: str
    target: str
    label: Optional[str] = None
    condition: Optional[str] = None  # "true", "false", or None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "condition": self.condition,
        }


@dataclass
class WorkflowTrigger:
    """Workflow trigger configuration."""

    type: TriggerType
    event: Optional[str] = None
    cron: Optional[str] = None
    interval_seconds: Optional[int] = None
    webhook_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "type": self.type.value if isinstance(self.type, TriggerType) else self.type,
            "event": self.event,
            "cron": self.cron,
            "interval_seconds": self.interval_seconds,
            "webhook_path": self.webhook_path,
            "config": self.config,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowTrigger":
        trigger_type = data.get("type")
        if isinstance(trigger_type, str):
            trigger_type = TriggerType(trigger_type)

        return cls(
            type=trigger_type,
            event=data.get("event"),
            cron=data.get("cron"),
            interval_seconds=data.get("interval_seconds"),
            webhook_path=data.get("webhook_path"),
            config=data.get("config", {}),
        )


@dataclass
class Workflow:
    """Complete workflow definition."""

    id: str
    name: str
    customer_id: str
    description: str = ""
    status: WorkflowStatus = WorkflowStatus.DRAFT
    version: int = 1
    trigger: Optional[WorkflowTrigger] = None
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    # Runtime stats
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_run_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "customer_id": self.customer_id,
            "description": self.description,
            "status": self.status.value,
            "version": self.version,
            "trigger": self.trigger.to_dict() if self.trigger else None,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "variables": self.variables,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "success_rate": (self.success_count / self.run_count * 100) if self.run_count > 0 else 0,
        }

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_start_nodes(self) -> List[str]:
        """Get nodes connected to trigger."""
        start_nodes = []
        for edge in self.edges:
            if edge.source == "trigger":
                start_nodes.append(edge.target)
        return start_nodes

    def get_next_nodes(self, node_id: str, condition: str = None) -> List[str]:
        """Get next nodes from current node."""
        next_nodes = []
        for edge in self.edges:
            if edge.source == node_id:
                if condition is None or edge.condition == condition:
                    next_nodes.append(edge.target)
        return next_nodes


@dataclass
class StepExecution:
    """Execution state of a single step/node."""

    id: str
    node_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "retry_count": self.retry_count,
            "duration_ms": self.duration_ms,
        }

    @property
    def duration_ms(self) -> Optional[int]:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None


@dataclass
class WorkflowExecution:
    """Execution instance of a workflow."""

    id: str
    workflow_id: str
    workflow_version: int
    status: ExecutionStatus = ExecutionStatus.PENDING
    trigger_type: Optional[str] = None
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    input_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    steps: List[StepExecution] = field(default_factory=list)
    current_node_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_version": self.workflow_version,
            "status": self.status.value,
            "trigger_type": self.trigger_type,
            "trigger_data": self.trigger_data,
            "input_data": self.input_data,
            "context": self.context,
            "steps": [s.to_dict() for s in self.steps],
            "current_node_id": self.current_node_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "steps_completed": len([s for s in self.steps if s.status == ExecutionStatus.COMPLETED]),
            "steps_total": len(self.steps),
        }

    @property
    def duration_ms(self) -> Optional[int]:
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None

    def get_step(self, node_id: str) -> Optional[StepExecution]:
        """Get step execution by node ID."""
        for step in self.steps:
            if step.node_id == node_id:
                return step
        return None

    def add_step(self, node_id: str) -> StepExecution:
        """Add new step execution."""
        step = StepExecution(
            id=f"step_{uuid4().hex[:12]}",
            node_id=node_id,
        )
        self.steps.append(step)
        return step
