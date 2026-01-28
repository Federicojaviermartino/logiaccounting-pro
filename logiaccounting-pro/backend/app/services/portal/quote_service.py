"""
Portal Quote Service
Customer quote management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from app.models.crm_store import crm_store
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class PortalQuoteService:
    """Customer quote management service."""

    def __init__(self):
        self._signatures: Dict[str, Dict] = {}

    def list_quotes(self, customer_id: str, status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """List customer quotes."""
        quotes = crm_store.list_quotes_for_company(customer_id)

        if status:
            quotes = [q for q in quotes if q.get("status") == status]

        quotes.sort(key=lambda q: q.get("created_at", ""), reverse=True)

        total = len(quotes)
        skip = (page - 1) * page_size
        quotes = quotes[skip:skip + page_size]

        return {"items": [self._quote_to_dict(q) for q in quotes], "total": total, "page": page, "page_size": page_size}

    def get_quote(self, quote_id: str, customer_id: str) -> Optional[Dict]:
        """Get quote detail."""
        quote = crm_store.get_quote(quote_id)
        if not quote or quote.get("company_id") != customer_id:
            return None
        return self._quote_to_dict(quote, include_items=True)

    def accept_quote(self, quote_id: str, customer_id: str, signature_data: str = None, acceptance_notes: str = None) -> Dict:
        """Accept a quote."""
        quote = crm_store.get_quote(quote_id)
        if not quote or quote.get("company_id") != customer_id:
            raise ValueError("Quote not found")

        if quote.get("status") != "sent":
            raise ValueError("Quote cannot be accepted in current status")

        valid_until = quote.get("valid_until")
        if valid_until:
            expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            if expiry < utc_now():
                raise ValueError("Quote has expired")

        crm_store.update_quote(quote_id, {
            "status": "accepted",
            "accepted_at": utc_now().isoformat(),
            "acceptance_notes": acceptance_notes,
        })

        if signature_data:
            self._signatures[quote_id] = {
                "quote_id": quote_id,
                "customer_id": customer_id,
                "signature_data": signature_data,
                "signed_at": utc_now().isoformat(),
                "ip_address": None,
            }

        logger.info(f"Quote {quote_id} accepted by customer {customer_id}")

        return {"success": True, "status": "accepted", "quote_id": quote_id}

    def decline_quote(self, quote_id: str, customer_id: str, reason: str = None) -> Dict:
        """Decline a quote."""
        quote = crm_store.get_quote(quote_id)
        if not quote or quote.get("company_id") != customer_id:
            raise ValueError("Quote not found")

        if quote.get("status") != "sent":
            raise ValueError("Quote cannot be declined in current status")

        crm_store.update_quote(quote_id, {
            "status": "declined",
            "declined_at": utc_now().isoformat(),
            "decline_reason": reason,
        })

        logger.info(f"Quote {quote_id} declined by customer {customer_id}")

        return {"success": True, "status": "declined", "quote_id": quote_id}

    def request_revision(self, quote_id: str, customer_id: str, revision_notes: str) -> Dict:
        """Request quote revision."""
        quote = crm_store.get_quote(quote_id)
        if not quote or quote.get("company_id") != customer_id:
            raise ValueError("Quote not found")

        crm_store.update_quote(quote_id, {
            "status": "revision_requested",
            "revision_notes": revision_notes,
            "revision_requested_at": utc_now().isoformat(),
        })

        return {"success": True, "status": "revision_requested", "quote_id": quote_id}

    def get_quote_stats(self, customer_id: str) -> Dict[str, Any]:
        """Get quote statistics."""
        quotes = crm_store.list_quotes_for_company(customer_id)

        pending = len([q for q in quotes if q.get("status") == "sent"])
        accepted = len([q for q in quotes if q.get("status") == "accepted"])
        declined = len([q for q in quotes if q.get("status") == "declined"])
        total_value = sum(q.get("total", 0) for q in quotes if q.get("status") == "accepted")

        return {"pending": pending, "accepted": accepted, "declined": declined, "total_accepted_value": total_value}

    def _quote_to_dict(self, quote: Dict, include_items: bool = False) -> Dict:
        result = {
            "id": quote["id"],
            "quote_number": quote.get("quote_number"),
            "subject": quote.get("subject"),
            "status": quote.get("status"),
            "total": quote.get("total", 0),
            "subtotal": quote.get("subtotal", 0),
            "tax": quote.get("tax", 0),
            "discount": quote.get("discount", 0),
            "valid_until": quote.get("valid_until"),
            "created_at": quote.get("created_at"),
            "accepted_at": quote.get("accepted_at"),
            "is_expired": self._is_expired(quote.get("valid_until")),
            "expires_soon": self._expires_soon(quote.get("valid_until")),
        }

        if include_items:
            result["items"] = quote.get("items", [])
            result["terms"] = quote.get("terms")
            result["notes"] = quote.get("notes")

        return result

    def _is_expired(self, valid_until: str) -> bool:
        if not valid_until:
            return False
        try:
            expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            return expiry < utc_now()
        except:
            return False

    def _expires_soon(self, valid_until: str, days: int = 7) -> bool:
        if not valid_until:
            return False
        try:
            expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            return utc_now() < expiry <= utc_now() + timedelta(days=days)
        except:
            return False


portal_quote_service = PortalQuoteService()
