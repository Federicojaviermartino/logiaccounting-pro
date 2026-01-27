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
