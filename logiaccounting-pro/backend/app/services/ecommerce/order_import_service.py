"""
Order Import Service
Handles importing orders from e-commerce platforms
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid
from app.utils.datetime_utils import utc_now


class OrderImportService:
    """Service for importing orders from e-commerce"""

    _instance = None
    _imported_orders: Dict[str, dict] = {}
    _import_history: List[dict] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def import_orders(
        self,
        store_id: str,
        adapter,
        since: datetime = None,
        status: str = None
    ) -> dict:
        """Import orders from e-commerce platform"""
        orders = await adapter.get_orders(status=status, since=since)

        stats = {
            "total": len(orders),
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "total_revenue": 0
        }

        for order in orders:
            try:
                order_key = f"{store_id}:{order['external_id']}"

                if order_key in self._imported_orders:
                    # Already imported, skip
                    stats["skipped"] += 1
                    continue

                # Create transaction record
                transaction = self._create_transaction(store_id, order, adapter.platform_name)
                self._imported_orders[order_key] = transaction

                stats["imported"] += 1
                stats["total_revenue"] += order.get("total", 0)

            except Exception as e:
                stats["errors"] += 1

        # Record import history
        import_record = {
            "id": f"IMP-{uuid.uuid4().hex[:8].upper()}",
            "store_id": store_id,
            "platform": adapter.platform_name,
            "status": "completed",
            "stats": stats,
            "completed_at": utc_now().isoformat() + "Z"
        }
        self._import_history.append(import_record)

        return import_record

    def _create_transaction(
        self,
        store_id: str,
        order: dict,
        platform: str
    ) -> dict:
        """Create a transaction from an imported order"""
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"

        # Map status
        status_map = {
            "pending": "pending",
            "processing": "processing",
            "completed": "completed",
            "cancelled": "cancelled",
            "refunded": "refunded"
        }

        return {
            "id": transaction_id,
            "type": "sale",
            "source": platform,
            "source_id": order["external_id"],
            "source_order_number": order.get("order_number", ""),
            "store_id": store_id,
            "date": order.get("created_at", utc_now().isoformat() + "Z"),
            "status": status_map.get(order.get("status", ""), "pending"),
            "client_name": order.get("customer_name", ""),
            "client_email": order.get("customer_email", ""),
            "items": order.get("items", []),
            "subtotal": order.get("subtotal", order.get("total", 0)),
            "tax": order.get("tax", 0),
            "total": order.get("total", 0),
            "currency": order.get("currency", "USD"),
            "shipping_address": order.get("shipping_address", {}),
            "payment_method": order.get("payment_method", ""),
            "imported_at": utc_now().isoformat() + "Z"
        }

    def get_imported_orders(
        self,
        store_id: str = None,
        status: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """Get imported orders"""
        orders = list(self._imported_orders.values())

        if store_id:
            orders = [o for o in orders if o["store_id"] == store_id]
        if status:
            orders = [o for o in orders if o["status"] == status]

        # Sort by date descending
        orders = sorted(orders, key=lambda x: x["date"], reverse=True)

        return orders[offset:offset + limit]

    def get_order(self, transaction_id: str) -> Optional[dict]:
        """Get a specific imported order"""
        for order in self._imported_orders.values():
            if order["id"] == transaction_id:
                return order
        return None

    def get_import_history(self, store_id: str = None, limit: int = 20) -> List[dict]:
        """Get import history"""
        history = self._import_history
        if store_id:
            history = [h for h in history if h["store_id"] == store_id]
        return sorted(history, key=lambda x: x["completed_at"], reverse=True)[:limit]

    def get_stats(self, store_id: str = None) -> dict:
        """Get import statistics"""
        orders = list(self._imported_orders.values())
        if store_id:
            orders = [o for o in orders if o["store_id"] == store_id]

        total_revenue = sum(o.get("total", 0) for o in orders)

        return {
            "total_orders": len(orders),
            "total_revenue": total_revenue,
            "by_status": {
                "pending": len([o for o in orders if o["status"] == "pending"]),
                "processing": len([o for o in orders if o["status"] == "processing"]),
                "completed": len([o for o in orders if o["status"] == "completed"]),
                "cancelled": len([o for o in orders if o["status"] == "cancelled"])
            }
        }


order_import_service = OrderImportService()
