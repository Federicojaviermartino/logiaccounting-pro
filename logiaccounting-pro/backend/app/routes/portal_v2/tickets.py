"""
Portal v2 Support Ticket Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from app.services.portal.ticket_service import ticket_service
from app.utils.auth import get_current_user


router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


class CreateTicketRequest(BaseModel):
    subject: str
    description: str
    category: str
    priority: Optional[str] = "normal"


class ReplyRequest(BaseModel):
    message: str


class ReopenRequest(BaseModel):
    reason: Optional[str] = None


class RateRequest(BaseModel):
    rating: int
    comment: Optional[str] = None


@router.get("/categories")
async def get_categories():
    """Get ticket categories."""
    return ticket_service.get_categories()


@router.get("/priorities")
async def get_priorities():
    """Get ticket priorities."""
    return ticket_service.get_priorities()


@router.get("")
async def list_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_portal_user),
):
    """List customer's tickets."""
    return ticket_service.list_tickets(
        customer_id=current_user.get("customer_id"),
        status=status,
        category=category,
        priority=priority,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/stats")
async def get_ticket_stats(current_user: dict = Depends(get_portal_user)):
    """Get ticket statistics."""
    return ticket_service.get_stats(current_user.get("customer_id"))


@router.post("")
async def create_ticket(
    data: CreateTicketRequest,
    current_user: dict = Depends(get_portal_user),
):
    """Create a new support ticket."""
    ticket = ticket_service.create_ticket(
        tenant_id=current_user.get("tenant_id"),
        customer_id=current_user.get("customer_id"),
        contact_id=current_user.get("contact_id"),
        subject=data.subject,
        description=data.description,
        category=data.category,
        priority=data.priority,
    )
    return ticket_service._ticket_to_dict(ticket, include_messages=True)


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_portal_user),
):
    """Get ticket details."""
    ticket = ticket_service.get_ticket(
        ticket_id=ticket_id,
        customer_id=current_user.get("customer_id"),
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket_service._ticket_to_dict(ticket, include_messages=True)


@router.post("/{ticket_id}/reply")
async def reply_to_ticket(
    ticket_id: str,
    data: ReplyRequest,
    current_user: dict = Depends(get_portal_user),
):
    """Reply to a ticket."""
    ticket = ticket_service.get_ticket(ticket_id, current_user.get("customer_id"))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.status in ["closed"]:
        raise HTTPException(status_code=400, detail="Cannot reply to closed ticket")

    from app.models.crm_store import crm_store
    contact = crm_store.get_contact(current_user.get("contact_id"))
    sender_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() if contact else "Customer"

    msg = ticket_service.add_reply(
        ticket_id=ticket_id,
        sender_type="customer",
        sender_id=current_user.get("contact_id"),
        sender_name=sender_name,
        message=data.message,
    )

    return {
        "id": msg.id,
        "message": msg.message,
        "created_at": msg.created_at.isoformat(),
    }


@router.post("/{ticket_id}/close")
async def close_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_portal_user),
):
    """Close a ticket."""
    try:
        ticket = ticket_service.close_ticket(
            ticket_id=ticket_id,
            customer_id=current_user.get("customer_id"),
        )
        return {"success": True, "status": ticket.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{ticket_id}/reopen")
async def reopen_ticket(
    ticket_id: str,
    data: ReopenRequest,
    current_user: dict = Depends(get_portal_user),
):
    """Reopen a closed ticket."""
    try:
        ticket = ticket_service.reopen_ticket(
            ticket_id=ticket_id,
            customer_id=current_user.get("customer_id"),
            reason=data.reason,
        )
        return {"success": True, "status": ticket.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{ticket_id}/rate")
async def rate_ticket(
    ticket_id: str,
    data: RateRequest,
    current_user: dict = Depends(get_portal_user),
):
    """Rate ticket satisfaction."""
    try:
        ticket = ticket_service.rate_ticket(
            ticket_id=ticket_id,
            customer_id=current_user.get("customer_id"),
            rating=data.rating,
            comment=data.comment,
        )
        return {
            "success": True,
            "rating": ticket.satisfaction_rating,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
