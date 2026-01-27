"""
Stripe Integration Client
Handles Stripe API communication
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.integrations.base import (
    BaseIntegration,
    IntegrationCategory,
    IntegrationCapability,
    IntegrationStatus,
    IntegrationError,
    SyncResult,
)
from app.integrations.registry import register_integration

logger = logging.getLogger(__name__)


@register_integration
class StripeIntegration(BaseIntegration):
    """Stripe payment gateway integration."""

    PROVIDER_ID = "stripe"
    PROVIDER_NAME = "Stripe"
    DESCRIPTION = "Accept credit cards, ACH, and SEPA payments"
    CATEGORY = IntegrationCategory.PAYMENTS
    ICON_URL = "/icons/integrations/stripe.svg"
    DOCS_URL = "https://stripe.com/docs"

    CAPABILITIES = [
        IntegrationCapability.API_KEY,
        IntegrationCapability.WEBHOOKS,
        IntegrationCapability.SYNC,
    ]

    # Stripe API base URL
    API_BASE = "https://api.stripe.com/v1"

    def __init__(self, credentials: Dict[str, Any] = None):
        super().__init__(credentials)
        self._api_key = None
        self._webhook_secret = None

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Connect to Stripe."""
        self._validate_credentials(["api_key"])

        self._api_key = credentials.get("api_key")
        self._webhook_secret = credentials.get("webhook_secret")
        self.credentials = credentials

        # Test connection
        if await self.test_connection():
            self._set_status(IntegrationStatus.CONNECTED)
            return True

        self._set_status(IntegrationStatus.ERROR, "Failed to connect to Stripe")
        return False

    async def disconnect(self) -> bool:
        """Disconnect from Stripe."""
        self._api_key = None
        self._webhook_secret = None
        self.credentials = {}
        self._set_status(IntegrationStatus.DISCONNECTED)
        return True

    async def test_connection(self) -> bool:
        """Test Stripe connection."""
        try:
            # In production, make actual API call
            # response = await self._request("GET", "/account")
            # return response.get("id") is not None

            # Demo mode
            if self._api_key and self._api_key.startswith("sk_"):
                return True
            return False

        except Exception as e:
            self._log_error(f"Connection test failed: {e}")
            return False

    async def refresh_credentials(self) -> Dict[str, Any]:
        """Stripe uses API keys, no refresh needed."""
        return self.credentials

    # ==================== Payment Methods ====================

    async def create_payment_intent(self, amount: int, currency: str, customer_id: str = None, metadata: Dict = None) -> Dict:
        """Create a payment intent."""
        data = {
            "amount": amount,
            "currency": currency.lower(),
            "automatic_payment_methods": {"enabled": True},
        }

        if customer_id:
            data["customer"] = customer_id
        if metadata:
            data["metadata"] = metadata

        # In production: return await self._request("POST", "/payment_intents", data)

        # Demo response
        return {
            "id": f"pi_{datetime.utcnow().timestamp()}",
            "client_secret": f"pi_secret_{datetime.utcnow().timestamp()}",
            "amount": amount,
            "currency": currency,
            "status": "requires_payment_method",
        }

    async def create_payment_link(self, invoice_id: str, amount: int, currency: str, description: str) -> Dict:
        """Create a payment link for invoice."""
        # Create price
        price_data = {
            "unit_amount": amount,
            "currency": currency.lower(),
            "product_data": {"name": description},
        }

        # Demo response
        return {
            "id": f"plink_{datetime.utcnow().timestamp()}",
            "url": f"https://pay.stripe.com/test_{invoice_id}",
            "active": True,
            "metadata": {"invoice_id": invoice_id},
        }

    async def get_payment(self, payment_intent_id: str) -> Dict:
        """Get payment intent details."""
        # In production: return await self._request("GET", f"/payment_intents/{payment_intent_id}")

        return {
            "id": payment_intent_id,
            "amount": 10000,
            "currency": "usd",
            "status": "succeeded",
        }

    async def refund_payment(self, payment_intent_id: str, amount: int = None, reason: str = None) -> Dict:
        """Refund a payment."""
        data = {"payment_intent": payment_intent_id}
        if amount:
            data["amount"] = amount
        if reason:
            data["reason"] = reason

        # Demo response
        return {
            "id": f"re_{datetime.utcnow().timestamp()}",
            "payment_intent": payment_intent_id,
            "amount": amount or 10000,
            "status": "succeeded",
        }

    # ==================== Customer Methods ====================

    async def create_customer(self, email: str, name: str = None, metadata: Dict = None) -> Dict:
        """Create a Stripe customer."""
        data = {"email": email}
        if name:
            data["name"] = name
        if metadata:
            data["metadata"] = metadata

        # Demo response
        return {
            "id": f"cus_{datetime.utcnow().timestamp()}",
            "email": email,
            "name": name,
            "created": int(datetime.utcnow().timestamp()),
        }

    async def get_customer(self, customer_id: str) -> Dict:
        """Get customer details."""
        return {
            "id": customer_id,
            "email": "customer@example.com",
            "name": "Test Customer",
        }

    async def update_customer(self, customer_id: str, data: Dict) -> Dict:
        """Update customer details."""
        return {"id": customer_id, **data}

    async def list_customers(self, limit: int = 100, starting_after: str = None) -> Dict:
        """List customers."""
        return {
            "data": [],
            "has_more": False,
        }

    # ==================== Invoice Methods ====================

    async def create_invoice(self, customer_id: str, items: List[Dict], metadata: Dict = None) -> Dict:
        """Create a Stripe invoice."""
        return {
            "id": f"in_{datetime.utcnow().timestamp()}",
            "customer": customer_id,
            "status": "draft",
            "total": sum(item.get("amount", 0) for item in items),
        }

    async def finalize_invoice(self, invoice_id: str) -> Dict:
        """Finalize and send invoice."""
        return {
            "id": invoice_id,
            "status": "open",
            "hosted_invoice_url": f"https://invoice.stripe.com/{invoice_id}",
        }

    # ==================== Sync Methods ====================

    async def sync(self, entity_type: str, direction: str = "pull") -> SyncResult:
        """Sync data with Stripe."""
        result = SyncResult(entity_type, direction)

        try:
            if entity_type == "customers" and direction == "pull":
                await self._sync_customers_from_stripe(result)
            elif entity_type == "payments" and direction == "pull":
                await self._sync_payments_from_stripe(result)

            result.complete()

        except Exception as e:
            result.errors.append(str(e))
            result.complete()

        return result

    async def _sync_customers_from_stripe(self, result: SyncResult):
        """Pull customers from Stripe."""
        customers = await self.list_customers()

        for customer in customers.get("data", []):
            # In production: create/update local customer
            result.updated += 1

    async def _sync_payments_from_stripe(self, result: SyncResult):
        """Pull payments from Stripe."""
        # In production: fetch and sync payment intents
        result.updated += 0

    # ==================== API Helper ====================

    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to Stripe."""
        import aiohttp

        url = f"{self.API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, data=data) as response:
                result = await response.json()

                if response.status >= 400:
                    raise IntegrationError(
                        message=result.get("error", {}).get("message", "Unknown error"),
                        provider=self.PROVIDER_ID,
                        code=result.get("error", {}).get("code"),
                        details=result,
                    )

                return result
