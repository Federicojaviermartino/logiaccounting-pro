"""
Phase 14: QuickBooks Online Connector
Full integration with QuickBooks Online API
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import logging
import base64

from ..base_connector import (
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

    def get_entity_schema(self, entity_name: str) -> Optional[EntitySchema]:
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

    async def record_payment(
        self,
        customer_id: str,
        amount: float,
        invoice_id: str = None,
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
