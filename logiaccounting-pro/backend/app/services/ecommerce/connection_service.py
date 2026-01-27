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
            "icon": "shopify",
            "auth_type": "oauth",
            "features": ["products", "inventory", "orders", "customers", "webhooks"],
            "markets": ["US", "EU", "UK", "CA", "AU"]
        },
        "woocommerce": {
            "name": "WooCommerce",
            "icon": "woocommerce",
            "auth_type": "api_key",
            "features": ["products", "inventory", "orders", "customers", "webhooks"],
            "markets": ["Global"]
        },
        "amazon": {
            "name": "Amazon Seller Central",
            "icon": "amazon",
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
