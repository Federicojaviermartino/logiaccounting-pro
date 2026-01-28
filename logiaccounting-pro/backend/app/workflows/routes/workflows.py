"""
Workflow API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.utils.datetime_utils import utc_now
from app.routes.auth import get_current_user
from app.workflows.models.workflow import (
    Workflow, WorkflowCreate, WorkflowUpdate, WorkflowVersion,
    WorkflowMetadata, ErrorHandler
)
from app.workflows.models.execution import ExecutionContext
from app.workflows.models.store import workflow_store
from app.workflows.config import WorkflowStatus, TriggerType
from app.workflows.engine.core import workflow_engine
from app.workflows.triggers.manual_trigger import ManualTrigger


router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("", response_model=dict)
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Query(default="default")
):
    """Create a new workflow."""
    metadata = WorkflowMetadata(
        created_at=utc_now(),
        created_by=current_user["id"],
        tags=workflow_data.tags,
        category=workflow_data.category
    )

    workflow = Workflow(
        name=workflow_data.name,
        description=workflow_data.description,
        trigger=workflow_data.trigger,
        nodes=workflow_data.nodes,
        connections=workflow_data.connections,
        error_handler=workflow_data.error_handler or ErrorHandler(),
        tenant_id=tenant_id,
        metadata=metadata
    )

    workflow_store.save_workflow(workflow)

    version = WorkflowVersion(
        workflow_id=workflow.id,
        version=1,
        snapshot=workflow.dict(),
        created_by=current_user["id"],
        change_summary="Initial version"
    )
    workflow_store.save_version(version)

    return {"id": workflow.id, "name": workflow.name, "status": workflow.status}


@router.get("", response_model=List[dict])
async def list_workflows(
    status: Optional[WorkflowStatus] = None,
    category: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Query(default="default")
):
    """List workflows for the tenant."""
    workflows = workflow_store.get_workflows_by_tenant(
        tenant_id=tenant_id,
        status=status,
        category=category,
        skip=skip,
        limit=limit
    )

    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "status": w.status,
            "trigger_type": w.trigger.type,
            "execution_count": w.execution_count,
            "last_executed": w.last_executed,
            "version": w.version,
            "category": w.metadata.category,
            "tags": w.metadata.tags
        }
        for w in workflows
    ]


@router.get("/{workflow_id}", response_model=dict)
async def get_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a workflow by ID."""
    workflow = workflow_store.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow.dict()


@router.put("/{workflow_id}", response_model=dict)
async def update_workflow(
    workflow_id: str,
    updates: WorkflowUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a workflow."""
    workflow = workflow_store.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if updates.name is not None:
        workflow.name = updates.name
    if updates.description is not None:
        workflow.description = updates.description
    if updates.trigger is not None:
        workflow.trigger = updates.trigger
    if updates.nodes is not None:
        workflow.nodes = updates.nodes
    if updates.connections is not None:
        workflow.connections = updates.connections
    if updates.error_handler is not None:
        workflow.error_handler = updates.error_handler
    if updates.tags is not None:
        workflow.metadata.tags = updates.tags
    if updates.category is not None:
        workflow.metadata.category = updates.category

    workflow.version += 1
    workflow.metadata.updated_at = utc_now()
    workflow.metadata.updated_by = current_user["id"]

    workflow_store.save_workflow(workflow)

    version = WorkflowVersion(
        workflow_id=workflow.id,
        version=workflow.version,
        snapshot=workflow.dict(),
        created_by=current_user["id"]
    )
    workflow_store.save_version(version)

    return {"id": workflow.id, "version": workflow.version, "updated": True}


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a workflow."""
    if not workflow_store.delete_workflow(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"deleted": True}


@router.post("/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Activate a workflow."""
    workflow = workflow_store.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.status = WorkflowStatus.ACTIVE
    workflow_store.save_workflow(workflow)

    return {"id": workflow.id, "status": workflow.status}


@router.post("/{workflow_id}/pause")
async def pause_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Pause a workflow."""
    workflow = workflow_store.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.status = WorkflowStatus.PAUSED
    workflow_store.save_workflow(workflow)

    return {"id": workflow.id, "status": workflow.status}


@router.post("/{workflow_id}/archive")
async def archive_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Archive a workflow."""
    workflow = workflow_store.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.status = WorkflowStatus.ARCHIVED
    workflow_store.save_workflow(workflow)

    return {"id": workflow.id, "status": workflow.status}


@router.post("/{workflow_id}/trigger")
async def trigger_workflow(
    workflow_id: str,
    parameters: dict = {},
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Query(default="default")
):
    """Manually trigger a workflow."""
    manual_trigger = ManualTrigger(workflow_engine)

    try:
        result = await manual_trigger.trigger(
            workflow_id=workflow_id,
            parameters=parameters,
            user_id=current_user["id"],
            user_role=current_user.get("role", "user"),
            tenant_id=tenant_id
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workflow_id}/test")
async def test_workflow(
    workflow_id: str,
    test_data: dict,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Query(default="default")
):
    """Test a workflow with sample data without saving execution."""
    workflow = workflow_store.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    context = ExecutionContext(
        trigger_type="manual",
        trigger_data=test_data,
        tenant_id=tenant_id,
        user_id=current_user["id"]
    )

    return {
        "valid": True,
        "workflow_id": workflow.id,
        "nodes_count": len(workflow.nodes),
        "test_data": test_data
    }


@router.get("/{workflow_id}/versions")
async def list_versions(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """List all versions of a workflow."""
    versions = workflow_store.get_versions(workflow_id)

    return [
        {
            "version": v.version,
            "created_at": v.created_at,
            "created_by": v.created_by,
            "change_summary": v.change_summary
        }
        for v in versions
    ]


@router.get("/{workflow_id}/versions/{version}")
async def get_version(
    workflow_id: str,
    version: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific version of a workflow."""
    wf_version = workflow_store.get_version(workflow_id, version)

    if not wf_version:
        raise HTTPException(status_code=404, detail="Version not found")

    return wf_version.dict()


@router.post("/{workflow_id}/rollback/{version}")
async def rollback_to_version(
    workflow_id: str,
    version: int,
    current_user: dict = Depends(get_current_user)
):
    """Rollback workflow to a specific version."""
    wf_version = workflow_store.get_version(workflow_id, version)

    if not wf_version:
        raise HTTPException(status_code=404, detail="Version not found")

    workflow = workflow_store.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    snapshot = wf_version.snapshot
    workflow.name = snapshot.get("name", workflow.name)
    workflow.description = snapshot.get("description")

    workflow.version += 1
    workflow.metadata.updated_at = utc_now()
    workflow.metadata.updated_by = current_user["id"]

    workflow_store.save_workflow(workflow)

    new_version = WorkflowVersion(
        workflow_id=workflow.id,
        version=workflow.version,
        snapshot=workflow.dict(),
        created_by=current_user["id"],
        change_summary=f"Rolled back to version {version}"
    )
    workflow_store.save_version(new_version)

    return {"id": workflow.id, "version": workflow.version, "rolled_back_from": version}
