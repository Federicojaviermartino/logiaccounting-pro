"""
Phase 14: HubSpot Connector
Integration with HubSpot CRM
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
from app.utils.datetime_utils import utc_now
import logging

from ..base_connector import (
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

    def get_entity_schema(self, entity_name: str) -> Optional[EntitySchema]:
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
                    EntityField(name='address', label='Address', type='string'),
                    EntityField(name='city', label='City', type='string'),
                    EntityField(name='state', label='State', type='string'),
                    EntityField(name='zip', label='Postal Code', type='string'),
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

        params = {'limit': min(page_size, 100)}

        if fields:
            params['properties'] = ','.join(fields)

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
            result = await self._make_request(
                'GET',
                f'crm/v3/objects/{hs_entity}',
                params=params
            )

        records = result.get('results', [])
        has_more = result.get('paging', {}).get('next') is not None

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
        result = await self._make_request('GET', f'crm/v3/pipelines/{object_type}')
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
                'timestamp': int(utc_now().timestamp() * 1000),
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
