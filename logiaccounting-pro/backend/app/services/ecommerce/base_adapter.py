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
