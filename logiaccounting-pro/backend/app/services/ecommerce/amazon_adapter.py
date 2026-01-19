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
