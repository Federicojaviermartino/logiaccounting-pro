"""
Task Management routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.collaboration_service import collaboration_service
from app.utils.auth import get_current_user

router = APIRouter()


class CreateTaskRequest(BaseModel):
    title: str
    entity_type: str
    entity_id: str
    assigned_to: str
    due_date: Optional[str] = None
    priority: str = "medium"
    notes: str = ""


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@router.get("/statuses")
async def get_statuses():
    """Get task statuses"""
    return {"statuses": collaboration_service.TASK_STATUSES}


@router.get("/priorities")
async def get_priorities():
    """Get task priorities"""
    return {"priorities": collaboration_service.TASK_PRIORITIES}


@router.get("/my")
async def get_my_tasks(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get current user's tasks"""
    return {"tasks": collaboration_service.get_user_tasks(current_user["id"], status)}


@router.get("/overdue")
async def get_overdue_tasks(current_user: dict = Depends(get_current_user)):
    """Get all overdue tasks"""
    return {"tasks": collaboration_service.get_overdue_tasks()}


@router.post("")
async def create_task(
    request: CreateTaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a task"""
    return collaboration_service.create_task(
        title=request.title,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        assigned_to=request.assigned_to,
        assigned_by=current_user["id"],
        due_date=request.due_date,
        priority=request.priority,
        notes=request.notes
    )


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_tasks(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get tasks for an entity"""
    return {"tasks": collaboration_service.get_entity_tasks(entity_type, entity_id)}


@router.get("/activity/{entity_type}/{entity_id}")
async def get_activity_feed(
    entity_type: str,
    entity_id: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get activity feed for an entity"""
    return {"activities": collaboration_service.get_activity_feed(entity_type, entity_id, limit)}


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a task"""
    task = collaboration_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a task"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    task = collaboration_service.update_task(task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a task"""
    if collaboration_service.delete_task(task_id):
        return {"message": "Task deleted"}
    raise HTTPException(status_code=404, detail="Task not found")
