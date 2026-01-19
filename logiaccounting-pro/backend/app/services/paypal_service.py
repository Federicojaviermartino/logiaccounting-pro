"""
PayPal Payment Service (Simulated)
Handles PayPal payment processing
"""

from datetime import datetime
from typing import Dict, Optional
import secrets


class PayPalService:
    """Simulated PayPal integration"""

    _instance = None
    _orders: Dict[str, dict] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._orders = {}
        return cls._instance

    def create_order(
        self,
        amount: float,
        currency: str,
        description: str = "",
        return_url: str = "",
        cancel_url: str = ""
    ) -> dict:
        """Create a PayPal order"""
        order_id = secrets.token_hex(9).upper()

        order = {
            "id": order_id,
            "status": "CREATED",
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": f"ref_{secrets.token_hex(6)}",
                "description": description,
                "amount": {
                    "currency_code": currency.upper(),
                    "value": f"{amount:.2f}"
                }
            }],
            "create_time": datetime.utcnow().isoformat() + "Z",
            "links": [
                {
                    "href": f"https://api.sandbox.paypal.com/v2/checkout/orders/{order_id}",
                    "rel": "self",
                    "method": "GET"
                },
                {
                    "href": f"https://www.sandbox.paypal.com/checkoutnow?token={order_id}",
                    "rel": "approve",
                    "method": "GET"
                },
                {
                    "href": f"https://api.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture",
                    "rel": "capture",
                    "method": "POST"
                }
            ]
        }

        self._orders[order_id] = order
        return order

    def get_order(self, order_id: str) -> Optional[dict]:
        """Get order details"""
        return self._orders.get(order_id)

    def approve_order(self, order_id: str) -> dict:
        """Simulate user approval (for demo)"""
        order = self._orders.get(order_id)
        if not order:
            return {"error": "Order not found"}

        order["status"] = "APPROVED"
        order["payer"] = {
            "payer_id": f"PAYER{secrets.token_hex(6).upper()}",
            "email_address": "buyer@example.com",
            "name": {
                "given_name": "John",
                "surname": "Doe"
            }
        }

        return {"success": True, "order": order}

    def capture_order(self, order_id: str) -> dict:
        """Capture an approved order"""
        order = self._orders.get(order_id)
        if not order:
            return {"error": "Order not found"}

        if order["status"] not in ["APPROVED", "CREATED"]:
            return {"error": f"Cannot capture order in {order['status']} status"}

        # Simulate approval if not already approved (for demo simplicity)
        if order["status"] == "CREATED":
            self.approve_order(order_id)

        capture_id = f"CAPTURE{secrets.token_hex(8).upper()}"

        order["status"] = "COMPLETED"
        order["purchase_units"][0]["payments"] = {
            "captures": [{
                "id": capture_id,
                "status": "COMPLETED",
                "amount": order["purchase_units"][0]["amount"],
                "final_capture": True,
                "create_time": datetime.utcnow().isoformat() + "Z"
            }]
        }

        return {
            "success": True,
            "order": order,
            "capture_id": capture_id,
            "transaction_id": capture_id
        }

    def create_refund(
        self,
        capture_id: str,
        amount: float = None,
        note: str = ""
    ) -> dict:
        """Create a refund for a captured payment"""
        # Find order with this capture
        order = None
        for o in self._orders.values():
            captures = o.get("purchase_units", [{}])[0].get("payments", {}).get("captures", [])
            for capture in captures:
                if capture["id"] == capture_id:
                    order = o
                    break

        if not order:
            return {"error": "Capture not found"}

        capture = order["purchase_units"][0]["payments"]["captures"][0]
        original_amount = float(capture["amount"]["value"])
        refund_amount = amount or original_amount

        if refund_amount > original_amount:
            return {"error": "Refund amount exceeds capture amount"}

        refund = {
            "id": f"REFUND{secrets.token_hex(8).upper()}",
            "status": "COMPLETED",
            "amount": {
                "currency_code": capture["amount"]["currency_code"],
                "value": f"{refund_amount:.2f}"
            },
            "note_to_payer": note,
            "create_time": datetime.utcnow().isoformat() + "Z"
        }

        # Update capture status
        if refund_amount >= original_amount:
            capture["status"] = "REFUNDED"
        else:
            capture["status"] = "PARTIALLY_REFUNDED"

        return {"success": True, "refund": refund}

    def verify_webhook_signature(
        self,
        payload: str,
        headers: dict,
        webhook_id: str
    ) -> bool:
        """Verify webhook signature (simulated)"""
        # In production, use PayPal SDK to verify
        return True


paypal_service = PayPalService()
