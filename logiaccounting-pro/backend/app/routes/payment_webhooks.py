"""
Webhook handlers for payment gateways
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from app.services.stripe_service import stripe_service
from app.services.paypal_service import paypal_service
from app.services.mercadopago_service import mercadopago_service
from app.services.payment_link_service import payment_link_service
from app.services.gateway_service import gateway_service

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature")
):
    """Handle Stripe webhooks"""
    try:
        payload = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid payload")

    # In production, verify signature
    # stripe_service.verify_webhook_signature(payload, stripe_signature, webhook_secret)

    event_type = payload.get("type", "")
    data = payload.get("data", {}).get("object", {})

    # Handle different event types
    if event_type == "payment_intent.succeeded":
        await handle_stripe_payment_succeeded(data)

    elif event_type == "payment_intent.payment_failed":
        await handle_stripe_payment_failed(data)

    elif event_type == "charge.refunded":
        await handle_stripe_refund(data)

    return {"received": True, "event_type": event_type}


async def handle_stripe_payment_succeeded(payment_intent: dict):
    """Handle successful Stripe payment"""
    metadata = payment_intent.get("metadata", {})
    payment_link_code = metadata.get("payment_link_code")

    if payment_link_code:
        amount = payment_intent.get("amount_received", 0) / 100
        fee = gateway_service.calculate_fee("stripe", amount)

        payment_link_service.mark_as_paid(
            code=payment_link_code,
            amount=amount,
            gateway="stripe",
            transaction_id=payment_intent.get("id"),
            fee_amount=fee.get("total_fee", 0)
        )


async def handle_stripe_payment_failed(payment_intent: dict):
    """Handle failed Stripe payment"""
    metadata = payment_intent.get("metadata", {})
    payment_link_code = metadata.get("payment_link_code")

    if payment_link_code:
        payment_link_service.record_attempt(payment_link_code)


async def handle_stripe_refund(charge: dict):
    """Handle Stripe refund"""
    # Log refund for audit
    pass


@router.post("/paypal")
async def paypal_webhook(request: Request):
    """Handle PayPal webhooks"""
    try:
        payload = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = payload.get("event_type", "")
    resource = payload.get("resource", {})

    # Handle different event types
    if event_type == "CHECKOUT.ORDER.APPROVED":
        await handle_paypal_order_approved(resource)

    elif event_type == "PAYMENT.CAPTURE.COMPLETED":
        await handle_paypal_capture_completed(resource)

    elif event_type == "PAYMENT.CAPTURE.REFUNDED":
        await handle_paypal_refund(resource)

    return {"received": True, "event_type": event_type}


async def handle_paypal_order_approved(order: dict):
    """Handle PayPal order approval"""
    pass


async def handle_paypal_capture_completed(capture: dict):
    """Handle PayPal payment capture"""
    custom_id = capture.get("custom_id", "")

    if custom_id.startswith("PLINK:"):
        payment_link_code = custom_id.replace("PLINK:", "")
        amount = float(capture.get("amount", {}).get("value", 0))
        fee = gateway_service.calculate_fee("paypal", amount)

        payment_link_service.mark_as_paid(
            code=payment_link_code,
            amount=amount,
            gateway="paypal",
            transaction_id=capture.get("id"),
            fee_amount=fee.get("total_fee", 0)
        )


async def handle_paypal_refund(refund: dict):
    """Handle PayPal refund"""
    pass


@router.post("/mercadopago")
async def mercadopago_webhook(
    request: Request,
    topic: Optional[str] = None,
    id: Optional[str] = None
):
    """Handle MercadoPago IPN"""
    # MercadoPago sends topic and id as query params
    if not topic or not id:
        try:
            payload = await request.json()
            topic = payload.get("topic") or payload.get("type")
            id = payload.get("data", {}).get("id") or payload.get("id")
        except:
            pass

    if topic == "payment":
        await handle_mercadopago_payment(id)

    return {"received": True, "topic": topic, "id": id}


async def handle_mercadopago_payment(payment_id: str):
    """Handle MercadoPago payment notification"""
    payment = mercadopago_service.get_payment(payment_id)
    if not payment:
        return

    if payment.get("status") == "approved":
        external_ref = payment.get("external_reference", "")

        if external_ref.startswith("PLINK:"):
            payment_link_code = external_ref.replace("PLINK:", "")
            amount = payment.get("transaction_amount", 0)
            fee = gateway_service.calculate_fee("mercadopago", amount)

            payment_link_service.mark_as_paid(
                code=payment_link_code,
                amount=amount,
                gateway="mercadopago",
                transaction_id=str(payment.get("id")),
                fee_amount=fee.get("total_fee", 0)
            )
