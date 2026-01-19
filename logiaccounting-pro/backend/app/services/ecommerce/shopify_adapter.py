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
