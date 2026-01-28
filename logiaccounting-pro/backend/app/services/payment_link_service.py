"""
Payment Links Service
Generate and manage payment links
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import secrets
from app.utils.datetime_utils import utc_now
import hashlib
import base64


class PaymentLinkService:
    """Manages payment link generation and tracking"""

    _instance = None
    _links: Dict[str, dict] = {}
    _counter = 0

    LINK_STATUSES = ["active", "paid", "expired", "cancelled"]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._links = {}
            cls._counter = 0
        return cls._instance

    def _generate_code(self) -> str:
        """Generate unique short code for link"""
        return secrets.token_urlsafe(8)[:12]

    def _generate_qr_placeholder(self, url: str) -> str:
        """Generate QR code placeholder (in production, use qrcode library)"""
        # Returns a data URL placeholder
        # In production: import qrcode, generate actual QR
        return f"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><rect fill='%23f0f0f0' width='200' height='200'/><text x='50%' y='50%' text-anchor='middle' dy='.3em' font-family='Arial' font-size='12'>QR Code</text></svg>"

    def create_link(
        self,
        payment_id: str,
        amount: float,
        currency: str,
        description: str,
        client_id: str = None,
        client_name: str = None,
        client_email: str = None,
        invoice_number: str = None,
        gateways: List[str] = None,
        expires_in_days: int = 30,
        single_use: bool = True,
        allow_partial: bool = False,
        minimum_amount: float = None,
        send_receipt: bool = True,
        created_by: str = None,
        base_url: str = "https://logiaccounting-pro.onrender.com"
    ) -> dict:
        """Create a new payment link"""
        self._counter += 1
        link_id = f"PLINK-{self._counter:05d}"
        code = self._generate_code()

        url = f"{base_url}/pay/{code}"

        link = {
            "id": link_id,
            "code": code,
            "url": url,
            "qr_code": self._generate_qr_placeholder(url),

            # Payment details
            "payment_id": payment_id,
            "invoice_number": invoice_number,
            "description": description,

            # Amount
            "amount": amount,
            "currency": currency.upper(),
            "allow_partial": allow_partial,
            "minimum_amount": minimum_amount,

            # Client
            "client_id": client_id,
            "client_name": client_name,
            "client_email": client_email,

            # Settings
            "gateways": gateways or ["stripe", "paypal"],
            "expires_at": (utc_now() + timedelta(days=expires_in_days)).isoformat(),
            "single_use": single_use,
            "send_receipt": send_receipt,

            # Tracking
            "status": "active",
            "views": 0,
            "attempts": 0,
            "paid_at": None,
            "paid_amount": None,
            "paid_via": None,
            "transaction_id": None,
            "fee_amount": None,
            "net_amount": None,

            # Metadata
            "created_by": created_by,
            "created_at": utc_now().isoformat()
        }

        self._links[link_id] = link
        return link

    def get_link(self, link_id: str) -> Optional[dict]:
        """Get link by ID"""
        return self._links.get(link_id)

    def get_link_by_code(self, code: str) -> Optional[dict]:
        """Get link by public code"""
        for link in self._links.values():
            if link["code"] == code:
                return link
        return None

    def list_links(
        self,
        status: str = None,
        client_id: str = None,
        payment_id: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """List payment links with filters"""
        links = list(self._links.values())

        if status:
            links = [l for l in links if l["status"] == status]
        if client_id:
            links = [l for l in links if l["client_id"] == client_id]
        if payment_id:
            links = [l for l in links if l["payment_id"] == payment_id]

        # Check for expired links
        now = utc_now().isoformat()
        for link in links:
            if link["status"] == "active" and link["expires_at"] < now:
                link["status"] = "expired"

        # Sort by created_at descending
        links = sorted(links, key=lambda x: x["created_at"], reverse=True)

        total = len(links)
        paginated = links[offset:offset + limit]

        return {
            "links": paginated,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def record_view(self, code: str) -> Optional[dict]:
        """Record a link view"""
        link = self.get_link_by_code(code)
        if link:
            link["views"] += 1
            return link
        return None

    def record_attempt(self, code: str) -> Optional[dict]:
        """Record a payment attempt"""
        link = self.get_link_by_code(code)
        if link:
            link["attempts"] += 1
            return link
        return None

    def mark_as_paid(
        self,
        code: str,
        amount: float,
        gateway: str,
        transaction_id: str,
        fee_amount: float = 0
    ) -> Optional[dict]:
        """Mark link as paid"""
        link = self.get_link_by_code(code)
        if not link:
            return None

        link["status"] = "paid"
        link["paid_at"] = utc_now().isoformat()
        link["paid_amount"] = amount
        link["paid_via"] = gateway
        link["transaction_id"] = transaction_id
        link["fee_amount"] = fee_amount
        link["net_amount"] = amount - fee_amount

        return link

    def cancel_link(self, link_id: str) -> Optional[dict]:
        """Cancel a payment link"""
        link = self._links.get(link_id)
        if link and link["status"] == "active":
            link["status"] = "cancelled"
            return link
        return None

    def update_link(self, link_id: str, updates: dict) -> Optional[dict]:
        """Update a payment link"""
        link = self._links.get(link_id)
        if not link or link["status"] != "active":
            return None

        for key, value in updates.items():
            if key in link and key not in ["id", "code", "url", "created_at", "status"]:
                link[key] = value

        return link

    def get_checkout_data(self, code: str) -> Optional[dict]:
        """Get data needed for checkout page (public)"""
        link = self.get_link_by_code(code)
        if not link:
            return None

        # Check if expired
        if link["expires_at"] < utc_now().isoformat():
            link["status"] = "expired"

        # Return only public data
        return {
            "code": link["code"],
            "status": link["status"],
            "amount": link["amount"],
            "currency": link["currency"],
            "description": link["description"],
            "invoice_number": link["invoice_number"],
            "client_name": link["client_name"],
            "gateways": link["gateways"],
            "allow_partial": link["allow_partial"],
            "minimum_amount": link["minimum_amount"],
            "expires_at": link["expires_at"],
            "paid_at": link["paid_at"],
            "paid_amount": link["paid_amount"]
        }

    def get_statistics(self) -> dict:
        """Get payment link statistics"""
        links = list(self._links.values())

        total = len(links)
        active = len([l for l in links if l["status"] == "active"])
        paid = len([l for l in links if l["status"] == "paid"])
        expired = len([l for l in links if l["status"] == "expired"])
        cancelled = len([l for l in links if l["status"] == "cancelled"])

        total_collected = sum(l.get("paid_amount", 0) or 0 for l in links if l["status"] == "paid")
        total_fees = sum(l.get("fee_amount", 0) or 0 for l in links if l["status"] == "paid")
        total_views = sum(l.get("views", 0) for l in links)
        total_attempts = sum(l.get("attempts", 0) for l in links)

        conversion_rate = (paid / total * 100) if total > 0 else 0

        return {
            "total_links": total,
            "by_status": {
                "active": active,
                "paid": paid,
                "expired": expired,
                "cancelled": cancelled
            },
            "total_collected": round(total_collected, 2),
            "total_fees": round(total_fees, 2),
            "net_collected": round(total_collected - total_fees, 2),
            "total_views": total_views,
            "total_attempts": total_attempts,
            "conversion_rate": round(conversion_rate, 1)
        }


payment_link_service = PaymentLinkService()
