# LogiAccounting Pro - Phase 9 Tasks Part 1

## BACKEND SERVICES & ADAPTERS (EU/US Market)

---

## TASK 1: BASE ADAPTER

### 1.1 Create Base Adapter Class

**File:** `backend/app/services/ecommerce/__init__.py`

```python
"""
E-commerce integration services
"""

from app.services.ecommerce.base_adapter import BaseEcommerceAdapter
from app.services.ecommerce.connection_service import EcommerceConnectionService
from app.services.ecommerce.shopify_adapter import ShopifyAdapter
from app.services.ecommerce.woocommerce_adapter import WooCommerceAdapter
from app.services.ecommerce.amazon_adapter import AmazonAdapter

__all__ = [
    "BaseEcommerceAdapter",
    "EcommerceConnectionService",
    "ShopifyAdapter",
    "WooCommerceAdapter",
    "AmazonAdapter"
]
```

**File:** `backend/app/services/ecommerce/base_adapter.py`

```python
"""
Base E-commerce Adapter
Abstract base class for all e-commerce platform integrations
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional


class BaseEcommerceAdapter(ABC):
    """Abstract base class for e-commerce adapters"""
    
    def __init__(self, store_config: dict):
        """Initialize adapter with store configuration"""
        self.store_id = store_config.get("id", "")
        self.store_name = store_config.get("name", "")
        self.credentials = store_config.get("credentials", {})
        self.settings = store_config.get("settings", {})
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return platform name (shopify, woocommerce, amazon)"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> dict:
        """Test connection to the e-commerce platform"""
        pass
    
    # Products
    @abstractmethod
    async def get_products(self, limit: int = 50, page: int = 1) -> List[dict]:
        """Get products from the platform"""
        pass
    
    @abstractmethod
    async def get_product(self, product_id: str) -> Optional[dict]:
        """Get a single product by ID"""
        pass
    
    @abstractmethod
    async def create_product(self, product_data: dict) -> dict:
        """Create a new product"""
        pass
    
    @abstractmethod
    async def update_product(self, product_id: str, product_data: dict) -> dict:
        """Update an existing product"""
        pass
    
    @abstractmethod
    async def delete_product(self, product_id: str) -> bool:
        """Delete a product"""
        pass
    
    # Inventory
    @abstractmethod
    async def get_inventory(self, product_id: str = None) -> List[dict]:
        """Get inventory levels"""
        pass
    
    @abstractmethod
    async def update_inventory(self, product_id: str, quantity: int) -> dict:
        """Update inventory for a product"""
        pass
    
    # Orders
    @abstractmethod
    async def get_orders(
        self, 
        status: str = None, 
        since: datetime = None,
        limit: int = 50
    ) -> List[dict]:
        """Get orders from the platform"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[dict]:
        """Get a single order by ID"""
        pass
    
    # Customers
    @abstractmethod
    async def get_customers(self, limit: int = 50, page: int = 1) -> List[dict]:
        """Get customers from the platform"""
        pass
    
    @abstractmethod
    async def get_customer(self, customer_id: str) -> Optional[dict]:
        """Get a single customer by ID"""
        pass
    
    # Normalization methods
    @abstractmethod
    def normalize_product(self, raw_product: dict) -> dict:
        """Normalize platform product to common format"""
        pass
    
    @abstractmethod
    def normalize_order(self, raw_order: dict) -> dict:
        """Normalize platform order to common format"""
        pass
    
    @abstractmethod
    def normalize_customer(self, raw_customer: dict) -> dict:
        """Normalize platform customer to common format"""
        pass
```

---

## TASK 2: CONNECTION SERVICE

### 2.1 Create Connection Service

**File:** `backend/app/services/ecommerce/connection_service.py`

```python
"""
E-commerce Connection Service
Manages connections to multiple e-commerce platforms
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid


class EcommerceConnectionService:
    """Singleton service for managing e-commerce connections"""
    
    _instance = None
    _stores: Dict[str, dict] = {}
    
    SUPPORTED_PLATFORMS = {
        "shopify": {
            "name": "Shopify",
            "icon": "🟢",
            "auth_type": "oauth",
            "features": ["products", "inventory", "orders", "customers", "webhooks"],
            "markets": ["US", "EU", "UK", "CA", "AU"]
        },
        "woocommerce": {
            "name": "WooCommerce",
            "icon": "🔵",
            "auth_type": "api_key",
            "features": ["products", "inventory", "orders", "customers", "webhooks"],
            "markets": ["Global"]
        },
        "amazon": {
            "name": "Amazon Seller Central",
            "icon": "🟠",
            "auth_type": "sp_api",
            "features": ["products", "inventory", "orders", "fba"],
            "markets": ["US", "UK", "DE", "FR", "IT", "ES", "NL", "CA", "AU"]
        }
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_demo_stores()
        return cls._instance
    
    def _initialize_demo_stores(self):
        """Initialize demo stores for testing"""
        self._stores = {
            "demo-shopify": {
                "id": "demo-shopify",
                "platform": "shopify",
                "name": "Demo Shopify Store (US)",
                "status": "connected",
                "credentials": {
                    "shop_domain": "demo-store.myshopify.com",
                    "access_token": "demo_token",
                    "api_version": "2024-01"
                },
                "settings": {
                    "sync_products": True,
                    "sync_orders": True,
                    "sync_inventory": True,
                    "auto_sync_interval": 30,
                    "low_stock_threshold": 10
                },
                "last_sync": {
                    "products": datetime.utcnow().isoformat() + "Z",
                    "orders": datetime.utcnow().isoformat() + "Z",
                    "inventory": datetime.utcnow().isoformat() + "Z"
                },
                "stats": {
                    "total_products": 5,
                    "synced_products": 5,
                    "imported_orders": 10
                },
                "created_at": "2025-01-01T00:00:00Z"
            },
            "demo-woocommerce": {
                "id": "demo-woocommerce",
                "platform": "woocommerce",
                "name": "Demo WooCommerce Store (EU)",
                "status": "connected",
                "credentials": {
                    "store_url": "https://demo-woo.example.com",
                    "consumer_key": "ck_demo",
                    "consumer_secret": "cs_demo"
                },
                "settings": {
                    "sync_products": True,
                    "sync_orders": True,
                    "sync_inventory": True,
                    "auto_sync_interval": 30,
                    "low_stock_threshold": 10
                },
                "last_sync": {
                    "products": datetime.utcnow().isoformat() + "Z",
                    "orders": datetime.utcnow().isoformat() + "Z",
                    "inventory": datetime.utcnow().isoformat() + "Z"
                },
                "stats": {
                    "total_products": 4,
                    "synced_products": 4,
                    "imported_orders": 8
                },
                "created_at": "2025-01-01T00:00:00Z"
            },
            "demo-amazon": {
                "id": "demo-amazon",
                "platform": "amazon",
                "name": "Demo Amazon Store (US)",
                "status": "connected",
                "credentials": {
                    "seller_id": "A1234567890XYZ",
                    "marketplace": "US",
                    "refresh_token": "demo_refresh_token"
                },
                "settings": {
                    "sync_products": True,
                    "sync_orders": True,
                    "sync_inventory": True,
                    "auto_sync_interval": 15,
                    "low_stock_threshold": 20
                },
                "last_sync": {
                    "products": datetime.utcnow().isoformat() + "Z",
                    "orders": datetime.utcnow().isoformat() + "Z",
                    "inventory": datetime.utcnow().isoformat() + "Z"
                },
                "stats": {
                    "total_products": 3,
                    "synced_products": 3,
                    "imported_orders": 12
                },
                "created_at": "2025-01-01T00:00:00Z"
            }
        }
    
    def get_platforms(self) -> dict:
        """Get list of supported platforms"""
        return self.SUPPORTED_PLATFORMS
    
    def get_stores(self) -> List[dict]:
        """Get all connected stores"""
        return list(self._stores.values())
    
    def get_store(self, store_id: str) -> Optional[dict]:
        """Get a specific store by ID"""
        return self._stores.get(store_id)
    
    def connect_store(self, store_data: dict) -> dict:
        """Connect a new store"""
        store_id = f"store-{uuid.uuid4().hex[:8]}"
        
        store = {
            "id": store_id,
            "platform": store_data.get("platform"),
            "name": store_data.get("name"),
            "status": "pending",
            "credentials": store_data.get("credentials", {}),
            "settings": {
                "sync_products": True,
                "sync_orders": True,
                "sync_inventory": True,
                "auto_sync_interval": 30,
                "low_stock_threshold": 10,
                **store_data.get("settings", {})
            },
            "last_sync": {
                "products": None,
                "orders": None,
                "inventory": None
            },
            "stats": {
                "total_products": 0,
                "synced_products": 0,
                "imported_orders": 0
            },
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        self._stores[store_id] = store
        
        # Simulate connection test
        store["status"] = "connected"
        
        return store
    
    def update_store(self, store_id: str, store_data: dict) -> Optional[dict]:
        """Update store settings"""
        if store_id not in self._stores:
            return None
        
        store = self._stores[store_id]
        
        if "name" in store_data:
            store["name"] = store_data["name"]
        if "settings" in store_data:
            store["settings"].update(store_data["settings"])
        if "credentials" in store_data:
            store["credentials"].update(store_data["credentials"])
        
        return store
    
    def disconnect_store(self, store_id: str) -> bool:
        """Disconnect a store"""
        if store_id in self._stores:
            del self._stores[store_id]
            return True
        return False
    
    def update_sync_status(self, store_id: str, sync_type: str):
        """Update last sync timestamp"""
        if store_id in self._stores:
            self._stores[store_id]["last_sync"][sync_type] = (
                datetime.utcnow().isoformat() + "Z"
            )
    
    def update_stats(self, store_id: str, stats: dict):
        """Update store statistics"""
        if store_id in self._stores:
            self._stores[store_id]["stats"].update(stats)
    
    def get_adapter(self, store_id: str):
        """Get the appropriate adapter for a store"""
        store = self._stores.get(store_id)
        if not store:
            return None
        
        if store["platform"] == "shopify":
            from app.services.ecommerce.shopify_adapter import ShopifyAdapter
            return ShopifyAdapter(store)
        elif store["platform"] == "woocommerce":
            from app.services.ecommerce.woocommerce_adapter import WooCommerceAdapter
            return WooCommerceAdapter(store)
        elif store["platform"] == "amazon":
            from app.services.ecommerce.amazon_adapter import AmazonAdapter
            return AmazonAdapter(store)
        
        return None


# Singleton instance
ecommerce_service = EcommerceConnectionService()
```

---

## TASK 3: SHOPIFY ADAPTER

### 3.1 Create Shopify Adapter

**File:** `backend/app/services/ecommerce/shopify_adapter.py`

```python
"""
Shopify Adapter
Handles all Shopify API interactions (simulated for demo)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
from app.services.ecommerce.base_adapter import BaseEcommerceAdapter


class ShopifyAdapter(BaseEcommerceAdapter):
    """Shopify adapter (simulated for demo)"""
    
    # Demo product data
    _demo_products = [
        {
            "id": "7654321098765",
            "title": "Classic Cotton T-Shirt",
            "body_html": "<p>Premium cotton t-shirt with modern fit</p>",
            "vendor": "Fashion Co",
            "product_type": "Apparel",
            "created_at": "2024-06-15T10:00:00Z",
            "updated_at": "2025-01-15T10:00:00Z",
            "status": "active",
            "variants": [{
                "id": "43210987654321",
                "sku": "TSHIRT-BLK-M",
                "price": "24.99",
                "inventory_quantity": 50,
                "inventory_item_id": "inv_001"
            }],
            "images": [{"src": "https://via.placeholder.com/400x400?text=T-Shirt"}]
        },
        {
            "id": "7654321098766",
            "title": "Premium Hoodie",
            "body_html": "<p>Warm and comfortable premium hoodie</p>",
            "vendor": "Fashion Co",
            "product_type": "Apparel",
            "created_at": "2024-07-20T10:00:00Z",
            "updated_at": "2025-01-10T10:00:00Z",
            "status": "active",
            "variants": [{
                "id": "43210987654322",
                "sku": "HOODIE-GRY-L",
                "price": "59.99",
                "inventory_quantity": 25,
                "inventory_item_id": "inv_002"
            }],
            "images": [{"src": "https://via.placeholder.com/400x400?text=Hoodie"}]
        },
        {
            "id": "7654321098767",
            "title": "Running Shoes Pro",
            "body_html": "<p>Lightweight running shoes for athletes</p>",
            "vendor": "SportGear",
            "product_type": "Footwear",
            "created_at": "2024-08-10T10:00:00Z",
            "updated_at": "2025-01-18T10:00:00Z",
            "status": "active",
            "variants": [{
                "id": "43210987654323",
                "sku": "SHOES-RUN-42",
                "price": "89.99",
                "inventory_quantity": 15,
                "inventory_item_id": "inv_003"
            }],
            "images": [{"src": "https://via.placeholder.com/400x400?text=Shoes"}]
        },
        {
            "id": "7654321098768",
            "title": "Wireless Earbuds Pro",
            "body_html": "<p>True wireless earbuds with noise cancellation</p>",
            "vendor": "TechAudio",
            "product_type": "Electronics",
            "created_at": "2024-09-05T10:00:00Z",
            "updated_at": "2025-01-17T10:00:00Z",
            "status": "active",
            "variants": [{
                "id": "43210987654324",
                "sku": "EARBUDS-PRO-WHT",
                "price": "79.99",
                "inventory_quantity": 100,
                "inventory_item_id": "inv_004"
            }],
            "images": [{"src": "https://via.placeholder.com/400x400?text=Earbuds"}]
        },
        {
            "id": "7654321098769",
            "title": "Leather Wallet Classic",
            "body_html": "<p>Genuine leather wallet with RFID protection</p>",
            "vendor": "LeatherCraft",
            "product_type": "Accessories",
            "created_at": "2024-10-12T10:00:00Z",
            "updated_at": "2025-01-16T10:00:00Z",
            "status": "active",
            "variants": [{
                "id": "43210987654325",
                "sku": "WALLET-BRN-STD",
                "price": "49.99",
                "inventory_quantity": 30,
                "inventory_item_id": "inv_005"
            }],
            "images": [{"src": "https://via.placeholder.com/400x400?text=Wallet"}]
        }
    ]
    
    _demo_orders = []
    
    @property
    def platform_name(self) -> str:
        return "shopify"
    
    async def test_connection(self) -> dict:
        """Test Shopify API connection"""
        shop_domain = self.credentials.get("shop_domain", "demo.myshopify.com")
        return {
            "success": True,
            "shop_info": {
                "name": self.store_name,
                "domain": shop_domain,
                "currency": "USD",
                "timezone": "America/New_York"
            }
        }
    
    async def get_products(self, limit: int = 50, page: int = 1) -> List[dict]:
        """Get products from Shopify"""
        start = (page - 1) * limit
        end = start + limit
        products = self._demo_products[start:end]
        return [self.normalize_product(p) for p in products]
    
    async def get_product(self, product_id: str) -> Optional[dict]:
        """Get single product by ID"""
        for product in self._demo_products:
            if str(product["id"]) == str(product_id):
                return self.normalize_product(product)
        return None
    
    async def create_product(self, product_data: dict) -> dict:
        """Create product in Shopify"""
        new_product = {
            "id": str(random.randint(1000000000000, 9999999999999)),
            "title": product_data.get("name", ""),
            "body_html": f"<p>{product_data.get('description', '')}</p>",
            "vendor": product_data.get("vendor", ""),
            "product_type": product_data.get("category", ""),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "status": "active",
            "variants": [{
                "id": str(random.randint(10000000000000, 99999999999999)),
                "sku": product_data.get("sku", ""),
                "price": str(product_data.get("price", 0)),
                "inventory_quantity": product_data.get("stock", 0),
                "inventory_item_id": f"inv_{random.randint(100, 999)}"
            }],
            "images": []
        }
        self._demo_products.append(new_product)
        return self.normalize_product(new_product)
    
    async def update_product(self, product_id: str, product_data: dict) -> dict:
        """Update product in Shopify"""
        for product in self._demo_products:
            if str(product["id"]) == str(product_id):
                if "name" in product_data:
                    product["title"] = product_data["name"]
                if "description" in product_data:
                    product["body_html"] = f"<p>{product_data['description']}</p>"
                if "price" in product_data:
                    product["variants"][0]["price"] = str(product_data["price"])
                if "stock" in product_data:
                    product["variants"][0]["inventory_quantity"] = product_data["stock"]
                product["updated_at"] = datetime.utcnow().isoformat() + "Z"
                return self.normalize_product(product)
        return {"error": "Product not found"}
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete product from Shopify"""
        for i, product in enumerate(self._demo_products):
            if str(product["id"]) == str(product_id):
                self._demo_products.pop(i)
                return True
        return False
    
    async def get_inventory(self, product_id: str = None) -> List[dict]:
        """Get inventory levels"""
        inventory = []
        for product in self._demo_products:
            if product_id and str(product["id"]) != str(product_id):
                continue
            variant = product["variants"][0]
            inventory.append({
                "product_id": str(product["id"]),
                "sku": variant["sku"],
                "quantity": variant["inventory_quantity"],
                "location_id": "loc_main"
            })
        return inventory
    
    async def update_inventory(self, product_id: str, quantity: int) -> dict:
        """Update inventory in Shopify"""
        for product in self._demo_products:
            if str(product["id"]) == str(product_id):
                product["variants"][0]["inventory_quantity"] = quantity
                return {
                    "success": True,
                    "product_id": product_id,
                    "new_quantity": quantity
                }
        return {"error": "Product not found"}
    
    async def get_orders(
        self, 
        status: str = None, 
        since: datetime = None,
        limit: int = 50
    ) -> List[dict]:
        """Get orders from Shopify"""
        if not self._demo_orders:
            self._generate_demo_orders()
        
        orders = self._demo_orders
        if status:
            orders = [o for o in orders if o["financial_status"] == status]
        if since:
            orders = [o for o in orders if o["created_at"] >= since.isoformat()]
        
        return [self.normalize_order(o) for o in orders[:limit]]
    
    async def get_order(self, order_id: str) -> Optional[dict]:
        """Get single order"""
        for order in self._demo_orders:
            if str(order["id"]) == str(order_id):
                return self.normalize_order(order)
        return None
    
    async def get_customers(self, limit: int = 50, page: int = 1) -> List[dict]:
        """Get customers from Shopify"""
        customers = []
        for order in self._demo_orders[:limit]:
            if order.get("customer"):
                customers.append(self.normalize_customer(order["customer"]))
        return customers
    
    async def get_customer(self, customer_id: str) -> Optional[dict]:
        """Get single customer"""
        for order in self._demo_orders:
            if order.get("customer", {}).get("id") == customer_id:
                return self.normalize_customer(order["customer"])
        return None
    
    def _generate_demo_orders(self):
        """Generate demo orders"""
        statuses = ["paid", "pending", "refunded"]
        
        for i in range(10):
            product = random.choice(self._demo_products)
            variant = product["variants"][0]
            quantity = random.randint(1, 3)
            subtotal = float(variant["price"]) * quantity
            tax = subtotal * 0.08
            
            order = {
                "id": str(5000000000000 + i),
                "order_number": 1001 + i,
                "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat() + "Z",
                "updated_at": (datetime.utcnow() - timedelta(days=i)).isoformat() + "Z",
                "financial_status": random.choice(statuses),
                "fulfillment_status": "fulfilled" if i < 7 else None,
                "currency": "USD",
                "subtotal_price": f"{subtotal:.2f}",
                "total_tax": f"{tax:.2f}",
                "total_price": f"{subtotal + tax:.2f}",
                "customer": {
                    "id": str(1000 + i),
                    "email": f"customer{i}@example.com",
                    "first_name": f"John{i}",
                    "last_name": "Doe",
                    "phone": f"+1-555-{1000 + i}"
                },
                "shipping_address": {
                    "first_name": f"John{i}",
                    "last_name": "Doe",
                    "address1": f"{100 + i} Main Street",
                    "city": "New York",
                    "province": "NY",
                    "zip": "10001",
                    "country": "US"
                },
                "line_items": [{
                    "id": str(9000000000000 + i),
                    "product_id": product["id"],
                    "variant_id": variant["id"],
                    "title": product["title"],
                    "sku": variant["sku"],
                    "quantity": quantity,
                    "price": variant["price"]
                }]
            }
            self._demo_orders.append(order)
    
    def normalize_product(self, raw_product: dict) -> dict:
        """Normalize Shopify product to common format"""
        variant = raw_product.get("variants", [{}])[0]
        images = raw_product.get("images", [])
        
        return {
            "external_id": str(raw_product.get("id", "")),
            "platform": "shopify",
            "name": raw_product.get("title", ""),
            "description": raw_product.get("body_html", "").replace("<p>", "").replace("</p>", ""),
            "sku": variant.get("sku", ""),
            "price": float(variant.get("price", 0)),
            "stock": variant.get("inventory_quantity", 0),
            "category": raw_product.get("product_type", ""),
            "vendor": raw_product.get("vendor", ""),
            "image_url": images[0]["src"] if images else "",
            "status": raw_product.get("status", ""),
            "created_at": raw_product.get("created_at", ""),
            "updated_at": raw_product.get("updated_at", ""),
            "raw_data": raw_product
        }
    
    def normalize_order(self, raw_order: dict) -> dict:
        """Normalize Shopify order to common format"""
        customer = raw_order.get("customer", {})
        shipping = raw_order.get("shipping_address", {})
        
        items = []
        for item in raw_order.get("line_items", []):
            items.append({
                "product_id": str(item.get("product_id", "")),
                "name": item.get("title", ""),
                "sku": item.get("sku", ""),
                "quantity": item.get("quantity", 0),
                "price": float(item.get("price", 0))
            })
        
        # Map Shopify status to common status
        status_map = {
            "pending": "pending",
            "authorized": "pending",
            "paid": "completed",
            "partially_paid": "partial",
            "refunded": "refunded",
            "voided": "cancelled"
        }
        
        return {
            "external_id": str(raw_order.get("id", "")),
            "order_number": f"#{raw_order.get('order_number', '')}",
            "platform": "shopify",
            "status": status_map.get(raw_order.get("financial_status", ""), "pending"),
            "original_status": raw_order.get("financial_status", ""),
            "customer_email": customer.get("email", ""),
            "customer_name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
            "subtotal": float(raw_order.get("subtotal_price", 0)),
            "tax": float(raw_order.get("total_tax", 0)),
            "total": float(raw_order.get("total_price", 0)),
            "currency": raw_order.get("currency", "USD"),
            "items": items,
            "shipping_address": {
                "name": f"{shipping.get('first_name', '')} {shipping.get('last_name', '')}".strip(),
                "address1": shipping.get("address1", ""),
                "city": shipping.get("city", ""),
                "state": shipping.get("province", ""),
                "zip": shipping.get("zip", ""),
                "country": shipping.get("country", "")
            },
            "created_at": raw_order.get("created_at", ""),
            "raw_data": raw_order
        }
    
    def normalize_customer(self, raw_customer: dict) -> dict:
        """Normalize Shopify customer to common format"""
        return {
            "external_id": str(raw_customer.get("id", "")),
            "platform": "shopify",
            "email": raw_customer.get("email", ""),
            "name": f"{raw_customer.get('first_name', '')} {raw_customer.get('last_name', '')}".strip(),
            "phone": raw_customer.get("phone", ""),
            "raw_data": raw_customer
        }
```

---

## TASK 4: WOOCOMMERCE ADAPTER

### 4.1 Create WooCommerce Adapter

**File:** `backend/app/services/ecommerce/woocommerce_adapter.py`

```python
"""
WooCommerce Adapter
Handles all WooCommerce REST API interactions (simulated for demo)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
from app.services.ecommerce.base_adapter import BaseEcommerceAdapter


class WooCommerceAdapter(BaseEcommerceAdapter):
    """WooCommerce adapter (simulated for demo)"""
    
    # Demo product data (EU-focused)
    _demo_products = [
        {
            "id": 101,
            "name": "Organic Coffee Beans",
            "description": "Premium organic coffee beans from Colombia",
            "sku": "COFFEE-ORG-500G",
            "regular_price": "18.99",
            "sale_price": "",
            "stock_quantity": 75,
            "stock_status": "instock",
            "categories": [{"id": 1, "name": "Food & Beverage"}],
            "images": [{"src": "https://via.placeholder.com/400x400?text=Coffee"}],
            "date_created": "2024-05-10T10:00:00",
            "date_modified": "2025-01-15T10:00:00"
        },
        {
            "id": 102,
            "name": "Stainless Steel Water Bottle",
            "description": "Eco-friendly reusable water bottle 750ml",
            "sku": "BOTTLE-SS-750",
            "regular_price": "29.99",
            "sale_price": "24.99",
            "stock_quantity": 120,
            "stock_status": "instock",
            "categories": [{"id": 2, "name": "Home & Garden"}],
            "images": [{"src": "https://via.placeholder.com/400x400?text=Bottle"}],
            "date_created": "2024-06-20T10:00:00",
            "date_modified": "2025-01-10T10:00:00"
        },
        {
            "id": 103,
            "name": "Yoga Mat Premium",
            "description": "Non-slip yoga mat 6mm thickness",
            "sku": "YOGA-MAT-PRO",
            "regular_price": "39.99",
            "sale_price": "",
            "stock_quantity": 45,
            "stock_status": "instock",
            "categories": [{"id": 3, "name": "Sports"}],
            "images": [{"src": "https://via.placeholder.com/400x400?text=Yoga+Mat"}],
            "date_created": "2024-07-15T10:00:00",
            "date_modified": "2025-01-12T10:00:00"
        },
        {
            "id": 104,
            "name": "Bamboo Desk Organizer",
            "description": "Sustainable bamboo desk organizer set",
            "sku": "DESK-ORG-BAMB",
            "regular_price": "24.99",
            "sale_price": "",
            "stock_quantity": 60,
            "stock_status": "instock",
            "categories": [{"id": 4, "name": "Office"}],
            "images": [{"src": "https://via.placeholder.com/400x400?text=Organizer"}],
            "date_created": "2024-08-05T10:00:00",
            "date_modified": "2025-01-18T10:00:00"
        }
    ]
    
    _demo_orders = []
    
    @property
    def platform_name(self) -> str:
        return "woocommerce"
    
    async def test_connection(self) -> dict:
        """Test WooCommerce API connection"""
        store_url = self.credentials.get("store_url", "https://demo.example.com")
        return {
            "success": True,
            "store_info": {
                "name": self.store_name,
                "url": store_url,
                "currency": "EUR",
                "timezone": "Europe/Berlin"
            }
        }
    
    async def get_products(self, limit: int = 50, page: int = 1) -> List[dict]:
        """Get products from WooCommerce"""
        start = (page - 1) * limit
        end = start + limit
        products = self._demo_products[start:end]
        return [self.normalize_product(p) for p in products]
    
    async def get_product(self, product_id: str) -> Optional[dict]:
        """Get single product by ID"""
        for product in self._demo_products:
            if str(product["id"]) == str(product_id):
                return self.normalize_product(product)
        return None
    
    async def create_product(self, product_data: dict) -> dict:
        """Create product in WooCommerce"""
        new_product = {
            "id": random.randint(200, 999),
            "name": product_data.get("name", ""),
            "description": product_data.get("description", ""),
            "sku": product_data.get("sku", ""),
            "regular_price": str(product_data.get("price", 0)),
            "sale_price": "",
            "stock_quantity": product_data.get("stock", 0),
            "stock_status": "instock",
            "categories": [{"id": 1, "name": product_data.get("category", "General")}],
            "images": [],
            "date_created": datetime.utcnow().isoformat(),
            "date_modified": datetime.utcnow().isoformat()
        }
        self._demo_products.append(new_product)
        return self.normalize_product(new_product)
    
    async def update_product(self, product_id: str, product_data: dict) -> dict:
        """Update product in WooCommerce"""
        for product in self._demo_products:
            if str(product["id"]) == str(product_id):
                if "name" in product_data:
                    product["name"] = product_data["name"]
                if "description" in product_data:
                    product["description"] = product_data["description"]
                if "price" in product_data:
                    product["regular_price"] = str(product_data["price"])
                if "stock" in product_data:
                    product["stock_quantity"] = product_data["stock"]
                product["date_modified"] = datetime.utcnow().isoformat()
                return self.normalize_product(product)
        return {"error": "Product not found"}
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete product from WooCommerce"""
        for i, product in enumerate(self._demo_products):
            if str(product["id"]) == str(product_id):
                self._demo_products.pop(i)
                return True
        return False
    
    async def get_inventory(self, product_id: str = None) -> List[dict]:
        """Get inventory levels"""
        inventory = []
        for product in self._demo_products:
            if product_id and str(product["id"]) != str(product_id):
                continue
            inventory.append({
                "product_id": str(product["id"]),
                "sku": product["sku"],
                "quantity": product["stock_quantity"],
                "status": product["stock_status"]
            })
        return inventory
    
    async def update_inventory(self, product_id: str, quantity: int) -> dict:
        """Update inventory in WooCommerce"""
        for product in self._demo_products:
            if str(product["id"]) == str(product_id):
                product["stock_quantity"] = quantity
                product["stock_status"] = "instock" if quantity > 0 else "outofstock"
                return {
                    "success": True,
                    "product_id": product_id,
                    "new_quantity": quantity
                }
        return {"error": "Product not found"}
    
    async def get_orders(
        self, 
        status: str = None, 
        since: datetime = None,
        limit: int = 50
    ) -> List[dict]:
        """Get orders from WooCommerce"""
        if not self._demo_orders:
            self._generate_demo_orders()
        
        orders = self._demo_orders
        if status:
            orders = [o for o in orders if o["status"] == status]
        if since:
            orders = [o for o in orders if o["date_created"] >= since.isoformat()]
        
        return [self.normalize_order(o) for o in orders[:limit]]
    
    async def get_order(self, order_id: str) -> Optional[dict]:
        """Get single order"""
        for order in self._demo_orders:
            if str(order["id"]) == str(order_id):
                return self.normalize_order(order)
        return None
    
    async def get_customers(self, limit: int = 50, page: int = 1) -> List[dict]:
        """Get customers from WooCommerce"""
        customers = []
        for order in self._demo_orders[:limit]:
            if order.get("billing"):
                customers.append(self.normalize_customer(order["billing"]))
        return customers
    
    async def get_customer(self, customer_id: str) -> Optional[dict]:
        """Get single customer"""
        for order in self._demo_orders:
            billing = order.get("billing", {})
            if billing.get("email") == customer_id:
                return self.normalize_customer(billing)
        return None
    
    def _generate_demo_orders(self):
        """Generate demo orders (EU market)"""
        statuses = ["completed", "processing", "pending", "on-hold"]
        eu_cities = [
            ("Berlin", "10115", "DE"),
            ("Paris", "75001", "FR"),
            ("Madrid", "28001", "ES"),
            ("Amsterdam", "1012", "NL"),
            ("Rome", "00100", "IT")
        ]
        
        for i in range(8):
            product = random.choice(self._demo_products)
            quantity = random.randint(1, 4)
            price = float(product["sale_price"] or product["regular_price"])
            subtotal = price * quantity
            vat = subtotal * 0.19  # EU VAT
            city, postcode, country = random.choice(eu_cities)
            
            order = {
                "id": 2001 + i,
                "number": f"WC-{2001 + i}",
                "status": random.choice(statuses),
                "currency": "EUR",
                "date_created": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "date_modified": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "total": f"{subtotal + vat:.2f}",
                "total_tax": f"{vat:.2f}",
                "billing": {
                    "first_name": f"Customer{i}",
                    "last_name": "European",
                    "email": f"customer{i}@eu-example.com",
                    "phone": f"+49-30-{1000000 + i}",
                    "address_1": f"Hauptstraße {100 + i}",
                    "city": city,
                    "postcode": postcode,
                    "country": country
                },
                "shipping": {
                    "first_name": f"Customer{i}",
                    "last_name": "European",
                    "address_1": f"Hauptstraße {100 + i}",
                    "city": city,
                    "postcode": postcode,
                    "country": country
                },
                "line_items": [{
                    "id": 3001 + i,
                    "product_id": product["id"],
                    "name": product["name"],
                    "sku": product["sku"],
                    "quantity": quantity,
                    "price": price,
                    "total": f"{subtotal:.2f}"
                }],
                "payment_method": random.choice(["stripe", "paypal", "bacs"]),
                "payment_method_title": random.choice(["Credit Card", "PayPal", "Bank Transfer"])
            }
            self._demo_orders.append(order)
    
    def normalize_product(self, raw_product: dict) -> dict:
        """Normalize WooCommerce product to common format"""
        categories = raw_product.get("categories", [])
        images = raw_product.get("images", [])
        price = raw_product.get("sale_price") or raw_product.get("regular_price", "0")
        
        return {
            "external_id": str(raw_product.get("id", "")),
            "platform": "woocommerce",
            "name": raw_product.get("name", ""),
            "description": raw_product.get("description", ""),
            "sku": raw_product.get("sku", ""),
            "price": float(price) if price else 0,
            "stock": raw_product.get("stock_quantity", 0),
            "category": categories[0]["name"] if categories else "",
            "image_url": images[0]["src"] if images else "",
            "status": raw_product.get("stock_status", ""),
            "created_at": raw_product.get("date_created", ""),
            "updated_at": raw_product.get("date_modified", ""),
            "raw_data": raw_product
        }
    
    def normalize_order(self, raw_order: dict) -> dict:
        """Normalize WooCommerce order to common format"""
        billing = raw_order.get("billing", {})
        shipping = raw_order.get("shipping", {})
        
        items = []
        for item in raw_order.get("line_items", []):
            items.append({
                "product_id": str(item.get("product_id", "")),
                "name": item.get("name", ""),
                "sku": item.get("sku", ""),
                "quantity": item.get("quantity", 0),
                "price": float(item.get("price", 0))
            })
        
        # Map WooCommerce status to common status
        status_map = {
            "pending": "pending",
            "processing": "processing",
            "on-hold": "on_hold",
            "completed": "completed",
            "cancelled": "cancelled",
            "refunded": "refunded",
            "failed": "failed"
        }
        
        return {
            "external_id": str(raw_order.get("id", "")),
            "order_number": raw_order.get("number", ""),
            "platform": "woocommerce",
            "status": status_map.get(raw_order.get("status", ""), "pending"),
            "original_status": raw_order.get("status", ""),
            "customer_email": billing.get("email", ""),
            "customer_name": f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip(),
            "total": float(raw_order.get("total", 0)),
            "tax": float(raw_order.get("total_tax", 0)),
            "currency": raw_order.get("currency", "EUR"),
            "items": items,
            "shipping_address": {
                "name": f"{shipping.get('first_name', '')} {shipping.get('last_name', '')}".strip(),
                "address1": shipping.get("address_1", ""),
                "city": shipping.get("city", ""),
                "state": shipping.get("state", ""),
                "zip": shipping.get("postcode", ""),
                "country": shipping.get("country", "")
            },
            "payment_method": raw_order.get("payment_method_title", ""),
            "created_at": raw_order.get("date_created", ""),
            "raw_data": raw_order
        }
    
    def normalize_customer(self, raw_customer: dict) -> dict:
        """Normalize WooCommerce customer to common format"""
        return {
            "external_id": raw_customer.get("email", ""),
            "platform": "woocommerce",
            "email": raw_customer.get("email", ""),
            "name": f"{raw_customer.get('first_name', '')} {raw_customer.get('last_name', '')}".strip(),
            "phone": raw_customer.get("phone", ""),
            "address": {
                "address1": raw_customer.get("address_1", ""),
                "city": raw_customer.get("city", ""),
                "state": raw_customer.get("state", ""),
                "zip": raw_customer.get("postcode", ""),
                "country": raw_customer.get("country", "")
            },
            "raw_data": raw_customer
        }
```

---

## TASK 5: AMAZON ADAPTER

### 5.1 Create Amazon Seller Adapter

**File:** `backend/app/services/ecommerce/amazon_adapter.py`

```python
"""
Amazon Seller Central Adapter
Handles all Amazon SP-API interactions (simulated for demo)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
from app.services.ecommerce.base_adapter import BaseEcommerceAdapter


class AmazonAdapter(BaseEcommerceAdapter):
    """Amazon Seller Central adapter (simulated)"""
    
    # Amazon Marketplace IDs
    MARKETPLACES = {
        "US": {"id": "ATVPDKIKX0DER", "currency": "USD", "name": "Amazon.com"},
        "UK": {"id": "A1F83G8C2ARO7P", "currency": "GBP", "name": "Amazon.co.uk"},
        "DE": {"id": "A1PA6795UKMFR9", "currency": "EUR", "name": "Amazon.de"},
        "FR": {"id": "A13V1IB3VIYZZH", "currency": "EUR", "name": "Amazon.fr"},
        "IT": {"id": "APJ6JRA9NG5V4", "currency": "EUR", "name": "Amazon.it"},
        "ES": {"id": "A1RKKUPIHCS9HS", "currency": "EUR", "name": "Amazon.es"},
        "NL": {"id": "A1805IZSGTT6HS", "currency": "EUR", "name": "Amazon.nl"},
        "CA": {"id": "A2EUQ1WTGCTBG2", "currency": "CAD", "name": "Amazon.ca"},
        "AU": {"id": "A39IBJ37TRP1C6", "currency": "AUD", "name": "Amazon.com.au"}
    }
    
    # Simulated product data
    _demo_products = [
        {
            "asin": "B08N5WRWNW",
            "seller_sku": "AMZ-HDPH-001",
            "item_name": "Premium Wireless Headphones",
            "product_description": "High-quality wireless headphones with noise cancellation",
            "price": {"amount": 79.99, "currency": "USD"},
            "fulfillable_quantity": 150,
            "fulfillment_channel": "FBA",
            "status": "Active",
            "image_url": "https://via.placeholder.com/400x400?text=Headphones"
        },
        {
            "asin": "B09XYZ1234",
            "seller_sku": "AMZ-SPKR-001",
            "item_name": "Portable Bluetooth Speaker",
            "product_description": "Waterproof portable speaker with 20-hour battery",
            "price": {"amount": 49.99, "currency": "USD"},
            "fulfillable_quantity": 200,
            "fulfillment_channel": "MFN",
            "status": "Active",
            "image_url": "https://via.placeholder.com/400x400?text=Speaker"
        },
        {
            "asin": "B07ABC5678",
            "seller_sku": "AMZ-CHRG-001",
            "item_name": "Fast Wireless Charger",
            "product_description": "15W fast wireless charging pad for smartphones",
            "price": {"amount": 29.99, "currency": "USD"},
            "fulfillable_quantity": 300,
            "fulfillment_channel": "FBA",
            "status": "Active",
            "image_url": "https://via.placeholder.com/400x400?text=Charger"
        }
    ]
    
    _demo_orders = []
    
    @property
    def platform_name(self) -> str:
        return "amazon"
    
    async def test_connection(self) -> dict:
        """Test Amazon SP-API connection"""
        marketplace = self.credentials.get("marketplace", "US")
        mp_info = self.MARKETPLACES.get(marketplace, self.MARKETPLACES["US"])
        
        return {
            "success": True,
            "seller_info": {
                "marketplace": mp_info["name"],
                "marketplace_id": mp_info["id"],
                "currency": mp_info["currency"],
                "seller_id": self.credentials.get("seller_id", "A1234567890XYZ")
            }
        }
    
    async def get_products(self, limit: int = 50, page: int = 1) -> List[dict]:
        """Get products from Amazon"""
        start = (page - 1) * limit
        end = start + limit
        products = self._demo_products[start:end]
        return [self.normalize_product(p) for p in products]
    
    async def get_product(self, product_id: str) -> Optional[dict]:
        """Get single product by ASIN or SKU"""
        for product in self._demo_products:
            if product["asin"] == product_id or product["seller_sku"] == product_id:
                return self.normalize_product(product)
        return None
    
    async def create_product(self, product_data: dict) -> dict:
        """Create product listing in Amazon"""
        new_product = {
            "asin": f"B{random.randint(10000000, 99999999)}",
            "seller_sku": product_data.get("sku", f"AMZ-{random.randint(1000, 9999)}"),
            "item_name": product_data.get("name", ""),
            "product_description": product_data.get("description", ""),
            "price": {"amount": product_data.get("price", 0), "currency": "USD"},
            "fulfillable_quantity": product_data.get("stock", 0),
            "fulfillment_channel": "MFN",
            "status": "Active",
            "image_url": ""
        }
        self._demo_products.append(new_product)
        return self.normalize_product(new_product)
    
    async def update_product(self, product_id: str, product_data: dict) -> dict:
        """Update product in Amazon"""
        for product in self._demo_products:
            if product["asin"] == product_id or product["seller_sku"] == product_id:
                if "name" in product_data:
                    product["item_name"] = product_data["name"]
                if "description" in product_data:
                    product["product_description"] = product_data["description"]
                if "price" in product_data:
                    product["price"]["amount"] = product_data["price"]
                if "stock" in product_data:
                    product["fulfillable_quantity"] = product_data["stock"]
                return self.normalize_product(product)
        return {"error": "Product not found"}
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete product from Amazon (set to inactive)"""
        for product in self._demo_products:
            if product["asin"] == product_id or product["seller_sku"] == product_id:
                product["status"] = "Inactive"
                return True
        return False
    
    async def get_inventory(self, product_id: str = None) -> List[dict]:
        """Get FBA and MFN inventory levels"""
        inventory = []
        for product in self._demo_products:
            if product_id and product["asin"] != product_id and product["seller_sku"] != product_id:
                continue
            inventory.append({
                "product_id": product["asin"],
                "sku": product["seller_sku"],
                "quantity": product["fulfillable_quantity"],
                "fulfillment_channel": product["fulfillment_channel"]
            })
        return inventory
    
    async def update_inventory(self, product_id: str, quantity: int) -> dict:
        """Update inventory in Amazon"""
        for product in self._demo_products:
            if product["asin"] == product_id or product["seller_sku"] == product_id:
                product["fulfillable_quantity"] = quantity
                return {
                    "success": True,
                    "product_id": product_id,
                    "new_quantity": quantity,
                    "fulfillment_channel": product["fulfillment_channel"]
                }
        return {"error": "Product not found"}
    
    async def get_orders(
        self,
        status: str = None,
        since: datetime = None,
        limit: int = 50
    ) -> List[dict]:
        """Get orders from Amazon"""
        if not self._demo_orders:
            self._generate_demo_orders()
        
        orders = self._demo_orders
        if status:
            orders = [o for o in orders if o["order_status"] == status]
        if since:
            orders = [o for o in orders if o["purchase_date"] >= since.isoformat()]
        
        return [self.normalize_order(o) for o in orders[:limit]]
    
    async def get_order(self, order_id: str) -> Optional[dict]:
        """Get single order"""
        for order in self._demo_orders:
            if order["amazon_order_id"] == order_id:
                return self.normalize_order(order)
        return None
    
    async def get_customers(self, limit: int = 50, page: int = 1) -> List[dict]:
        """Get customers from orders"""
        customers = {}
        for order in self._demo_orders:
            buyer = order.get("buyer_info", {})
            if buyer.get("buyer_email"):
                customers[buyer["buyer_email"]] = buyer
        
        return [self.normalize_customer(c) for c in list(customers.values())[:limit]]
    
    async def get_customer(self, customer_id: str) -> Optional[dict]:
        """Get single customer"""
        for order in self._demo_orders:
            buyer = order.get("buyer_info", {})
            if buyer.get("buyer_email") == customer_id:
                return self.normalize_customer(buyer)
        return None
    
    def _generate_demo_orders(self):
        """Generate demo Amazon orders"""
        statuses = ["Shipped", "Pending", "Unshipped"]
        
        for i in range(12):
            product = random.choice(self._demo_products)
            quantity = random.randint(1, 3)
            subtotal = product["price"]["amount"] * quantity
            
            order = {
                "amazon_order_id": f"111-{random.randint(1000000, 9999999)}-{random.randint(1000000, 9999999)}",
                "purchase_date": (datetime.utcnow() - timedelta(days=i)).isoformat() + "Z",
                "order_status": random.choice(statuses),
                "fulfillment_channel": product["fulfillment_channel"],
                "order_total": {"amount": subtotal + 5.99, "currency": "USD"},
                "buyer_info": {
                    "buyer_email": f"buyer{i}@marketplace.amazon.com",
                    "buyer_name": f"Amazon Customer {1000 + i}"
                },
                "shipping_address": {
                    "name": f"Customer {1000 + i}",
                    "address_line1": f"{100 + i} Commerce St",
                    "city": random.choice(["New York", "Los Angeles", "Chicago", "London", "Berlin"]),
                    "state_or_region": random.choice(["NY", "CA", "IL", "UK", "DE"]),
                    "postal_code": f"{10000 + i}",
                    "country_code": random.choice(["US", "GB", "DE"])
                },
                "order_items": [{
                    "asin": product["asin"],
                    "seller_sku": product["seller_sku"],
                    "title": product["item_name"],
                    "quantity_ordered": quantity,
                    "item_price": {"amount": product["price"]["amount"], "currency": "USD"}
                }]
            }
            self._demo_orders.append(order)
    
    def normalize_product(self, raw_product: dict) -> dict:
        """Normalize Amazon product to common format"""
        price = raw_product.get("price", {})
        
        return {
            "external_id": raw_product.get("asin", ""),
            "platform": "amazon",
            "name": raw_product.get("item_name", ""),
            "description": raw_product.get("product_description", ""),
            "sku": raw_product.get("seller_sku", ""),
            "price": price.get("amount", 0),
            "currency": price.get("currency", "USD"),
            "stock": raw_product.get("fulfillable_quantity", 0),
            "fulfillment_channel": raw_product.get("fulfillment_channel", "MFN"),
            "image_url": raw_product.get("image_url", ""),
            "status": raw_product.get("status", ""),
            "asin": raw_product.get("asin", ""),
            "raw_data": raw_product
        }
    
    def normalize_order(self, raw_order: dict) -> dict:
        """Normalize Amazon order to common format"""
        buyer = raw_order.get("buyer_info", {})
        order_total = raw_order.get("order_total", {})
        shipping = raw_order.get("shipping_address", {})
        
        items = []
        for item in raw_order.get("order_items", []):
            item_price = item.get("item_price", {})
            items.append({
                "product_id": item.get("asin", ""),
                "name": item.get("title", ""),
                "sku": item.get("seller_sku", ""),
                "quantity": item.get("quantity_ordered", 0),
                "price": item_price.get("amount", 0)
            })
        
        # Map Amazon status to common status
        status_map = {
            "Pending": "pending",
            "Unshipped": "processing",
            "Shipped": "completed",
            "Canceled": "cancelled"
        }
        
        return {
            "external_id": raw_order.get("amazon_order_id", ""),
            "order_number": raw_order.get("amazon_order_id", ""),
            "platform": "amazon",
            "status": status_map.get(raw_order.get("order_status", ""), "pending"),
            "original_status": raw_order.get("order_status", ""),
            "fulfillment_channel": raw_order.get("fulfillment_channel", ""),
            "customer_email": buyer.get("buyer_email", ""),
            "customer_name": buyer.get("buyer_name", ""),
            "total": order_total.get("amount", 0),
            "currency": order_total.get("currency", "USD"),
            "items": items,
            "shipping_address": {
                "name": shipping.get("name", ""),
                "address1": shipping.get("address_line1", ""),
                "city": shipping.get("city", ""),
                "state": shipping.get("state_or_region", ""),
                "zip": shipping.get("postal_code", ""),
                "country": shipping.get("country_code", "")
            },
            "created_at": raw_order.get("purchase_date", ""),
            "raw_data": raw_order
        }
    
    def normalize_customer(self, raw_customer: dict) -> dict:
        """Normalize Amazon customer to common format"""
        return {
            "external_id": raw_customer.get("buyer_email", ""),
            "platform": "amazon",
            "email": raw_customer.get("buyer_email", ""),
            "name": raw_customer.get("buyer_name", ""),
            "raw_data": raw_customer
        }
```

---

## FILES CHECKLIST - PART 1

### Backend Services Created:
- [x] `backend/app/services/ecommerce/__init__.py`
- [x] `backend/app/services/ecommerce/base_adapter.py`
- [x] `backend/app/services/ecommerce/connection_service.py`
- [x] `backend/app/services/ecommerce/shopify_adapter.py`
- [x] `backend/app/services/ecommerce/woocommerce_adapter.py`
- [x] `backend/app/services/ecommerce/amazon_adapter.py`

### Platforms Supported (EU/US):
- [x] Shopify (Global)
- [x] WooCommerce (EU focus)
- [x] Amazon Seller Central (US/EU marketplaces)

---

*Continue to Part 2 for Sync Services, Routes, and Webhooks*
