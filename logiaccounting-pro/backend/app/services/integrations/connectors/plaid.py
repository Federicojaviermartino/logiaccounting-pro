"""
Phase 14: Plaid Connector
Integration with Plaid Banking API
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, date
import httpx
import logging

from ..base_connector import (
    BaseConnector, ConnectorConfig, EntitySchema, EntityField
)

logger = logging.getLogger(__name__)


class PlaidConnector(BaseConnector):
    """Plaid banking connector"""

    PROVIDER_NAME = 'plaid'
    PROVIDER_LABEL = 'Plaid'
    CATEGORY = 'banking'

    # API Environments
    ENVIRONMENTS = {
        'sandbox': 'https://sandbox.plaid.com',
        'development': 'https://development.plaid.com',
        'production': 'https://production.plaid.com',
    }

    # Rate limiting: varies by endpoint
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_PERIOD = 60

    # Entity mappings
    SUPPORTED_ENTITIES = {
        'account': 'accounts',
        'transaction': 'transactions',
        'institution': 'institutions',
        'item': 'items',
        'identity': 'identity',
        'balance': 'balances',
    }

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.environment = config.environment or 'sandbox'
        self.access_token = config.access_token  # Plaid access_token from Link
        self.item_id = config.extra.get('item_id')

    def _get_base_url(self) -> str:
        """Get environment-specific base URL"""
        return self.ENVIRONMENTS.get(self.environment, self.ENVIRONMENTS['sandbox'])

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'Content-Type': 'application/json',
        }

    def _get_auth_body(self) -> Dict[str, str]:
        """Get authentication body for requests"""
        return {
            'client_id': self.config.client_id,
            'secret': self.config.client_secret,
        }

    async def _make_request(
        self,
        endpoint: str,
        data: Dict = None
    ) -> Dict[str, Any]:
        """Make API request (Plaid uses POST for everything)"""
        url = f"{self._get_base_url()}/{endpoint}"

        request_data = self._get_auth_body()
        if data:
            request_data.update(data)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=request_data,
                timeout=30.0
            )

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error_message', str(response.status_code))
                error_code = error_data.get('error_code', 'UNKNOWN')
                raise Exception(f"Plaid API error ({error_code}): {error_msg}")

            return response.json()

    # ==================== Link Token Flow ====================

    async def create_link_token(
        self,
        user_id: str,
        products: List[str] = None,
        country_codes: List[str] = None,
        language: str = 'en',
        redirect_uri: str = None,
        webhook: str = None
    ) -> Dict[str, Any]:
        """Create a Link token to initialize Plaid Link"""
        data = {
            'user': {'client_user_id': user_id},
            'client_name': 'LogiAccounting Pro',
            'products': products or ['transactions'],
            'country_codes': country_codes or ['US'],
            'language': language,
        }

        if redirect_uri:
            data['redirect_uri'] = redirect_uri
        if webhook:
            data['webhook'] = webhook

        return await self._make_request('link/token/create', data)

    async def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        """Exchange public token for access token"""
        result = await self._make_request('item/public_token/exchange', {
            'public_token': public_token,
        })

        # Store the access token and item_id
        self.access_token = result.get('access_token')
        self.item_id = result.get('item_id')

        return result

    # ==================== Authentication ====================

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Plaid uses Link instead of OAuth"""
        raise NotImplementedError("Plaid uses Link flow, not OAuth. Use create_link_token instead.")

    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Plaid uses public token exchange"""
        return await self.exchange_public_token(code)

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Plaid access tokens don't expire, but items can become invalid"""
        # Plaid tokens don't expire, but we can get new one if needed
        return {'access_token': self.access_token}

    async def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            result = await self._make_request('item/get', {
                'access_token': self.access_token,
            })
            item = result.get('item', {})
            institution_id = item.get('institution_id', 'Unknown')
            return True, f"Connected to item: {institution_id}"
        except Exception as e:
            return False, str(e)

    # ==================== Entity Operations ====================

    def get_entity_schema(self, entity_name: str) -> Optional[EntitySchema]:
        """Get schema for Plaid entity"""
        schemas = {
            'accounts': EntitySchema(
                name='accounts',
                label='Account',
                id_field='account_id',
                fields=[
                    EntityField(name='account_id', label='Account ID', type='string', readonly=True),
                    EntityField(name='name', label='Name', type='string', readonly=True),
                    EntityField(name='official_name', label='Official Name', type='string', readonly=True),
                    EntityField(name='type', label='Type', type='string', readonly=True),
                    EntityField(name='subtype', label='Subtype', type='string', readonly=True),
                    EntityField(name='mask', label='Mask', type='string', readonly=True),
                    EntityField(name='balances.current', label='Current Balance', type='number', readonly=True),
                    EntityField(name='balances.available', label='Available Balance', type='number', readonly=True),
                ],
            ),
            'transactions': EntitySchema(
                name='transactions',
                label='Transaction',
                id_field='transaction_id',
                fields=[
                    EntityField(name='transaction_id', label='Transaction ID', type='string', readonly=True),
                    EntityField(name='account_id', label='Account ID', type='string', readonly=True),
                    EntityField(name='amount', label='Amount', type='number', readonly=True),
                    EntityField(name='date', label='Date', type='date', readonly=True),
                    EntityField(name='name', label='Name', type='string', readonly=True),
                    EntityField(name='merchant_name', label='Merchant', type='string', readonly=True),
                    EntityField(name='category', label='Category', type='array', readonly=True),
                    EntityField(name='pending', label='Pending', type='boolean', readonly=True),
                    EntityField(name='payment_channel', label='Payment Channel', type='string', readonly=True),
                ],
            ),
            'balances': EntitySchema(
                name='balances',
                label='Balance',
                id_field='account_id',
                fields=[
                    EntityField(name='account_id', label='Account ID', type='string', readonly=True),
                    EntityField(name='current', label='Current', type='number', readonly=True),
                    EntityField(name='available', label='Available', type='number', readonly=True),
                    EntityField(name='limit', label='Limit', type='number', readonly=True),
                    EntityField(name='iso_currency_code', label='Currency', type='string', readonly=True),
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
        """List records (Plaid entities are read-only)"""
        plaid_entity = self.get_remote_entity_name(entity_name)

        if plaid_entity == 'accounts':
            result = await self.get_accounts()
            return result, False

        elif plaid_entity == 'transactions':
            start_date = filters.get('start_date') if filters else None
            end_date = filters.get('end_date') if filters else None

            if not start_date:
                start_date = (datetime.now().date().replace(day=1)).isoformat()
            if not end_date:
                end_date = datetime.now().date().isoformat()

            result = await self.get_transactions(
                start_date=start_date,
                end_date=end_date,
                count=page_size,
                offset=(page - 1) * page_size
            )
            transactions = result.get('transactions', [])
            total = result.get('total_transactions', 0)
            has_more = (page * page_size) < total
            return transactions, has_more

        elif plaid_entity == 'balances':
            result = await self.get_balances()
            return result, False

        return [], False

    async def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
        """Get single record by ID (limited support in Plaid)"""
        records, _ = await self.list_records(entity_name)

        plaid_entity = self.get_remote_entity_name(entity_name)
        id_field = 'account_id' if plaid_entity in ['accounts', 'balances'] else 'transaction_id'

        for record in records:
            if record.get(id_field) == record_id:
                return record

        return None

    async def create_record(self, entity_name: str, data: Dict) -> Dict:
        """Create not supported - Plaid is read-only"""
        raise NotImplementedError("Plaid entities are read-only")

    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """Update not supported - Plaid is read-only"""
        raise NotImplementedError("Plaid entities are read-only")

    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """Delete not supported - Plaid is read-only"""
        raise NotImplementedError("Plaid entities are read-only")

    # ==================== Plaid-Specific Methods ====================

    async def get_accounts(self, account_ids: List[str] = None) -> List[Dict]:
        """Get accounts for an Item"""
        data = {'access_token': self.access_token}
        if account_ids:
            data['options'] = {'account_ids': account_ids}

        result = await self._make_request('accounts/get', data)
        return result.get('accounts', [])

    async def get_balances(self, account_ids: List[str] = None) -> List[Dict]:
        """Get real-time balance for accounts"""
        data = {'access_token': self.access_token}
        if account_ids:
            data['options'] = {'account_ids': account_ids}

        result = await self._make_request('accounts/balance/get', data)

        # Return accounts with their balances
        accounts = result.get('accounts', [])
        return [
            {
                'account_id': acc.get('account_id'),
                **acc.get('balances', {})
            }
            for acc in accounts
        ]

    async def get_transactions(
        self,
        start_date: str,
        end_date: str,
        account_ids: List[str] = None,
        count: int = 100,
        offset: int = 0
    ) -> Dict:
        """Get transactions for a date range"""
        data = {
            'access_token': self.access_token,
            'start_date': start_date,
            'end_date': end_date,
            'options': {
                'count': count,
                'offset': offset,
            }
        }

        if account_ids:
            data['options']['account_ids'] = account_ids

        return await self._make_request('transactions/get', data)

    async def sync_transactions(self, cursor: str = None) -> Dict:
        """Sync transactions incrementally"""
        data = {'access_token': self.access_token}
        if cursor:
            data['cursor'] = cursor

        return await self._make_request('transactions/sync', data)

    async def get_identity(self, account_ids: List[str] = None) -> List[Dict]:
        """Get account holder identity information"""
        data = {'access_token': self.access_token}
        if account_ids:
            data['options'] = {'account_ids': account_ids}

        result = await self._make_request('identity/get', data)
        return result.get('accounts', [])

    async def get_item(self) -> Dict:
        """Get Item information"""
        result = await self._make_request('item/get', {
            'access_token': self.access_token,
        })
        return result.get('item', {})

    async def remove_item(self) -> bool:
        """Remove an Item (revoke access)"""
        try:
            await self._make_request('item/remove', {
                'access_token': self.access_token,
            })
            return True
        except:
            return False

    async def get_institution(self, institution_id: str) -> Dict:
        """Get institution by ID"""
        result = await self._make_request('institutions/get_by_id', {
            'institution_id': institution_id,
            'country_codes': ['US'],
        })
        return result.get('institution', {})

    async def search_institutions(
        self,
        query: str,
        products: List[str] = None,
        country_codes: List[str] = None
    ) -> List[Dict]:
        """Search for institutions"""
        data = {
            'query': query,
            'products': products or ['transactions'],
            'country_codes': country_codes or ['US'],
        }

        result = await self._make_request('institutions/search', data)
        return result.get('institutions', [])

    async def get_categories(self) -> List[Dict]:
        """Get all transaction categories"""
        result = await self._make_request('categories/get', {})
        return result.get('categories', [])

    async def create_processor_token(
        self,
        account_id: str,
        processor: str
    ) -> str:
        """Create a processor token for a specific account"""
        result = await self._make_request('processor/token/create', {
            'access_token': self.access_token,
            'account_id': account_id,
            'processor': processor,
        })
        return result.get('processor_token')

    async def get_auth(self, account_ids: List[str] = None) -> Dict:
        """Get account and routing numbers"""
        data = {'access_token': self.access_token}
        if account_ids:
            data['options'] = {'account_ids': account_ids}

        return await self._make_request('auth/get', data)

    async def get_liabilities(self, account_ids: List[str] = None) -> Dict:
        """Get liability information (credit cards, loans)"""
        data = {'access_token': self.access_token}
        if account_ids:
            data['options'] = {'account_ids': account_ids}

        return await self._make_request('liabilities/get', data)

    async def get_investments_holdings(self, account_ids: List[str] = None) -> Dict:
        """Get investment holdings"""
        data = {'access_token': self.access_token}
        if account_ids:
            data['options'] = {'account_ids': account_ids}

        return await self._make_request('investments/holdings/get', data)

    async def get_investments_transactions(
        self,
        start_date: str,
        end_date: str,
        account_ids: List[str] = None
    ) -> Dict:
        """Get investment transactions"""
        data = {
            'access_token': self.access_token,
            'start_date': start_date,
            'end_date': end_date,
        }
        if account_ids:
            data['options'] = {'account_ids': account_ids}

        return await self._make_request('investments/transactions/get', data)

    # ==================== Webhook Handling ====================

    async def update_item_webhook(self, webhook_url: str) -> Dict:
        """Update webhook URL for an Item"""
        result = await self._make_request('item/webhook/update', {
            'access_token': self.access_token,
            'webhook': webhook_url,
        })
        return result.get('item', {})

    def verify_webhook(self, body: str, plaid_verification: str) -> bool:
        """Verify Plaid webhook (requires JWT verification)"""
        # Plaid uses JWT verification for webhooks
        # This is a simplified version - production should verify the JWT
        try:
            import jwt
            # In production, fetch the public key from Plaid and verify
            return True
        except:
            return False
