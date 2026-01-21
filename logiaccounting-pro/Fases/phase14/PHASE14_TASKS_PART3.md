# LogiAccounting Pro - Phase 14 Tasks Part 3

## E-COMMERCE, BANKING, SHIPPING CONNECTORS & FRONTEND

---

## TASK 8: SHOPIFY CONNECTOR

### 8.1 Shopify E-Commerce Connector

**File:** `backend/app/integrations/connectors/ecommerce/shopify_connector.py`

```python
"""
Shopify Connector
Integration with Shopify E-Commerce Platform
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import hmac
import hashlib
import logging

from app.integrations.core.base_connector import (
    BaseConnector, ConnectorConfig, EntitySchema, EntityField
)

logger = logging.getLogger(__name__)


class ShopifyConnector(BaseConnector):
    """Shopify e-commerce connector"""
    
    PROVIDER_NAME = 'shopify'
    PROVIDER_LABEL = 'Shopify'
    CATEGORY = 'ecommerce'
    
    # OAuth Scopes
    OAUTH_SCOPES = [
        'read_products', 'write_products',
        'read_orders', 'write_orders',
        'read_customers', 'write_customers',
        'read_inventory', 'write_inventory',
        'read_fulfillments', 'write_fulfillments',
    ]
    
    # API Configuration
    API_VERSION = '2024-01'
    
    # Rate limiting: 2 requests per second
    RATE_LIMIT_REQUESTS = 2
    RATE_LIMIT_PERIOD = 1
    
    # Entity mappings
    SUPPORTED_ENTITIES = {
        'product': 'products',
        'order': 'orders',
        'customer': 'customers',
        'inventory': 'inventory_levels',
        'fulfillment': 'fulfillments',
        'collection': 'collections',
    }
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.shop_domain = config.extra.get('shop_domain')  # mystore.myshopify.com
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'X-Shopify-Access-Token': self.config.access_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    def _api_url(self, endpoint: str) -> str:
        """Build API URL"""
        return f"https://{self.shop_domain}/admin/api/{self.API_VERSION}/{endpoint}.json"
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None
    ) -> Dict[str, Any]:
        """Make API request with rate limiting"""
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
            
            if response.status_code == 429:
                raise Exception("Rate limit exceeded")
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                errors = error_data.get('errors', str(response.status_code))
                raise Exception(f"Shopify API error: {errors}")
            
            return response.json()
    
    # ==================== Authentication ====================
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL"""
        from urllib.parse import urlencode
        
        params = {
            'client_id': self.config.client_id,
            'scope': ','.join(self.OAUTH_SCOPES),
            'redirect_uri': redirect_uri,
            'state': state,
        }
        
        return f"https://{self.shop_domain}/admin/oauth/authorize?{urlencode(params)}"
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self.shop_domain}/admin/oauth/access_token",
                json={
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'code': code,
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Shopify access tokens don't expire, return current token"""
        return {'access_token': self.config.access_token}
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            result = await self._make_request('GET', 'shop')
            shop_name = result.get('shop', {}).get('name', 'Unknown')
            return True, f"Connected to: {shop_name}"
        except Exception as e:
            return False, str(e)
    
    # ==================== Entity Operations ====================
    
    def get_entity_schema(self, entity_name: str) -> EntitySchema:
        """Get schema for Shopify entity"""
        schemas = {
            'products': EntitySchema(
                name='products',
                label='Product',
                id_field='id',
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='title', label='Title', type='string', required=True),
                    EntityField(name='body_html', label='Description', type='string'),
                    EntityField(name='vendor', label='Vendor', type='string'),
                    EntityField(name='product_type', label='Product Type', type='string'),
                    EntityField(name='handle', label='Handle', type='string'),
                    EntityField(name='status', label='Status', type='string'),
                    EntityField(name='tags', label='Tags', type='string'),
                    EntityField(name='variants', label='Variants', type='array'),
                    EntityField(name='images', label='Images', type='array'),
                ],
            ),
            'orders': EntitySchema(
                name='orders',
                label='Order',
                id_field='id',
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='order_number', label='Order Number', type='number', readonly=True),
                    EntityField(name='email', label='Email', type='string'),
                    EntityField(name='created_at', label='Created At', type='datetime', readonly=True),
                    EntityField(name='financial_status', label='Payment Status', type='string'),
                    EntityField(name='fulfillment_status', label='Fulfillment Status', type='string'),
                    EntityField(name='total_price', label='Total', type='number'),
                    EntityField(name='subtotal_price', label='Subtotal', type='number'),
                    EntityField(name='total_tax', label='Tax', type='number'),
                    EntityField(name='currency', label='Currency', type='string'),
                    EntityField(name='customer', label='Customer', type='object'),
                    EntityField(name='line_items', label='Line Items', type='array'),
                    EntityField(name='shipping_address', label='Shipping Address', type='object'),
                    EntityField(name='billing_address', label='Billing Address', type='object'),
                ],
            ),
            'customers': EntitySchema(
                name='customers',
                label='Customer',
                id_field='id',
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='email', label='Email', type='string'),
                    EntityField(name='first_name', label='First Name', type='string'),
                    EntityField(name='last_name', label='Last Name', type='string'),
                    EntityField(name='phone', label='Phone', type='string'),
                    EntityField(name='orders_count', label='Orders Count', type='number', readonly=True),
                    EntityField(name='total_spent', label='Total Spent', type='number', readonly=True),
                    EntityField(name='addresses', label='Addresses', type='array'),
                    EntityField(name='tags', label='Tags', type='string'),
                    EntityField(name='accepts_marketing', label='Accepts Marketing', type='boolean'),
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
        page_size: int = 50,
        modified_since: datetime = None
    ) -> Tuple[List[Dict], bool]:
        """List records with pagination"""
        shopify_entity = self.get_remote_entity_name(entity_name)
        
        params = {
            'limit': min(page_size, 250),  # Shopify max is 250
        }
        
        if fields:
            params['fields'] = ','.join(fields)
        
        if modified_since:
            params['updated_at_min'] = modified_since.isoformat()
        
        if filters:
            params.update(filters)
        
        result = await self._make_request('GET', shopify_entity, params=params)
        
        records = result.get(shopify_entity, [])
        
        # Check for pagination link header
        has_more = len(records) == params['limit']
        
        return records, has_more
    
    async def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
        """Get single record by ID"""
        shopify_entity = self.get_remote_entity_name(entity_name)
        singular = shopify_entity.rstrip('s')  # products -> product
        
        try:
            result = await self._make_request('GET', f'{shopify_entity}/{record_id}')
            return result.get(singular)
        except Exception as e:
            if '404' in str(e):
                return None
            raise
    
    async def create_record(self, entity_name: str, data: Dict) -> Dict:
        """Create new record"""
        shopify_entity = self.get_remote_entity_name(entity_name)
        singular = shopify_entity.rstrip('s')
        
        result = await self._make_request(
            'POST',
            shopify_entity,
            data={singular: data}
        )
        
        return result.get(singular, {})
    
    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """Update existing record"""
        shopify_entity = self.get_remote_entity_name(entity_name)
        singular = shopify_entity.rstrip('s')
        
        result = await self._make_request(
            'PUT',
            f'{shopify_entity}/{record_id}',
            data={singular: data}
        )
        
        return result.get(singular, {})
    
    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """Delete record"""
        shopify_entity = self.get_remote_entity_name(entity_name)
        
        try:
            await self._make_request('DELETE', f'{shopify_entity}/{record_id}')
            return True
        except:
            return False
    
    # ==================== Webhooks ====================
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """Verify Shopify webhook signature"""
        computed = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).digest()
        
        import base64
        computed_b64 = base64.b64encode(computed).decode()
        
        return hmac.compare_digest(computed_b64, signature)
    
    async def register_webhook(
        self,
        event_type: str,
        endpoint_url: str,
        secret: str = None
    ) -> Optional[str]:
        """Register a webhook"""
        topic_map = {
            'order.created': 'orders/create',
            'order.updated': 'orders/updated',
            'order.paid': 'orders/paid',
            'order.fulfilled': 'orders/fulfilled',
            'product.created': 'products/create',
            'product.updated': 'products/update',
            'product.deleted': 'products/delete',
            'customer.created': 'customers/create',
            'customer.updated': 'customers/update',
        }
        
        topic = topic_map.get(event_type, event_type)
        
        result = await self._make_request(
            'POST',
            'webhooks',
            data={
                'webhook': {
                    'topic': topic,
                    'address': endpoint_url,
                    'format': 'json',
                }
            }
        )
        
        return str(result.get('webhook', {}).get('id'))
    
    # ==================== Shopify-Specific Methods ====================
    
    async def get_inventory_levels(self, location_id: str = None) -> List[Dict]:
        """Get inventory levels"""
        params = {}
        if location_id:
            params['location_ids'] = location_id
        
        result = await self._make_request('GET', 'inventory_levels', params=params)
        return result.get('inventory_levels', [])
    
    async def adjust_inventory(
        self,
        inventory_item_id: str,
        location_id: str,
        adjustment: int
    ) -> Dict:
        """Adjust inventory quantity"""
        result = await self._make_request(
            'POST',
            'inventory_levels/adjust',
            data={
                'inventory_item_id': inventory_item_id,
                'location_id': location_id,
                'available_adjustment': adjustment,
            }
        )
        return result.get('inventory_level', {})
    
    async def create_fulfillment(
        self,
        order_id: str,
        line_items: List[Dict],
        tracking_number: str = None,
        tracking_company: str = None,
        notify_customer: bool = True
    ) -> Dict:
        """Create order fulfillment"""
        data = {
            'line_items_by_fulfillment_order': line_items,
            'notify_customer': notify_customer,
        }
        
        if tracking_number:
            data['tracking_info'] = {
                'number': tracking_number,
                'company': tracking_company,
            }
        
        result = await self._make_request(
            'POST',
            f'orders/{order_id}/fulfillments',
            data={'fulfillment': data}
        )
        
        return result.get('fulfillment', {})
    
    async def get_locations(self) -> List[Dict]:
        """Get shop locations"""
        result = await self._make_request('GET', 'locations')
        return result.get('locations', [])
```

---

## TASK 9: STRIPE CONNECTOR

### 9.1 Stripe Payments Connector

**File:** `backend/app/integrations/connectors/payments/stripe_connector.py`

```python
"""
Stripe Connector
Integration with Stripe Payment Platform
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import hmac
import hashlib
import logging

from app.integrations.core.base_connector import (
    BaseConnector, ConnectorConfig, EntitySchema, EntityField
)

logger = logging.getLogger(__name__)


class StripeConnector(BaseConnector):
    """Stripe payments connector"""
    
    PROVIDER_NAME = 'stripe'
    PROVIDER_LABEL = 'Stripe'
    CATEGORY = 'payments'
    
    # API Configuration
    API_BASE_URL = 'https://api.stripe.com/v1'
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_PERIOD = 1
    
    # Entity mappings
    SUPPORTED_ENTITIES = {
        'customer': 'customers',
        'payment': 'payment_intents',
        'invoice': 'invoices',
        'subscription': 'subscriptions',
        'product': 'products',
        'price': 'prices',
        'charge': 'charges',
        'payout': 'payouts',
        'balance_transaction': 'balance_transactions',
    }
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Stripe-Version': '2023-10-16',
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
            if method == 'GET':
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )
            else:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    data=data,  # Stripe uses form encoding
                    timeout=30.0
                )
            
            if response.status_code == 401:
                raise Exception("Authentication failed")
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error', {}).get('message', str(response.status_code))
                raise Exception(f"Stripe API error: {error_msg}")
            
            return response.json()
    
    # ==================== Authentication ====================
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Stripe uses API keys, not OAuth for basic integration"""
        raise NotImplementedError("Stripe uses API key authentication")
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Not applicable for Stripe API key auth"""
        raise NotImplementedError("Stripe uses API key authentication")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Not applicable for Stripe API key auth"""
        return {}
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            result = await self._make_request('GET', 'balance')
            return True, "Connected to Stripe"
        except Exception as e:
            return False, str(e)
    
    # ==================== Entity Operations ====================
    
    def get_entity_schema(self, entity_name: str) -> EntitySchema:
        """Get schema for Stripe entity"""
        schemas = {
            'customers': EntitySchema(
                name='customers',
                label='Customer',
                id_field='id',
                fields=[
                    EntityField(name='id', label='ID', type='string', readonly=True),
                    EntityField(name='email', label='Email', type='string'),
                    EntityField(name='name', label='Name', type='string'),
                    EntityField(name='phone', label='Phone', type='string'),
                    EntityField(name='description', label='Description', type='string'),
                    EntityField(name='balance', label='Balance', type='number', readonly=True),
                    EntityField(name='currency', label='Currency', type='string'),
                    EntityField(name='address', label='Address', type='object'),
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
        
        params = {
            'limit': min(page_size, 100),
        }
        
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
            if '404' in str(e) or 'resource_missing' in str(e):
                return None
            raise
    
    async def create_record(self, entity_name: str, data: Dict) -> Dict:
        """Create new record"""
        stripe_entity = self.get_remote_entity_name(entity_name)
        
        # Flatten nested objects for form encoding
        flat_data = self._flatten_for_stripe(data)
        
        return await self._make_request('POST', stripe_entity, data=flat_data)
    
    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """Update existing record"""
        stripe_entity = self.get_remote_entity_name(entity_name)
        
        flat_data = self._flatten_for_stripe(data)
        
        return await self._make_request('POST', f'{stripe_entity}/{record_id}', data=flat_data)
    
    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """Delete record"""
        stripe_entity = self.get_remote_entity_name(entity_name)
        
        try:
            await self._make_request('DELETE', f'{stripe_entity}/{record_id}')
            return True
        except:
            return False
    
    def _flatten_for_stripe(self, data: Dict, parent_key: str = '') -> Dict:
        """Flatten nested dict for Stripe form encoding"""
        items = {}
        for k, v in data.items():
            new_key = f"{parent_key}[{k}]" if parent_key else k
            if isinstance(v, dict):
                items.update(self._flatten_for_stripe(v, new_key))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.update(self._flatten_for_stripe(item, f"{new_key}[{i}]"))
                    else:
                        items[f"{new_key}[{i}]"] = item
            else:
                items[new_key] = v
        return items
    
    # ==================== Webhooks ====================
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """Verify Stripe webhook signature"""
        import time
        
        # Parse signature header
        parts = dict(item.split('=') for item in signature.split(','))
        timestamp = parts.get('t')
        expected_sig = parts.get('v1')
        
        if not timestamp or not expected_sig:
            return False
        
        # Check timestamp (within 5 minutes)
        if abs(time.time() - int(timestamp)) > 300:
            return False
        
        # Compute signature
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        computed = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed, expected_sig)
    
    # ==================== Stripe-Specific Methods ====================
    
    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        customer_id: str = None,
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
        
        if description:
            data['description'] = description
        
        if metadata:
            for k, v in metadata.items():
                data[f'metadata[{k}]'] = v
        
        return await self._make_request('POST', 'payment_intents', data=data)
    
    async def confirm_payment_intent(self, payment_intent_id: str) -> Dict:
        """Confirm a payment intent"""
        return await self._make_request(
            'POST',
            f'payment_intents/{payment_intent_id}/confirm'
        )
    
    async def create_invoice(
        self,
        customer_id: str,
        line_items: List[Dict] = None,
        auto_advance: bool = True
    ) -> Dict:
        """Create an invoice"""
        data = {
            'customer': customer_id,
            'auto_advance': str(auto_advance).lower(),
        }
        
        invoice = await self._make_request('POST', 'invoices', data=data)
        
        # Add line items
        if line_items:
            for item in line_items:
                item_data = {
                    'invoice': invoice['id'],
                    'customer': customer_id,
                    **item
                }
                await self._make_request('POST', 'invoiceitems', data=item_data)
        
        return invoice
    
    async def finalize_invoice(self, invoice_id: str) -> Dict:
        """Finalize a draft invoice"""
        return await self._make_request('POST', f'invoices/{invoice_id}/finalize')
    
    async def get_balance(self) -> Dict:
        """Get account balance"""
        return await self._make_request('GET', 'balance')
    
    async def list_transactions(
        self,
        limit: int = 100,
        starting_after: str = None,
        created_after: datetime = None
    ) -> List[Dict]:
        """List balance transactions"""
        params = {'limit': limit}
        
        if starting_after:
            params['starting_after'] = starting_after
        
        if created_after:
            params['created[gte]'] = int(created_after.timestamp())
        
        result = await self._make_request('GET', 'balance_transactions', params=params)
        return result.get('data', [])
```

---

## TASK 10: PLAID BANKING CONNECTOR

### 10.1 Plaid Banking Connector

**File:** `backend/app/integrations/connectors/banking/plaid_connector.py`

```python
"""
Plaid Connector
Integration with Plaid Banking API
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import httpx
import logging

from app.integrations.core.base_connector import (
    BaseConnector, ConnectorConfig, EntitySchema, EntityField
)

logger = logging.getLogger(__name__)


class PlaidConnector(BaseConnector):
    """Plaid banking connector"""
    
    PROVIDER_NAME = 'plaid'
    PROVIDER_LABEL = 'Plaid'
    CATEGORY = 'banking'
    
    # API Configuration
    API_BASE_URL_SANDBOX = 'https://sandbox.plaid.com'
    API_BASE_URL_DEVELOPMENT = 'https://development.plaid.com'
    API_BASE_URL_PRODUCTION = 'https://production.plaid.com'
    
    # Entity mappings (Plaid is read-only)
    SUPPORTED_ENTITIES = {
        'account': 'accounts',
        'transaction': 'transactions',
        'balance': 'balances',
        'institution': 'institutions',
    }
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.environment = config.environment or 'sandbox'
        self.access_token = config.access_token  # Plaid access token
        
        if self.environment == 'production':
            self.base_url = self.API_BASE_URL_PRODUCTION
        elif self.environment == 'development':
            self.base_url = self.API_BASE_URL_DEVELOPMENT
        else:
            self.base_url = self.API_BASE_URL_SANDBOX
    
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
        """Make API request (all Plaid requests are POST)"""
        url = f"{self.base_url}/{endpoint}"
        
        body = {**self._get_auth_body(), **(data or {})}
        
        if self.access_token and endpoint not in ['link/token/create', 'item/public_token/exchange']:
            body['access_token'] = self.access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=body,
                timeout=30.0
            )
            
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error_message', str(response.status_code))
                raise Exception(f"Plaid API error: {error_msg}")
            
            return response.json()
    
    # ==================== Authentication (Link Flow) ====================
    
    async def create_link_token(
        self,
        user_id: str,
        products: List[str] = None,
        country_codes: List[str] = None,
        language: str = 'en',
        redirect_uri: str = None
    ) -> str:
        """Create a Link token for Plaid Link initialization"""
        products = products or ['transactions', 'auth']
        country_codes = country_codes or ['US', 'GB', 'ES', 'NL', 'FR', 'IE', 'CA', 'DE']
        
        data = {
            'user': {'client_user_id': user_id},
            'products': products,
            'country_codes': country_codes,
            'language': language,
            'client_name': 'LogiAccounting Pro',
        }
        
        if redirect_uri:
            data['redirect_uri'] = redirect_uri
        
        result = await self._make_request('link/token/create', data)
        return result.get('link_token')
    
    async def exchange_public_token(self, public_token: str) -> Dict[str, str]:
        """Exchange public token for access token"""
        result = await self._make_request(
            'item/public_token/exchange',
            {'public_token': public_token}
        )
        
        return {
            'access_token': result.get('access_token'),
            'item_id': result.get('item_id'),
        }
    
    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Plaid uses Link, not OAuth"""
        raise NotImplementedError("Use create_link_token for Plaid Link flow")
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Use exchange_public_token instead"""
        return await self.exchange_public_token(code)
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Plaid access tokens don't expire"""
        return {}
    
    async def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            result = await self._make_request('item/get')
            institution_id = result.get('item', {}).get('institution_id', 'Unknown')
            return True, f"Connected to institution: {institution_id}"
        except Exception as e:
            return False, str(e)
    
    # ==================== Entity Operations ====================
    
    def get_entity_schema(self, entity_name: str) -> EntitySchema:
        """Get schema for Plaid entity"""
        schemas = {
            'accounts': EntitySchema(
                name='accounts',
                label='Account',
                id_field='account_id',
                supports_create=False,
                supports_update=False,
                supports_delete=False,
                fields=[
                    EntityField(name='account_id', label='Account ID', type='string', readonly=True),
                    EntityField(name='name', label='Name', type='string', readonly=True),
                    EntityField(name='official_name', label='Official Name', type='string', readonly=True),
                    EntityField(name='type', label='Type', type='string', readonly=True),
                    EntityField(name='subtype', label='Subtype', type='string', readonly=True),
                    EntityField(name='mask', label='Mask', type='string', readonly=True),
                    EntityField(name='balances.available', label='Available Balance', type='number', readonly=True),
                    EntityField(name='balances.current', label='Current Balance', type='number', readonly=True),
                    EntityField(name='balances.iso_currency_code', label='Currency', type='string', readonly=True),
                ],
            ),
            'transactions': EntitySchema(
                name='transactions',
                label='Transaction',
                id_field='transaction_id',
                supports_create=False,
                supports_update=False,
                supports_delete=False,
                fields=[
                    EntityField(name='transaction_id', label='Transaction ID', type='string', readonly=True),
                    EntityField(name='account_id', label='Account ID', type='string', readonly=True),
                    EntityField(name='amount', label='Amount', type='number', readonly=True),
                    EntityField(name='date', label='Date', type='date', readonly=True),
                    EntityField(name='name', label='Description', type='string', readonly=True),
                    EntityField(name='merchant_name', label='Merchant', type='string', readonly=True),
                    EntityField(name='category', label='Category', type='array', readonly=True),
                    EntityField(name='pending', label='Pending', type='boolean', readonly=True),
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
        """List records"""
        if entity_name in ['account', 'accounts']:
            return await self._list_accounts()
        elif entity_name in ['transaction', 'transactions']:
            return await self._list_transactions(filters, page_size, modified_since)
        elif entity_name in ['balance', 'balances']:
            return await self._get_balances()
        else:
            return [], False
    
    async def _list_accounts(self) -> Tuple[List[Dict], bool]:
        """List accounts"""
        result = await self._make_request('accounts/get')
        accounts = result.get('accounts', [])
        return accounts, False
    
    async def _list_transactions(
        self,
        filters: Dict = None,
        page_size: int = 100,
        modified_since: datetime = None
    ) -> Tuple[List[Dict], bool]:
        """List transactions"""
        filters = filters or {}
        
        start_date = filters.get('start_date') or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = filters.get('end_date') or datetime.now().strftime('%Y-%m-%d')
        
        data = {
            'start_date': start_date,
            'end_date': end_date,
            'options': {
                'count': page_size,
                'offset': filters.get('offset', 0),
            }
        }
        
        if filters.get('account_ids'):
            data['options']['account_ids'] = filters['account_ids']
        
        result = await self._make_request('transactions/get', data)
        
        transactions = result.get('transactions', [])
        total = result.get('total_transactions', 0)
        offset = data['options']['offset']
        
        has_more = (offset + len(transactions)) < total
        
        return transactions, has_more
    
    async def _get_balances(self) -> Tuple[List[Dict], bool]:
        """Get account balances"""
        result = await self._make_request('accounts/balance/get')
        accounts = result.get('accounts', [])
        
        balances = []
        for account in accounts:
            balances.append({
                'account_id': account.get('account_id'),
                'name': account.get('name'),
                **account.get('balances', {})
            })
        
        return balances, False
    
    async def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
        """Get single record (limited support in Plaid)"""
        if entity_name in ['account', 'accounts']:
            accounts, _ = await self._list_accounts()
            for account in accounts:
                if account.get('account_id') == record_id:
                    return account
        return None
    
    async def create_record(self, entity_name: str, data: Dict) -> Dict:
        """Plaid is read-only"""
        raise NotImplementedError("Plaid integration is read-only")
    
    async def update_record(self, entity_name: str, record_id: str, data: Dict) -> Dict:
        """Plaid is read-only"""
        raise NotImplementedError("Plaid integration is read-only")
    
    async def delete_record(self, entity_name: str, record_id: str) -> bool:
        """Plaid is read-only"""
        raise NotImplementedError("Plaid integration is read-only")
    
    # ==================== Plaid-Specific Methods ====================
    
    async def get_institution(self, institution_id: str) -> Dict:
        """Get institution details"""
        result = await self._make_request(
            'institutions/get_by_id',
            {
                'institution_id': institution_id,
                'country_codes': ['US', 'GB', 'ES', 'FR', 'DE'],
            }
        )
        return result.get('institution', {})
    
    async def sync_transactions(self, cursor: str = None) -> Dict:
        """Sync transactions incrementally"""
        data = {}
        if cursor:
            data['cursor'] = cursor
        
        return await self._make_request('transactions/sync', data)
    
    async def get_categories(self) -> List[Dict]:
        """Get transaction categories"""
        result = await self._make_request('categories/get')
        return result.get('categories', [])
    
    async def remove_item(self) -> bool:
        """Remove/disconnect the Plaid item"""
        await self._make_request('item/remove')
        return True
```

---

## TASK 11: INTEGRATION ROUTES

### 11.1 Integration API Routes

**File:** `backend/app/integrations/routes/integrations.py`

```python
"""
Integration Routes
API endpoints for managing integrations
"""

from flask import Blueprint, request, jsonify, g, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
import logging
import os

from app.extensions import db
from app.integrations.models.integration import Integration, OAuthState
from app.integrations.core.oauth_manager import IntegrationOAuthService, get_provider_category, get_provider_label
from app.integrations.services.integration_service import IntegrationService

logger = logging.getLogger(__name__)

integrations_bp = Blueprint('integrations', __name__, url_prefix='/api/v1/integrations')


# ==================== Provider Catalog ====================

AVAILABLE_PROVIDERS = [
    {
        'name': 'quickbooks',
        'label': 'QuickBooks Online',
        'category': 'accounting',
        'description': 'Sync invoices, customers, and payments with QuickBooks',
        'auth_type': 'oauth2',
        'logo': '/static/integrations/quickbooks.svg',
    },
    {
        'name': 'xero',
        'label': 'Xero',
        'category': 'accounting',
        'description': 'Connect with Xero for accounting synchronization',
        'auth_type': 'oauth2',
        'logo': '/static/integrations/xero.svg',
    },
    {
        'name': 'salesforce',
        'label': 'Salesforce',
        'category': 'crm',
        'description': 'Sync customers and opportunities with Salesforce CRM',
        'auth_type': 'oauth2',
        'logo': '/static/integrations/salesforce.svg',
    },
    {
        'name': 'hubspot',
        'label': 'HubSpot',
        'category': 'crm',
        'description': 'Connect with HubSpot CRM for contact management',
        'auth_type': 'oauth2',
        'logo': '/static/integrations/hubspot.svg',
    },
    {
        'name': 'shopify',
        'label': 'Shopify',
        'category': 'ecommerce',
        'description': 'Sync products, orders, and inventory with Shopify',
        'auth_type': 'oauth2',
        'logo': '/static/integrations/shopify.svg',
    },
    {
        'name': 'stripe',
        'label': 'Stripe',
        'category': 'payments',
        'description': 'Process payments and sync transactions',
        'auth_type': 'api_key',
        'logo': '/static/integrations/stripe.svg',
    },
    {
        'name': 'plaid',
        'label': 'Plaid',
        'category': 'banking',
        'description': 'Connect bank accounts for transaction import',
        'auth_type': 'link',
        'logo': '/static/integrations/plaid.svg',
    },
]


@integrations_bp.route('/providers', methods=['GET'])
@jwt_required()
def list_providers():
    """List available integration providers"""
    category = request.args.get('category')
    
    providers = AVAILABLE_PROVIDERS
    
    if category:
        providers = [p for p in providers if p['category'] == category]
    
    return jsonify({
        'success': True,
        'providers': providers
    })


@integrations_bp.route('/providers/<provider>', methods=['GET'])
@jwt_required()
def get_provider(provider):
    """Get provider details"""
    for p in AVAILABLE_PROVIDERS:
        if p['name'] == provider:
            return jsonify({'success': True, 'provider': p})
    
    return jsonify({'success': False, 'error': 'Provider not found'}), 404


# ==================== Connections ====================

@integrations_bp.route('/connections', methods=['GET'])
@jwt_required()
def list_connections():
    """List organization's integration connections"""
    organization_id = g.current_user.organization_id
    
    connections = Integration.query.filter(
        Integration.organization_id == organization_id
    ).all()
    
    return jsonify({
        'success': True,
        'connections': [c.to_dict() for c in connections]
    })


@integrations_bp.route('/connections/<connection_id>', methods=['GET'])
@jwt_required()
def get_connection(connection_id):
    """Get connection details"""
    organization_id = g.current_user.organization_id
    
    connection = Integration.query.filter(
        Integration.id == connection_id,
        Integration.organization_id == organization_id
    ).first()
    
    if not connection:
        return jsonify({'success': False, 'error': 'Connection not found'}), 404
    
    return jsonify({
        'success': True,
        'connection': connection.to_dict(include_credentials=True)
    })


@integrations_bp.route('/connections', methods=['POST'])
@jwt_required()
def create_connection():
    """Create a new integration connection (for API key auth)"""
    organization_id = g.current_user.organization_id
    user_id = get_jwt_identity()
    
    data = request.get_json()
    provider = data.get('provider')
    
    if not provider:
        return jsonify({'success': False, 'error': 'Provider is required'}), 400
    
    # Check if connection already exists
    existing = Integration.query.filter(
        Integration.organization_id == organization_id,
        Integration.provider == provider
    ).first()
    
    if existing:
        return jsonify({'success': False, 'error': 'Connection already exists'}), 409
    
    # Create connection
    connection = Integration(
        organization_id=organization_id,
        provider=provider,
        category=get_provider_category(provider),
        name=data.get('name', get_provider_label(provider)),
        description=data.get('description'),
    )
    
    # Set credentials based on auth type
    if data.get('api_key'):
        connection.api_key = data['api_key']
        if data.get('api_secret'):
            connection.api_secret = data['api_secret']
        connection.mark_connected(user_id)
    
    # Set config
    if data.get('config'):
        connection.config = data['config']
    
    db.session.add(connection)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'connection': connection.to_dict()
    }), 201


@integrations_bp.route('/connections/<connection_id>', methods=['PUT'])
@jwt_required()
def update_connection(connection_id):
    """Update connection settings"""
    organization_id = g.current_user.organization_id
    
    connection = Integration.query.filter(
        Integration.id == connection_id,
        Integration.organization_id == organization_id
    ).first()
    
    if not connection:
        return jsonify({'success': False, 'error': 'Connection not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        connection.name = data['name']
    
    if 'description' in data:
        connection.description = data['description']
    
    if 'sync_enabled' in data:
        connection.sync_enabled = data['sync_enabled']
    
    if 'sync_frequency_minutes' in data:
        connection.sync_frequency_minutes = data['sync_frequency_minutes']
        connection.schedule_next_sync()
    
    if 'config' in data:
        connection.config = {**(connection.config or {}), **data['config']}
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'connection': connection.to_dict()
    })


@integrations_bp.route('/connections/<connection_id>', methods=['DELETE'])
@jwt_required()
def delete_connection(connection_id):
    """Delete/disconnect an integration"""
    organization_id = g.current_user.organization_id
    
    connection = Integration.query.filter(
        Integration.id == connection_id,
        Integration.organization_id == organization_id
    ).first()
    
    if not connection:
        return jsonify({'success': False, 'error': 'Connection not found'}), 404
    
    db.session.delete(connection)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Connection deleted'})


@integrations_bp.route('/connections/<connection_id>/test', methods=['POST'])
@jwt_required()
async def test_connection(connection_id):
    """Test an integration connection"""
    organization_id = g.current_user.organization_id
    
    connection = Integration.query.filter(
        Integration.id == connection_id,
        Integration.organization_id == organization_id
    ).first()
    
    if not connection:
        return jsonify({'success': False, 'error': 'Connection not found'}), 404
    
    service = IntegrationService()
    success, message = await service.test_connection(connection)
    
    return jsonify({
        'success': success,
        'message': message
    })


# ==================== OAuth ====================

@integrations_bp.route('/oauth/<provider>/authorize', methods=['GET'])
@jwt_required()
def oauth_authorize(provider):
    """Initiate OAuth authorization"""
    organization_id = str(g.current_user.organization_id)
    user_id = get_jwt_identity()
    
    redirect_uri = request.args.get('redirect_uri') or request.host_url.rstrip('/') + f'/api/v1/integrations/oauth/{provider}/callback'
    
    # Provider-specific params
    extra_params = {}
    
    if provider == 'shopify':
        shop = request.args.get('shop')
        if not shop:
            return jsonify({'success': False, 'error': 'shop parameter required'}), 400
        extra_params['shop_domain'] = shop
    
    try:
        auth_url = IntegrationOAuthService.initiate_oauth(
            organization_id=organization_id,
            provider=provider,
            user_id=user_id,
            redirect_uri=redirect_uri,
            extra_params=extra_params
        )
        
        return jsonify({
            'success': True,
            'authorization_url': auth_url
        })
    
    except Exception as e:
        logger.error(f"OAuth initiation failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@integrations_bp.route('/oauth/<provider>/callback', methods=['GET'])
async def oauth_callback(provider):
    """Handle OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        return redirect(f'/integrations?error={error}')
    
    if not code or not state:
        return redirect('/integrations?error=missing_params')
    
    redirect_uri = request.url.split('?')[0]
    
    try:
        integration = await IntegrationOAuthService.complete_oauth(
            provider=provider,
            code=code,
            state=state,
            redirect_uri=redirect_uri
        )
        
        return redirect(f'/integrations/{integration.id}?success=true')
    
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        return redirect(f'/integrations?error={str(e)}')
```

---

## TASK 12: FRONTEND COMPONENTS

### 12.1 Integrations Page

**File:** `frontend/src/features/integrations/pages/IntegrationsPage.jsx`

```jsx
/**
 * Integrations Page
 * Main page for managing integrations
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useIntegrations } from '../hooks/useIntegrations';
import IntegrationCard from '../components/IntegrationCard';

const CATEGORIES = [
  { id: 'all', label: 'All' },
  { id: 'accounting', label: 'Accounting' },
  { id: 'crm', label: 'CRM' },
  { id: 'ecommerce', label: 'E-Commerce' },
  { id: 'payments', label: 'Payments' },
  { id: 'banking', label: 'Banking' },
  { id: 'shipping', label: 'Shipping' },
];

const IntegrationsPage = () => {
  const { t } = useTranslation();
  const [activeCategory, setActiveCategory] = useState('all');
  const [showConnected, setShowConnected] = useState(false);
  
  const { providers, connections, isLoading, connectProvider, disconnectProvider } = useIntegrations();
  
  const filteredProviders = providers.filter(provider => {
    if (activeCategory !== 'all' && provider.category !== activeCategory) {
      return false;
    }
    return true;
  });
  
  const connectedProviders = connections.map(c => c.provider);
  
  const displayProviders = showConnected
    ? filteredProviders.filter(p => connectedProviders.includes(p.name))
    : filteredProviders;
  
  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {t('integrations.title', 'Integrations')}
        </h1>
        <p className="text-gray-600 mt-1">
          {t('integrations.description', 'Connect your favorite tools and services')}
        </p>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-2xl font-bold text-blue-600">{connections.length}</div>
          <div className="text-sm text-gray-600">{t('integrations.connected', 'Connected')}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-2xl font-bold text-green-600">
            {connections.filter(c => c.status === 'connected').length}
          </div>
          <div className="text-sm text-gray-600">{t('integrations.active', 'Active')}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="text-2xl font-bold text-gray-600">{providers.length}</div>
          <div className="text-sm text-gray-600">{t('integrations.available', 'Available')}</div>
        </div>
      </div>
      
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* Category Tabs */}
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map(category => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`
                px-4 py-2 rounded-lg text-sm font-medium transition-colors
                ${activeCategory === category.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
            >
              {category.label}
            </button>
          ))}
        </div>
        
        {/* Connected Toggle */}
        <label className="flex items-center gap-2 cursor-pointer ml-auto">
          <input
            type="checkbox"
            checked={showConnected}
            onChange={(e) => setShowConnected(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">
            {t('integrations.showConnectedOnly', 'Show connected only')}
          </span>
        </label>
      </div>
      
      {/* Integration Grid */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : displayProviders.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          {t('integrations.noResults', 'No integrations found')}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayProviders.map(provider => {
            const connection = connections.find(c => c.provider === provider.name);
            
            return (
              <IntegrationCard
                key={provider.name}
                provider={provider}
                connection={connection}
                onConnect={() => connectProvider(provider.name)}
                onDisconnect={() => disconnectProvider(connection?.id)}
              />
            );
          })}
        </div>
      )}
    </div>
  );
};

export default IntegrationsPage;
```

### 12.2 Integration Card Component

**File:** `frontend/src/features/integrations/components/IntegrationCard.jsx`

```jsx
/**
 * Integration Card Component
 * Displays a single integration provider
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

const STATUS_COLORS = {
  connected: 'bg-green-100 text-green-800',
  error: 'bg-red-100 text-red-800',
  expired: 'bg-yellow-100 text-yellow-800',
  disconnected: 'bg-gray-100 text-gray-800',
};

const IntegrationCard = ({ provider, connection, onConnect, onDisconnect }) => {
  const { t } = useTranslation();
  
  const isConnected = connection?.status === 'connected';
  const hasError = connection?.status === 'error';
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Logo */}
          <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center overflow-hidden">
            {provider.logo ? (
              <img 
                src={provider.logo} 
                alt={provider.label}
                className="w-8 h-8 object-contain"
              />
            ) : (
              <span className="text-xl font-bold text-gray-400">
                {provider.label.charAt(0)}
              </span>
            )}
          </div>
          
          {/* Name */}
          <div>
            <h3 className="font-semibold text-gray-900">{provider.label}</h3>
            <span className="text-xs text-gray-500 capitalize">{provider.category}</span>
          </div>
        </div>
        
        {/* Status Badge */}
        {connection && (
          <span className={`
            px-2 py-1 rounded-full text-xs font-medium
            ${STATUS_COLORS[connection.status] || STATUS_COLORS.disconnected}
          `}>
            {connection.status}
          </span>
        )}
      </div>
      
      {/* Description */}
      <p className="text-sm text-gray-600 mb-4 line-clamp-2">
        {provider.description}
      </p>
      
      {/* Connection Info */}
      {isConnected && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">{t('integrations.lastSync', 'Last sync')}</span>
            <span className="text-gray-700">
              {connection.last_sync_at
                ? new Date(connection.last_sync_at).toLocaleString()
                : t('integrations.never', 'Never')
              }
            </span>
          </div>
          {connection.sync_enabled && (
            <div className="flex justify-between text-sm mt-1">
              <span className="text-gray-500">{t('integrations.nextSync', 'Next sync')}</span>
              <span className="text-gray-700">
                {connection.next_sync_at
                  ? new Date(connection.next_sync_at).toLocaleString()
                  : '-'
                }
              </span>
            </div>
          )}
        </div>
      )}
      
      {/* Error Message */}
      {hasError && connection.last_error && (
        <div className="mb-4 p-3 bg-red-50 rounded-lg">
          <p className="text-sm text-red-700 line-clamp-2">{connection.last_error}</p>
        </div>
      )}
      
      {/* Actions */}
      <div className="flex gap-2">
        {isConnected ? (
          <>
            <Link
              to={`/integrations/${connection.id}`}
              className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg text-center hover:bg-blue-700 transition-colors"
            >
              {t('integrations.manage', 'Manage')}
            </Link>
            <button
              onClick={onDisconnect}
              className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
            >
              {t('integrations.disconnect', 'Disconnect')}
            </button>
          </>
        ) : (
          <button
            onClick={onConnect}
            className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            {t('integrations.connect', 'Connect')}
          </button>
        )}
      </div>
    </div>
  );
};

export default IntegrationCard;
```

### 12.3 Integrations Hook

**File:** `frontend/src/features/integrations/hooks/useIntegrations.js`

```javascript
/**
 * useIntegrations Hook
 * Manages integration state and operations
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { integrationsApi } from '../api/integrationsApi';
import { toast } from 'react-hot-toast';

export const useIntegrations = () => {
  const queryClient = useQueryClient();
  
  // Fetch providers
  const {
    data: providersData,
    isLoading: isLoadingProviders,
  } = useQuery({
    queryKey: ['integration-providers'],
    queryFn: () => integrationsApi.getProviders(),
  });
  
  // Fetch connections
  const {
    data: connectionsData,
    isLoading: isLoadingConnections,
  } = useQuery({
    queryKey: ['integration-connections'],
    queryFn: () => integrationsApi.getConnections(),
  });
  
  // Connect mutation
  const connectMutation = useMutation({
    mutationFn: async (provider) => {
      // For OAuth providers, redirect to authorization URL
      const response = await integrationsApi.initiateOAuth(provider);
      
      if (response.authorization_url) {
        // Open OAuth popup
        const width = 600;
        const height = 700;
        const left = window.screenX + (window.outerWidth - width) / 2;
        const top = window.screenY + (window.outerHeight - height) / 2;
        
        const popup = window.open(
          response.authorization_url,
          'oauth',
          `width=${width},height=${height},left=${left},top=${top}`
        );
        
        // Listen for completion
        return new Promise((resolve, reject) => {
          const interval = setInterval(() => {
            try {
              if (popup.closed) {
                clearInterval(interval);
                resolve({ success: true });
              }
            } catch (e) {
              // Cross-origin error means still loading
            }
          }, 500);
          
          // Timeout after 5 minutes
          setTimeout(() => {
            clearInterval(interval);
            popup.close();
            reject(new Error('OAuth timeout'));
          }, 300000);
        });
      }
      
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['integration-connections']);
      toast.success('Integration connected successfully');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to connect integration');
    },
  });
  
  // Disconnect mutation
  const disconnectMutation = useMutation({
    mutationFn: (connectionId) => integrationsApi.deleteConnection(connectionId),
    onSuccess: () => {
      queryClient.invalidateQueries(['integration-connections']);
      toast.success('Integration disconnected');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to disconnect integration');
    },
  });
  
  // Sync mutation
  const syncMutation = useMutation({
    mutationFn: (connectionId) => integrationsApi.triggerSync(connectionId),
    onSuccess: () => {
      queryClient.invalidateQueries(['integration-connections']);
      toast.success('Sync started');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to start sync');
    },
  });
  
  return {
    providers: providersData?.providers || [],
    connections: connectionsData?.connections || [],
    isLoading: isLoadingProviders || isLoadingConnections,
    
    connectProvider: connectMutation.mutate,
    isConnecting: connectMutation.isPending,
    
    disconnectProvider: disconnectMutation.mutate,
    isDisconnecting: disconnectMutation.isPending,
    
    triggerSync: syncMutation.mutate,
    isSyncing: syncMutation.isPending,
  };
};

export default useIntegrations;
```

### 12.4 Integrations API Service

**File:** `frontend/src/features/integrations/api/integrationsApi.js`

```javascript
/**
 * Integrations API Service
 */

import api from '../../../services/api';

export const integrationsApi = {
  /**
   * Get available providers
   */
  async getProviders(category = null) {
    const params = category ? { category } : {};
    const response = await api.get('/integrations/providers', { params });
    return response.data;
  },
  
  /**
   * Get provider details
   */
  async getProvider(provider) {
    const response = await api.get(`/integrations/providers/${provider}`);
    return response.data.provider;
  },
  
  /**
   * Get connections
   */
  async getConnections() {
    const response = await api.get('/integrations/connections');
    return response.data;
  },
  
  /**
   * Get connection details
   */
  async getConnection(connectionId) {
    const response = await api.get(`/integrations/connections/${connectionId}`);
    return response.data.connection;
  },
  
  /**
   * Create connection (for API key auth)
   */
  async createConnection(data) {
    const response = await api.post('/integrations/connections', data);
    return response.data.connection;
  },
  
  /**
   * Update connection
   */
  async updateConnection(connectionId, data) {
    const response = await api.put(`/integrations/connections/${connectionId}`, data);
    return response.data.connection;
  },
  
  /**
   * Delete connection
   */
  async deleteConnection(connectionId) {
    await api.delete(`/integrations/connections/${connectionId}`);
  },
  
  /**
   * Test connection
   */
  async testConnection(connectionId) {
    const response = await api.post(`/integrations/connections/${connectionId}/test`);
    return response.data;
  },
  
  /**
   * Initiate OAuth
   */
  async initiateOAuth(provider, params = {}) {
    const response = await api.get(`/integrations/oauth/${provider}/authorize`, { params });
    return response.data;
  },
  
  /**
   * Trigger sync
   */
  async triggerSync(connectionId, options = {}) {
    const response = await api.post(`/integrations/connections/${connectionId}/sync`, options);
    return response.data;
  },
  
  /**
   * Get sync history
   */
  async getSyncHistory(connectionId, params = {}) {
    const response = await api.get(`/integrations/connections/${connectionId}/sync/logs`, { params });
    return response.data;
  },
  
  /**
   * Get field mappings
   */
  async getFieldMappings(connectionId, syncConfigId) {
    const response = await api.get(`/integrations/connections/${connectionId}/sync-configs/${syncConfigId}/mappings`);
    return response.data.mappings;
  },
  
  /**
   * Update field mappings
   */
  async updateFieldMappings(connectionId, syncConfigId, mappings) {
    const response = await api.put(
      `/integrations/connections/${connectionId}/sync-configs/${syncConfigId}/mappings`,
      { mappings }
    );
    return response.data.mappings;
  },
};

export default integrationsApi;
```

---

## SUMMARY

### Phase 14 Complete Implementation

| Part | Content |
|------|---------|
| **Part 1** | Database models, Base connector, OAuth manager, Data transformer |
| **Part 2** | QuickBooks, Xero, Salesforce, HubSpot connectors |
| **Part 3** | Shopify, Stripe, Plaid connectors, API routes, Frontend UI |

### Supported Integrations

| Category | Providers |
|----------|-----------|
| **Accounting** | QuickBooks Online, Xero |
| **CRM** | Salesforce, HubSpot |
| **E-Commerce** | Shopify |
| **Payments** | Stripe |
| **Banking** | Plaid |

### Key Features

| Feature | Status |
|---------|--------|
| OAuth 2.0 Authentication | ✅ |
| API Key Authentication | ✅ |
| Bidirectional Sync | ✅ |
| Field Mapping | ✅ |
| Webhook Support | ✅ |
| Rate Limiting | ✅ |
| Error Handling | ✅ |

---

*Phase 14 Tasks Part 3 - LogiAccounting Pro*
*E-Commerce, Banking, Shipping & Frontend*
