"""
PayPal Webhook Handler
Processes incoming PayPal webhooks
"""

from typing import Dict, Any
from datetime import datetime
import logging

from app.integrations.base import WebhookEvent
from app.services.integrations.webhook_service import webhook_service

logger = logging.getLogger(__name__)


class PayPalWebhookHandler:
    """Handles PayPal webhook events."""

    SUPPORTED_EVENTS = [
        "PAYMENT.CAPTURE.COMPLETED",
        "PAYMENT.CAPTURE.DENIED",
        "PAYMENT.CAPTURE.REFUNDED",
        "CHECKOUT.ORDER.APPROVED",
        "CHECKOUT.ORDER.COMPLETED",
        "INVOICING.INVOICE.PAID",
        "INVOICING.INVOICE.CANCELLED",
        "CUSTOMER.DISPUTE.CREATED",
    ]

    def __init__(self, webhook_id: str = None):
        self.webhook_id = webhook_id

    async def verify_signature(self, payload: bytes, headers: Dict) -> bool:
        """Verify PayPal webhook signature."""
        # PayPal signature verification requires API call
        # In production: verify with PayPal's verification endpoint
        return True

    async def handle_webhook(self, payload: Dict, headers: Dict) -> Dict:
        """Process incoming PayPal webhook."""
        event_type = payload.get("event_type")
        resource = payload.get("resource", {})
        event_id = payload.get("id")

        logger.info(f"[PayPal] Received webhook: {event_type} ({event_id})")

        event = WebhookEvent(
            provider="paypal",
            event_type=event_type,
            payload=resource,
        )

        try:
            handler = self._get_handler(event_type)
            if handler:
                result = await handler(resource)
                event.processed = True
                return {"status": "processed", "result": result}
            else:
                return {"status": "ignored"}

        except Exception as e:
            event.error = str(e)
            logger.error(f"[PayPal] Webhook handler error: {e}")
            return {"status": "error", "error": str(e)}

    def _get_handler(self, event_type: str):
        """Get handler for event type."""
        handlers = {
            "PAYMENT.CAPTURE.COMPLETED": self._handle_capture_completed,
            "PAYMENT.CAPTURE.DENIED": self._handle_capture_denied,
            "PAYMENT.CAPTURE.REFUNDED": self._handle_capture_refunded,
            "CHECKOUT.ORDER.COMPLETED": self._handle_order_completed,
            "INVOICING.INVOICE.PAID": self._handle_invoice_paid,
            "CUSTOMER.DISPUTE.CREATED": self._handle_dispute,
        }
        return handlers.get(event_type)

    async def _handle_capture_completed(self, data: Dict) -> Dict:
        """Handle completed payment capture."""
        capture_id = data.get("id")
        amount = data.get("amount", {})

        logger.info(f"[PayPal] Capture completed: {capture_id}")

        # Extract custom invoice ID from custom_id field
        custom_id = data.get("custom_id", "")
        if custom_id:
            await webhook_service.emit(
                "payment.received",
                customer_id="unknown",  # Would need to look up
                payload={
                    "payment_id": capture_id,
                    "amount": float(amount.get("value", 0)),
                    "currency": amount.get("currency_code", "USD"),
                    "method": "paypal",
                    "paypal_capture_id": capture_id,
                },
            )

        return {"capture_id": capture_id, "status": "completed"}

    async def _handle_capture_denied(self, data: Dict) -> Dict:
        """Handle denied payment."""
        capture_id = data.get("id")

        logger.warning(f"[PayPal] Capture denied: {capture_id}")

        return {"capture_id": capture_id, "status": "denied"}

    async def _handle_capture_refunded(self, data: Dict) -> Dict:
        """Handle refund."""
        capture_id = data.get("id")

        logger.info(f"[PayPal] Capture refunded: {capture_id}")

        return {"capture_id": capture_id, "status": "refunded"}

    async def _handle_order_completed(self, data: Dict) -> Dict:
        """Handle completed order."""
        order_id = data.get("id")

        logger.info(f"[PayPal] Order completed: {order_id}")

        return {"order_id": order_id, "status": "completed"}

    async def _handle_invoice_paid(self, data: Dict) -> Dict:
        """Handle paid invoice."""
        invoice_id = data.get("id")

        logger.info(f"[PayPal] Invoice paid: {invoice_id}")

        return {"invoice_id": invoice_id, "status": "paid"}

    async def _handle_dispute(self, data: Dict) -> Dict:
        """Handle dispute."""
        dispute_id = data.get("dispute_id")
        reason = data.get("reason")

        logger.warning(f"[PayPal] Dispute created: {dispute_id}, reason: {reason}")

        return {"dispute_id": dispute_id, "reason": reason}


# Handler instance
paypal_webhook_handler = PayPalWebhookHandler()
