"""
Public Checkout routes (no authentication required)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.payment_link_service import payment_link_service
from app.services.gateway_service import gateway_service

router = APIRouter()


class ProcessPaymentRequest(BaseModel):
    gateway: str
    card_number: Optional[str] = None  # For card payments
    card_expiry: Optional[str] = None
    card_cvc: Optional[str] = None
    card_zip: Optional[str] = None
    amount: Optional[float] = None  # For partial payments
    email: Optional[str] = None


@router.get("/{code}")
async def get_checkout_data(code: str):
    """Get checkout page data (public)"""
    # Record view
    payment_link_service.record_view(code)

    data = payment_link_service.get_checkout_data(code)
    if not data:
        raise HTTPException(status_code=404, detail="Payment link not found")

    if data["status"] == "expired":
        raise HTTPException(status_code=410, detail="Payment link has expired")

    if data["status"] == "paid":
        return {
            **data,
            "already_paid": True,
            "message": "This payment has already been completed"
        }

    if data["status"] == "cancelled":
        raise HTTPException(status_code=410, detail="Payment link has been cancelled")

    # Get available gateways with their info
    available_gateways = []
    for gw_id in data["gateways"]:
        gw = gateway_service.get_gateway(gw_id)
        if gw and gw["enabled"]:
            available_gateways.append({
                "id": gw["provider"],
                "name": gw["name"],
                "icon": gw["icon"],
                "methods": gw["supported_methods"]
            })

    return {
        **data,
        "available_gateways": available_gateways
    }


@router.post("/{code}/pay")
async def process_payment(code: str, request: ProcessPaymentRequest):
    """Process payment (public)"""
    # Get link
    link = payment_link_service.get_link_by_code(code)
    if not link:
        raise HTTPException(status_code=404, detail="Payment link not found")

    if link["status"] != "active":
        raise HTTPException(status_code=400, detail=f"Payment link is {link['status']}")

    # Record attempt
    payment_link_service.record_attempt(code)

    # Validate gateway
    if request.gateway not in link["gateways"]:
        raise HTTPException(status_code=400, detail="Gateway not allowed for this link")

    gateway = gateway_service.get_gateway(request.gateway)
    if not gateway or not gateway["enabled"]:
        raise HTTPException(status_code=400, detail="Gateway not available")

    # Determine amount
    pay_amount = request.amount if request.amount and link["allow_partial"] else link["amount"]

    # Validate partial payment
    if link["allow_partial"] and link["minimum_amount"]:
        if pay_amount < link["minimum_amount"]:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum payment amount is {link['minimum_amount']} {link['currency']}"
            )

    # Simulate payment processing based on gateway
    result = _simulate_payment(
        gateway=request.gateway,
        amount=pay_amount,
        currency=link["currency"],
        card_number=request.card_number
    )

    if result["success"]:
        # Calculate fees
        fee_info = gateway_service.calculate_fee(request.gateway, pay_amount)

        # Mark as paid
        payment_link_service.mark_as_paid(
            code=code,
            amount=pay_amount,
            gateway=request.gateway,
            transaction_id=result["transaction_id"],
            fee_amount=fee_info["total_fee"]
        )

        return {
            "success": True,
            "transaction_id": result["transaction_id"],
            "amount_paid": pay_amount,
            "currency": link["currency"],
            "fee": fee_info["total_fee"],
            "net": fee_info["net_amount"],
            "gateway": request.gateway,
            "receipt_sent": link["send_receipt"]
        }
    else:
        return {
            "success": False,
            "error": result["error"],
            "error_code": result.get("error_code", "payment_failed")
        }


@router.get("/{code}/status")
async def get_payment_status(code: str):
    """Get payment status (public)"""
    link = payment_link_service.get_link_by_code(code)
    if not link:
        raise HTTPException(status_code=404, detail="Payment link not found")

    return {
        "code": code,
        "status": link["status"],
        "paid_at": link.get("paid_at"),
        "paid_amount": link.get("paid_amount"),
        "paid_via": link.get("paid_via"),
        "transaction_id": link.get("transaction_id")
    }


def _simulate_payment(gateway: str, amount: float, currency: str, card_number: str = None) -> dict:
    """Simulate payment processing"""
    import secrets

    # Test card numbers for simulation
    if card_number:
        card_clean = card_number.replace(" ", "").replace("-", "")

        # Declined card
        if card_clean == "4000000000000002":
            return {
                "success": False,
                "error": "Your card was declined",
                "error_code": "card_declined"
            }

        # Insufficient funds
        if card_clean == "4000000000009995":
            return {
                "success": False,
                "error": "Insufficient funds",
                "error_code": "insufficient_funds"
            }

        # Expired card
        if card_clean == "4000000000000069":
            return {
                "success": False,
                "error": "Your card has expired",
                "error_code": "expired_card"
            }

    # Simulate successful payment
    transaction_id = f"txn_{secrets.token_hex(12)}"

    return {
        "success": True,
        "transaction_id": transaction_id,
        "gateway_response": {
            "status": "succeeded",
            "amount": amount,
            "currency": currency
        }
    }
