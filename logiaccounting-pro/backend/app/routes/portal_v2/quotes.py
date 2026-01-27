"""
Portal v2 Quote Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.portal.quote_service import portal_quote_service
from app.utils.auth import get_current_user

router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("")
async def list_quotes(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    current_user: dict = Depends(get_portal_user)
):
    """List customer quotes."""
    return portal_quote_service.list_quotes(current_user.get("customer_id"), status, page)


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_portal_user)):
    """Get quote statistics."""
    return portal_quote_service.get_quote_stats(current_user.get("customer_id"))


@router.get("/{quote_id}")
async def get_quote(quote_id: str, current_user: dict = Depends(get_portal_user)):
    """Get quote details."""
    quote = portal_quote_service.get_quote(quote_id, current_user.get("customer_id"))
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


class AcceptRequest(BaseModel):
    signature_data: Optional[str] = None
    acceptance_notes: Optional[str] = None


@router.post("/{quote_id}/accept")
async def accept_quote(
    quote_id: str,
    data: AcceptRequest,
    current_user: dict = Depends(get_portal_user)
):
    """Accept a quote."""
    try:
        return portal_quote_service.accept_quote(
            quote_id, current_user.get("customer_id"),
            data.signature_data, data.acceptance_notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class DeclineRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/{quote_id}/decline")
async def decline_quote(
    quote_id: str,
    data: DeclineRequest,
    current_user: dict = Depends(get_portal_user)
):
    """Decline a quote."""
    try:
        return portal_quote_service.decline_quote(
            quote_id, current_user.get("customer_id"), data.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class RevisionRequest(BaseModel):
    revision_notes: str


@router.post("/{quote_id}/revision")
async def request_revision(
    quote_id: str,
    data: RevisionRequest,
    current_user: dict = Depends(get_portal_user)
):
    """Request quote revision."""
    try:
        return portal_quote_service.request_revision(
            quote_id, current_user.get("customer_id"), data.revision_notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
