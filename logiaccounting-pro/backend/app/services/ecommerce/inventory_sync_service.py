"""
Inventory Sync Service
Handles real-time inventory synchronization
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid


class InventorySyncService:
    """Service for syncing inventory between systems"""

    _instance = None
    _inventory_cache: Dict[str, dict] = {}
    _low_stock_alerts: List[dict] = []
    _sync_log: List[dict] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def pull_inventory(self, store_id: str, adapter) -> dict:
        """Pull inventory from e-commerce platform"""
        inventory = await adapter.get_inventory()

        stats = {
            "total": len(inventory),
            "updated": 0,
            "alerts_created": 0
        }

        threshold = adapter.settings.get("low_stock_threshold", 10)

        for item in inventory:
            cache_key = f"{store_id}:{item['product_id']}"

            # Update cache
            self._inventory_cache[cache_key] = {
                "store_id": store_id,
                "product_id": item["product_id"],
                "sku": item["sku"],
                "quantity": item["quantity"],
                "platform": adapter.platform_name,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            stats["updated"] += 1

            # Check for low stock
            if item["quantity"] <= threshold:
                alert = {
                    "id": f"ALERT-{uuid.uuid4().hex[:8].upper()}",
                    "store_id": store_id,
                    "product_id": item["product_id"],
                    "sku": item["sku"],
                    "current_stock": item["quantity"],
                    "threshold": threshold,
                    "platform": adapter.platform_name,
                    "severity": "critical" if item["quantity"] == 0 else "warning",
                    "created_at": datetime.utcnow().isoformat() + "Z"
                }
                self._low_stock_alerts.append(alert)
                stats["alerts_created"] += 1

        # Log sync
        self._sync_log.append({
            "id": f"INVLOG-{uuid.uuid4().hex[:8].upper()}",
            "store_id": store_id,
            "action": "pull",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

        return {"success": True, "stats": stats}

    async def push_inventory(
        self,
        store_id: str,
        adapter,
        product_id: str,
        quantity: int,
        reason: str = None
    ) -> dict:
        """Push inventory update to e-commerce platform"""
        result = await adapter.update_inventory(product_id, quantity)

        if result.get("success"):
            cache_key = f"{store_id}:{product_id}"
            if cache_key in self._inventory_cache:
                self._inventory_cache[cache_key]["quantity"] = quantity
                self._inventory_cache[cache_key]["updated_at"] = (
                    datetime.utcnow().isoformat() + "Z"
                )

            self._sync_log.append({
                "id": f"INVLOG-{uuid.uuid4().hex[:8].upper()}",
                "store_id": store_id,
                "action": "push",
                "product_id": product_id,
                "new_quantity": quantity,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        return result

    def get_low_stock_alerts(
        self,
        store_id: str = None,
        severity: str = None
    ) -> List[dict]:
        """Get low stock alerts"""
        alerts = self._low_stock_alerts
        if store_id:
            alerts = [a for a in alerts if a["store_id"] == store_id]
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        return sorted(alerts, key=lambda x: x["created_at"], reverse=True)

    def clear_alert(self, alert_id: str) -> bool:
        """Clear a low stock alert"""
        for i, alert in enumerate(self._low_stock_alerts):
            if alert["id"] == alert_id:
                self._low_stock_alerts.pop(i)
                return True
        return False

    def get_sync_log(self, store_id: str = None, limit: int = 50) -> List[dict]:
        """Get inventory sync log"""
        log = self._sync_log
        if store_id:
            log = [l for l in log if l["store_id"] == store_id]
        return sorted(log, key=lambda x: x["timestamp"], reverse=True)[:limit]


inventory_sync_service = InventorySyncService()
