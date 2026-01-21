"""
Phase 14: Shopify Connector
Integration with Shopify E-commerce Platform
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx
import logging
import hmac
import hashlib
import base64

from ..base_connector import (
    BaseConnector, ConnectorConfig, EntitySchema, EntityField, SyncResult
)

logger = logging.getLogger(__name__)


class ShopifyConnector(BaseConnector):
    """Shopify e-commerce connector"""

    PROVIDER_NAME = 'shopify'
    PROVIDER_LABEL = 'Shopify'
    CATEGORY = 'ecommerce'

    # OAuth URLs (shop-specific)
    OAUTH_SCOPES = [
        'read_products', 'write_products',
        'read_orders', 'write_orders',
        'read_customers', 'write_customers',
        'read_inventory', 'write_inventory',
        'read_fulfillments', 'write_fulfillments',
    ]

    # API Configuration
    API_VERSION = '2024-01'

    # Rate limiting: 2 requests per second (bucket leak rate)
    RATE_LIMIT_REQUESTS = 40
    RATE_LIMIT_PERIOD = 1

    # Entity mappings
    SUPPORTED_ENTITIES = {
        'customer': 'customers',
        'product': 'products',
        'order': 'orders',
        'inventory': 'inventory_items',
        'fulfillment': 'fulfillments',
        'variant': 'variants',
    }

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.shop_domain = config.extra.get('shop_domain', '').replace('.myshopify.com', '')

    def _get_base_url(self) -> str:
        """Get shop-specific API base URL"""
        return f"https://{self.shop_domain}.myshopify.com/admin/api/{self.API_VERSION}"

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            'X-Shopify-Access-Token': self.config.access_token,
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
        url = f"{self._get_base_url()}/{endpoint}.json"

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

            if response.status_code == 404:
                return None

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('errors', str(response.status_code))
                raise Exception(f"Shopify API error: {error_msg}")

            return response.json() if response.content else {}

    # ==================== Authentication ====================

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL"""
        from urllib.parse import urlencode

        params = {
            'client_id': self.config.client_id,
            'redirect_uri': redirect_uri,
            'scope': ','.join(self.OAUTH_SCOPES),
            'state': state,
        }

        return f"https://{self.shop_domain}.myshopify.com/admin/oauth/authorize?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self.shop_domain}.myshopify.com/admin/oauth/access_token",
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
        """Shopify uses permanent access tokens - no refresh needed"""
        # Shopify access tokens don't expire
        return {'access_token': self.config.access_token}

    async def test_connection(self) -> Tuple[bool, str]:
        """Test API connection"""
        try:
            result = await self._make_request('GET', 'shop')
            shop_name = result.get('shop', {}).get('name', 'Unknown')
            return True, f"Connected to: {shop_name}"
        except Exception as e:
            return False, str(e)

    # ==================== Webhook Verification ====================

    def verify_webhook(self, data: bytes, hmac_header: str) -> bool:
        """Verify Shopify webhook signature"""
        if not self.config.client_secret:
            return False

        computed_hmac = base64.b64encode(
            hmac.new(
                self.config.client_secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')

        return hmac.compare_digest(computed_hmac, hmac_header)

    # ==================== Entity Operations ====================

    def get_entity_schema(self, entity_name: str) -> Optional[EntitySchema]:
        """Get schema for Shopify entity"""
        schemas = {
            'customers': EntitySchema(
                name='customers',
                label='Customer',
                id_field='id',
                supports_bulk=True,
                fields=[
                    EntityField(name='id', label='ID', type='number', readonly=True),
                    EntityField(name='email', label='Email', type='string'),
                    EntityField(name='first_name', label='First Name', type='string'),
                    EntityField(name='last_name', label='Last Name', type='string'),
                    EntityField(name='phone', label='Phone', type='string'),
                    EntityField(name='verified_email', label='Email Verified', type='boolean'),
                    EntityField(name='accepts_marketing', label='Accepts Marketing', type='boolean'),
                    EntityField(name='orders_count', label='Orders Count', type='number', readonly=True),
                    EntityField(name='total_spent', label='Total Spent', type='string', readonly=True),
                    EntityField(name='tags', label='Tags', type='string'),
                    EntityField(name='note', label='Note', type='string'),
                ],
            ),
            'products': EntitySchema(
                name='products',
                label='Product',
                id_field='id',
                supports_bulk=True,
                fields=[
                    EntityField(name='id', label='ID', type='number', readonly=True),
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
                    EntityField(name='id', label='ID', type='number', readonly=True),
                    EntityField(name='order_number', label='Order Number', type='number', readonly=True),
                    EntityField(name='name', label='Name', type='string', readonly=True),
                    EntityField(name='email', label='Email', type='string'),
                    EntityField(name='financial_status', label='Financial Status', type='string'),
                    EntityField(name='fulfillment_status', label='Fulfillment Status', type='string'),
                    EntityField(name='total_price', label='Total Price', type='string'),
                    EntityField(name='subtotal_price', label='Subtotal', type='string'),
                    EntityField(name='total_tax', label='Total Tax', type='string'),
                    EntityField(name='currency', label='Currency', type='string'),
                    EntityField(name='line_items', label='Line Items', type='array'),
                    EntityField(name='customer', label='Customer', type='object'),
                    EntityField(name='shipping_address', label='Shipping Address', type='object'),
                    EntityField(name='billing_address', label='Billing Address', type='object'),
                ],
            ),
            'inventory_items': EntitySchema(
                name='inventory_items',
                label='Inventory Item',
                id_field='id',
                fields=[
                    EntityField(name='id', label='ID', type='number', readonly=True),
                    EntityField(name='sku', label='SKU', type='string'),
                    EntityField(name='tracked', label='Tracked', type='boolean'),
                    EntityField(name='cost', label='Cost', type='string'),
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

        params = {'limit': min(page_size, 250)}

        if modified_since:
            params['updated_at_min'] = modified_since.strftime('%Y-%m-%dT%H:%M:%S%z')

        if filters:
            params.update(filters)

        if fields:
            params['fields'] = ','.join(fields)

        result = await self._make_request('GET', shopify_entity, params=params)

        if result is None:
            return [], False

        records = result.get(shopify_entity, [])
        # Shopify uses Link header for pagination, simplified here
        has_more = len(records) == page_size

        return records, has_more

    async def get_record(self, entity_name: str, record_id: str) -> Optional[Dict]:
        """Get single record by ID"""
        shopify_entity = self.get_remote_entity_name(entity_name)
        singular = shopify_entity.rstrip('s')

        try:
            result = await self._make_request('GET', f'{shopify_entity}/{record_id}')
            return result.get(singular) if result else None
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

    # ==================== Shopify-Specific Methods ====================

    async def get_inventory_levels(self, inventory_item_ids: List[str] = None, location_ids: List[str] = None) -> List[Dict]:
        """Get inventory levels"""
        params = {}
        if inventory_item_ids:
            params['inventory_item_ids'] = ','.join(map(str, inventory_item_ids))
        if location_ids:
            params['location_ids'] = ','.join(map(str, location_ids))

        result = await self._make_request('GET', 'inventory_levels', params=params)
        return result.get('inventory_levels', [])

    async def set_inventory_level(
        self,
        inventory_item_id: str,
        location_id: str,
        available: int
    ) -> Dict:
        """Set inventory level"""
        result = await self._make_request(
            'POST',
            'inventory_levels/set',
            data={
                'inventory_item_id': inventory_item_id,
                'location_id': location_id,
                'available': available,
            }
        )
        return result.get('inventory_level', {})

    async def adjust_inventory_level(
        self,
        inventory_item_id: str,
        location_id: str,
        adjustment: int
    ) -> Dict:
        """Adjust inventory level"""
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

    async def get_locations(self) -> List[Dict]:
        """Get all locations"""
        result = await self._make_request('GET', 'locations')
        return result.get('locations', [])

    async def create_fulfillment(
        self,
        order_id: str,
        location_id: str,
        line_items: List[Dict] = None,
        tracking_number: str = None,
        tracking_company: str = None,
        notify_customer: bool = True
    ) -> Dict:
        """Create order fulfillment"""
        data = {
            'location_id': location_id,
            'notify_customer': notify_customer,
        }

        if line_items:
            data['line_items'] = line_items
        if tracking_number:
            data['tracking_number'] = tracking_number
        if tracking_company:
            data['tracking_company'] = tracking_company

        result = await self._make_request(
            'POST',
            f'orders/{order_id}/fulfillments',
            data={'fulfillment': data}
        )
        return result.get('fulfillment', {})

    async def cancel_order(self, order_id: str, reason: str = None) -> Dict:
        """Cancel an order"""
        data = {}
        if reason:
            data['reason'] = reason

        result = await self._make_request(
            'POST',
            f'orders/{order_id}/cancel',
            data=data
        )
        return result.get('order', {})

    async def create_refund(
        self,
        order_id: str,
        refund_line_items: List[Dict] = None,
        shipping_amount: float = None,
        note: str = None,
        notify: bool = True
    ) -> Dict:
        """Create a refund"""
        data = {
            'notify': notify,
        }

        if refund_line_items:
            data['refund_line_items'] = refund_line_items
        if shipping_amount:
            data['shipping'] = {'amount': shipping_amount}
        if note:
            data['note'] = note

        result = await self._make_request(
            'POST',
            f'orders/{order_id}/refunds',
            data={'refund': data}
        )
        return result.get('refund', {})

    async def register_webhook(self, topic: str, address: str) -> Dict:
        """Register a webhook"""
        result = await self._make_request(
            'POST',
            'webhooks',
            data={
                'webhook': {
                    'topic': topic,
                    'address': address,
                    'format': 'json',
                }
            }
        )
        return result.get('webhook', {})

    async def list_webhooks(self) -> List[Dict]:
        """List all webhooks"""
        result = await self._make_request('GET', 'webhooks')
        return result.get('webhooks', [])

    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        try:
            await self._make_request('DELETE', f'webhooks/{webhook_id}')
            return True
        except:
            return False
