"""
Quote/Proposal Management Service
Handles quote creation, approval, and conversion to invoice
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4
from decimal import Decimal

from app.models.crm_store import crm_store


class QuoteService:
    """
    Service for managing sales quotes/proposals
    """

    # Quote statuses
    QUOTE_STATUSES = [
        "draft",
        "pending_approval",
        "approved",
        "sent",
        "viewed",
        "accepted",
        "rejected",
        "expired",
        "converted",
    ]

    def __init__(self):
        self._quotes = {}
        self._quote_items = {}
        self._quote_counter = 1000

    def create_quote(
        self,
        tenant_id: str,
        created_by: str,
        opportunity_id: str = None,
        contact_id: str = None,
        company_id: str = None,
        valid_days: int = 30,
        currency: str = "USD",
        terms: str = None,
        notes: str = None,
        **kwargs
    ) -> dict:
        """Create a new quote"""
        quote_id = str(uuid4())
        self._quote_counter += 1
        quote_number = f"QT-{self._quote_counter:05d}"

        quote = {
            "id": quote_id,
            "tenant_id": tenant_id,
            "quote_number": quote_number,
            "opportunity_id": opportunity_id,
            "contact_id": contact_id,
            "company_id": company_id,
            "status": "draft",
            "valid_until": (datetime.utcnow() + timedelta(days=valid_days)).isoformat(),
            "currency": currency,
            "subtotal": 0,
            "discount_percent": 0,
            "discount_amount": 0,
            "tax_percent": 0,
            "tax_amount": 0,
            "total": 0,
            "terms": terms,
            "notes": notes,
            "items": [],
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **kwargs,
        }

        self._quotes[quote_id] = quote
        return quote

    def update_quote(self, quote_id: str, user_id: str, **updates) -> dict:
        """Update quote"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        if quote["status"] not in ["draft", "pending_approval"]:
            raise ValueError(f"Cannot edit quote in status: {quote['status']}")

        updates["updated_at"] = datetime.utcnow().isoformat()
        quote.update(updates)

        return quote

    def get_quote(self, quote_id: str) -> dict:
        """Get quote with items"""
        quote = self._quotes.get(quote_id)
        if not quote:
            return None

        # Enrich with related data
        if quote.get("contact_id"):
            quote["contact"] = crm_store.get_contact(quote["contact_id"])
        if quote.get("company_id"):
            quote["company"] = crm_store.get_company(quote["company_id"])
        if quote.get("opportunity_id"):
            quote["opportunity"] = crm_store.get_opportunity(quote["opportunity_id"])

        return quote

    def delete_quote(self, quote_id: str, user_id: str):
        """Delete quote (only drafts)"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        if quote["status"] != "draft":
            raise ValueError("Can only delete draft quotes")

        del self._quotes[quote_id]

    def list_quotes(
        self,
        tenant_id: str,
        status: str = None,
        opportunity_id: str = None,
        company_id: str = None,
        created_by: str = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """List quotes with filters"""
        quotes = [q for q in self._quotes.values() if q.get("tenant_id") == tenant_id]

        if status:
            quotes = [q for q in quotes if q.get("status") == status]
        if opportunity_id:
            quotes = [q for q in quotes if q.get("opportunity_id") == opportunity_id]
        if company_id:
            quotes = [q for q in quotes if q.get("company_id") == company_id]
        if created_by:
            quotes = [q for q in quotes if q.get("created_by") == created_by]

        total = len(quotes)
        quotes = sorted(quotes, key=lambda x: x.get("created_at", ""), reverse=True)

        skip = (page - 1) * page_size
        quotes = quotes[skip:skip + page_size]

        return {
            "items": quotes,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    # ==========================================
    # LINE ITEMS
    # ==========================================

    def add_item(
        self,
        quote_id: str,
        description: str,
        quantity: float,
        unit_price: float,
        product_id: str = None,
        discount_percent: float = 0,
    ) -> dict:
        """Add line item to quote"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        if quote["status"] not in ["draft", "pending_approval"]:
            raise ValueError("Cannot modify items for this quote")

        item_id = str(uuid4())
        line_total = quantity * unit_price * (1 - discount_percent / 100)

        item = {
            "id": item_id,
            "quote_id": quote_id,
            "product_id": product_id,
            "description": description,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_percent": discount_percent,
            "total": round(line_total, 2),
            "position": len(quote["items"]) + 1,
        }

        quote["items"].append(item)
        self._recalculate_totals(quote_id)

        return item

    def update_item(self, quote_id: str, item_id: str, **updates) -> dict:
        """Update line item"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        item = next((i for i in quote["items"] if i["id"] == item_id), None)
        if not item:
            raise ValueError(f"Item not found: {item_id}")

        item.update(updates)

        # Recalculate line total
        item["total"] = round(
            item["quantity"] * item["unit_price"] * (1 - item.get("discount_percent", 0) / 100),
            2
        )

        self._recalculate_totals(quote_id)
        return item

    def remove_item(self, quote_id: str, item_id: str):
        """Remove line item"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        quote["items"] = [i for i in quote["items"] if i["id"] != item_id]

        # Reorder positions
        for i, item in enumerate(quote["items"]):
            item["position"] = i + 1

        self._recalculate_totals(quote_id)

    def _recalculate_totals(self, quote_id: str):
        """Recalculate quote totals"""
        quote = self._quotes.get(quote_id)
        if not quote:
            return

        subtotal = sum(item["total"] for item in quote["items"])

        # Apply quote-level discount
        discount_amount = subtotal * (quote.get("discount_percent", 0) / 100)
        after_discount = subtotal - discount_amount

        # Calculate tax
        tax_amount = after_discount * (quote.get("tax_percent", 0) / 100)

        total = after_discount + tax_amount

        quote["subtotal"] = round(subtotal, 2)
        quote["discount_amount"] = round(discount_amount, 2)
        quote["tax_amount"] = round(tax_amount, 2)
        quote["total"] = round(total, 2)
        quote["updated_at"] = datetime.utcnow().isoformat()

    # ==========================================
    # WORKFLOW
    # ==========================================

    def submit_for_approval(self, quote_id: str, user_id: str) -> dict:
        """Submit quote for approval"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        if quote["status"] != "draft":
            raise ValueError("Only draft quotes can be submitted")

        if not quote["items"]:
            raise ValueError("Quote must have at least one item")

        quote["status"] = "pending_approval"
        quote["submitted_at"] = datetime.utcnow().isoformat()
        quote["submitted_by"] = user_id
        quote["updated_at"] = datetime.utcnow().isoformat()

        return quote

    def approve_quote(self, quote_id: str, user_id: str) -> dict:
        """Approve quote"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        if quote["status"] != "pending_approval":
            raise ValueError("Quote is not pending approval")

        quote["status"] = "approved"
        quote["approved_at"] = datetime.utcnow().isoformat()
        quote["approved_by"] = user_id
        quote["updated_at"] = datetime.utcnow().isoformat()

        return quote

    def reject_quote(self, quote_id: str, user_id: str, reason: str = None) -> dict:
        """Reject quote"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        quote["status"] = "draft"  # Return to draft for revision
        quote["rejection_reason"] = reason
        quote["rejected_at"] = datetime.utcnow().isoformat()
        quote["rejected_by"] = user_id
        quote["updated_at"] = datetime.utcnow().isoformat()

        return quote

    def send_quote(self, quote_id: str, user_id: str, email: str = None) -> dict:
        """Mark quote as sent"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        if quote["status"] not in ["approved", "sent"]:
            raise ValueError("Quote must be approved before sending")

        quote["status"] = "sent"
        quote["sent_at"] = datetime.utcnow().isoformat()
        quote["sent_by"] = user_id
        quote["sent_to_email"] = email
        quote["updated_at"] = datetime.utcnow().isoformat()

        return quote

    def mark_viewed(self, quote_id: str) -> dict:
        """Mark quote as viewed by customer"""
        quote = self._quotes.get(quote_id)
        if not quote:
            return None

        if quote["status"] == "sent":
            quote["status"] = "viewed"

        quote["viewed_at"] = datetime.utcnow().isoformat()
        quote["view_count"] = quote.get("view_count", 0) + 1

        return quote

    def accept_quote(self, quote_id: str, signature: str = None) -> dict:
        """Accept quote (customer action)"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        if quote["status"] not in ["sent", "viewed"]:
            raise ValueError("Quote cannot be accepted in current status")

        # Check expiry
        if quote.get("valid_until"):
            if datetime.fromisoformat(quote["valid_until"]) < datetime.utcnow():
                quote["status"] = "expired"
                raise ValueError("Quote has expired")

        quote["status"] = "accepted"
        quote["accepted_at"] = datetime.utcnow().isoformat()
        quote["customer_signature"] = signature
        quote["updated_at"] = datetime.utcnow().isoformat()

        # Update opportunity if linked
        if quote.get("opportunity_id"):
            crm_store.update_opportunity(quote["opportunity_id"], {
                "status": "won",
                "actual_close_date": datetime.utcnow().isoformat(),
            })

        return quote

    def decline_quote(self, quote_id: str, reason: str = None) -> dict:
        """Decline quote (customer action)"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        quote["status"] = "rejected"
        quote["declined_at"] = datetime.utcnow().isoformat()
        quote["decline_reason"] = reason
        quote["updated_at"] = datetime.utcnow().isoformat()

        return quote

    # ==========================================
    # CONVERSION
    # ==========================================

    def convert_to_invoice(self, quote_id: str, user_id: str) -> dict:
        """Convert accepted quote to invoice"""
        quote = self._quotes.get(quote_id)
        if not quote:
            raise ValueError(f"Quote not found: {quote_id}")

        if quote["status"] != "accepted":
            raise ValueError("Only accepted quotes can be converted to invoice")

        # Get client
        client_id = None
        if quote.get("company_id"):
            company = crm_store.get_company(quote["company_id"])
            client_id = company.get("linked_client_id") if company else None

        # Create invoice data (to be processed by invoice service)
        invoice_data = {
            "client_id": client_id,
            "quote_id": quote_id,
            "currency": quote["currency"],
            "subtotal": quote["subtotal"],
            "discount": quote["discount_amount"],
            "tax": quote["tax_amount"],
            "total": quote["total"],
            "items": [
                {
                    "description": item["description"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "total": item["total"],
                }
                for item in quote["items"]
            ],
            "status": "pending",
            "created_by": user_id,
        }

        # Update quote
        quote["status"] = "converted"
        quote["converted_at"] = datetime.utcnow().isoformat()
        quote["converted_by"] = user_id
        quote["updated_at"] = datetime.utcnow().isoformat()

        return {
            "quote": quote,
            "invoice_data": invoice_data,
        }

    def duplicate_quote(self, quote_id: str, user_id: str) -> dict:
        """Duplicate a quote"""
        original = self._quotes.get(quote_id)
        if not original:
            raise ValueError(f"Quote not found: {quote_id}")

        new_quote = self.create_quote(
            tenant_id=original["tenant_id"],
            created_by=user_id,
            opportunity_id=original.get("opportunity_id"),
            contact_id=original.get("contact_id"),
            company_id=original.get("company_id"),
            currency=original["currency"],
            terms=original.get("terms"),
            notes=original.get("notes"),
            discount_percent=original.get("discount_percent", 0),
            tax_percent=original.get("tax_percent", 0),
        )

        # Copy items
        for item in original["items"]:
            self.add_item(
                quote_id=new_quote["id"],
                description=item["description"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                product_id=item.get("product_id"),
                discount_percent=item.get("discount_percent", 0),
            )

        return new_quote


# Service instance
quote_service = QuoteService()
