"""
Stripe Payment Service (Simulated)
Handles Stripe payment processing
"""

from datetime import datetime
from typing import Dict, Optional
import secrets


class StripeService:
    """Simulated Stripe integration"""

    _instance = None
    _payments: Dict[str, dict] = {}

    # Test card behaviors
    TEST_CARDS = {
        "4242424242424242": {"status": "succeeded", "brand": "visa"},
        "4000000000000002": {"status": "card_declined", "error": "Your card was declined"},
        "4000000000009995": {"status": "insufficient_funds", "error": "Insufficient funds"},
        "4000000000000069": {"status": "expired_card", "error": "Your card has expired"},
        "4000000000003220": {"status": "requires_action", "requires_3ds": True},
        "5555555555554444": {"status": "succeeded", "brand": "mastercard"},
        "378282246310005": {"status": "succeeded", "brand": "amex"}
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._payments = {}
        return cls._instance

    def create_payment_intent(
        self,
        amount: float,
        currency: str,
        description: str = "",
        metadata: dict = None
    ) -> dict:
        """Create a payment intent"""
        intent_id = f"pi_{secrets.token_hex(12)}"
        client_secret = f"{intent_id}_secret_{secrets.token_hex(12)}"

        payment = {
            "id": intent_id,
            "object": "payment_intent",
            "amount": int(amount * 100),  # Stripe uses cents
            "amount_received": 0,
            "currency": currency.lower(),
            "description": description,
            "metadata": metadata or {},
            "status": "requires_payment_method",
            "client_secret": client_secret,
            "created": int(datetime.utcnow().timestamp()),
            "livemode": False
        }

        self._payments[intent_id] = payment
        return payment

    def confirm_payment(
        self,
        payment_intent_id: str,
        card_number: str = None
    ) -> dict:
        """Confirm/process a payment"""
        payment = self._payments.get(payment_intent_id)
        if not payment:
            return {"error": "Payment intent not found"}

        # Simulate card processing
        card_clean = (card_number or "").replace(" ", "").replace("-", "")
        card_result = self.TEST_CARDS.get(card_clean, {"status": "succeeded", "brand": "visa"})

        if card_result["status"] == "succeeded":
            payment["status"] = "succeeded"
            payment["amount_received"] = payment["amount"]
            payment["charges"] = {
                "data": [{
                    "id": f"ch_{secrets.token_hex(12)}",
                    "amount": payment["amount"],
                    "status": "succeeded",
                    "payment_method_details": {
                        "card": {
                            "brand": card_result["brand"],
                            "last4": card_clean[-4:] if card_clean else "4242"
                        }
                    }
                }]
            }
            return {
                "success": True,
                "payment_intent": payment,
                "transaction_id": payment["charges"]["data"][0]["id"]
            }

        elif card_result.get("requires_3ds"):
            payment["status"] = "requires_action"
            payment["next_action"] = {
                "type": "use_stripe_sdk",
                "redirect_to_url": {
                    "url": f"https://hooks.stripe.com/3d_secure_2/{payment_intent_id}"
                }
            }
            return {
                "success": False,
                "requires_action": True,
                "payment_intent": payment
            }

        else:
            payment["status"] = "failed"
            payment["last_payment_error"] = {
                "code": card_result["status"],
                "message": card_result["error"]
            }
            return {
                "success": False,
                "error": card_result["error"],
                "error_code": card_result["status"]
            }

    def get_payment_intent(self, payment_intent_id: str) -> Optional[dict]:
        """Get payment intent details"""
        return self._payments.get(payment_intent_id)

    def cancel_payment(self, payment_intent_id: str) -> dict:
        """Cancel a payment intent"""
        payment = self._payments.get(payment_intent_id)
        if not payment:
            return {"error": "Payment intent not found"}

        if payment["status"] in ["succeeded", "canceled"]:
            return {"error": f"Cannot cancel payment in {payment['status']} status"}

        payment["status"] = "canceled"
        payment["canceled_at"] = int(datetime.utcnow().timestamp())

        return {"success": True, "payment_intent": payment}

    def create_refund(
        self,
        payment_intent_id: str,
        amount: float = None,
        reason: str = "requested_by_customer"
    ) -> dict:
        """Create a refund"""
        payment = self._payments.get(payment_intent_id)
        if not payment:
            return {"error": "Payment intent not found"}

        if payment["status"] != "succeeded":
            return {"error": "Can only refund succeeded payments"}

        refund_amount = int((amount or payment["amount"] / 100) * 100)
        if refund_amount > payment["amount_received"]:
            return {"error": "Refund amount exceeds payment amount"}

        refund = {
            "id": f"re_{secrets.token_hex(12)}",
            "object": "refund",
            "amount": refund_amount,
            "currency": payment["currency"],
            "payment_intent": payment_intent_id,
            "reason": reason,
            "status": "succeeded",
            "created": int(datetime.utcnow().timestamp())
        }

        # Update payment
        payment["amount_received"] -= refund_amount
        if payment["amount_received"] == 0:
            payment["status"] = "refunded"

        return {"success": True, "refund": refund}

    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str
    ) -> bool:
        """Verify webhook signature (simulated - always returns True in demo)"""
        # In production, use stripe.Webhook.construct_event()
        return True

    def construct_webhook_event(self, payload: dict, event_type: str) -> dict:
        """Construct a webhook event object"""
        return {
            "id": f"evt_{secrets.token_hex(12)}",
            "object": "event",
            "type": event_type,
            "data": {
                "object": payload
            },
            "created": int(datetime.utcnow().timestamp()),
            "livemode": False
        }


stripe_service = StripeService()
