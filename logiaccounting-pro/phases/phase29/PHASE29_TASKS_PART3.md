# Phase 29: Integration Hub - Part 3: Accounting Providers

## Overview
This part covers accounting platform integrations including QuickBooks Online and Xero for syncing customers, invoices, and payments.

---

## File 1: QuickBooks Client
**Path:** `backend/app/integrations/providers/quickbooks/client.py`

```python
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
            "access_token": f"qb_access_{datetime.utcnow().timestamp()}",
            "refresh_token": f"qb_refresh_{datetime.utcnow().timestamp()}",
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
            "access_token": f"qb_access_{datetime.utcnow().timestamp()}",
            "token_refreshed_at": datetime.utcnow().isoformat(),
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
                "Id": f"qb_cust_{datetime.utcnow().timestamp()}",
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
                "Id": f"qb_inv_{datetime.utcnow().timestamp()}",
                "DocNumber": f"INV-{int(datetime.utcnow().timestamp())}",
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
                "Id": f"qb_pmt_{datetime.utcnow().timestamp()}",
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
```

---

## File 2: QuickBooks OAuth Handler
**Path:** `backend/app/integrations/providers/quickbooks/oauth.py`

```python
"""
QuickBooks OAuth Handler
Manages OAuth flow for QuickBooks
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import base64
import logging

logger = logging.getLogger(__name__)


class QuickBooksOAuth:
    """Handles QuickBooks OAuth flow."""
    
    TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    def get_authorization_url(self, state: str, scopes: list = None) -> str:
        """Generate OAuth authorization URL."""
        if scopes is None:
            scopes = ["com.intuit.quickbooks.accounting"]
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
        }
        
        base_url = "https://appcenter.intuit.com/connect/oauth2"
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query}"
    
    async def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for tokens."""
        import aiohttp
        
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.TOKEN_URL, headers=headers, data=data) as response:
                result = await response.json()
                
                if response.status != 200:
                    logger.error(f"[QuickBooks OAuth] Token exchange failed: {result}")
                    raise Exception(result.get("error_description", "Token exchange failed"))
                
                return {
                    "access_token": result["access_token"],
                    "refresh_token": result["refresh_token"],
                    "expires_in": result["expires_in"],
                    "token_type": result["token_type"],
                    "obtained_at": datetime.utcnow().isoformat(),
                }
    
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh access token."""
        import aiohttp
        
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.TOKEN_URL, headers=headers, data=data) as response:
                result = await response.json()
                
                if response.status != 200:
                    logger.error(f"[QuickBooks OAuth] Token refresh failed: {result}")
                    raise Exception(result.get("error_description", "Token refresh failed"))
                
                return {
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token", refresh_token),
                    "expires_in": result["expires_in"],
                    "token_type": result["token_type"],
                    "refreshed_at": datetime.utcnow().isoformat(),
                }
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke access or refresh token."""
        import aiohttp
        
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        data = {"token": token}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.REVOKE_URL, headers=headers, json=data) as response:
                return response.status == 200
    
    def is_token_expired(self, obtained_at: str, expires_in: int, buffer_minutes: int = 5) -> bool:
        """Check if token is expired or about to expire."""
        obtained = datetime.fromisoformat(obtained_at)
        expires_at = obtained + timedelta(seconds=expires_in)
        buffer = timedelta(minutes=buffer_minutes)
        
        return datetime.utcnow() >= (expires_at - buffer)
```

---

## File 3: QuickBooks Init
**Path:** `backend/app/integrations/providers/quickbooks/__init__.py`

```python
"""
QuickBooks Integration Provider
"""

from app.integrations.providers.quickbooks.client import QuickBooksIntegration
from app.integrations.providers.quickbooks.oauth import QuickBooksOAuth


__all__ = [
    'QuickBooksIntegration',
    'QuickBooksOAuth',
]
```

---

## File 4: Xero Client
**Path:** `backend/app/integrations/providers/xero/client.py`

```python
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
            "access_token": f"xero_access_{datetime.utcnow().timestamp()}",
            "refresh_token": f"xero_refresh_{datetime.utcnow().timestamp()}",
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
            "access_token": f"xero_access_{datetime.utcnow().timestamp()}",
            "token_refreshed_at": datetime.utcnow().isoformat(),
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
                "ContactID": f"xero_contact_{datetime.utcnow().timestamp()}",
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
                "InvoiceID": f"xero_inv_{datetime.utcnow().timestamp()}",
                "InvoiceNumber": invoice_number or f"INV-{int(datetime.utcnow().timestamp())}",
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
            "Date": date or datetime.utcnow().strftime("%Y-%m-%d"),
        }
        
        return {
            "Payments": [{
                "PaymentID": f"xero_pmt_{datetime.utcnow().timestamp()}",
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
```

---

## File 5: Xero Sync Mappings
**Path:** `backend/app/integrations/providers/xero/sync.py`

```python
"""
Xero Sync Utilities
Field mappings and sync helpers
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class XeroFieldMapper:
    """Maps fields between LogiAccounting and Xero."""
    
    # Customer to Contact mapping
    CUSTOMER_TO_CONTACT = {
        "name": "Name",
        "email": "EmailAddress",
        "first_name": "FirstName",
        "last_name": "LastName",
        "phone": "Phones[0].PhoneNumber",
        "company_name": "CompanyName",
        "tax_number": "TaxNumber",
    }
    
    CONTACT_TO_CUSTOMER = {v: k for k, v in CUSTOMER_TO_CONTACT.items()}
    
    # Invoice mapping
    INVOICE_TO_XERO = {
        "number": "InvoiceNumber",
        "customer_id": "Contact.ContactID",
        "due_date": "DueDate",
        "issue_date": "Date",
        "currency": "CurrencyCode",
        "reference": "Reference",
        "notes": "LineAmountTypes",
    }
    
    # Invoice status mapping
    INVOICE_STATUS_MAP = {
        "draft": "DRAFT",
        "sent": "AUTHORISED",
        "paid": "PAID",
        "voided": "VOIDED",
    }
    
    XERO_STATUS_MAP = {v: k for k, v in INVOICE_STATUS_MAP.items()}
    
    @classmethod
    def customer_to_xero(cls, customer: Dict) -> Dict:
        """Convert LogiAccounting customer to Xero contact."""
        contact = {}
        
        for local_field, xero_field in cls.CUSTOMER_TO_CONTACT.items():
            value = customer.get(local_field)
            if value:
                if "." in xero_field:
                    # Handle nested fields like Phones[0].PhoneNumber
                    parts = xero_field.split(".")
                    # Simplified - in production handle arrays properly
                    contact[parts[0].split("[")[0]] = [{"PhoneType": "DEFAULT", "PhoneNumber": value}]
                else:
                    contact[xero_field] = value
        
        # Handle address
        if customer.get("address"):
            addr = customer["address"]
            contact["Addresses"] = [{
                "AddressType": "POBOX",
                "AddressLine1": addr.get("line1", ""),
                "AddressLine2": addr.get("line2", ""),
                "City": addr.get("city", ""),
                "Region": addr.get("state", ""),
                "PostalCode": addr.get("postal_code", ""),
                "Country": addr.get("country", ""),
            }]
        
        return contact
    
    @classmethod
    def xero_to_customer(cls, contact: Dict) -> Dict:
        """Convert Xero contact to LogiAccounting customer."""
        customer = {
            "external_id": contact.get("ContactID"),
            "external_provider": "xero",
        }
        
        # Direct mappings
        customer["name"] = contact.get("Name")
        customer["email"] = contact.get("EmailAddress")
        customer["first_name"] = contact.get("FirstName")
        customer["last_name"] = contact.get("LastName")
        customer["company_name"] = contact.get("CompanyName")
        customer["tax_number"] = contact.get("TaxNumber")
        
        # Phone
        phones = contact.get("Phones", [])
        if phones:
            customer["phone"] = phones[0].get("PhoneNumber")
        
        # Address
        addresses = contact.get("Addresses", [])
        if addresses:
            addr = addresses[0]
            customer["address"] = {
                "line1": addr.get("AddressLine1"),
                "line2": addr.get("AddressLine2"),
                "city": addr.get("City"),
                "state": addr.get("Region"),
                "postal_code": addr.get("PostalCode"),
                "country": addr.get("Country"),
            }
        
        return customer
    
    @classmethod
    def invoice_to_xero(cls, invoice: Dict, contact_id: str) -> Dict:
        """Convert LogiAccounting invoice to Xero invoice."""
        xero_invoice = {
            "Type": "ACCREC",
            "Contact": {"ContactID": contact_id},
            "Status": cls.INVOICE_STATUS_MAP.get(invoice.get("status"), "DRAFT"),
            "LineAmountTypes": "Exclusive",  # Tax exclusive
        }
        
        if invoice.get("number"):
            xero_invoice["InvoiceNumber"] = invoice["number"]
        if invoice.get("due_date"):
            xero_invoice["DueDate"] = invoice["due_date"]
        if invoice.get("issue_date"):
            xero_invoice["Date"] = invoice["issue_date"]
        if invoice.get("currency"):
            xero_invoice["CurrencyCode"] = invoice["currency"].upper()
        if invoice.get("reference"):
            xero_invoice["Reference"] = invoice["reference"]
        
        # Line items
        xero_invoice["LineItems"] = []
        for item in invoice.get("items", []):
            xero_invoice["LineItems"].append({
                "Description": item.get("description"),
                "Quantity": item.get("quantity", 1),
                "UnitAmount": item.get("unit_price"),
                "AccountCode": item.get("account_code", "200"),
                "TaxType": item.get("tax_type", "OUTPUT"),
            })
        
        return xero_invoice
    
    @classmethod
    def xero_to_invoice(cls, xero_invoice: Dict) -> Dict:
        """Convert Xero invoice to LogiAccounting invoice."""
        invoice = {
            "external_id": xero_invoice.get("InvoiceID"),
            "external_provider": "xero",
            "number": xero_invoice.get("InvoiceNumber"),
            "status": cls.XERO_STATUS_MAP.get(xero_invoice.get("Status"), "draft"),
            "total": xero_invoice.get("Total"),
            "subtotal": xero_invoice.get("SubTotal"),
            "tax": xero_invoice.get("TotalTax"),
            "amount_due": xero_invoice.get("AmountDue"),
            "amount_paid": xero_invoice.get("AmountPaid"),
            "currency": xero_invoice.get("CurrencyCode"),
            "due_date": xero_invoice.get("DueDate"),
            "issue_date": xero_invoice.get("Date"),
        }
        
        # Contact reference
        contact = xero_invoice.get("Contact", {})
        invoice["external_customer_id"] = contact.get("ContactID")
        
        # Line items
        invoice["items"] = []
        for item in xero_invoice.get("LineItems", []):
            invoice["items"].append({
                "description": item.get("Description"),
                "quantity": item.get("Quantity"),
                "unit_price": item.get("UnitAmount"),
                "total": item.get("LineAmount"),
                "account_code": item.get("AccountCode"),
            })
        
        return invoice
```

---

## File 6: Xero Init
**Path:** `backend/app/integrations/providers/xero/__init__.py`

```python
"""
Xero Integration Provider
"""

from app.integrations.providers.xero.client import XeroIntegration
from app.integrations.providers.xero.sync import XeroFieldMapper


__all__ = [
    'XeroIntegration',
    'XeroFieldMapper',
]
```

---

## Summary Part 3

| File | Description | Lines |
|------|-------------|-------|
| `quickbooks/client.py` | QuickBooks API client | ~320 |
| `quickbooks/oauth.py` | QuickBooks OAuth handler | ~130 |
| `quickbooks/__init__.py` | QuickBooks init | ~15 |
| `xero/client.py` | Xero API client | ~320 |
| `xero/sync.py` | Xero field mappings | ~200 |
| `xero/__init__.py` | Xero init | ~15 |
| **Total** | | **~1,000 lines** |
