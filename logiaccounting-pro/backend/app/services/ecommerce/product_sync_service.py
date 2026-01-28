"""
Product Sync Service
Handles bidirectional product synchronization
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid
from app.utils.datetime_utils import utc_now


class ProductSyncService:
    """Service for syncing products between LogiAccounting and e-commerce"""

    _instance = None
    _product_mappings: Dict[str, dict] = {}
    _sync_history: List[dict] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def import_products(
        self,
        store_id: str,
        adapter,
        options: dict = None
    ) -> dict:
        """Import products from e-commerce to LogiAccounting"""
        options = options or {}

        # Get products from platform
        products = await adapter.get_products(limit=100)

        stats = {
            "total": len(products),
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }

        for product in products:
            try:
                external_id = product["external_id"]
                mapping_key = f"{store_id}:{external_id}"

                if mapping_key in self._product_mappings:
                    # Update existing
                    if options.get("update_existing", True):
                        stats["updated"] += 1
                        self._product_mappings[mapping_key]["last_synced"] = (
                            utc_now().isoformat() + "Z"
                        )
                    else:
                        stats["skipped"] += 1
                else:
                    # Create new mapping
                    if options.get("create_missing", True):
                        material_id = f"MAT-{uuid.uuid4().hex[:8].upper()}"
                        self._product_mappings[mapping_key] = {
                            "material_id": material_id,
                            "store_id": store_id,
                            "external_id": external_id,
                            "platform": product["platform"],
                            "name": product["name"],
                            "sku": product["sku"],
                            "sync_direction": "import",
                            "last_synced": utc_now().isoformat() + "Z",
                            "created_at": utc_now().isoformat() + "Z"
                        }
                        stats["created"] += 1
                    else:
                        stats["skipped"] += 1
            except Exception as e:
                stats["errors"] += 1

        # Record sync history
        sync_record = {
            "id": f"SYNC-{uuid.uuid4().hex[:8].upper()}",
            "store_id": store_id,
            "type": "products",
            "direction": "import",
            "status": "completed",
            "stats": stats,
            "completed_at": utc_now().isoformat() + "Z"
        }
        self._sync_history.append(sync_record)

        return sync_record

    async def export_products(
        self,
        store_id: str,
        adapter,
        material_ids: List[str] = None
    ) -> dict:
        """Export products from LogiAccounting to e-commerce"""
        stats = {
            "total": 0,
            "created": 0,
            "updated": 0,
            "errors": 0
        }

        # Get mappings for this store
        mappings = [
            m for m in self._product_mappings.values()
            if m["store_id"] == store_id
        ]

        if material_ids:
            mappings = [m for m in mappings if m["material_id"] in material_ids]

        stats["total"] = len(mappings)

        for mapping in mappings:
            try:
                # In real implementation, would push to platform
                mapping["last_synced"] = utc_now().isoformat() + "Z"
                stats["updated"] += 1
            except Exception:
                stats["errors"] += 1

        sync_record = {
            "id": f"SYNC-{uuid.uuid4().hex[:8].upper()}",
            "store_id": store_id,
            "type": "products",
            "direction": "export",
            "status": "completed",
            "stats": stats,
            "completed_at": utc_now().isoformat() + "Z"
        }
        self._sync_history.append(sync_record)

        return sync_record

    def get_mappings(self, store_id: str = None) -> List[dict]:
        """Get product mappings"""
        mappings = list(self._product_mappings.values())
        if store_id:
            mappings = [m for m in mappings if m["store_id"] == store_id]
        return mappings

    def get_sync_history(self, store_id: str = None, limit: int = 20) -> List[dict]:
        """Get sync history"""
        history = self._sync_history
        if store_id:
            history = [h for h in history if h["store_id"] == store_id]
        return sorted(history, key=lambda x: x["completed_at"], reverse=True)[:limit]


product_sync_service = ProductSyncService()
