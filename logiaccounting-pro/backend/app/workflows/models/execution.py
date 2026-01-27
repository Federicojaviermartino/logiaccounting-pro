"""
Workflow execution model.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import uuid4

from app.workflows.config import ExecutionStatus, StepStatus


class ExecutionContext(BaseModel):
    """Execution context with trigger data."""
    trigger_type: str
    trigger_data: Dict[str, Any] = {}
    entity: Optional[str] = None
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: str


class ExecutionStep(BaseModel):
    """Single execution step."""
    id: str = Field(default_factory=lambda: f"step_{uuid4().hex[:8]}")
    node_id: str
    node_type: str
    node_name: str

    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    input_data: Dict[str, Any] = {}
    output_data: Dict[str, Any] = {}
    error: Optional[str] = None

    retry_count: int = 0
    skipped_reason: Optional[str] = None


class WorkflowExecution(BaseModel):
    """Workflow execution record."""
    id: str = Field(default_factory=lambda: f"exec_{uuid4().hex[:12]}")
    workflow_id: str
    workflow_name: str
    workflow_version: int
    tenant_id: str

    status: ExecutionStatus = ExecutionStatus.PENDING
    context: ExecutionContext

    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    current_node_id: Optional[str] = None
    steps: List[ExecutionStep] = []
    variables: Dict[str, Any] = {}

    error: Optional[str] = None
    error_node_id: Optional[str] = None
    retry_count: int = 0

    waiting_for: Optional[str] = None
    resume_at: Optional[datetime] = None


class ExecutionLog(BaseModel):
    """Execution log entry."""
    id: str = Field(default_factory=lambda: f"log_{uuid4().hex[:8]}")
    execution_id: str
    step_id: Optional[str] = None

    level: str
    message: str
    data: Dict[str, Any] = {}

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExecutionSummary(BaseModel):
    """Execution summary for listing."""
    id: str
    workflow_id: str
    workflow_name: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    trigger_type: str
    error: Optional[str]
