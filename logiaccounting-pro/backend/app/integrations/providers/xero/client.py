"""
Xero Integration Client
Handles Xero API communication
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
class XeroIntegration(BaseIntegration):
    """Xero accounting integration."""

    PROVIDER_ID = "xero"
    PROVIDER_NAME = "Xero"
    DESCRIPTION = "Sync contacts, invoices, and payments with Xero"
    CATEGORY = IntegrationCategory.ACCOUNTING
    ICON_URL = "/icons/integrations/xero.svg"
    DOCS_URL = "https://developer.xero.com/documentation"

    CAPABILITIES = [
        IntegrationCapability.OAUTH,
        IntegrationCapability.WEBHOOKS,
        IntegrationCapability.SYNC,
    ]

    # OAuth URLs
    OAUTH_AUTHORIZE_URL = "https://login.xero.com/identity/connect/authorize"
    OAUTH_TOKEN_URL = "https://identity.xero.com/connect/token"
    OAUTH_SCOPES = ["openid", "profile", "email", "accounting.transactions", "accounting.contacts", "accounting.settings"]

    # API URL
    API_URL = "https://api.xero.com/api.xro/2.0"

    def __init__(self, credentials: Dict[str, Any] = None):
        super().__init__(credentials)
        self._access_token = None
        self._refresh_token = None
        self._tenant_id = None
        self._token_expires_at = None

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
        """Handle OAuth callback."""
        # Demo response
        return {
            "access_token": f"xero_access_{utc_now().timestamp()}",
            "refresh_token": f"xero_refresh_{utc_now().timestamp()}",
            "expires_in": 1800,
            "tenant_id": "xero-tenant-123",
        }

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """Connect to Xero."""
        self._access_token = credentials.get("access_token")
        self._refresh_token = credentials.get("refresh_token")
        self._tenant_id = credentials.get("tenant_id")
        self.credentials = credentials

        if self._access_token and self._tenant_id:
            if await self.test_connection():
                self._set_status(IntegrationStatus.CONNECTED)
                return True

        self._set_status(IntegrationStatus.ERROR, "Invalid credentials")
        return False

    async def disconnect(self) -> bool:
        """Disconnect from Xero."""
        self._access_token = None
        self._refresh_token = None
        self._tenant_id = None
        self.credentials = {}
        self._set_status(IntegrationStatus.DISCONNECTED)
        return True

    async def test_connection(self) -> bool:
        """Test Xero connection."""
        try:
            return bool(self._access_token and self._tenant_id)
        except Exception as e:
            self._log_error(f"Connection test failed: {e}")
            return False

    async def refresh_credentials(self) -> Dict[str, Any]:
        """Refresh OAuth tokens."""
        if not self._refresh_token:
            return self.credentials

        new_credentials = {
            **self.credentials,
            "access_token": f"xero_access_{utc_now().timestamp()}",
            "token_refreshed_at": utc_now().isoformat(),
        }

        self._access_token = new_credentials["access_token"]
        self.credentials = new_credentials

        return new_credentials

    # ==================== Contact Methods ====================

    async def create_contact(self, data: Dict) -> Dict:
        """Create a Xero contact."""
        contact_data = {
            "Name": data.get("name"),
            "EmailAddress": data.get("email"),
            "FirstName": data.get("first_name"),
            "LastName": data.get("last_name"),
        }

        if data.get("phone"):
            contact_data["Phones"] = [{"PhoneType": "DEFAULT", "PhoneNumber": data["phone"]}]

        if data.get("address"):
            addr = data["address"]
            contact_data["Addresses"] = [{
                "AddressType": "POBOX",
                "AddressLine1": addr.get("line1"),
                "City": addr.get("city"),
                "Region": addr.get("state"),
                "PostalCode": addr.get("postal_code"),
                "Country": addr.get("country"),
            }]

        # Demo response
        return {
            "Contacts": [{
                "ContactID": f"xero_contact_{utc_now().timestamp()}",
                "Name": data.get("name"),
                "EmailAddress": data.get("email"),
            }]
        }

    async def get_contact(self, contact_id: str) -> Dict:
        """Get contact by ID."""
        return {
            "Contacts": [{
                "ContactID": contact_id,
                "Name": "Sample Contact",
                "EmailAddress": "contact@example.com",
            }]
        }

    async def query_contacts(self, where: str = None, page: int = 1) -> Dict:
        """Query contacts."""
        return {
            "Contacts": [
                {"ContactID": "1", "Name": "Contact 1", "EmailAddress": "c1@example.com"},
                {"ContactID": "2", "Name": "Contact 2", "EmailAddress": "c2@example.com"},
            ]
        }

    # ==================== Invoice Methods ====================

    async def create_invoice(self, contact_id: str, line_items: List[Dict], due_date: str = None, invoice_number: str = None) -> Dict:
        """Create a Xero invoice."""
        invoice_data = {
            "Type": "ACCREC",  # Accounts Receivable
            "Contact": {"ContactID": contact_id},
            "LineItems": [
                {
                    "Description": item.get("description"),
                    "Quantity": item.get("quantity", 1),
                    "UnitAmount": item.get("unit_price"),
                    "AccountCode": item.get("account_code", "200"),  # Default sales account
                }
                for item in line_items
            ],
            "Status": "DRAFT",
        }

        if due_date:
            invoice_data["DueDate"] = due_date
        if invoice_number:
            invoice_data["InvoiceNumber"] = invoice_number

        # Demo response
        total = sum(item.get("quantity", 1) * item.get("unit_price", 0) for item in line_items)
        return {
            "Invoices": [{
                "InvoiceID": f"xero_inv_{utc_now().timestamp()}",
                "InvoiceNumber": invoice_number or f"INV-{int(utc_now().timestamp())}",
                "Contact": {"ContactID": contact_id},
                "Total": total,
                "AmountDue": total,
                "Status": "DRAFT",
            }]
        }

    async def get_invoice(self, invoice_id: str) -> Dict:
        """Get invoice by ID."""
        return {
            "Invoices": [{
                "InvoiceID": invoice_id,
                "InvoiceNumber": "INV-001",
                "Total": 1000.00,
                "AmountDue": 1000.00,
                "Status": "AUTHORISED",
            }]
        }

    async def approve_invoice(self, invoice_id: str) -> Dict:
        """Approve (authorise) an invoice."""
        return {
            "Invoices": [{
                "InvoiceID": invoice_id,
                "Status": "AUTHORISED",
            }]
        }

    async def query_invoices(self, where: str = None, page: int = 1) -> Dict:
        """Query invoices."""
        return {
            "Invoices": []
        }

    # ==================== Payment Methods ====================

    async def create_payment(self, invoice_id: str, amount: float, account_id: str, date: str = None) -> Dict:
        """Record a payment against an invoice."""
        payment_data = {
            "Invoice": {"InvoiceID": invoice_id},
            "Account": {"AccountID": account_id},
            "Amount": amount,
            "Date": date or utc_now().strftime("%Y-%m-%d"),
        }

        return {
            "Payments": [{
                "PaymentID": f"xero_pmt_{utc_now().timestamp()}",
                "Invoice": {"InvoiceID": invoice_id},
                "Amount": amount,
                "Status": "AUTHORISED",
            }]
        }

    # ==================== Account Methods ====================

    async def get_accounts(self, account_type: str = None) -> Dict:
        """Get chart of accounts."""
        return {
            "Accounts": [
                {"AccountID": "acc_1", "Code": "200", "Name": "Sales", "Type": "REVENUE"},
                {"AccountID": "acc_2", "Code": "090", "Name": "Bank", "Type": "BANK"},
            ]
        }

    # ==================== Sync Methods ====================

    async def sync(self, entity_type: str, direction: str = "pull") -> SyncResult:
        """Sync data with Xero."""
        result = SyncResult(entity_type, direction)

        try:
            if direction == "pull":
                if entity_type == "customers":
                    await self._pull_contacts(result)
                elif entity_type == "invoices":
                    await self._pull_invoices(result)
            elif direction == "push":
                if entity_type == "customers":
                    await self._push_contacts(result)
                elif entity_type == "invoices":
                    await self._push_invoices(result)

            result.complete()
            self._update_last_sync()

        except Exception as e:
            result.errors.append(str(e))
            result.complete()

        return result

    async def _pull_contacts(self, result: SyncResult):
        """Pull contacts from Xero."""
        response = await self.query_contacts()
        contacts = response.get("Contacts", [])

        for contact in contacts:
            result.updated += 1

        logger.info(f"[Xero] Pulled {len(contacts)} contacts")

    async def _pull_invoices(self, result: SyncResult):
        """Pull invoices from Xero."""
        response = await self.query_invoices()
        invoices = response.get("Invoices", [])

        for invoice in invoices:
            result.updated += 1

        logger.info(f"[Xero] Pulled {len(invoices)} invoices")

    async def _push_contacts(self, result: SyncResult):
        """Push contacts to Xero."""
        result.created += 0

    async def _push_invoices(self, result: SyncResult):
        """Push invoices to Xero."""
        result.created += 0

    # ==================== API Helper ====================

    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make API request to Xero."""
        import aiohttp

        url = f"{self.API_URL}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Xero-Tenant-Id": self._tenant_id,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=data) as response:
                result = await response.json()

                if response.status >= 400:
                    raise IntegrationError(
                        message=result.get("Message", "Unknown error"),
                        provider=self.PROVIDER_ID,
                        code=str(response.status),
                        details=result,
                    )

                return result
