"""
MercadoPago Payment Service (Simulated)
Handles MercadoPago payment processing for LATAM
"""

from datetime import datetime
from typing import Dict, Optional
import secrets


class MercadoPagoService:
    """Simulated MercadoPago integration"""

    _instance = None
    _preferences: Dict[str, dict] = {}
    _payments: Dict[str, dict] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._preferences = {}
            cls._payments = {}
        return cls._instance

    def create_preference(
        self,
        items: list,
        payer: dict = None,
        back_urls: dict = None,
        external_reference: str = None
    ) -> dict:
        """Create a payment preference"""
        pref_id = secrets.token_hex(16)

        # Calculate total
        total = sum(item.get("unit_price", 0) * item.get("quantity", 1) for item in items)

        preference = {
            "id": pref_id,
            "items": items,
            "payer": payer or {},
            "back_urls": back_urls or {
                "success": "https://logiaccounting-pro.onrender.com/payment/success",
                "failure": "https://logiaccounting-pro.onrender.com/payment/failure",
                "pending": "https://logiaccounting-pro.onrender.com/payment/pending"
            },
            "external_reference": external_reference or f"ref_{secrets.token_hex(8)}",
            "total_amount": total,
            "init_point": f"https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id={pref_id}",
            "sandbox_init_point": f"https://sandbox.mercadopago.com.ar/checkout/v1/redirect?pref_id={pref_id}",
            "date_created": datetime.utcnow().isoformat() + ".000-04:00"
        }

        self._preferences[pref_id] = preference
        return preference

    def get_preference(self, preference_id: str) -> Optional[dict]:
        """Get preference details"""
        return self._preferences.get(preference_id)

    def create_payment(
        self,
        preference_id: str,
        payment_method: str = "credit_card",
        installments: int = 1
    ) -> dict:
        """Simulate a payment being made"""
        preference = self._preferences.get(preference_id)
        if not preference:
            return {"error": "Preference not found"}

        payment_id = secrets.randbelow(9000000000) + 1000000000

        payment = {
            "id": payment_id,
            "status": "approved",
            "status_detail": "accredited",
            "payment_type_id": payment_method,
            "payment_method_id": "visa" if payment_method == "credit_card" else payment_method,
            "transaction_amount": preference["total_amount"],
            "currency_id": "ARS",
            "installments": installments,
            "external_reference": preference["external_reference"],
            "date_created": datetime.utcnow().isoformat() + ".000-04:00",
            "date_approved": datetime.utcnow().isoformat() + ".000-04:00",
            "payer": preference.get("payer", {}),
            "fee_details": [{
                "type": "mercadopago_fee",
                "amount": round(preference["total_amount"] * 0.0499, 2),
                "fee_payer": "collector"
            }]
        }

        self._payments[str(payment_id)] = payment
        return {"success": True, "payment": payment, "transaction_id": str(payment_id)}

    def get_payment(self, payment_id: str) -> Optional[dict]:
        """Get payment details"""
        return self._payments.get(str(payment_id))

    def create_refund(
        self,
        payment_id: str,
        amount: float = None
    ) -> dict:
        """Create a refund"""
        payment = self._payments.get(str(payment_id))
        if not payment:
            return {"error": "Payment not found"}

        if payment["status"] != "approved":
            return {"error": "Can only refund approved payments"}

        refund_amount = amount or payment["transaction_amount"]

        refund = {
            "id": secrets.randbelow(9000000000) + 1000000000,
            "payment_id": payment_id,
            "amount": refund_amount,
            "status": "approved",
            "date_created": datetime.utcnow().isoformat() + ".000-04:00"
        }

        # Update payment status
        if refund_amount >= payment["transaction_amount"]:
            payment["status"] = "refunded"
        else:
            payment["status"] = "partially_refunded"

        return {"success": True, "refund": refund}

    def handle_ipn(self, topic: str, id: str) -> dict:
        """Handle IPN (Instant Payment Notification)"""
        if topic == "payment":
            payment = self.get_payment(id)
            if payment:
                return {"success": True, "payment": payment}

        return {"success": False, "error": "Unknown notification"}


mercadopago_service = MercadoPagoService()
