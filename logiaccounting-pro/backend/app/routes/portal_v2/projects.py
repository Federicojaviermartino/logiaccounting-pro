"""
Portal v2 Project Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.portal.project_service import portal_project_service
from app.utils.auth import get_current_user

router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("")
async def list_projects(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    current_user: dict = Depends(get_portal_user)
):
    """List customer projects."""
    return portal_project_service.list_projects(current_user.get("customer_id"), status, page)


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_portal_user)):
    """Get project statistics."""
    return portal_project_service.get_project_stats(current_user.get("customer_id"))


@router.get("/{project_id}")
async def get_project(project_id: str, current_user: dict = Depends(get_portal_user)):
    """Get project details."""
    project = portal_project_service.get_project(project_id, current_user.get("customer_id"))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/timeline")
async def get_timeline(project_id: str, current_user: dict = Depends(get_portal_user)):
    """Get project timeline/milestones."""
    timeline = portal_project_service.get_project_timeline(project_id, current_user.get("customer_id"))
    if timeline is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return timeline


@router.get("/{project_id}/documents")
async def get_documents(project_id: str, current_user: dict = Depends(get_portal_user)):
    """Get project documents."""
    return portal_project_service.get_project_documents(project_id, current_user.get("customer_id"))


class FeedbackRequest(BaseModel):
    content: str
    rating: Optional[int] = None


@router.post("/{project_id}/feedback")
async def submit_feedback(
    project_id: str,
    data: FeedbackRequest,
    current_user: dict = Depends(get_portal_user)
):
    """Submit project feedback."""
    try:
        return portal_project_service.submit_feedback(
            project_id, current_user.get("customer_id"), data.content, data.rating
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class ApprovalRequest(BaseModel):
    approved: bool
    comment: Optional[str] = None


@router.post("/{project_id}/deliverables/{deliverable_id}/approve")
async def approve_deliverable(
    project_id: str,
    deliverable_id: str,
    data: ApprovalRequest,
    current_user: dict = Depends(get_portal_user)
):
    """Approve or reject a deliverable."""
    try:
        return portal_project_service.approve_deliverable(
            project_id, deliverable_id, current_user.get("customer_id"),
            data.approved, data.comment
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
