"""
Workflow Execution Monitoring API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket
from typing import Optional
import asyncio

from app.utils.auth import get_current_user
from app.workflows.services.execution_monitor import execution_monitor
from app.workflows.models.store import workflow_store
from app.workflows.config import ExecutionStatus


router = APIRouter()


@router.get("")
async def list_executions(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    """List recent executions."""
    return execution_monitor.get_recent_executions(
        tenant_id=current_user.get("tenant_id"),
        workflow_id=workflow_id,
        status=status,
        limit=limit,
    )


@router.get("/active")
async def get_active_executions(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """Get currently running executions."""
    return execution_monitor.get_active_executions(
        tenant_id=current_user.get("tenant_id"),
        limit=limit,
    )


@router.get("/dashboard")
async def get_dashboard_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
):
    """Get dashboard statistics."""
    return execution_monitor.get_dashboard_stats(
        tenant_id=current_user.get("tenant_id"),
        days=days,
    )


@router.get("/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get execution details."""
    execution = workflow_store.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution_monitor.get_execution_timeline(execution_id)


@router.get("/{execution_id}/timeline")
async def get_execution_timeline(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get execution timeline with step details."""
    timeline = execution_monitor.get_execution_timeline(execution_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Execution not found")
    return timeline


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cancel a running execution."""
    execution = workflow_store.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.status != ExecutionStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Execution is not running")

    execution.status = ExecutionStatus.CANCELLED
    execution.error = f"Cancelled by {current_user['id']}"

    return {"success": True, "status": "cancelled"}


@router.post("/{execution_id}/retry")
async def retry_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retry a failed execution."""
    execution = workflow_store.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    if execution.status not in [ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Execution cannot be retried")

    from app.workflows.engine.core import workflow_engine
    from app.workflows.models.execution import ExecutionContext

    context = ExecutionContext(
        trigger_type="retry",
        trigger_data={
            "original_execution_id": execution_id,
            **(execution.context.trigger_data if execution.context else {}),
        },
        user_id=current_user["id"],
        tenant_id=execution.tenant_id,
    )

    new_execution = await workflow_engine.trigger_workflow(
        workflow_id=execution.workflow_id,
        context=context,
        run_async=True,
    )

    return {
        "success": True,
        "new_execution_id": new_execution.id,
        "original_execution_id": execution_id,
    }


@router.get("/workflows/{workflow_id}/stats")
async def get_workflow_stats(
    workflow_id: str,
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),
):
    """Get workflow execution statistics."""
    return execution_monitor.get_workflow_stats(workflow_id, days)


@router.websocket("/{execution_id}/live")
async def execution_live_updates(websocket: WebSocket, execution_id: str):
    """WebSocket for live execution updates."""
    await websocket.accept()

    queue = await execution_monitor.subscribe(execution_id)

    try:
        # Send initial state
        timeline = execution_monitor.get_execution_timeline(execution_id)
        if timeline:
            await websocket.send_json({"type": "initial", "data": timeline})

        # Send updates
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_json(event)

                # Check if execution is complete
                if event.get("type") == "completed":
                    break
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
    except Exception as e:
        pass
    finally:
        await execution_monitor.unsubscribe(execution_id, queue)
