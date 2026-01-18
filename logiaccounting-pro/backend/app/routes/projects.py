"""
Projects routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.store import db
from app.utils.auth import get_current_user, require_roles
from app.schemas.schemas import ProjectCreate, ProjectUpdate

router = APIRouter()


@router.get("")
async def get_projects(
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all projects"""
    filters = {}
    
    if status_filter:
        filters["status"] = status_filter
    
    if current_user["role"] == "client":
        filters["client_id"] = current_user["id"]
    
    projects = db.projects.find_all(filters if filters else None)
    
    if search:
        search_lower = search.lower()
        projects = [p for p in projects if search_lower in p["name"].lower() or search_lower in p.get("code", "").lower()]
    
    for p in projects:
        client = db.users.find_by_id(p.get("client_id"))
        p["client_name"] = client.get("company_name") if client else p.get("client")
    
    return {"projects": projects}


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific project"""
    project = db.projects.find_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    if current_user["role"] == "client" and project.get("client_id") != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return project


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new project (admin only)"""
    from datetime import datetime
    from uuid import uuid4
    
    data = request.model_dump()
    data["code"] = data.get("code") or f"PRJ-{datetime.now().year}-{str(uuid4())[:4].upper()}"
    
    return db.projects.create(data)


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    request: ProjectUpdate,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a project (admin only)"""
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    updated = db.projects.update(project_id, update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return updated


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a project (admin only)"""
    if not db.projects.delete(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return {"success": True}
