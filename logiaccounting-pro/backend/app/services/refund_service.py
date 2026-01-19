"""
Refund Management Service
"""

from datetime import datetime
from typing import Dict, List, Optional
from app.services.stripe_service import stripe_service
from app.services.paypal_service import paypal_service
from app.services.mercadopago_service import mercadopago_service
from app.services.payment_link_service import payment_link_service


class RefundService:
    """Manages refunds across all gateways"""

    _instance = None
    _refunds: Dict[str, dict] = {}
    _counter = 0

    REFUND_REASONS = [
        "full_refund",
        "partial_service",
        "duplicate_payment",
        "customer_request",
        "quality_issue",
        "other"
    ]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._refunds = {}
            cls._counter = 0
        return cls._instance

    def create_refund(
        self,
        payment_link_id: str,
        amount: float = None,
        reason: str = "customer_request",
        reason_note: str = "",
        requested_by: str = None
    ) -> dict:
        """Create a refund for a payment"""
        # Get payment link
        link = payment_link_service.get_link(payment_link_id)
        if not link:
            return {"error": "Payment link not found"}

        if link["status"] != "paid":
            return {"error": "Can only refund paid payments"}

        original_amount = link["paid_amount"]
        refund_amount = amount or original_amount

        if refund_amount > original_amount:
            return {"error": "Refund amount exceeds payment amount"}

        # Process refund through gateway
        gateway = link["paid_via"]
        transaction_id = link["transaction_id"]

        if gateway == "stripe":
            result = stripe_service.create_refund(transaction_id, refund_amount, reason)
        elif gateway == "paypal":
            result = paypal_service.create_refund(transaction_id, refund_amount, reason_note)
        elif gateway == "mercadopago":
            result = mercadopago_service.create_refund(transaction_id, refund_amount)
        else:
            return {"error": f"Unknown gateway: {gateway}"}

        if not result.get("success"):
            return {"error": result.get("error", "Refund failed")}

        # Create refund record
        self._counter += 1
        refund_id = f"REF-{self._counter:05d}"

        refund = {
            "id": refund_id,
            "payment_link_id": payment_link_id,
            "original_amount": original_amount,
            "refund_amount": refund_amount,
            "currency": link["currency"],
            "reason": reason,
            "reason_note": reason_note,
            "gateway": gateway,
            "gateway_refund_id": result.get("refund", {}).get("id"),
            "status": "completed",
            "requested_by": requested_by,
            "processed_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }

        self._refunds[refund_id] = refund

        # Update payment link if fully refunded
        if refund_amount >= original_amount:
            link["status"] = "refunded"

        return {"success": True, "refund": refund}

    def get_refund(self, refund_id: str) -> Optional[dict]:
        """Get refund details"""
        return self._refunds.get(refund_id)

    def list_refunds(
        self,
        payment_link_id: str = None,
        gateway: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """List refunds with filters"""
        refunds = list(self._refunds.values())

        if payment_link_id:
            refunds = [r for r in refunds if r["payment_link_id"] == payment_link_id]
        if gateway:
            refunds = [r for r in refunds if r["gateway"] == gateway]

        refunds = sorted(refunds, key=lambda x: x["created_at"], reverse=True)

        total = len(refunds)
        paginated = refunds[offset:offset + limit]

        return {
            "refunds": paginated,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def get_statistics(self) -> dict:
        """Get refund statistics"""
        refunds = list(self._refunds.values())

        total_refunded = sum(r["refund_amount"] for r in refunds)

        by_reason = {}
        for refund in refunds:
            reason = refund["reason"]
            by_reason[reason] = by_reason.get(reason, 0) + 1

        by_gateway = {}
        for refund in refunds:
            gateway = refund["gateway"]
            by_gateway[gateway] = by_gateway.get(gateway, 0) + refund["refund_amount"]

        return {
            "total_refunds": len(refunds),
            "total_refunded": round(total_refunded, 2),
            "by_reason": by_reason,
            "by_gateway": by_gateway
        }


refund_service = RefundService()
