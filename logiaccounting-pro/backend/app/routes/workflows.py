"""
Workflow API Routes
REST endpoints for workflow management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.services.workflow_service import workflow_service
from app.workflows.errors import ValidationError
from app.auth.dependencies import get_current_user, get_current_customer_id

router = APIRouter(prefix="/workflows", tags=["Workflows"])


# ==================== Request/Response Models ====================

class TriggerConfig(BaseModel):
    type: str = Field(..., description="Trigger type: event, schedule, manual, webhook")
    event: Optional[str] = None
    cron: Optional[str] = None
    interval_seconds: Optional[int] = None
    webhook_path: Optional[str] = None


class NodePosition(BaseModel):
    x: int = 0
    y: int = 0


class WorkflowNode(BaseModel):
    id: str
    type: str
    name: Optional[str] = ""
    config: dict = {}
    position: Optional[NodePosition] = None
    action: Optional[str] = None
    condition: Optional[dict] = None
    true_branch: Optional[List[str]] = []
    false_branch: Optional[List[str]] = []
    collection: Optional[str] = None
    item_variable: Optional[str] = None
    body: Optional[List[str]] = []
    outputs: Optional[List[str]] = []


class WorkflowEdge(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    label: Optional[str] = None
    condition: Optional[str] = None


class CreateWorkflowRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    trigger: TriggerConfig
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []


class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[TriggerConfig] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None


class ExecuteWorkflowRequest(BaseModel):
    input_data: Optional[dict] = {}
    trigger_data: Optional[dict] = {}


class CreateFromTemplateRequest(BaseModel):
    template_id: str
    name: Optional[str] = None
    description: Optional[str] = None


# ==================== Routes ====================

@router.get("")
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    customer_id: str = Depends(get_current_customer_id),
):
    """List all workflows for the current customer."""
    return workflow_service.list_workflows(
        customer_id=customer_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("")
async def create_workflow(
    request: CreateWorkflowRequest,
    customer_id: str = Depends(get_current_customer_id),
    user = Depends(get_current_user),
):
    """Create a new workflow."""
    try:
        workflow = workflow_service.create_workflow(
            data=request.dict(),
            customer_id=customer_id,
            user_id=user.get("id"),
        )
        return workflow.to_dict()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "errors": e.details.get("errors", [])})


@router.get("/templates")
async def get_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """Get available workflow templates."""
    return {"templates": workflow_service.get_templates(category)}


@router.post("/from-template")
async def create_from_template(
    request: CreateFromTemplateRequest,
    customer_id: str = Depends(get_current_customer_id),
    user = Depends(get_current_user),
):
    """Create a workflow from a template."""
    try:
        overrides = {}
        if request.name:
            overrides["name"] = request.name
        if request.description:
            overrides["description"] = request.description

        workflow = workflow_service.create_from_template(
            template_id=request.template_id,
            customer_id=customer_id,
            user_id=user.get("id"),
            overrides=overrides,
        )
        return workflow.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stats")
async def get_customer_stats(
    customer_id: str = Depends(get_current_customer_id),
):
    """Get workflow statistics for the customer."""
    return workflow_service.get_customer_stats(customer_id)


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Get a specific workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.to_dict()


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    request: UpdateWorkflowRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    """Update a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        updated = workflow_service.update_workflow(
            workflow_id=workflow_id,
            data=request.dict(exclude_none=True),
        )
        return updated.to_dict()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "errors": e.details.get("errors", [])})


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Delete a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow_service.delete_workflow(workflow_id)
    return {"success": True, "message": "Workflow deleted"}


@router.post("/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Activate a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        activated = workflow_service.activate_workflow(workflow_id)
        return {"success": True, "workflow": activated.to_dict()}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={"message": e.message, "errors": e.details.get("errors", [])})


@router.post("/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Deactivate a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    deactivated = workflow_service.deactivate_workflow(workflow_id)
    return {"success": True, "workflow": deactivated.to_dict()}


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    background_tasks: BackgroundTasks,
    customer_id: str = Depends(get_current_customer_id),
):
    """Manually execute a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Execute in background
    execution = await workflow_service.execute_workflow(
        workflow_id=workflow_id,
        input_data=request.input_data,
        trigger_data={"type": "manual", **request.trigger_data},
    )

    return {
        "execution_id": execution.id,
        "status": execution.status.value,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
    }


@router.get("/{workflow_id}/executions")
async def get_executions(
    workflow_id: str,
    limit: int = Query(20, ge=1, le=100),
    customer_id: str = Depends(get_current_customer_id),
):
    """Get workflow execution history."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    executions = workflow_service.get_executions(workflow_id, limit)
    return {"executions": executions}


@router.get("/{workflow_id}/executions/{execution_id}")
async def get_execution(
    workflow_id: str,
    execution_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Get execution details."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    execution = workflow_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return execution


@router.get("/{workflow_id}/stats")
async def get_workflow_stats(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    """Get workflow statistics."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow_service.get_workflow_stats(workflow_id)


@router.post("/{workflow_id}/duplicate")
async def duplicate_workflow(
    workflow_id: str,
    customer_id: str = Depends(get_current_customer_id),
    user = Depends(get_current_user),
):
    """Duplicate a workflow."""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow or workflow.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Create copy
    data = workflow.to_dict()
    data["name"] = f"{data['name']} (Copy)"
    data.pop("id")
    data.pop("created_at")
    data.pop("updated_at")
    data.pop("run_count")
    data.pop("success_count")
    data.pop("failure_count")

    new_workflow = workflow_service.create_workflow(
        data=data,
        customer_id=customer_id,
        user_id=user.get("id"),
    )

    return new_workflow.to_dict()
