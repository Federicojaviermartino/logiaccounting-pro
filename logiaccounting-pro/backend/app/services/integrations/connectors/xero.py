"""
Phase 14: Xero Connector
Integration with Xero Accounting API
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import logging
import base64

from ..base_connector import (
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

    def get_entity_schema(self, entity_name: str) -> Optional[EntitySchema]:
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
                    EntityField(name='SalesDetails.UnitPrice', label='Sale Price', type='number'),
                    EntityField(name='PurchaseDetails.UnitPrice', label='Purchase Price', type='number'),
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

        params = {'page': page}
        headers = self._get_headers()

        if modified_since:
            headers['If-Modified-Since'] = modified_since.strftime('%Y-%m-%dT%H:%M:%S')

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
        has_more = len(records) == 100

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
        schema = self.get_entity_schema(xero_entity)
        id_field = schema.id_field if schema else 'id'
        data[id_field] = record_id

        payload = {xero_entity: [data]}
        result = await self._make_request('POST', xero_entity, data=payload)

        records = result.get(xero_entity, [])
        return records[0] if records else {}

    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """Archive/delete record"""
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
        invoice_type: str = 'ACCREC',
        invoice_date: str = None,
        due_date: str = None
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

        return await self.create_record('invoice', data)

    async def approve_invoice(self, invoice_id: str) -> Dict:
        """Approve a draft invoice"""
        return await self.update_record('invoice', invoice_id, {
            'InvoiceID': invoice_id,
            'Status': 'AUTHORISED'
        })

    async def get_profit_and_loss(self, from_date: str, to_date: str) -> Dict:
        """Get profit and loss report"""
        params = {'fromDate': from_date, 'toDate': to_date}
        result = await self._make_request('GET', 'Reports/ProfitAndLoss', params=params)
        return result.get('Reports', [{}])[0]

    async def get_balance_sheet(self, date: str = None) -> Dict:
        """Get balance sheet report"""
        params = {}
        if date:
            params['date'] = date
        result = await self._make_request('GET', 'Reports/BalanceSheet', params=params)
        return result.get('Reports', [{}])[0]
