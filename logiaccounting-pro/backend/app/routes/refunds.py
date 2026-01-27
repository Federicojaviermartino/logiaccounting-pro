"""
Refund routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.refund_service import refund_service
from app.utils.auth import require_roles

router = APIRouter()


class CreateRefundRequest(BaseModel):
    payment_link_id: str
    amount: Optional[float] = None
    reason: str = "customer_request"
    reason_note: str = ""


@router.get("/reasons")
async def get_refund_reasons():
    """Get available refund reasons"""
    return {"reasons": refund_service.REFUND_REASONS}


@router.get("/statistics")
async def get_statistics(current_user: dict = Depends(require_roles("admin"))):
    """Get refund statistics"""
    return refund_service.get_statistics()


@router.get("")
async def list_refunds(
    payment_link_id: Optional[str] = None,
    gateway: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_roles("admin"))
):
    """List refunds"""
    return refund_service.list_refunds(payment_link_id, gateway, limit, offset)


@router.post("")
async def create_refund(
    request: CreateRefundRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a refund"""
    result = refund_service.create_refund(
        payment_link_id=request.payment_link_id,
        amount=request.amount,
        reason=request.reason,
        reason_note=request.reason_note,
        requested_by=current_user["id"]
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/{refund_id}")
async def get_refund(
    refund_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get refund details"""
    refund = refund_service.get_refund(refund_id)
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    return refund
