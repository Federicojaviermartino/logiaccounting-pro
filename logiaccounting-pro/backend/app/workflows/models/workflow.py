"""
Workflow definition model.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import uuid4

from app.workflows.config import WorkflowStatus, TriggerType, NodeType


class TriggerCondition(BaseModel):
    """Single trigger condition."""
    field: str
    operator: str
    value: Any


class TriggerConfig(BaseModel):
    """Workflow trigger configuration."""
    type: TriggerType
    entity: Optional[str] = None
    event: Optional[str] = None
    conditions: List[TriggerCondition] = []
    cron: Optional[str] = None
    timezone: Optional[str] = "UTC"
    webhook_path: Optional[str] = None
    allowed_roles: List[str] = []
    parameters: List[Dict[str, Any]] = []


class NodeConnection(BaseModel):
    """Connection between nodes."""
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    source: str
    target: str
    condition: Optional[str] = None
    label: Optional[str] = None


class WorkflowNode(BaseModel):
    """Single workflow node."""
    id: str
    type: NodeType
    name: str
    description: Optional[str] = None
    config: Dict[str, Any] = {}
    position: Dict[str, float] = {"x": 0, "y": 0}
    next: Optional[str] = None


class ErrorHandler(BaseModel):
    """Workflow error handling configuration."""
    retry_count: int = 3
    retry_delay_seconds: int = 300
    on_failure: Optional[Dict[str, Any]] = None
    notify_on_error: List[str] = []


class WorkflowMetadata(BaseModel):
    """Workflow metadata."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    tags: List[str] = []
    category: Optional[str] = None


class Workflow(BaseModel):
    """Complete workflow definition."""
    id: str = Field(default_factory=lambda: f"wf_{uuid4().hex[:12]}")
    name: str
    description: Optional[str] = None
    version: int = 1
    status: WorkflowStatus = WorkflowStatus.DRAFT
    tenant_id: str

    trigger: TriggerConfig
    nodes: List[WorkflowNode]
    connections: List[NodeConnection] = []

    error_handler: ErrorHandler = Field(default_factory=ErrorHandler)
    metadata: WorkflowMetadata

    execution_count: int = 0
    last_executed: Optional[datetime] = None
    success_rate: float = 100.0


class WorkflowVersion(BaseModel):
    """Workflow version snapshot."""
    id: str = Field(default_factory=lambda: f"wfv_{uuid4().hex[:12]}")
    workflow_id: str
    version: int
    snapshot: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    change_summary: Optional[str] = None


class WorkflowCreate(BaseModel):
    """Schema for creating a workflow."""
    name: str
    description: Optional[str] = None
    trigger: TriggerConfig
    nodes: List[WorkflowNode]
    connections: List[NodeConnection] = []
    error_handler: Optional[ErrorHandler] = None
    tags: List[str] = []
    category: Optional[str] = None


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[TriggerConfig] = None
    nodes: Optional[List[WorkflowNode]] = None
    connections: Optional[List[NodeConnection]] = None
    error_handler: Optional[ErrorHandler] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
