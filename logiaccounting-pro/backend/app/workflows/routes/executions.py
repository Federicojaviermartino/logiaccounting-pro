"""
Workflow execution API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.routes.auth import get_current_user
from app.workflows.models.store import workflow_store
from app.workflows.config import ExecutionStatus
from app.workflows.engine.core import workflow_engine


router = APIRouter(prefix="/executions", tags=["Workflow Executions"])


@router.get("", response_model=List[dict])
async def list_executions(
    workflow_id: Optional[str] = None,
    status: Optional[ExecutionStatus] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Query(default="default")
):
    """List workflow executions."""
    if workflow_id:
        executions = workflow_store.get_executions_by_workflow(
            workflow_id=workflow_id,
            status=status,
            skip=skip,
            limit=limit
        )
    else:
        executions = workflow_store.get_executions_by_tenant(
            tenant_id=tenant_id,
            status=status,
            skip=skip,
            limit=limit
        )

    return [
        {
            "id": e.id,
            "workflow_id": e.workflow_id,
            "workflow_name": e.workflow_name,
            "status": e.status,
            "started_at": e.started_at,
            "completed_at": e.completed_at,
            "duration_ms": e.duration_ms,
            "trigger_type": e.context.trigger_type,
            "error": e.error
        }
        for e in executions
    ]


@router.get("/{execution_id}", response_model=dict)
async def get_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get execution details."""
    execution = workflow_store.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return execution.dict()


@router.get("/{execution_id}/steps", response_model=List[dict])
async def get_execution_steps(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get execution steps."""
    execution = workflow_store.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return [step.dict() for step in execution.steps]


@router.get("/{execution_id}/logs", response_model=List[dict])
async def get_execution_logs(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get execution logs."""
    logs = workflow_store.get_logs(execution_id)

    return [log.dict() for log in logs]


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a running execution."""
    success = await workflow_engine.cancel_execution(execution_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel execution (not running or not found)"
        )

    return {"cancelled": True, "execution_id": execution_id}


@router.post("/{execution_id}/retry")
async def retry_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Query(default="default")
):
    """Retry a failed execution."""
    execution = workflow_store.get_execution(execution_id)

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.status != ExecutionStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed executions can be retried")

    new_execution = await workflow_engine.trigger_workflow(
        workflow_id=execution.workflow_id,
        context=execution.context,
        run_async=True
    )

    return {
        "original_execution_id": execution_id,
        "new_execution_id": new_execution.id,
        "status": new_execution.status
    }


@router.get("/stats/summary", response_model=dict)
async def get_execution_stats(
    workflow_id: Optional[str] = None,
    period: str = Query(default="24h"),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Query(default="default")
):
    """Get execution statistics."""
    if workflow_id:
        executions = workflow_store.get_executions_by_workflow(
            workflow_id=workflow_id,
            limit=1000
        )
    else:
        executions = workflow_store.get_executions_by_tenant(
            tenant_id=tenant_id,
            limit=1000
        )

    total = len(executions)
    completed = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
    failed = len([e for e in executions if e.status == ExecutionStatus.FAILED])
    running = len([e for e in executions if e.status == ExecutionStatus.RUNNING])

    durations = [e.duration_ms for e in executions if e.duration_ms]
    avg_duration = sum(durations) / len(durations) if durations else 0

    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "running": running,
        "success_rate": (completed / total * 100) if total > 0 else 100,
        "avg_duration_ms": avg_duration,
        "period": period
    }
