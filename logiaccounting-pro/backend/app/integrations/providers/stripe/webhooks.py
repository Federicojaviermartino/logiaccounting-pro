"""
Stripe Webhook Handler
Processes incoming Stripe webhooks
"""

from typing import Dict, Any
from datetime import datetime
import hmac
import hashlib
import logging

from app.integrations.base import WebhookEvent
from app.services.integrations.webhook_service import webhook_service

logger = logging.getLogger(__name__)


class StripeWebhookHandler:
    """Handles Stripe webhook events."""

    # Stripe event types we handle
    SUPPORTED_EVENTS = [
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "payment_intent.canceled",
        "charge.refunded",
        "charge.dispute.created",
        "customer.created",
        "customer.updated",
        "customer.deleted",
        "invoice.paid",
        "invoice.payment_failed",
        "invoice.finalized",
        "checkout.session.completed",
    ]

    def __init__(self, webhook_secret: str = None):
        self.webhook_secret = webhook_secret

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature."""
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return True

        try:
            # Parse signature header
            # Format: t=timestamp,v1=signature
            parts = dict(item.split("=") for item in signature.split(","))
            timestamp = parts.get("t")
            sig = parts.get("v1")

            if not timestamp or not sig:
                return False

            # Compute expected signature
            signed_payload = f"{timestamp}.{payload.decode()}"
            expected_sig = hmac.new(
                self.webhook_secret.encode(),
                signed_payload.encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(expected_sig, sig)

        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    async def handle_webhook(self, payload: Dict, headers: Dict) -> Dict:
        """Process incoming Stripe webhook."""
        event_type = payload.get("type")
        event_data = payload.get("data", {}).get("object", {})
        event_id = payload.get("id")

        logger.info(f"[Stripe] Received webhook: {event_type} ({event_id})")

        # Create webhook event record
        event = WebhookEvent(
            provider="stripe",
            event_type=event_type,
            payload=event_data,
        )

        try:
            # Route to specific handler
            handler = self._get_handler(event_type)
            if handler:
                result = await handler(event_data)
                event.processed = True
                return {"status": "processed", "result": result}
            else:
                logger.info(f"[Stripe] No handler for event: {event_type}")
                return {"status": "ignored", "reason": "No handler"}

        except Exception as e:
            event.error = str(e)
            logger.error(f"[Stripe] Webhook handler error: {e}")
            return {"status": "error", "error": str(e)}

    def _get_handler(self, event_type: str):
        """Get handler for event type."""
        handlers = {
            "payment_intent.succeeded": self._handle_payment_succeeded,
            "payment_intent.payment_failed": self._handle_payment_failed,
            "charge.refunded": self._handle_refund,
            "charge.dispute.created": self._handle_dispute,
            "customer.created": self._handle_customer_created,
            "invoice.paid": self._handle_invoice_paid,
            "checkout.session.completed": self._handle_checkout_completed,
        }
        return handlers.get(event_type)

    async def _handle_payment_succeeded(self, data: Dict) -> Dict:
        """Handle successful payment."""
        payment_intent_id = data.get("id")
        amount = data.get("amount")
        currency = data.get("currency")
        customer_id = data.get("customer")
        metadata = data.get("metadata", {})

        invoice_id = metadata.get("invoice_id")

        logger.info(f"[Stripe] Payment succeeded: {payment_intent_id}, amount: {amount}")

        # Emit internal event
        if invoice_id:
            await webhook_service.emit(
                "payment.received",
                customer_id=metadata.get("logiaccounting_customer_id", "unknown"),
                payload={
                    "invoice_id": invoice_id,
                    "payment_id": payment_intent_id,
                    "amount": amount / 100,  # Convert from cents
                    "currency": currency.upper(),
                    "method": "stripe",
                    "stripe_payment_intent": payment_intent_id,
                },
            )

        return {"payment_intent_id": payment_intent_id, "status": "processed"}

    async def _handle_payment_failed(self, data: Dict) -> Dict:
        """Handle failed payment."""
        payment_intent_id = data.get("id")
        error = data.get("last_payment_error", {})
        metadata = data.get("metadata", {})

        logger.warning(f"[Stripe] Payment failed: {payment_intent_id}")

        if metadata.get("logiaccounting_customer_id"):
            await webhook_service.emit(
                "payment.failed",
                customer_id=metadata["logiaccounting_customer_id"],
                payload={
                    "payment_id": payment_intent_id,
                    "error_code": error.get("code"),
                    "error_message": error.get("message"),
                },
            )

        return {"payment_intent_id": payment_intent_id, "status": "failed"}

    async def _handle_refund(self, data: Dict) -> Dict:
        """Handle refund."""
        charge_id = data.get("id")
        refunds = data.get("refunds", {}).get("data", [])

        for refund in refunds:
            logger.info(f"[Stripe] Refund processed: {refund.get('id')}")

        return {"charge_id": charge_id, "refunds": len(refunds)}

    async def _handle_dispute(self, data: Dict) -> Dict:
        """Handle dispute/chargeback."""
        dispute_id = data.get("id")
        amount = data.get("amount")
        reason = data.get("reason")

        logger.warning(f"[Stripe] Dispute created: {dispute_id}, reason: {reason}")

        # In production: create internal dispute record, notify admin

        return {"dispute_id": dispute_id, "reason": reason}

    async def _handle_customer_created(self, data: Dict) -> Dict:
        """Handle new Stripe customer."""
        customer_id = data.get("id")
        email = data.get("email")

        logger.info(f"[Stripe] Customer created: {customer_id}")

        return {"customer_id": customer_id, "email": email}

    async def _handle_invoice_paid(self, data: Dict) -> Dict:
        """Handle paid Stripe invoice."""
        invoice_id = data.get("id")
        amount_paid = data.get("amount_paid")

        logger.info(f"[Stripe] Invoice paid: {invoice_id}")

        return {"invoice_id": invoice_id, "amount": amount_paid}

    async def _handle_checkout_completed(self, data: Dict) -> Dict:
        """Handle completed checkout session."""
        session_id = data.get("id")
        payment_status = data.get("payment_status")
        metadata = data.get("metadata", {})

        logger.info(f"[Stripe] Checkout completed: {session_id}")

        return {"session_id": session_id, "payment_status": payment_status}


# Handler instance
stripe_webhook_handler = StripeWebhookHandler()
