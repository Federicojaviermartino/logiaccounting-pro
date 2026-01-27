"""
Payment Links routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.payment_link_service import payment_link_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class CreateLinkRequest(BaseModel):
    payment_id: str
    amount: float
    currency: str = "USD"
    description: str
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    invoice_number: Optional[str] = None
    gateways: List[str] = ["stripe", "paypal"]
    expires_in_days: int = 30
    single_use: bool = True
    allow_partial: bool = False
    minimum_amount: Optional[float] = None
    send_receipt: bool = True


class UpdateLinkRequest(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    gateways: Optional[List[str]] = None
    expires_in_days: Optional[int] = None


@router.get("/statistics")
async def get_statistics(current_user: dict = Depends(require_roles("admin"))):
    """Get payment link statistics"""
    return payment_link_service.get_statistics()


@router.get("")
async def list_links(
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    payment_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(require_roles("admin"))
):
    """List payment links"""
    return payment_link_service.list_links(status, client_id, payment_id, limit, offset)


@router.post("")
async def create_link(
    request: CreateLinkRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a payment link"""
    return payment_link_service.create_link(
        **request.model_dump(),
        created_by=current_user["id"]
    )


@router.get("/{link_id}")
async def get_link(
    link_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get a payment link"""
    link = payment_link_service.get_link(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


@router.put("/{link_id}")
async def update_link(
    link_id: str,
    request: UpdateLinkRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a payment link"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    link = payment_link_service.update_link(link_id, updates)
    if not link:
        raise HTTPException(status_code=400, detail="Cannot update link")
    return link


@router.delete("/{link_id}")
async def cancel_link(
    link_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Cancel a payment link"""
    link = payment_link_service.cancel_link(link_id)
    if not link:
        raise HTTPException(status_code=400, detail="Cannot cancel link")
    return {"message": "Link cancelled", "link": link}


@router.post("/{link_id}/send")
async def send_link(
    link_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Send payment link to client (simulated)"""
    link = payment_link_service.get_link(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if not link.get("client_email"):
        raise HTTPException(status_code=400, detail="No client email configured")

    # In production, this would send an actual email
    return {
        "message": "Link sent successfully",
        "sent_to": link["client_email"],
        "link_url": link["url"]
    }
