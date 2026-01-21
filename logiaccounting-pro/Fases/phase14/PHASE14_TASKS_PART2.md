# LogiAccounting Pro - Phase 14 Tasks Part 2

## ACCOUNTING & CRM CONNECTORS

---

## TASK 4: QUICKBOOKS CONNECTOR

### 4.1 QuickBooks Online Connector

**File:** `backend/app/integrations/connectors/accounting/quickbooks_connector.py`

```python
"""
QuickBooks Online Connector
Full integration with QuickBooks Online API
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass
import httpx
import logging

from app.integrations.core.base_connector import (
    BaseConnector, ConnectorConfig, EntitySchema, EntityField, SyncResult
)

logger = logging.getLogger(__name__)


class QuickBooksConnector(BaseConnector):
    """QuickBooks Online connector"""
    
    PROVIDER_NAME = 'quickbooks'
    PROVIDER_LABEL = 'QuickBooks Online'
    CATEGORY = 'accounting'
    
    # OAuth URLs
    OAUTH_AUTHORIZATION_URL = 'https://appcenter.intuit.com/connect/oauth2'
    OAUTH_TOKEN_URL = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
    OAUTH_SCOPES = ['com.intuit.quickbooks.accounting']
    
    # API Configuration
    API_BASE_URL_PRODUCTION = 'https://quickbooks.api.intuit.com'
    API_BASE_URL_SANDBOX = 'https://sandbox-quickbooks.api.intuit.com'
    API_VERSION = 'v3'
    
    # Rate limiting: 500 requests per minute
    RATE_LIMIT_REQUESTS = 500
    RATE_LIMIT_PERIOD = 60
    
    # Entity mappings
    SUPPORTED_ENTITIES = {
        'customer': 'Customer',
        'supplier': 'Vendor',
        'product': 'Item',
        'invoice': 'Invoice',
        'bill': 'Bill',
        'payment': 'Payment',
        'account': 'Account',
        'tax_rate': 'TaxRate',
    }
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.realm_id = config.extra.get('realm_id')
        self.environment = config.environment or 'production'
        
        self.base_url = (
            self.API_BASE_URL_SANDBOX if self.environment == 'sandbox'
            else self.API_BASE_URL_PRODUCTION
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    def _api_url(self, endpoint: str) -> str:
        """Build API URL"""
        return f"{self.base_url}/{self.API_VERSION}/company/{self.realm_id}/{endpoint}"
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None
    ) -> Dict[str, Any]:
        """Make API request with error handling"""
        url = self._api_url(endpoint)
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data,
                timeout=30.0
            )
            
            if response.status_code == 401:
                raise Exception("Authentication failed - token may be expired")
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('Fault', {}).get('Error', [{}])[0].get('Detail', str(response.status_code))
                raise Exception(f"QuickBooks API error: {error_msg}")
            
            return response.json()
    
    # ==================== Authentication ====================
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL"""
        from urllib.parse import urlencode
        
        params = {
            'client_id': self.config.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.OAUTH_SCOPES),
            'state': state,
        }
        
        return f"{self.OAUTH_AUTHORIZATION_URL}?{urlencode(params)}"
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        import base64
        
        auth_string = f"{self.config.client_id}:{self.config.client_secret}"
        auth_header = base64.b64encode(auth_string.encode()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                headers={
                    'Authorization': f'Basic {auth_header}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                },
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        import base64
        
        auth_string = f"{self.config.client_id}:{self.config.client_secret}"
        auth_header = base64.b64encode(auth_string.encode()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                headers={
                    'Authorization': f'Basic {auth_header}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Token refresh failed: {response.text}")
            
            return response.json()
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            result = await self._make_request('GET', 'companyinfo/' + self.realm_id)
            company_name = result.get('CompanyInfo', {}).get('CompanyName', 'Unknown')
            return True, f"Connected to: {company_name}"
        except Exception as e:
            return False, str(e)
    
    # ==================== Entity Operations ====================
    
    def get_entity_schema(self, entity_name: str) -> EntitySchema:
        """Get schema for QuickBooks entity"""
        schemas = {
            'Customer': EntitySchema(
                name='Customer',
                label='Customer',
                id_field='Id',
                fields=[
                    EntityField(name='Id', label='ID', type='string', readonly=True),
                    EntityField(name='DisplayName', label='Display Name', type='string', required=True),
                    EntityField(name='CompanyName', label='Company Name', type='string'),
                    EntityField(name='GivenName', label='First Name', type='string'),
                    EntityField(name='FamilyName', label='Last Name', type='string'),
                    EntityField(name='PrimaryEmailAddr.Address', label='Email', type='string'),
                    EntityField(name='PrimaryPhone.FreeFormNumber', label='Phone', type='string'),
                    EntityField(name='BillAddr.Line1', label='Billing Address', type='string'),
                    EntityField(name='BillAddr.City', label='Billing City', type='string'),
                    EntityField(name='BillAddr.PostalCode', label='Billing Postal Code', type='string'),
                    EntityField(name='BillAddr.Country', label='Billing Country', type='string'),
                    EntityField(name='Balance', label='Balance', type='number', readonly=True),
                    EntityField(name='Active', label='Active', type='boolean'),
                ],
            ),
            'Invoice': EntitySchema(
                name='Invoice',
                label='Invoice',
                id_field='Id',
                fields=[
                    EntityField(name='Id', label='ID', type='string', readonly=True),
                    EntityField(name='DocNumber', label='Invoice Number', type='string'),
                    EntityField(name='CustomerRef.value', label='Customer ID', type='string', required=True),
                    EntityField(name='TxnDate', label='Date', type='date'),
                    EntityField(name='DueDate', label='Due Date', type='date'),
                    EntityField(name='Line', label='Line Items', type='array'),
                    EntityField(name='TotalAmt', label='Total', type='number', readonly=True),
                    EntityField(name='Balance', label='Balance Due', type='number', readonly=True),
                    EntityField(name='EmailStatus', label='Email Status', type='string'),
                ],
            ),
            'Item': EntitySchema(
                name='Item',
                label='Product/Service',
                id_field='Id',
                fields=[
                    EntityField(name='Id', label='ID', type='string', readonly=True),
                    EntityField(name='Name', label='Name', type='string', required=True),
                    EntityField(name='Description', label='Description', type='string'),
                    EntityField(name='Type', label='Type', type='string'),
                    EntityField(name='UnitPrice', label='Price', type='number'),
                    EntityField(name='PurchaseCost', label='Cost', type='number'),
                    EntityField(name='QtyOnHand', label='Quantity on Hand', type='number'),
                    EntityField(name='Active', label='Active', type='boolean'),
                ],
            ),
            'Vendor': EntitySchema(
                name='Vendor',
                label='Vendor',
                id_field='Id',
                fields=[
                    EntityField(name='Id', label='ID', type='string', readonly=True),
                    EntityField(name='DisplayName', label='Display Name', type='string', required=True),
                    EntityField(name='CompanyName', label='Company Name', type='string'),
                    EntityField(name='PrimaryEmailAddr.Address', label='Email', type='string'),
                    EntityField(name='PrimaryPhone.FreeFormNumber', label='Phone', type='string'),
                    EntityField(name='Balance', label='Balance', type='number', readonly=True),
                    EntityField(name='Active', label='Active', type='boolean'),
                ],
            ),
        }
        
        return schemas.get(entity_name)
    
    async def list_records(
        self,
        entity_name: str,
        filters: Dict[str, Any] = None,
        fields: List[str] = None,
        page: int = 1,
        page_size: int = 100,
        modified_since: datetime = None
    ) -> Tuple[List[Dict], bool]:
        """List records with pagination"""
        qb_entity = self.get_remote_entity_name(entity_name)
        
        # Build query
        select = '*' if not fields else ', '.join(fields)
        query = f"SELECT {select} FROM {qb_entity}"
        
        # Add filters
        conditions = []
        
        if modified_since:
            conditions.append(f"MetaData.LastUpdatedTime >= '{modified_since.isoformat()}'")
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f"{key} = '{value}'")
                elif isinstance(value, bool):
                    conditions.append(f"{key} = {str(value).lower()}")
                else:
                    conditions.append(f"{key} = {value}")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Add pagination
        start_position = (page - 1) * page_size + 1
        query += f" STARTPOSITION {start_position} MAXRESULTS {page_size}"
        
        # Execute query
        result = await self._make_request(
            'GET',
            'query',
            params={'query': query}
        )
        
        records = result.get('QueryResponse', {}).get(qb_entity, [])
        
        # Check if there are more records
        has_more = len(records) == page_size
        
        return records, has_more
    
    async def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
        """Get single record by ID"""
        qb_entity = self.get_remote_entity_name(entity_name)
        
        try:
            result = await self._make_request(
                'GET',
                f'{qb_entity.lower()}/{record_id}'
            )
            return result.get(qb_entity)
        except Exception as e:
            if '404' in str(e):
                return None
            raise
    
    async def create_record(self, entity_name: str, data: Dict) -> Dict:
        """Create new record"""
        qb_entity = self.get_remote_entity_name(entity_name)
        
        result = await self._make_request(
            'POST',
            qb_entity.lower(),
            data=data
        )
        
        return result.get(qb_entity)
    
    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """Update existing record"""
        qb_entity = self.get_remote_entity_name(entity_name)
        
        # QuickBooks requires SyncToken for updates
        existing = await self.get_record(entity_name, record_id)
        
        if not existing:
            raise Exception(f"Record not found: {record_id}")
        
        data['Id'] = record_id
        data['SyncToken'] = existing.get('SyncToken')
        
        result = await self._make_request(
            'POST',
            qb_entity.lower(),
            data=data
        )
        
        return result.get(qb_entity)
    
    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """Delete/deactivate record"""
        qb_entity = self.get_remote_entity_name(entity_name)
        
        # QuickBooks uses soft delete (set Active = false)
        existing = await self.get_record(entity_name, record_id)
        
        if not existing:
            return False
        
        data = {
            'Id': record_id,
            'SyncToken': existing.get('SyncToken'),
            'Active': False,
        }
        
        await self._make_request(
            'POST',
            qb_entity.lower(),
            data=data
        )
        
        return True
    
    # ==================== QuickBooks-Specific Methods ====================
    
    async def get_company_info(self) -> Dict:
        """Get company information"""
        result = await self._make_request('GET', f'companyinfo/{self.realm_id}')
        return result.get('CompanyInfo', {})
    
    async def create_invoice(
        self,
        customer_id: str,
        line_items: List[Dict],
        invoice_date: str = None,
        due_date: str = None,
        doc_number: str = None
    ) -> Dict:
        """Create a new invoice"""
        data = {
            'CustomerRef': {'value': customer_id},
            'Line': line_items,
        }
        
        if invoice_date:
            data['TxnDate'] = invoice_date
        
        if due_date:
            data['DueDate'] = due_date
        
        if doc_number:
            data['DocNumber'] = doc_number
        
        return await self.create_record('invoice', data)
    
    async def send_invoice_email(self, invoice_id: str, email: str = None) -> bool:
        """Send invoice via email"""
        endpoint = f'invoice/{invoice_id}/send'
        
        params = {}
        if email:
            params['sendTo'] = email
        
        await self._make_request('POST', endpoint, params=params)
        return True
    
    async def record_payment(
        self,
        customer_id: str,
        amount: float,
        invoice_id: str = None,
        payment_method: str = None,
        payment_date: str = None
    ) -> Dict:
        """Record a payment"""
        data = {
            'CustomerRef': {'value': customer_id},
            'TotalAmt': amount,
        }
        
        if invoice_id:
            data['Line'] = [{
                'Amount': amount,
                'LinkedTxn': [{
                    'TxnId': invoice_id,
                    'TxnType': 'Invoice'
                }]
            }]
        
        if payment_method:
            data['PaymentMethodRef'] = {'value': payment_method}
        
        if payment_date:
            data['TxnDate'] = payment_date
        
        return await self.create_record('payment', data)
    
    async def get_account_balances(self) -> List[Dict]:
        """Get all account balances"""
        accounts, _ = await self.list_records('account')
        return [{
            'id': acc.get('Id'),
            'name': acc.get('Name'),
            'type': acc.get('AccountType'),
            'balance': acc.get('CurrentBalance', 0),
        } for acc in accounts]
```

---

## TASK 5: XERO CONNECTOR

### 5.1 Xero Connector

**File:** `backend/app/integrations/connectors/accounting/xero_connector.py`

```python
"""
Xero Connector
Integration with Xero Accounting API
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import logging

from app.integrations.core.base_connector import (
    BaseConnector, ConnectorConfig, EntitySchema, EntityField
)

logger = logging.getLogger(__name__)


class XeroConnector(BaseConnector):
    """Xero accounting connector"""
    
    PROVIDER_NAME = 'xero'
    PROVIDER_LABEL = 'Xero'
    CATEGORY = 'accounting'
    
    # OAuth URLs
    OAUTH_AUTHORIZATION_URL = 'https://login.xero.com/identity/connect/authorize'
    OAUTH_TOKEN_URL = 'https://identity.xero.com/connect/token'
    OAUTH_SCOPES = [
        'openid', 'profile', 'email', 'offline_access',
        'accounting.transactions', 'accounting.contacts',
        'accounting.settings', 'accounting.reports.read'
    ]
    
    # API Configuration
    API_BASE_URL = 'https://api.xero.com/api.xro/2.0'
    
    # Rate limiting: 60 requests per minute
    RATE_LIMIT_REQUESTS = 60
    RATE_LIMIT_PERIOD = 60
    
    # Entity mappings
    SUPPORTED_ENTITIES = {
        'customer': 'Contacts',
        'supplier': 'Contacts',
        'invoice': 'Invoices',
        'bill': 'Invoices',
        'payment': 'Payments',
        'product': 'Items',
        'account': 'Accounts',
    }
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.tenant_id = config.extra.get('tenant_id')
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        headers = {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        if self.tenant_id:
            headers['Xero-tenant-id'] = self.tenant_id
        
        return headers
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None
    ) -> Dict[str, Any]:
        """Make API request"""
        url = f"{self.API_BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data,
                timeout=30.0
            )
            
            if response.status_code == 401:
                raise Exception("Authentication failed")
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise Exception(f"Xero API error: {response.status_code} - {error_data}")
            
            return response.json()
    
    # ==================== Authentication ====================
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL"""
        from urllib.parse import urlencode
        
        params = {
            'client_id': self.config.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.OAUTH_SCOPES),
            'state': state,
        }
        
        return f"{self.OAUTH_AUTHORIZATION_URL}?{urlencode(params)}"
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        import base64
        
        auth_string = f"{self.config.client_id}:{self.config.client_secret}"
        auth_header = base64.b64encode(auth_string.encode()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                headers={
                    'Authorization': f'Basic {auth_header}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        import base64
        
        auth_string = f"{self.config.client_id}:{self.config.client_secret}"
        auth_header = base64.b64encode(auth_string.encode()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                headers={
                    'Authorization': f'Basic {auth_header}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Token refresh failed: {response.text}")
            
            return response.json()
    
    async def get_tenants(self) -> List[Dict]:
        """Get available Xero tenants (organizations)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.xero.com/connections',
                headers={'Authorization': f'Bearer {self.config.access_token}'}
            )
            
            if response.status_code != 200:
                raise Exception("Failed to get tenants")
            
            return response.json()
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            result = await self._make_request('GET', 'Organisation')
            org_name = result.get('Organisations', [{}])[0].get('Name', 'Unknown')
            return True, f"Connected to: {org_name}"
        except Exception as e:
            return False, str(e)
    
    # ==================== Entity Operations ====================
    
    def get_entity_schema(self, entity_name: str) -> EntitySchema:
        """Get schema for Xero entity"""
        schemas = {
            'Contacts': EntitySchema(
                name='Contacts',
                label='Contact',
                id_field='ContactID',
                fields=[
                    EntityField(name='ContactID', label='ID', type='string', readonly=True),
                    EntityField(name='Name', label='Name', type='string', required=True),
                    EntityField(name='FirstName', label='First Name', type='string'),
                    EntityField(name='LastName', label='Last Name', type='string'),
                    EntityField(name='EmailAddress', label='Email', type='string'),
                    EntityField(name='ContactStatus', label='Status', type='string'),
                    EntityField(name='IsCustomer', label='Is Customer', type='boolean'),
                    EntityField(name='IsSupplier', label='Is Supplier', type='boolean'),
                    EntityField(name='Phones', label='Phone Numbers', type='array'),
                    EntityField(name='Addresses', label='Addresses', type='array'),
                ],
            ),
            'Invoices': EntitySchema(
                name='Invoices',
                label='Invoice',
                id_field='InvoiceID',
                fields=[
                    EntityField(name='InvoiceID', label='ID', type='string', readonly=True),
                    EntityField(name='InvoiceNumber', label='Invoice Number', type='string'),
                    EntityField(name='Type', label='Type', type='string', required=True),
                    EntityField(name='Contact.ContactID', label='Contact ID', type='string', required=True),
                    EntityField(name='Date', label='Date', type='date'),
                    EntityField(name='DueDate', label='Due Date', type='date'),
                    EntityField(name='LineItems', label='Line Items', type='array', required=True),
                    EntityField(name='Total', label='Total', type='number', readonly=True),
                    EntityField(name='AmountDue', label='Amount Due', type='number', readonly=True),
                    EntityField(name='Status', label='Status', type='string'),
                ],
            ),
            'Items': EntitySchema(
                name='Items',
                label='Item',
                id_field='ItemID',
                fields=[
                    EntityField(name='ItemID', label='ID', type='string', readonly=True),
                    EntityField(name='Code', label='Code', type='string', required=True),
                    EntityField(name='Name', label='Name', type='string'),
                    EntityField(name='Description', label='Description', type='string'),
                    EntityField(name='PurchaseDescription', label='Purchase Description', type='string'),
                    EntityField(name='SalesDetails.UnitPrice', label='Sale Price', type='number'),
                    EntityField(name='PurchaseDetails.UnitPrice', label='Purchase Price', type='number'),
                    EntityField(name='IsTrackedAsInventory', label='Tracked Inventory', type='boolean'),
                    EntityField(name='QuantityOnHand', label='Qty on Hand', type='number', readonly=True),
                ],
            ),
        }
        
        return schemas.get(entity_name)
    
    async def list_records(
        self,
        entity_name: str,
        filters: Dict[str, Any] = None,
        fields: List[str] = None,
        page: int = 1,
        page_size: int = 100,
        modified_since: datetime = None
    ) -> Tuple[List[Dict], bool]:
        """List records with pagination"""
        xero_entity = self.get_remote_entity_name(entity_name)
        
        params = {
            'page': page,
        }
        
        headers = self._get_headers()
        
        if modified_since:
            headers['If-Modified-Since'] = modified_since.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Build where clause for filters
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f'{key}=="{value}"')
                elif isinstance(value, bool):
                    where_clauses.append(f'{key}=={str(value).lower()}')
                else:
                    where_clauses.append(f'{key}=={value}')
            
            if where_clauses:
                params['where'] = '&&'.join(where_clauses)
        
        result = await self._make_request('GET', xero_entity, params=params)
        
        records = result.get(xero_entity, [])
        
        # Xero uses page-based pagination
        has_more = len(records) == 100  # Xero returns max 100 per page
        
        return records, has_more
    
    async def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
        """Get single record by ID"""
        xero_entity = self.get_remote_entity_name(entity_name)
        
        try:
            result = await self._make_request('GET', f'{xero_entity}/{record_id}')
            records = result.get(xero_entity, [])
            return records[0] if records else None
        except Exception as e:
            if '404' in str(e):
                return None
            raise
    
    async def create_record(self, entity_name: str, data: Dict) -> Dict:
        """Create new record"""
        xero_entity = self.get_remote_entity_name(entity_name)
        
        payload = {xero_entity: [data]}
        
        result = await self._make_request('POST', xero_entity, data=payload)
        
        records = result.get(xero_entity, [])
        return records[0] if records else {}
    
    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """Update existing record"""
        xero_entity = self.get_remote_entity_name(entity_name)
        
        # Ensure ID is in data
        id_field = self.get_entity_schema(xero_entity).id_field
        data[id_field] = record_id
        
        payload = {xero_entity: [data]}
        
        result = await self._make_request('POST', xero_entity, data=payload)
        
        records = result.get(xero_entity, [])
        return records[0] if records else {}
    
    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """Archive/delete record"""
        # Xero doesn't support hard delete for most entities
        # Use status update instead
        try:
            await self.update_record(entity_name, record_id, {'Status': 'ARCHIVED'})
            return True
        except:
            return False
    
    # ==================== Xero-Specific Methods ====================
    
    async def create_invoice(
        self,
        contact_id: str,
        line_items: List[Dict],
        invoice_type: str = 'ACCREC',  # ACCREC = Sales, ACCPAY = Purchase
        invoice_date: str = None,
        due_date: str = None,
        invoice_number: str = None,
        reference: str = None
    ) -> Dict:
        """Create a new invoice"""
        data = {
            'Type': invoice_type,
            'Contact': {'ContactID': contact_id},
            'LineItems': line_items,
            'Status': 'DRAFT',
        }
        
        if invoice_date:
            data['Date'] = invoice_date
        
        if due_date:
            data['DueDate'] = due_date
        
        if invoice_number:
            data['InvoiceNumber'] = invoice_number
        
        if reference:
            data['Reference'] = reference
        
        return await self.create_record('invoice', data)
    
    async def approve_invoice(self, invoice_id: str) -> Dict:
        """Approve a draft invoice"""
        return await self.update_record('invoice', invoice_id, {
            'InvoiceID': invoice_id,
            'Status': 'AUTHORISED'
        })
    
    async def record_payment(
        self,
        invoice_id: str,
        account_id: str,
        amount: float,
        payment_date: str = None,
        reference: str = None
    ) -> Dict:
        """Record a payment against an invoice"""
        data = {
            'Invoice': {'InvoiceID': invoice_id},
            'Account': {'AccountID': account_id},
            'Amount': amount,
        }
        
        if payment_date:
            data['Date'] = payment_date
        
        if reference:
            data['Reference'] = reference
        
        result = await self._make_request('PUT', 'Payments', data={'Payments': [data]})
        
        payments = result.get('Payments', [])
        return payments[0] if payments else {}
    
    async def get_profit_and_loss(
        self,
        from_date: str,
        to_date: str
    ) -> Dict:
        """Get profit and loss report"""
        params = {
            'fromDate': from_date,
            'toDate': to_date,
        }
        
        result = await self._make_request('GET', 'Reports/ProfitAndLoss', params=params)
        return result.get('Reports', [{}])[0]
    
    async def get_balance_sheet(self, date: str = None) -> Dict:
        """Get balance sheet report"""
        params = {}
        if date:
            params['date'] = date
        
        result = await self._make_request('GET', 'Reports/BalanceSheet', params=params)
        return result.get('Reports', [{}])[0]
```

---

## TASK 6: SALESFORCE CONNECTOR

### 6.1 Salesforce CRM Connector

**File:** `backend/app/integrations/connectors/crm/salesforce_connector.py`

```python
"""
Salesforce Connector
Integration with Salesforce CRM
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import logging

from app.integrations.core.base_connector import (
    BaseConnector, ConnectorConfig, EntitySchema, EntityField, SyncResult
)

logger = logging.getLogger(__name__)


class SalesforceConnector(BaseConnector):
    """Salesforce CRM connector"""
    
    PROVIDER_NAME = 'salesforce'
    PROVIDER_LABEL = 'Salesforce'
    CATEGORY = 'crm'
    
    # OAuth URLs
    OAUTH_AUTHORIZATION_URL = 'https://login.salesforce.com/services/oauth2/authorize'
    OAUTH_TOKEN_URL = 'https://login.salesforce.com/services/oauth2/token'
    OAUTH_SCOPES = ['api', 'refresh_token', 'offline_access']
    
    # For sandbox
    OAUTH_AUTHORIZATION_URL_SANDBOX = 'https://test.salesforce.com/services/oauth2/authorize'
    OAUTH_TOKEN_URL_SANDBOX = 'https://test.salesforce.com/services/oauth2/token'
    
    # API Configuration
    API_VERSION = 'v59.0'
    
    # Rate limiting: 100,000 requests per 24 hours (varies by edition)
    RATE_LIMIT_REQUESTS = 1000
    RATE_LIMIT_PERIOD = 3600
    
    # Entity mappings
    SUPPORTED_ENTITIES = {
        'customer': 'Account',
        'contact': 'Contact',
        'lead': 'Lead',
        'opportunity': 'Opportunity',
        'product': 'Product2',
        'order': 'Order',
        'task': 'Task',
    }
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.instance_url = config.extra.get('instance_url')
        self.environment = config.environment or 'production'
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    def _api_url(self, endpoint: str) -> str:
        """Build API URL"""
        return f"{self.instance_url}/services/data/{self.API_VERSION}/{endpoint}"
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None
    ) -> Dict[str, Any]:
        """Make API request"""
        url = self._api_url(endpoint)
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data,
                timeout=30.0
            )
            
            if response.status_code == 401:
                raise Exception("Authentication failed")
            
            if response.status_code == 204:
                return {}
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else []
                error_msg = error_data[0].get('message', str(response.status_code)) if error_data else str(response.status_code)
                raise Exception(f"Salesforce API error: {error_msg}")
            
            return response.json()
    
    # ==================== Authentication ====================
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL"""
        from urllib.parse import urlencode
        
        base_url = (
            self.OAUTH_AUTHORIZATION_URL_SANDBOX if self.environment == 'sandbox'
            else self.OAUTH_AUTHORIZATION_URL
        )
        
        params = {
            'client_id': self.config.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.OAUTH_SCOPES),
            'state': state,
        }
        
        return f"{base_url}?{urlencode(params)}"
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        token_url = (
            self.OAUTH_TOKEN_URL_SANDBOX if self.environment == 'sandbox'
            else self.OAUTH_TOKEN_URL
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    'grant_type': 'authorization_code',
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'code': code,
                    'redirect_uri': redirect_uri,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            result = response.json()
            
            # Store instance URL
            self.instance_url = result.get('instance_url')
            
            return result
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        token_url = (
            self.OAUTH_TOKEN_URL_SANDBOX if self.environment == 'sandbox'
            else self.OAUTH_TOKEN_URL
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    'grant_type': 'refresh_token',
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'refresh_token': refresh_token,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Token refresh failed: {response.text}")
            
            return response.json()
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            result = await self._make_request('GET', 'sobjects')
            return True, f"Connected to Salesforce (API v{self.API_VERSION})"
        except Exception as e:
            return False, str(e)
    
    # ==================== Entity Operations ====================
    
    def get_entity_schema(self, entity_name: str) -> EntitySchema:
        """Get schema for Salesforce entity"""
        schemas = {
            'Account': EntitySchema(
                name='Account',
                label='Account',
                id_field='Id',
                supports_bulk=True,
                fields=[
                    EntityField(name='Id', label='ID', type='string', readonly=True),
                    EntityField(name='Name', label='Account Name', type='string', required=True),
                    EntityField(name='Type', label='Type', type='string'),
                    EntityField(name='Industry', label='Industry', type='string'),
                    EntityField(name='Phone', label='Phone', type='string'),
                    EntityField(name='Website', label='Website', type='string'),
                    EntityField(name='BillingStreet', label='Billing Street', type='string'),
                    EntityField(name='BillingCity', label='Billing City', type='string'),
                    EntityField(name='BillingState', label='Billing State', type='string'),
                    EntityField(name='BillingPostalCode', label='Billing Postal Code', type='string'),
                    EntityField(name='BillingCountry', label='Billing Country', type='string'),
                    EntityField(name='Description', label='Description', type='string'),
                ],
            ),
            'Contact': EntitySchema(
                name='Contact',
                label='Contact',
                id_field='Id',
                supports_bulk=True,
                fields=[
                    EntityField(name='Id', label='ID', type='string', readonly=True),
                    EntityField(name='FirstName', label='First Name', type='string'),
                    EntityField(name='LastName', label='Last Name', type='string', required=True),
                    EntityField(name='Email', label='Email', type='string'),
                    EntityField(name='Phone', label='Phone', type='string'),
                    EntityField(name='MobilePhone', label='Mobile', type='string'),
                    EntityField(name='Title', label='Title', type='string'),
                    EntityField(name='AccountId', label='Account ID', type='string'),
                    EntityField(name='MailingStreet', label='Mailing Street', type='string'),
                    EntityField(name='MailingCity', label='Mailing City', type='string'),
                    EntityField(name='MailingState', label='Mailing State', type='string'),
                    EntityField(name='MailingPostalCode', label='Mailing Postal Code', type='string'),
                ],
            ),
            'Opportunity': EntitySchema(
                name='Opportunity',
                label='Opportunity',
                id_field='Id',
                fields=[
                    EntityField(name='Id', label='ID', type='string', readonly=True),
                    EntityField(name='Name', label='Opportunity Name', type='string', required=True),
                    EntityField(name='AccountId', label='Account ID', type='string'),
                    EntityField(name='Amount', label='Amount', type='number'),
                    EntityField(name='StageName', label='Stage', type='string', required=True),
                    EntityField(name='CloseDate', label='Close Date', type='date', required=True),
                    EntityField(name='Probability', label='Probability', type='number'),
                    EntityField(name='Type', label='Type', type='string'),
                    EntityField(name='Description', label='Description', type='string'),
                ],
            ),
            'Lead': EntitySchema(
                name='Lead',
                label='Lead',
                id_field='Id',
                fields=[
                    EntityField(name='Id', label='ID', type='string', readonly=True),
                    EntityField(name='FirstName', label='First Name', type='string'),
                    EntityField(name='LastName', label='Last Name', type='string', required=True),
                    EntityField(name='Company', label='Company', type='string', required=True),
                    EntityField(name='Email', label='Email', type='string'),
                    EntityField(name='Phone', label='Phone', type='string'),
                    EntityField(name='Status', label='Status', type='string'),
                    EntityField(name='LeadSource', label='Lead Source', type='string'),
                    EntityField(name='Industry', label='Industry', type='string'),
                ],
            ),
        }
        
        return schemas.get(entity_name)
    
    async def list_records(
        self,
        entity_name: str,
        filters: Dict[str, Any] = None,
        fields: List[str] = None,
        page: int = 1,
        page_size: int = 100,
        modified_since: datetime = None
    ) -> Tuple[List[Dict], bool]:
        """List records using SOQL query"""
        sf_entity = self.get_remote_entity_name(entity_name)
        
        # Get fields
        if not fields:
            schema = self.get_entity_schema(sf_entity)
            if schema:
                fields = [f.name for f in schema.fields]
            else:
                fields = ['Id', 'Name']
        
        # Build SOQL query
        query = f"SELECT {', '.join(fields)} FROM {sf_entity}"
        
        # Add WHERE clause
        conditions = []
        
        if modified_since:
            conditions.append(f"LastModifiedDate >= {modified_since.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f"{key} = '{value}'")
                elif isinstance(value, bool):
                    conditions.append(f"{key} = {str(value).lower()}")
                elif value is None:
                    conditions.append(f"{key} = null")
                else:
                    conditions.append(f"{key} = {value}")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Add pagination
        offset = (page - 1) * page_size
        query += f" LIMIT {page_size} OFFSET {offset}"
        
        # Execute query
        from urllib.parse import quote
        result = await self._make_request('GET', f"query?q={quote(query)}")
        
        records = result.get('records', [])
        has_more = result.get('nextRecordsUrl') is not None or len(records) == page_size
        
        return records, has_more
    
    async def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
        """Get single record by ID"""
        sf_entity = self.get_remote_entity_name(entity_name)
        
        try:
            return await self._make_request('GET', f'sobjects/{sf_entity}/{record_id}')
        except Exception as e:
            if '404' in str(e) or 'NOT_FOUND' in str(e):
                return None
            raise
    
    async def create_record(self, entity_name: str, data: Dict) -> Dict:
        """Create new record"""
        sf_entity = self.get_remote_entity_name(entity_name)
        
        result = await self._make_request('POST', f'sobjects/{sf_entity}', data=data)
        
        # Salesforce returns only the ID, fetch full record
        if result.get('id'):
            return await self.get_record(entity_name, result['id'])
        
        return result
    
    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """Update existing record"""
        sf_entity = self.get_remote_entity_name(entity_name)
        
        # Remove read-only fields
        data.pop('Id', None)
        data.pop('attributes', None)
        
        await self._make_request('PATCH', f'sobjects/{sf_entity}/{record_id}', data=data)
        
        return await self.get_record(entity_name, record_id)
    
    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """Delete record"""
        sf_entity = self.get_remote_entity_name(entity_name)
        
        try:
            await self._make_request('DELETE', f'sobjects/{sf_entity}/{record_id}')
            return True
        except:
            return False
    
    # ==================== Bulk Operations ====================
    
    async def bulk_create(self, entity_name: str, records: List[Dict]) -> SyncResult:
        """Create multiple records using Composite API"""
        sf_entity = self.get_remote_entity_name(entity_name)
        result = SyncResult(success=True)
        
        # Salesforce Composite API supports up to 25 records per request
        batch_size = 25
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            composite_request = {
                'allOrNone': False,
                'compositeRequest': [
                    {
                        'method': 'POST',
                        'url': f'/services/data/{self.API_VERSION}/sobjects/{sf_entity}',
                        'referenceId': f'record_{j}',
                        'body': record
                    }
                    for j, record in enumerate(batch)
                ]
            }
            
            try:
                response = await self._make_request('POST', 'composite', data=composite_request)
                
                for item in response.get('compositeResponse', []):
                    if item.get('httpStatusCode') == 201:
                        result.records_created += 1
                    else:
                        result.add_error(
                            record_id=item.get('referenceId', 'unknown'),
                            error=str(item.get('body', [{}])[0].get('message', 'Unknown error'))
                        )
            
            except Exception as e:
                for record in batch:
                    result.add_error(record_id='batch', error=str(e))
        
        result.records_processed = result.records_created + result.records_failed
        result.success = result.records_failed == 0
        
        return result
    
    # ==================== Salesforce-Specific Methods ====================
    
    async def convert_lead(
        self,
        lead_id: str,
        account_id: str = None,
        contact_id: str = None,
        opportunity_name: str = None,
        converted_status: str = 'Closed - Converted'
    ) -> Dict:
        """Convert a lead to Account/Contact/Opportunity"""
        data = {
            'leadId': lead_id,
            'convertedStatus': converted_status,
        }
        
        if account_id:
            data['accountId'] = account_id
        
        if contact_id:
            data['contactId'] = contact_id
        
        if opportunity_name:
            data['opportunityName'] = opportunity_name
        else:
            data['doNotCreateOpportunity'] = True
        
        result = await self._make_request('POST', 'sobjects/Lead/convert', data=[data])
        
        return result[0] if result else {}
    
    async def search(self, search_term: str, objects: List[str] = None) -> Dict:
        """Search across objects using SOSL"""
        from urllib.parse import quote
        
        objects_clause = ''
        if objects:
            objects_clause = ' IN ' + ', '.join(objects)
        
        sosl = f"FIND {{{search_term}}}{objects_clause}"
        
        result = await self._make_request('GET', f"search?q={quote(sosl)}")
        return result
    
    async def describe_object(self, object_name: str) -> Dict:
        """Get object metadata/schema"""
        return await self._make_request('GET', f'sobjects/{object_name}/describe')
```

---

## TASK 7: HUBSPOT CONNECTOR

### 7.1 HubSpot CRM Connector

**File:** `backend/app/integrations/connectors/crm/hubspot_connector.py`

```python
"""
HubSpot Connector
Integration with HubSpot CRM
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import logging

from app.integrations.core.base_connector import (
    BaseConnector, ConnectorConfig, EntitySchema, EntityField
)

logger = logging.getLogger(__name__)


class HubSpotConnector(BaseConnector):
    """HubSpot CRM connector"""
    
    PROVIDER_NAME = 'hubspot'
    PROVIDER_LABEL = 'HubSpot'
    CATEGORY = 'crm'
    
    # OAuth URLs
    OAUTH_AUTHORIZATION_URL = 'https://app.hubspot.com/oauth/authorize'
    OAUTH_TOKEN_URL = 'https://api.hubapi.com/oauth/v1/token'
    OAUTH_SCOPES = [
        'crm.objects.contacts.read', 'crm.objects.contacts.write',
        'crm.objects.companies.read', 'crm.objects.companies.write',
        'crm.objects.deals.read', 'crm.objects.deals.write',
        'crm.schemas.contacts.read', 'crm.schemas.companies.read',
        'crm.schemas.deals.read'
    ]
    
    # API Configuration
    API_BASE_URL = 'https://api.hubapi.com'
    
    # Rate limiting: 100 requests per 10 seconds
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_PERIOD = 10
    
    # Entity mappings
    SUPPORTED_ENTITIES = {
        'customer': 'contacts',
        'contact': 'contacts',
        'company': 'companies',
        'opportunity': 'deals',
        'deal': 'deals',
        'product': 'products',
        'ticket': 'tickets',
    }
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None
    ) -> Dict[str, Any]:
        """Make API request"""
        url = f"{self.API_BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data,
                timeout=30.0
            )
            
            if response.status_code == 401:
                raise Exception("Authentication failed")
            
            if response.status_code == 204:
                return {}
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', str(response.status_code))
                raise Exception(f"HubSpot API error: {error_msg}")
            
            return response.json()
    
    # ==================== Authentication ====================
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL"""
        from urllib.parse import urlencode
        
        params = {
            'client_id': self.config.client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.OAUTH_SCOPES),
            'state': state,
        }
        
        return f"{self.OAUTH_AUTHORIZATION_URL}?{urlencode(params)}"
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                data={
                    'grant_type': 'authorization_code',
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'code': code,
                    'redirect_uri': redirect_uri,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh expired access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'refresh_token': refresh_token,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Token refresh failed: {response.text}")
            
            return response.json()
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            result = await self._make_request('GET', 'crm/v3/objects/contacts?limit=1')
            return True, "Connected to HubSpot"
        except Exception as e:
            return False, str(e)
    
    # ==================== Entity Operations ====================
    
    def get_entity_schema(self, entity_name: str) -> EntitySchema:
        """Get schema for HubSpot entity"""
        schemas = {
            'contacts': EntitySchema(
                name='contacts',
                label='Contact',
                id_field='id',
                supports_bulk=True,
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='email', label='Email', type='string'),
                    EntityField(name='firstname', label='First Name', type='string'),
                    EntityField(name='lastname', label='Last Name', type='string'),
                    EntityField(name='phone', label='Phone', type='string'),
                    EntityField(name='company', label='Company', type='string'),
                    EntityField(name='jobtitle', label='Job Title', type='string'),
                    EntityField(name='lifecyclestage', label='Lifecycle Stage', type='string'),
                    EntityField(name='hs_lead_status', label='Lead Status', type='string'),
                    EntityField(name='address', label='Address', type='string'),
                    EntityField(name='city', label='City', type='string'),
                    EntityField(name='state', label='State', type='string'),
                    EntityField(name='zip', label='Postal Code', type='string'),
                    EntityField(name='country', label='Country', type='string'),
                ],
            ),
            'companies': EntitySchema(
                name='companies',
                label='Company',
                id_field='id',
                supports_bulk=True,
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='name', label='Company Name', type='string', required=True),
                    EntityField(name='domain', label='Domain', type='string'),
                    EntityField(name='industry', label='Industry', type='string'),
                    EntityField(name='phone', label='Phone', type='string'),
                    EntityField(name='address', label='Address', type='string'),
                    EntityField(name='city', label='City', type='string'),
                    EntityField(name='state', label='State', type='string'),
                    EntityField(name='zip', label='Postal Code', type='string'),
                    EntityField(name='country', label='Country', type='string'),
                    EntityField(name='numberofemployees', label='Employees', type='number'),
                    EntityField(name='annualrevenue', label='Annual Revenue', type='number'),
                ],
            ),
            'deals': EntitySchema(
                name='deals',
                label='Deal',
                id_field='id',
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='dealname', label='Deal Name', type='string', required=True),
                    EntityField(name='amount', label='Amount', type='number'),
                    EntityField(name='dealstage', label='Deal Stage', type='string', required=True),
                    EntityField(name='pipeline', label='Pipeline', type='string'),
                    EntityField(name='closedate', label='Close Date', type='date'),
                    EntityField(name='hubspot_owner_id', label='Owner ID', type='string'),
                    EntityField(name='description', label='Description', type='string'),
                ],
            ),
        }
        
        return schemas.get(entity_name)
    
    async def list_records(
        self,
        entity_name: str,
        filters: Dict[str, Any] = None,
        fields: List[str] = None,
        page: int = 1,
        page_size: int = 100,
        modified_since: datetime = None
    ) -> Tuple[List[Dict], bool]:
        """List records with pagination"""
        hs_entity = self.get_remote_entity_name(entity_name)
        
        params = {
            'limit': min(page_size, 100),  # HubSpot max is 100
        }
        
        if fields:
            params['properties'] = ','.join(fields)
        
        # Handle pagination with after cursor
        # For simplicity, we'll use limit/offset approach
        
        # Build filter groups for search
        filter_groups = []
        
        if modified_since:
            filter_groups.append({
                'filters': [{
                    'propertyName': 'hs_lastmodifieddate',
                    'operator': 'GTE',
                    'value': int(modified_since.timestamp() * 1000)
                }]
            })
        
        if filters:
            filter_list = []
            for key, value in filters.items():
                filter_list.append({
                    'propertyName': key,
                    'operator': 'EQ',
                    'value': str(value)
                })
            if filter_list:
                filter_groups.append({'filters': filter_list})
        
        if filter_groups:
            # Use search API
            search_body = {
                'filterGroups': filter_groups,
                'limit': params['limit'],
            }
            
            if fields:
                search_body['properties'] = fields
            
            result = await self._make_request(
                'POST',
                f'crm/v3/objects/{hs_entity}/search',
                data=search_body
            )
        else:
            # Use list API
            result = await self._make_request(
                'GET',
                f'crm/v3/objects/{hs_entity}',
                params=params
            )
        
        records = result.get('results', [])
        has_more = result.get('paging', {}).get('next') is not None
        
        # Flatten properties
        flat_records = []
        for record in records:
            flat_record = {'id': record.get('id')}
            flat_record.update(record.get('properties', {}))
            flat_records.append(flat_record)
        
        return flat_records, has_more
    
    async def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
        """Get single record by ID"""
        hs_entity = self.get_remote_entity_name(entity_name)
        
        try:
            result = await self._make_request(
                'GET',
                f'crm/v3/objects/{hs_entity}/{record_id}'
            )
            
            flat_record = {'id': result.get('id')}
            flat_record.update(result.get('properties', {}))
            return flat_record
        except Exception as e:
            if '404' in str(e):
                return None
            raise
    
    async def create_record(self, entity_name: str, data: Dict) -> Dict:
        """Create new record"""
        hs_entity = self.get_remote_entity_name(entity_name)
        
        # Remove id if present
        data.pop('id', None)
        
        result = await self._make_request(
            'POST',
            f'crm/v3/objects/{hs_entity}',
            data={'properties': data}
        )
        
        flat_record = {'id': result.get('id')}
        flat_record.update(result.get('properties', {}))
        return flat_record
    
    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """Update existing record"""
        hs_entity = self.get_remote_entity_name(entity_name)
        
        # Remove id if present
        data.pop('id', None)
        
        result = await self._make_request(
            'PATCH',
            f'crm/v3/objects/{hs_entity}/{record_id}',
            data={'properties': data}
        )
        
        flat_record = {'id': result.get('id')}
        flat_record.update(result.get('properties', {}))
        return flat_record
    
    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """Delete record"""
        hs_entity = self.get_remote_entity_name(entity_name)
        
        try:
            await self._make_request(
                'DELETE',
                f'crm/v3/objects/{hs_entity}/{record_id}'
            )
            return True
        except:
            return False
    
    # ==================== HubSpot-Specific Methods ====================
    
    async def associate_records(
        self,
        from_object: str,
        from_id: str,
        to_object: str,
        to_id: str,
        association_type: str = None
    ) -> bool:
        """Associate two records"""
        endpoint = f'crm/v3/objects/{from_object}/{from_id}/associations/{to_object}/{to_id}'
        
        if association_type:
            endpoint += f'/{association_type}'
        
        await self._make_request('PUT', endpoint)
        return True
    
    async def get_pipelines(self, object_type: str = 'deals') -> List[Dict]:
        """Get pipelines and stages"""
        result = await self._make_request(
            'GET',
            f'crm/v3/pipelines/{object_type}'
        )
        return result.get('results', [])
    
    async def create_engagement(
        self,
        engagement_type: str,
        contact_ids: List[str] = None,
        company_ids: List[str] = None,
        deal_ids: List[str] = None,
        metadata: Dict = None
    ) -> Dict:
        """Create an engagement (note, email, call, meeting, task)"""
        data = {
            'engagement': {
                'type': engagement_type.upper(),
                'timestamp': int(datetime.utcnow().timestamp() * 1000),
            },
            'associations': {
                'contactIds': contact_ids or [],
                'companyIds': company_ids or [],
                'dealIds': deal_ids or [],
            },
            'metadata': metadata or {},
        }
        
        return await self._make_request(
            'POST',
            'engagements/v1/engagements',
            data=data
        )
```

---

## Continue to Part 3 for E-Commerce, Banking, Shipping Connectors & Frontend

---

*Phase 14 Tasks Part 2 - LogiAccounting Pro*
*Accounting & CRM Connectors*
