"""
QuickBooks Online Integration Client
Handles QuickBooks API communication
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
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
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


@register_integration
class QuickBooksIntegration(BaseIntegration):
    """QuickBooks Online integration."""

    PROVIDER_ID = "quickbooks"
    PROVIDER_NAME = "QuickBooks Online"
    DESCRIPTION = "Sync customers, invoices, and payments with QuickBooks"
    CATEGORY = IntegrationCategory.ACCOUNTING
    ICON_URL = "/icons/integrations/quickbooks.svg"
    DOCS_URL = "https://developer.intuit.com/app/developer/qbo/docs"

    CAPABILITIES = [
        IntegrationCapability.OAUTH,
        IntegrationCapability.WEBHOOKS,
        IntegrationCapability.SYNC,
    ]

    # OAuth URLs
    OAUTH_AUTHORIZE_URL = "https://appcenter.intuit.com/connect/oauth2"
    OAUTH_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    OAUTH_SCOPES = ["com.intuit.quickbooks.accounting"]

    # API URLs
    SANDBOX_URL = "https://sandbox-quickbooks.api.intuit.com/v3/company"
    PRODUCTION_URL = "https://quickbooks.api.intuit.com/v3/company"

    def __init__(self, credentials: Dict[str, Any] = None):
        super().__init__(credentials)
        self._access_token = None
        self._refresh_token = None
        self._realm_id = None
        self._token_expires_at = None
        self._sandbox = True

    @property
    def api_base(self) -> str:
        base = self.SANDBOX_URL if self._sandbox else self.PRODUCTION_URL
        return f"{base}/{self._realm_id}"

    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth authorization URL."""
        params = {
            "client_id": self.credentials.get("client_id"),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.OAUTH_SCOPES),
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.OAUTH_AUTHORIZE_URL}?{query}"

    async def handle_oauth_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for tokens."""
        # In production: exchange code for tokens
        # Demo response
        return {
            "access_token": f"qb_access_{utc_now().timestamp()}",
            "refresh_token": f"qb_refresh_{utc_now().timestamp()}",
            "expires_in": 3600,
            "realm_id": "123456789",
        }

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Connect to QuickBooks."""
        self._access_token = credentials.get("access_token")
        self._refresh_token = credentials.get("refresh_token")
        self._realm_id = credentials.get("realm_id")
        self._sandbox = credentials.get("sandbox", True)
        self.credentials = credentials

        if self._access_token and self._realm_id:
            if await self.test_connection():
                self._set_status(IntegrationStatus.CONNECTED)
                return True

        self._set_status(IntegrationStatus.ERROR, "Invalid credentials")
        return False

    async def disconnect(self) -> bool:
        """Disconnect from QuickBooks."""
        # Revoke token if needed
        self._access_token = None
        self._refresh_token = None
        self._realm_id = None
        self.credentials = {}
        self._set_status(IntegrationStatus.DISCONNECTED)
        return True

    async def test_connection(self) -> bool:
        """Test QuickBooks connection."""
        try:
            # In production: await self._request("GET", "/companyinfo/{realm_id}")
            return bool(self._access_token and self._realm_id)
        except Exception as e:
            self._log_error(f"Connection test failed: {e}")
            return False

    async def refresh_credentials(self) -> Dict[str, Any]:
        """Refresh OAuth tokens."""
        if not self._refresh_token:
            return self.credentials

        # In production: make token refresh request
        # Demo response
        new_credentials = {
            **self.credentials,
            "access_token": f"qb_access_{utc_now().timestamp()}",
            "token_refreshed_at": utc_now().isoformat(),
        }

        self._access_token = new_credentials["access_token"]
        self.credentials = new_credentials

        return new_credentials

    # ==================== Customer Methods ====================

    async def create_customer(self, data: Dict) -> Dict:
        """Create a QuickBooks customer."""
        customer_data = {
            "DisplayName": data.get("name"),
            "PrimaryEmailAddr": {"Address": data.get("email")},
            "CompanyName": data.get("company_name"),
        }

        if data.get("phone"):
            customer_data["PrimaryPhone"] = {"FreeFormNumber": data["phone"]}

        if data.get("address"):
            addr = data["address"]
            customer_data["BillAddr"] = {
                "Line1": addr.get("line1"),
                "City": addr.get("city"),
                "CountrySubDivisionCode": addr.get("state"),
                "PostalCode": addr.get("postal_code"),
                "Country": addr.get("country"),
            }

        # Demo response
        return {
            "Customer": {
                "Id": f"qb_cust_{utc_now().timestamp()}",
                "DisplayName": data.get("name"),
                "PrimaryEmailAddr": {"Address": data.get("email")},
                "SyncToken": "0",
            }
        }

    async def get_customer(self, customer_id: str) -> Dict:
        """Get customer by ID."""
        return {
            "Customer": {
                "Id": customer_id,
                "DisplayName": "Sample Customer",
                "PrimaryEmailAddr": {"Address": "customer@example.com"},
            }
        }

    async def update_customer(self, customer_id: str, sync_token: str, data: Dict) -> Dict:
        """Update a customer."""
        return await self.create_customer({**data, "Id": customer_id, "SyncToken": sync_token})

    async def query_customers(self, query: str = None, max_results: int = 100) -> List[Dict]:
        """Query customers."""
        # Demo response
        return {
            "QueryResponse": {
                "Customer": [
                    {"Id": "1", "DisplayName": "Customer 1", "PrimaryEmailAddr": {"Address": "c1@example.com"}},
                    {"Id": "2", "DisplayName": "Customer 2", "PrimaryEmailAddr": {"Address": "c2@example.com"}},
                ],
                "maxResults": 2,
            }
        }

    # ==================== Invoice Methods ====================

    async def create_invoice(self, customer_id: str, line_items: List[Dict], due_date: str = None) -> Dict:
        """Create a QuickBooks invoice."""
        invoice_data = {
            "CustomerRef": {"value": customer_id},
            "Line": [
                {
                    "Amount": item.get("amount"),
                    "Description": item.get("description"),
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {
                        "Qty": item.get("quantity", 1),
                        "UnitPrice": item.get("unit_price"),
                    },
                }
                for item in line_items
            ],
        }

        if due_date:
            invoice_data["DueDate"] = due_date

        # Demo response
        total = sum(item.get("amount", 0) for item in line_items)
        return {
            "Invoice": {
                "Id": f"qb_inv_{utc_now().timestamp()}",
                "DocNumber": f"INV-{int(utc_now().timestamp())}",
                "CustomerRef": {"value": customer_id},
                "TotalAmt": total,
                "Balance": total,
                "SyncToken": "0",
            }
        }

    async def get_invoice(self, invoice_id: str) -> Dict:
        """Get invoice by ID."""
        return {
            "Invoice": {
                "Id": invoice_id,
                "DocNumber": "INV-001",
                "TotalAmt": 1000.00,
                "Balance": 1000.00,
            }
        }

    async def query_invoices(self, query: str = None, max_results: int = 100) -> Dict:
        """Query invoices."""
        return {
            "QueryResponse": {
                "Invoice": [],
                "maxResults": 0,
            }
        }

    # ==================== Payment Methods ====================

    async def create_payment(self, customer_id: str, amount: float, invoice_id: str = None) -> Dict:
        """Record a payment."""
        payment_data = {
            "CustomerRef": {"value": customer_id},
            "TotalAmt": amount,
        }

        if invoice_id:
            payment_data["Line"] = [{
                "Amount": amount,
                "LinkedTxn": [{"TxnId": invoice_id, "TxnType": "Invoice"}],
            }]

        return {
            "Payment": {
                "Id": f"qb_pmt_{utc_now().timestamp()}",
                "CustomerRef": {"value": customer_id},
                "TotalAmt": amount,
                "SyncToken": "0",
            }
        }

    # ==================== Sync Methods ====================

    async def sync(self, entity_type: str, direction: str = "pull") -> SyncResult:
        """Sync data with QuickBooks."""
        result = SyncResult(entity_type, direction)

        try:
            if direction == "pull":
                if entity_type == "customers":
                    await self._pull_customers(result)
                elif entity_type == "invoices":
                    await self._pull_invoices(result)
                elif entity_type == "payments":
                    await self._pull_payments(result)
            elif direction == "push":
                if entity_type == "customers":
                    await self._push_customers(result)
                elif entity_type == "invoices":
                    await self._push_invoices(result)

            result.complete()
            self._update_last_sync()

        except Exception as e:
            result.errors.append(str(e))
            result.complete()

        return result

    async def _pull_customers(self, result: SyncResult):
        """Pull customers from QuickBooks."""
        response = await self.query_customers()
        customers = response.get("QueryResponse", {}).get("Customer", [])

        for qb_customer in customers:
            # In production: create/update local customer
            result.updated += 1

        logger.info(f"[QuickBooks] Pulled {len(customers)} customers")

    async def _pull_invoices(self, result: SyncResult):
        """Pull invoices from QuickBooks."""
        response = await self.query_invoices()
        invoices = response.get("QueryResponse", {}).get("Invoice", [])

        for qb_invoice in invoices:
            result.updated += 1

        logger.info(f"[QuickBooks] Pulled {len(invoices)} invoices")

    async def _pull_payments(self, result: SyncResult):
        """Pull payments from QuickBooks."""
        result.updated += 0

    async def _push_customers(self, result: SyncResult):
        """Push customers to QuickBooks."""
        # In production: get local customers and push to QB
        result.created += 0

    async def _push_invoices(self, result: SyncResult):
        """Push invoices to QuickBooks."""
        result.created += 0

    # ==================== API Helper ====================

    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to QuickBooks."""
        import aiohttp

        url = f"{self.api_base}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=data) as response:
                result = await response.json()

                if response.status >= 400:
                    fault = result.get("Fault", {})
                    error = fault.get("Error", [{}])[0]
                    raise IntegrationError(
                        message=error.get("Message", "Unknown error"),
                        provider=self.PROVIDER_ID,
                        code=error.get("code"),
                        details=result,
                    )

                return result
