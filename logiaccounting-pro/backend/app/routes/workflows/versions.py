"""
Workflow Version API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.workflows.services.version_service import version_service
from app.workflows.models.store import workflow_store


router = APIRouter()


class SaveVersionRequest(BaseModel):
    comment: Optional[str] = None

class RollbackRequest(BaseModel):
    version: int


@router.get("/{workflow_id}/versions")
async def list_versions(workflow_id: str, limit: int = Query(20, ge=1, le=100), current_user: dict = Depends(get_current_user)):
    if not workflow_store.get_workflow(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return version_service.list_versions(workflow_id, limit=limit)


@router.post("/{workflow_id}/versions")
async def save_version(workflow_id: str, data: SaveVersionRequest, current_user: dict = Depends(get_current_user)):
    workflow = workflow_store.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return version_service.save_version(workflow, user_id=current_user["id"], comment=data.comment)


@router.get("/{workflow_id}/versions/{version}")
async def get_version(workflow_id: str, version: int, current_user: dict = Depends(get_current_user)):
    ver = version_service.get_version(workflow_id, version=version)
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    return ver


@router.get("/{workflow_id}/versions/compare")
async def compare_versions(workflow_id: str, version_a: int = Query(...), version_b: int = Query(...), current_user: dict = Depends(get_current_user)):
    result = version_service.compare_versions(workflow_id, version_a, version_b)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/{workflow_id}/versions/rollback")
async def rollback_version(workflow_id: str, data: RollbackRequest, current_user: dict = Depends(get_current_user)):
    try:
        return version_service.rollback(workflow_id, data.version, current_user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
