"""
Approval Workflow routes
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.approval_service import approval_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class ApprovalActionRequest(BaseModel):
    comment: str = ""


class UpdateRulesRequest(BaseModel):
    rules: List[dict]


@router.get("/rules")
async def get_rules(current_user: dict = Depends(require_roles("admin"))):
    """Get approval rules"""
    return {"rules": approval_service.get_rules()}


@router.put("/rules")
async def update_rules(
    request: UpdateRulesRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update approval rules"""
    approval_service.update_rules(request.rules)
    return {"message": "Rules updated", "rules": approval_service.get_rules()}


@router.get("/pending")
async def get_pending(current_user: dict = Depends(get_current_user)):
    """Get pending approvals for current user"""
    role = current_user.get("role", "user")
    pending = approval_service.get_pending_approvals(role if role != "admin" else None)
    return {"approvals": pending}


@router.get("")
async def get_all(
    status: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get all approvals"""
    return {"approvals": approval_service.get_all_approvals(status)}


@router.get("/{approval_id}")
async def get_approval(
    approval_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific approval"""
    approval = approval_service.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/{approval_id}/approve")
async def approve(
    approval_id: str,
    request: ApprovalActionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Approve a request"""
    result = approval_service.approve(
        approval_id=approval_id,
        approver_id=current_user["id"],
        approver_email=current_user["email"],
        approver_role=current_user.get("role", "user"),
        comment=request.comment
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/{approval_id}/reject")
async def reject(
    approval_id: str,
    request: ApprovalActionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Reject a request"""
    result = approval_service.reject(
        approval_id=approval_id,
        rejector_id=current_user["id"],
        rejector_email=current_user["email"],
        rejector_role=current_user.get("role", "user"),
        reason=request.comment
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
