"""
Phase 14: Stripe Connector
Integration with Stripe Payment Platform
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import logging
import hmac
import hashlib

from ..base_connector import (
    BaseConnector, ConnectorConfig, EntitySchema, EntityField
)

logger = logging.getLogger(__name__)


class StripeConnector(BaseConnector):
    """Stripe payments connector"""

    PROVIDER_NAME = 'stripe'
    PROVIDER_LABEL = 'Stripe'
    CATEGORY = 'payments'

    # OAuth URLs
    OAUTH_AUTHORIZATION_URL = 'https://connect.stripe.com/oauth/authorize'
    OAUTH_TOKEN_URL = 'https://connect.stripe.com/oauth/token'
    OAUTH_SCOPES = ['read_write']

    # API Configuration
    API_BASE_URL = 'https://api.stripe.com/v1'
    API_VERSION = '2023-10-16'

    # Rate limiting: 100 requests per second (standard)
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_PERIOD = 1

    # Entity mappings
    SUPPORTED_ENTITIES = {
        'customer': 'customers',
        'payment': 'payment_intents',
        'charge': 'charges',
        'invoice': 'invoices',
        'subscription': 'subscriptions',
        'product': 'products',
        'price': 'prices',
        'payout': 'payouts',
        'refund': 'refunds',
    }

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.stripe_account_id = config.extra.get('stripe_account_id')

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        headers = {
            'Authorization': f'Bearer {self.config.access_token}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Stripe-Version': self.API_VERSION,
        }

        # For Connect accounts
        if self.stripe_account_id:
            headers['Stripe-Account'] = self.stripe_account_id

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
                params=params if method == 'GET' else None,
                data=data if method != 'GET' else None,
                timeout=30.0
            )

            if response.status_code == 401:
                raise Exception("Authentication failed")

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error = error_data.get('error', {})
                error_msg = error.get('message', str(response.status_code))
                raise Exception(f"Stripe API error: {error_msg}")

            return response.json()

    # ==================== Authentication ====================

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL for Stripe Connect"""
        from urllib.parse import urlencode

        params = {
            'client_id': self.config.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
            'scope': 'read_write',
        }

        return f"{self.OAUTH_AUTHORIZATION_URL}?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                data={
                    'grant_type': 'authorization_code',
                    'client_secret': self.config.client_secret,
                    'code': code,
                }
            )

            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")

            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                data={
                    'grant_type': 'refresh_token',
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
            result = await self._make_request('GET', 'balance')
            available = result.get('available', [{}])[0]
            currency = available.get('currency', 'usd').upper()
            amount = available.get('amount', 0) / 100
            return True, f"Connected to Stripe (Balance: {amount} {currency})"
        except Exception as e:
            return False, str(e)

    # ==================== Webhook Verification ====================

    def verify_webhook(self, payload: bytes, sig_header: str, endpoint_secret: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            elements = dict(item.split('=') for item in sig_header.split(','))
            timestamp = elements.get('t')
            signature = elements.get('v1')

            if not timestamp or not signature:
                return False

            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_signature = hmac.new(
                endpoint_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False

    # ==================== Entity Operations ====================

    def get_entity_schema(self, entity_name: str) -> Optional[EntitySchema]:
        """Get schema for Stripe entity"""
        schemas = {
            'customers': EntitySchema(
                name='customers',
                label='Customer',
                id_field='id',
                supports_bulk=True,
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='email', label='Email', type='string'),
                    EntityField(name='name', label='Name', type='string'),
                    EntityField(name='phone', label='Phone', type='string'),
                    EntityField(name='description', label='Description', type='string'),
                    EntityField(name='balance', label='Balance', type='number', readonly=True),
                    EntityField(name='currency', label='Currency', type='string'),
                    EntityField(name='default_source', label='Default Source', type='string'),
                    EntityField(name='metadata', label='Metadata', type='object'),
                ],
            ),
            'payment_intents': EntitySchema(
                name='payment_intents',
                label='Payment Intent',
                id_field='id',
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='amount', label='Amount', type='number', required=True),
                    EntityField(name='currency', label='Currency', type='string', required=True),
                    EntityField(name='customer', label='Customer ID', type='string'),
                    EntityField(name='description', label='Description', type='string'),
                    EntityField(name='status', label='Status', type='string', readonly=True),
                    EntityField(name='payment_method', label='Payment Method', type='string'),
                    EntityField(name='metadata', label='Metadata', type='object'),
                ],
            ),
            'invoices': EntitySchema(
                name='invoices',
                label='Invoice',
                id_field='id',
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='customer', label='Customer ID', type='string', required=True),
                    EntityField(name='amount_due', label='Amount Due', type='number', readonly=True),
                    EntityField(name='amount_paid', label='Amount Paid', type='number', readonly=True),
                    EntityField(name='currency', label='Currency', type='string'),
                    EntityField(name='status', label='Status', type='string', readonly=True),
                    EntityField(name='due_date', label='Due Date', type='number'),
                    EntityField(name='description', label='Description', type='string'),
                    EntityField(name='metadata', label='Metadata', type='object'),
                ],
            ),
            'subscriptions': EntitySchema(
                name='subscriptions',
                label='Subscription',
                id_field='id',
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='customer', label='Customer ID', type='string', required=True),
                    EntityField(name='status', label='Status', type='string', readonly=True),
                    EntityField(name='current_period_start', label='Period Start', type='number', readonly=True),
                    EntityField(name='current_period_end', label='Period End', type='number', readonly=True),
                    EntityField(name='cancel_at_period_end', label='Cancel at Period End', type='boolean'),
                    EntityField(name='items', label='Items', type='array'),
                    EntityField(name='metadata', label='Metadata', type='object'),
                ],
            ),
            'products': EntitySchema(
                name='products',
                label='Product',
                id_field='id',
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='name', label='Name', type='string', required=True),
                    EntityField(name='description', label='Description', type='string'),
                    EntityField(name='active', label='Active', type='boolean'),
                    EntityField(name='metadata', label='Metadata', type='object'),
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
        stripe_entity = self.get_remote_entity_name(entity_name)

        params = {'limit': min(page_size, 100)}

        if modified_since:
            params['created[gte]'] = int(modified_since.timestamp())

        if filters:
            params.update(filters)

        result = await self._make_request('GET', stripe_entity, params=params)

        records = result.get('data', [])
        has_more = result.get('has_more', False)

        return records, has_more

    async def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
        """Get single record by ID"""
        stripe_entity = self.get_remote_entity_name(entity_name)

        try:
            return await self._make_request('GET', f'{stripe_entity}/{record_id}')
        except Exception as e:
            if '404' in str(e) or 'No such' in str(e):
                return None
            raise

    async def create_record(self, entity_name: str, data: Dict) -> Dict:
        """Create new record"""
        stripe_entity = self.get_remote_entity_name(entity_name)

        # Flatten nested objects for form encoding
        flat_data = self._flatten_data(data)

        return await self._make_request('POST', stripe_entity, data=flat_data)

    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """Update existing record"""
        stripe_entity = self.get_remote_entity_name(entity_name)

        # Flatten nested objects for form encoding
        flat_data = self._flatten_data(data)

        return await self._make_request('POST', f'{stripe_entity}/{record_id}', data=flat_data)

    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """Delete record"""
        stripe_entity = self.get_remote_entity_name(entity_name)

        try:
            await self._make_request('DELETE', f'{stripe_entity}/{record_id}')
            return True
        except:
            return False

    def _flatten_data(self, data: Dict, parent_key: str = '') -> Dict:
        """Flatten nested dict for Stripe's form encoding"""
        items = {}
        for key, value in data.items():
            new_key = f"{parent_key}[{key}]" if parent_key else key

            if isinstance(value, dict):
                items.update(self._flatten_data(value, new_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        items.update(self._flatten_data(item, f"{new_key}[{i}]"))
                    else:
                        items[f"{new_key}[{i}]"] = item
            else:
                items[new_key] = value

        return items

    # ==================== Stripe-Specific Methods ====================

    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        customer_id: str = None,
        payment_method: str = None,
        description: str = None,
        metadata: Dict = None
    ) -> Dict:
        """Create a payment intent"""
        data = {
            'amount': amount,
            'currency': currency,
        }

        if customer_id:
            data['customer'] = customer_id
        if payment_method:
            data['payment_method'] = payment_method
        if description:
            data['description'] = description
        if metadata:
            data['metadata'] = metadata

        return await self.create_record('payment', data)

    async def confirm_payment_intent(self, payment_intent_id: str, payment_method: str = None) -> Dict:
        """Confirm a payment intent"""
        data = {}
        if payment_method:
            data['payment_method'] = payment_method

        return await self._make_request(
            'POST',
            f'payment_intents/{payment_intent_id}/confirm',
            data=data
        )

    async def cancel_payment_intent(self, payment_intent_id: str) -> Dict:
        """Cancel a payment intent"""
        return await self._make_request(
            'POST',
            f'payment_intents/{payment_intent_id}/cancel'
        )

    async def create_refund(
        self,
        payment_intent_id: str = None,
        charge_id: str = None,
        amount: int = None,
        reason: str = None
    ) -> Dict:
        """Create a refund"""
        data = {}
        if payment_intent_id:
            data['payment_intent'] = payment_intent_id
        if charge_id:
            data['charge'] = charge_id
        if amount:
            data['amount'] = amount
        if reason:
            data['reason'] = reason

        return await self._make_request('POST', 'refunds', data=data)

    async def create_invoice(
        self,
        customer_id: str,
        auto_advance: bool = True,
        collection_method: str = 'charge_automatically',
        description: str = None,
        metadata: Dict = None
    ) -> Dict:
        """Create an invoice"""
        data = {
            'customer': customer_id,
            'auto_advance': auto_advance,
            'collection_method': collection_method,
        }

        if description:
            data['description'] = description
        if metadata:
            data['metadata'] = metadata

        return await self.create_record('invoice', data)

    async def finalize_invoice(self, invoice_id: str) -> Dict:
        """Finalize a draft invoice"""
        return await self._make_request('POST', f'invoices/{invoice_id}/finalize')

    async def pay_invoice(self, invoice_id: str, payment_method: str = None) -> Dict:
        """Pay an invoice"""
        data = {}
        if payment_method:
            data['payment_method'] = payment_method

        return await self._make_request('POST', f'invoices/{invoice_id}/pay', data=data)

    async def void_invoice(self, invoice_id: str) -> Dict:
        """Void an invoice"""
        return await self._make_request('POST', f'invoices/{invoice_id}/void')

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        quantity: int = 1,
        trial_period_days: int = None,
        metadata: Dict = None
    ) -> Dict:
        """Create a subscription"""
        data = {
            'customer': customer_id,
            'items[0][price]': price_id,
            'items[0][quantity]': quantity,
        }

        if trial_period_days:
            data['trial_period_days'] = trial_period_days
        if metadata:
            for key, value in metadata.items():
                data[f'metadata[{key}]'] = value

        return await self._make_request('POST', 'subscriptions', data=data)

    async def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Dict:
        """Cancel a subscription"""
        if at_period_end:
            return await self.update_record('subscription', subscription_id, {
                'cancel_at_period_end': True
            })
        else:
            return await self.delete_record('subscription', subscription_id)

    async def get_balance(self) -> Dict:
        """Get account balance"""
        return await self._make_request('GET', 'balance')

    async def get_balance_transactions(
        self,
        limit: int = 100,
        created_gte: datetime = None
    ) -> List[Dict]:
        """Get balance transactions"""
        params = {'limit': limit}
        if created_gte:
            params['created[gte]'] = int(created_gte.timestamp())

        result = await self._make_request('GET', 'balance_transactions', params=params)
        return result.get('data', [])

    async def create_payout(
        self,
        amount: int,
        currency: str,
        description: str = None,
        metadata: Dict = None
    ) -> Dict:
        """Create a payout"""
        data = {
            'amount': amount,
            'currency': currency,
        }

        if description:
            data['description'] = description
        if metadata:
            for key, value in metadata.items():
                data[f'metadata[{key}]'] = value

        return await self._make_request('POST', 'payouts', data=data)

    async def register_webhook(self, url: str, events: List[str]) -> Dict:
        """Register a webhook endpoint"""
        data = {
            'url': url,
            'enabled_events[]': events,
        }

        return await self._make_request('POST', 'webhook_endpoints', data=data)
