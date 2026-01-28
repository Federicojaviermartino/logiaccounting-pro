"""
PayPal Integration Client
Handles PayPal API communication
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import base64

from app.integrations.base import (
    BaseIntegration,
    IntegrationCategory,
    IntegrationCapability,
    IntegrationStatus,
    IntegrationError,
    SyncResult,
)
from app.integrations.registry import register_integration
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


@register_integration
class PayPalIntegration(BaseIntegration):
    """PayPal payment gateway integration."""

    PROVIDER_ID = "paypal"
    PROVIDER_NAME = "PayPal"
    DESCRIPTION = "Accept PayPal and credit card payments"
    CATEGORY = IntegrationCategory.PAYMENTS
    ICON_URL = "/icons/integrations/paypal.svg"
    DOCS_URL = "https://developer.paypal.com/docs"

    CAPABILITIES = [
        IntegrationCapability.OAUTH,
        IntegrationCapability.WEBHOOKS,
    ]

    # PayPal API URLs
    SANDBOX_URL = "https://api-m.sandbox.paypal.com"
    LIVE_URL = "https://api-m.paypal.com"

    # OAuth URLs
    OAUTH_AUTHORIZE_URL = "https://www.paypal.com/signin/authorize"
    OAUTH_TOKEN_URL = "https://api-m.paypal.com/v1/oauth2/token"

    def __init__(self, credentials: Dict[str, Any] = None):
        super().__init__(credentials)
        self._client_id = None
        self._client_secret = None
        self._access_token = None
        self._token_expires_at = None
        self._sandbox = True

    @property
    def api_base(self) -> str:
        return self.SANDBOX_URL if self._sandbox else self.LIVE_URL

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Connect to PayPal."""
        self._validate_credentials(["client_id", "client_secret"])

        self._client_id = credentials.get("client_id")
        self._client_secret = credentials.get("client_secret")
        self._sandbox = credentials.get("sandbox", True)
        self.credentials = credentials

        # Get access token
        if await self._get_access_token():
            self._set_status(IntegrationStatus.CONNECTED)
            return True

        self._set_status(IntegrationStatus.ERROR, "Failed to authenticate with PayPal")
        return False

    async def disconnect(self) -> bool:
        """Disconnect from PayPal."""
        self._client_id = None
        self._client_secret = None
        self._access_token = None
        self.credentials = {}
        self._set_status(IntegrationStatus.DISCONNECTED)
        return True

    async def test_connection(self) -> bool:
        """Test PayPal connection."""
        try:
            if not self._access_token:
                await self._get_access_token()
            return self._access_token is not None
        except Exception as e:
            self._log_error(f"Connection test failed: {e}")
            return False

    async def refresh_credentials(self) -> Dict[str, Any]:
        """Refresh access token."""
        if await self._get_access_token():
            return {
                **self.credentials,
                "access_token": self._access_token,
            }
        return self.credentials

    async def _get_access_token(self) -> bool:
        """Get PayPal access token."""
        try:
            # In production, make actual OAuth request
            # auth = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode()
            # response = await self._request_token(auth)

            # Demo mode
            if self._client_id and self._client_secret:
                self._access_token = f"A21AADemo_{utc_now().timestamp()}"
                self._token_expires_at = utc_now()
                return True

            return False

        except Exception as e:
            self._log_error(f"Failed to get access token: {e}")
            return False

    # ==================== Order Methods ====================

    async def create_order(self, amount: str, currency: str, description: str, invoice_id: str = None) -> Dict:
        """Create a PayPal order."""
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency.upper(),
                    "value": amount,
                },
                "description": description,
            }],
        }

        if invoice_id:
            order_data["purchase_units"][0]["invoice_id"] = invoice_id

        # Demo response
        return {
            "id": f"ORDER-{utc_now().timestamp()}",
            "status": "CREATED",
            "links": [
                {
                    "href": f"https://www.sandbox.paypal.com/checkoutnow?token=ORDER-{utc_now().timestamp()}",
                    "rel": "approve",
                    "method": "GET",
                },
            ],
        }

    async def capture_order(self, order_id: str) -> Dict:
        """Capture payment for an order."""
        # Demo response
        return {
            "id": order_id,
            "status": "COMPLETED",
            "purchase_units": [{
                "payments": {
                    "captures": [{
                        "id": f"CAPTURE-{utc_now().timestamp()}",
                        "status": "COMPLETED",
                        "amount": {"currency_code": "USD", "value": "100.00"},
                    }],
                },
            }],
        }

    async def get_order(self, order_id: str) -> Dict:
        """Get order details."""
        return {
            "id": order_id,
            "status": "APPROVED",
        }

    async def refund_capture(self, capture_id: str, amount: str = None, currency: str = "USD") -> Dict:
        """Refund a captured payment."""
        refund_data = {}
        if amount:
            refund_data["amount"] = {
                "currency_code": currency.upper(),
                "value": amount,
            }

        return {
            "id": f"REFUND-{utc_now().timestamp()}",
            "status": "COMPLETED",
            "amount": {"currency_code": currency, "value": amount or "100.00"},
        }

    # ==================== Invoice Methods ====================

    async def create_invoice(self, recipient_email: str, items: List[Dict], due_date: str = None) -> Dict:
        """Create a PayPal invoice."""
        total = sum(float(item.get("amount", 0)) * int(item.get("quantity", 1)) for item in items)

        return {
            "id": f"INV2-{utc_now().timestamp()}",
            "status": "DRAFT",
            "detail": {
                "invoice_number": f"INV-{int(utc_now().timestamp())}",
                "currency_code": "USD",
            },
            "amount": {"value": str(total)},
        }

    async def send_invoice(self, invoice_id: str) -> Dict:
        """Send invoice to recipient."""
        return {
            "href": f"https://www.paypal.com/invoice/payerView/details/{invoice_id}",
        }

    # ==================== Sync Methods ====================

    async def sync(self, entity_type: str, direction: str = "pull") -> SyncResult:
        """Sync data with PayPal."""
        result = SyncResult(entity_type, direction)

        try:
            if entity_type == "payments" and direction == "pull":
                await self._sync_transactions(result)

            result.complete()

        except Exception as e:
            result.errors.append(str(e))
            result.complete()

        return result

    async def _sync_transactions(self, result: SyncResult):
        """Sync transactions from PayPal."""
        # In production: fetch transaction history
        result.updated += 0

    # ==================== API Helper ====================

    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to PayPal."""
        import aiohttp

        url = f"{self.api_base}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=data) as response:
                result = await response.json()

                if response.status >= 400:
                    raise IntegrationError(
                        message=result.get("message", "Unknown error"),
                        provider=self.PROVIDER_ID,
                        code=result.get("name"),
                        details=result,
                    )

                return result
