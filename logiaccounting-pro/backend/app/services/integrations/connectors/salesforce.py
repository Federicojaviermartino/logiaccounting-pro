"""
Phase 14: Salesforce Connector
Integration with Salesforce CRM
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import logging
from urllib.parse import quote

from ..base_connector import (
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

    # Rate limiting
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
            return True, f"Connected to Salesforce (API {self.API_VERSION})"
        except Exception as e:
            return False, str(e)

    # ==================== Entity Operations ====================

    def get_entity_schema(self, entity_name: str) -> Optional[EntitySchema]:
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
                    EntityField(name='Title', label='Title', type='string'),
                    EntityField(name='AccountId', label='Account ID', type='string'),
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

        if not fields:
            schema = self.get_entity_schema(sf_entity)
            if schema:
                fields = [f.name for f in schema.fields]
            else:
                fields = ['Id', 'Name']

        query = f"SELECT {', '.join(fields)} FROM {sf_entity}"

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

        offset = (page - 1) * page_size
        query += f" LIMIT {page_size} OFFSET {offset}"

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

        if result.get('id'):
            return await self.get_record(entity_name, result['id'])

        return result

    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """Update existing record"""
        sf_entity = self.get_remote_entity_name(entity_name)

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

    # ==================== Salesforce-Specific Methods ====================

    async def search(self, search_term: str, objects: List[str] = None) -> Dict:
        """Search across objects using SOSL"""
        objects_clause = ''
        if objects:
            objects_clause = ' IN ' + ', '.join(objects)

        sosl = f"FIND {{{search_term}}}{objects_clause}"

        result = await self._make_request('GET', f"search?q={quote(sosl)}")
        return result

    async def describe_object(self, object_name: str) -> Dict:
        """Get object metadata/schema"""
        return await self._make_request('GET', f'sobjects/{object_name}/describe')

    async def bulk_create(self, entity_name: str, records: List[Dict]) -> SyncResult:
        """Create multiple records using Composite API"""
        sf_entity = self.get_remote_entity_name(entity_name)
        result = SyncResult(success=True)

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
