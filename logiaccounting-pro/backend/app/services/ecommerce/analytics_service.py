"""
E-commerce Analytics Service
Provides analytics and reporting for e-commerce channels
"""

from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict


class EcommerceAnalyticsService:
    """Service for e-commerce analytics"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_dashboard_summary(
        self,
        connection_service,
        order_service,
        product_sync_service
    ) -> dict:
        """Get dashboard summary data"""
        stores = connection_service.get_stores()
        orders = order_service.get_imported_orders(limit=1000)
        mappings = product_sync_service.get_mappings()

        # Calculate totals
        total_revenue = sum(o.get("total", 0) for o in orders)

        return {
            "stores": {
                "total": len(stores),
                "connected": len([s for s in stores if s["status"] == "connected"]),
                "error": len([s for s in stores if s["status"] == "error"])
            },
            "products": {
                "total": len(mappings),
                "synced": len([m for m in mappings if m.get("last_synced")])
            },
            "orders": {
                "total": len(orders),
                "pending": len([o for o in orders if o["status"] == "pending"]),
                "completed": len([o for o in orders if o["status"] == "completed"])
            },
            "revenue": {
                "total": total_revenue,
                "currency": "USD"
            }
        }

    def get_revenue_by_store(self, order_service, connection_service) -> List[dict]:
        """Get revenue breakdown by store"""
        stores = connection_service.get_stores()
        orders = order_service.get_imported_orders(limit=1000)

        revenue_by_store = defaultdict(float)
        orders_by_store = defaultdict(int)

        for order in orders:
            store_id = order.get("store_id")
            revenue_by_store[store_id] += order.get("total", 0)
            orders_by_store[store_id] += 1

        result = []
        for store in stores:
            store_id = store["id"]
            result.append({
                "store_id": store_id,
                "store_name": store["name"],
                "platform": store["platform"],
                "revenue": revenue_by_store.get(store_id, 0),
                "orders": orders_by_store.get(store_id, 0)
            })

        return sorted(result, key=lambda x: x["revenue"], reverse=True)

    def get_top_products(self, order_service, limit: int = 10) -> List[dict]:
        """Get top selling products"""
        orders = order_service.get_imported_orders(limit=1000)

        product_sales = defaultdict(lambda: {"quantity": 0, "revenue": 0})

        for order in orders:
            for item in order.get("items", []):
                key = item.get("sku") or item.get("product_id")
                if key:
                    product_sales[key]["name"] = item.get("name", "")
                    product_sales[key]["sku"] = item.get("sku", "")
                    product_sales[key]["quantity"] += item.get("quantity", 0)
                    product_sales[key]["revenue"] += (
                        item.get("price", 0) * item.get("quantity", 0)
                    )

        result = [
            {"sku": k, **v} for k, v in product_sales.items()
        ]

        return sorted(result, key=lambda x: x["revenue"], reverse=True)[:limit]

    def get_sync_status(self, connection_service) -> List[dict]:
        """Get sync status for all stores"""
        stores = connection_service.get_stores()

        result = []
        for store in stores:
            last_sync = store.get("last_sync", {})
            result.append({
                "store_id": store["id"],
                "store_name": store["name"],
                "platform": store["platform"],
                "status": store["status"],
                "last_product_sync": last_sync.get("products"),
                "last_inventory_sync": last_sync.get("inventory"),
                "last_order_sync": last_sync.get("orders")
            })

        return result

    def get_platform_distribution(self, connection_service) -> dict:
        """Get distribution of stores by platform"""
        stores = connection_service.get_stores()

        distribution = defaultdict(int)
        for store in stores:
            distribution[store["platform"]] += 1

        return dict(distribution)


analytics_service = EcommerceAnalyticsService()
