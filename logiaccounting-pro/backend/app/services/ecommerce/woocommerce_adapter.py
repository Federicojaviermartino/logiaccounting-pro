"""
WooCommerce Adapter
Handles all WooCommerce REST API interactions (simulated for demo)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
from app.services.ecommerce.base_adapter import BaseEcommerceAdapter
from app.utils.datetime_utils import utc_now


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
            "date_created": utc_now().isoformat(),
            "date_modified": utc_now().isoformat()
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
                product["date_modified"] = utc_now().isoformat()
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
                "date_created": (utc_now() - timedelta(days=i)).isoformat(),
                "date_modified": (utc_now() - timedelta(days=i)).isoformat(),
                "total": f"{subtotal + vat:.2f}",
                "total_tax": f"{vat:.2f}",
                "billing": {
                    "first_name": f"Customer{i}",
                    "last_name": "European",
                    "email": f"customer{i}@eu-example.com",
                    "phone": f"+49-30-{1000000 + i}",
                    "address_1": f"Hauptstrasse {100 + i}",
                    "city": city,
                    "postcode": postcode,
                    "country": country
                },
                "shipping": {
                    "first_name": f"Customer{i}",
                    "last_name": "European",
                    "address_1": f"Hauptstrasse {100 + i}",
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
