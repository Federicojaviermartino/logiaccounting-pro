"""
CRM Quotes API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.services.crm.quote_service import quote_service


router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class QuoteCreate(BaseModel):
    opportunity_id: Optional[str] = None
    contact_id: Optional[str] = None
    company_id: Optional[str] = None
    valid_days: Optional[int] = 30
    currency: Optional[str] = "USD"
    terms: Optional[str] = None
    notes: Optional[str] = None
    discount_percent: Optional[float] = 0
    tax_percent: Optional[float] = 0


class QuoteUpdate(BaseModel):
    terms: Optional[str] = None
    notes: Optional[str] = None
    discount_percent: Optional[float] = None
    tax_percent: Optional[float] = None
    valid_until: Optional[str] = None


class QuoteItemCreate(BaseModel):
    description: str
    quantity: float
    unit_price: float
    product_id: Optional[str] = None
    discount_percent: Optional[float] = 0


class QuoteItemUpdate(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    discount_percent: Optional[float] = None


class SendQuote(BaseModel):
    email: Optional[str] = None


class AcceptQuote(BaseModel):
    signature: Optional[str] = None


class DeclineQuote(BaseModel):
    reason: Optional[str] = None


class RejectQuote(BaseModel):
    reason: Optional[str] = None


# ============================================
# QUOTE ENDPOINTS
# ============================================

@router.get("")
async def list_quotes(
    status: Optional[str] = None,
    opportunity_id: Optional[str] = None,
    company_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List quotes with filters"""
    return quote_service.list_quotes(
        tenant_id=current_user.get("tenant_id"),
        status=status,
        opportunity_id=opportunity_id,
        company_id=company_id,
        page=page,
        page_size=page_size,
    )


@router.post("")
async def create_quote(
    data: QuoteCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new quote"""
    return quote_service.create_quote(
        tenant_id=current_user.get("tenant_id"),
        created_by=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.get("/statuses")
async def get_quote_statuses():
    """Get available quote statuses"""
    return quote_service.QUOTE_STATUSES


@router.get("/{quote_id}")
async def get_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get quote by ID"""
    quote = quote_service.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.put("/{quote_id}")
async def update_quote(
    quote_id: str,
    data: QuoteUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update quote"""
    return quote_service.update_quote(
        quote_id=quote_id,
        user_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete quote"""
    quote_service.delete_quote(quote_id, current_user["id"])
    return {"success": True}


@router.post("/{quote_id}/duplicate")
async def duplicate_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Duplicate a quote"""
    return quote_service.duplicate_quote(quote_id, current_user["id"])


# ============================================
# LINE ITEMS
# ============================================

@router.post("/{quote_id}/items")
async def add_item(
    quote_id: str,
    data: QuoteItemCreate,
    current_user: dict = Depends(get_current_user),
):
    """Add line item to quote"""
    return quote_service.add_item(
        quote_id=quote_id,
        **data.dict(exclude_none=True),
    )


@router.put("/{quote_id}/items/{item_id}")
async def update_item(
    quote_id: str,
    item_id: str,
    data: QuoteItemUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update line item"""
    return quote_service.update_item(
        quote_id=quote_id,
        item_id=item_id,
        **data.dict(exclude_none=True),
    )


@router.delete("/{quote_id}/items/{item_id}")
async def remove_item(
    quote_id: str,
    item_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove line item"""
    quote_service.remove_item(quote_id, item_id)
    return {"success": True}


# ============================================
# WORKFLOW
# ============================================

@router.post("/{quote_id}/submit")
async def submit_for_approval(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Submit quote for approval"""
    return quote_service.submit_for_approval(quote_id, current_user["id"])


@router.post("/{quote_id}/approve")
async def approve_quote(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Approve quote"""
    return quote_service.approve_quote(quote_id, current_user["id"])


@router.post("/{quote_id}/reject")
async def reject_quote(
    quote_id: str,
    data: RejectQuote,
    current_user: dict = Depends(get_current_user),
):
    """Reject quote (return to draft)"""
    return quote_service.reject_quote(
        quote_id,
        current_user["id"],
        data.reason,
    )


@router.post("/{quote_id}/send")
async def send_quote(
    quote_id: str,
    data: SendQuote,
    current_user: dict = Depends(get_current_user),
):
    """Send quote to customer"""
    return quote_service.send_quote(
        quote_id,
        current_user["id"],
        data.email,
    )


@router.post("/{quote_id}/accept")
async def accept_quote(
    quote_id: str,
    data: AcceptQuote,
):
    """Accept quote (customer action)"""
    return quote_service.accept_quote(quote_id, data.signature)


@router.post("/{quote_id}/decline")
async def decline_quote(
    quote_id: str,
    data: DeclineQuote,
):
    """Decline quote (customer action)"""
    return quote_service.decline_quote(quote_id, data.reason)


@router.post("/{quote_id}/convert")
async def convert_to_invoice(
    quote_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Convert accepted quote to invoice"""
    return quote_service.convert_to_invoice(quote_id, current_user["id"])


# Public endpoint for customer viewing
@router.get("/public/{quote_id}")
async def view_quote_public(quote_id: str):
    """Public quote view (marks as viewed)"""
    quote = quote_service.mark_viewed(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Return limited data
    return {
        "id": quote["id"],
        "quote_number": quote["quote_number"],
        "status": quote["status"],
        "valid_until": quote.get("valid_until"),
        "items": quote["items"],
        "subtotal": quote["subtotal"],
        "discount_amount": quote["discount_amount"],
        "tax_amount": quote["tax_amount"],
        "total": quote["total"],
        "terms": quote.get("terms"),
        "notes": quote.get("notes"),
    }
