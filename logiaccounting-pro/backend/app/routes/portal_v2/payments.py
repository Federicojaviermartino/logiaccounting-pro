"""
Portal v2 Payment Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.portal.payment_service import portal_payment_service
from app.utils.auth import get_current_user

router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("/invoices")
async def list_invoices(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_portal_user)
):
    """List customer invoices."""
    return portal_payment_service.get_invoices(current_user.get("customer_id"), status, page, page_size)


@router.get("/invoices/stats")
async def get_stats(current_user: dict = Depends(get_portal_user)):
    """Get invoice statistics."""
    return portal_payment_service.get_invoice_stats(current_user.get("customer_id"))


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, current_user: dict = Depends(get_portal_user)):
    """Get invoice details."""
    invoice = portal_payment_service.get_invoice(invoice_id, current_user.get("customer_id"))
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


class PayInvoiceRequest(BaseModel):
    payment_method: str
    amount: Optional[float] = None


@router.post("/invoices/{invoice_id}/pay")
async def pay_invoice(
    invoice_id: str,
    data: PayInvoiceRequest,
    current_user: dict = Depends(get_portal_user)
):
    """Pay an invoice."""
    try:
        return portal_payment_service.initiate_payment(
            invoice_id, current_user.get("customer_id"), data.payment_method, data.amount
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_portal_user)
):
    """Get payment history."""
    return portal_payment_service.get_payment_history(current_user.get("customer_id"), page, page_size)


@router.get("/receipts/{payment_id}")
async def get_receipt(payment_id: str, current_user: dict = Depends(get_portal_user)):
    """Get payment receipt."""
    receipt = portal_payment_service.get_payment_receipt(payment_id, current_user.get("customer_id"))
    if not receipt:
        raise HTTPException(status_code=404, detail="Payment not found")
    return receipt


@router.get("/methods")
async def list_methods(current_user: dict = Depends(get_portal_user)):
    """List saved payment methods."""
    return portal_payment_service.list_payment_methods(current_user.get("customer_id"))


class AddMethodRequest(BaseModel):
    method_type: str
    last_four: str
    brand: Optional[str] = None
    expiry: Optional[str] = None


@router.post("/methods")
async def add_method(data: AddMethodRequest, current_user: dict = Depends(get_portal_user)):
    """Add a payment method."""
    return portal_payment_service.add_payment_method(
        current_user.get("customer_id"), data.method_type, data.dict()
    )


@router.delete("/methods/{method_id}")
async def remove_method(method_id: str, current_user: dict = Depends(get_portal_user)):
    """Remove a payment method."""
    portal_payment_service.remove_payment_method(current_user.get("customer_id"), method_id)
    return {"success": True}


@router.get("/auto-pay")
async def get_auto_pay(current_user: dict = Depends(get_portal_user)):
    """Get auto-pay settings."""
    return portal_payment_service.get_auto_pay(current_user.get("customer_id"))


class AutoPayRequest(BaseModel):
    payment_method_id: str
    enabled: bool = True


@router.post("/auto-pay")
async def setup_auto_pay(data: AutoPayRequest, current_user: dict = Depends(get_portal_user)):
    """Setup auto-pay."""
    return portal_payment_service.setup_auto_pay(
        current_user.get("customer_id"), data.payment_method_id, data.enabled
    )


@router.delete("/auto-pay")
async def disable_auto_pay(current_user: dict = Depends(get_portal_user)):
    """Disable auto-pay."""
    portal_payment_service.disable_auto_pay(current_user.get("customer_id"))
    return {"success": True}


@router.get("/statements")
async def get_statement(
    start_date: str,
    end_date: str,
    current_user: dict = Depends(get_portal_user)
):
    """Get account statement."""
    return portal_payment_service.get_statement(current_user.get("customer_id"), start_date, end_date)
