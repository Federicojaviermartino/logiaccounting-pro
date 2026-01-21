# LogiAccounting Pro - Phase 9 Tasks Part 2

## SYNC SERVICES, ROUTES & WEBHOOKS

---

## TASK 6: PRODUCT SYNC SERVICE

### 6.1 Create Product Sync Service

**File:** `backend/app/services/ecommerce/product_sync_service.py`

```python
"""
Product Sync Service
Handles bidirectional product synchronization
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid


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
                            datetime.utcnow().isoformat() + "Z"
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
                            "last_synced": datetime.utcnow().isoformat() + "Z",
                            "created_at": datetime.utcnow().isoformat() + "Z"
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
            "completed_at": datetime.utcnow().isoformat() + "Z"
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
                mapping["last_synced"] = datetime.utcnow().isoformat() + "Z"
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
            "completed_at": datetime.utcnow().isoformat() + "Z"
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
```

---

## TASK 7: INVENTORY SYNC SERVICE

### 7.1 Create Inventory Sync Service

**File:** `backend/app/services/ecommerce/inventory_sync_service.py`

```python
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
```

---

## TASK 8: ORDER IMPORT SERVICE

### 8.1 Create Order Import Service

**File:** `backend/app/services/ecommerce/order_import_service.py`

```python
"""
Order Import Service
Handles importing orders from e-commerce platforms
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid


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
            "completed_at": datetime.utcnow().isoformat() + "Z"
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
            "date": order.get("created_at", datetime.utcnow().isoformat() + "Z"),
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
            "imported_at": datetime.utcnow().isoformat() + "Z"
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
```

---

## TASK 9: ANALYTICS SERVICE

### 9.1 Create E-commerce Analytics Service

**File:** `backend/app/services/ecommerce/analytics_service.py`

```python
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
```

---

## TASK 10: E-COMMERCE ROUTES

### 10.1 Create Main E-commerce Routes

**File:** `backend/app/routes/ecommerce.py`

```python
"""
E-commerce routes for store management and data access
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.ecommerce.connection_service import ecommerce_service
from app.services.ecommerce.product_sync_service import product_sync_service
from app.services.ecommerce.inventory_sync_service import inventory_sync_service
from app.services.ecommerce.order_import_service import order_import_service
from app.services.ecommerce.analytics_service import analytics_service

router = APIRouter(prefix="/api/v1/ecommerce", tags=["ecommerce"])


# Request/Response Models
class ConnectStoreRequest(BaseModel):
    platform: str
    name: str
    credentials: dict
    settings: Optional[dict] = None


class UpdateStoreRequest(BaseModel):
    name: Optional[str] = None
    settings: Optional[dict] = None
    credentials: Optional[dict] = None


# Store Management
@router.get("/platforms")
async def get_platforms():
    """Get supported e-commerce platforms"""
    return ecommerce_service.get_platforms()


@router.get("/stores")
async def get_stores():
    """Get all connected stores"""
    return ecommerce_service.get_stores()


@router.post("/stores")
async def connect_store(request: ConnectStoreRequest):
    """Connect a new e-commerce store"""
    store = ecommerce_service.connect_store(request.dict())
    return store


@router.get("/stores/{store_id}")
async def get_store(store_id: str):
    """Get a specific store"""
    store = ecommerce_service.get_store(store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.put("/stores/{store_id}")
async def update_store(store_id: str, request: UpdateStoreRequest):
    """Update store settings"""
    store = ecommerce_service.update_store(store_id, request.dict(exclude_none=True))
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.delete("/stores/{store_id}")
async def disconnect_store(store_id: str):
    """Disconnect a store"""
    success = ecommerce_service.disconnect_store(store_id)
    if not success:
        raise HTTPException(status_code=404, detail="Store not found")
    return {"success": True, "message": "Store disconnected"}


@router.post("/stores/{store_id}/test")
async def test_connection(store_id: str):
    """Test store connection"""
    adapter = ecommerce_service.get_adapter(store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    result = await adapter.test_connection()
    return result


# Products
@router.get("/stores/{store_id}/products")
async def get_store_products(store_id: str, limit: int = 50, page: int = 1):
    """Get products from a store"""
    adapter = ecommerce_service.get_adapter(store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    products = await adapter.get_products(limit=limit, page=page)
    return {"products": products, "count": len(products)}


@router.get("/stores/{store_id}/products/{product_id}")
async def get_store_product(store_id: str, product_id: str):
    """Get a specific product from a store"""
    adapter = ecommerce_service.get_adapter(store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    product = await adapter.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# Inventory
@router.get("/stores/{store_id}/inventory")
async def get_store_inventory(store_id: str, product_id: str = None):
    """Get inventory from a store"""
    adapter = ecommerce_service.get_adapter(store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    inventory = await adapter.get_inventory(product_id)
    return {"inventory": inventory}


@router.put("/stores/{store_id}/inventory/{product_id}")
async def update_store_inventory(store_id: str, product_id: str, quantity: int):
    """Update inventory for a product"""
    adapter = ecommerce_service.get_adapter(store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    result = await adapter.update_inventory(product_id, quantity)
    return result


# Orders
@router.get("/stores/{store_id}/orders")
async def get_store_orders(store_id: str, status: str = None, limit: int = 50):
    """Get orders from a store"""
    adapter = ecommerce_service.get_adapter(store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    orders = await adapter.get_orders(status=status, limit=limit)
    return {"orders": orders, "count": len(orders)}


@router.get("/stores/{store_id}/orders/{order_id}")
async def get_store_order(store_id: str, order_id: str):
    """Get a specific order from a store"""
    adapter = ecommerce_service.get_adapter(store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    order = await adapter.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# Customers
@router.get("/stores/{store_id}/customers")
async def get_store_customers(store_id: str, limit: int = 50, page: int = 1):
    """Get customers from a store"""
    adapter = ecommerce_service.get_adapter(store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    customers = await adapter.get_customers(limit=limit, page=page)
    return {"customers": customers, "count": len(customers)}
```

---

### 10.2 Create Sync Routes

**File:** `backend/app/routes/ecommerce_sync.py`

```python
"""
E-commerce sync routes
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from app.services.ecommerce.connection_service import ecommerce_service
from app.services.ecommerce.product_sync_service import product_sync_service
from app.services.ecommerce.inventory_sync_service import inventory_sync_service
from app.services.ecommerce.order_import_service import order_import_service

router = APIRouter(prefix="/api/v1/ecommerce/sync", tags=["ecommerce-sync"])


class SyncRequest(BaseModel):
    store_id: str
    options: Optional[dict] = None


class InventoryUpdateRequest(BaseModel):
    store_id: str
    product_id: str
    quantity: int
    reason: Optional[str] = None


# Product Sync
@router.post("/products")
async def sync_products(request: SyncRequest):
    """Sync products from a store"""
    adapter = ecommerce_service.get_adapter(request.store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    result = await product_sync_service.import_products(
        request.store_id,
        adapter,
        request.options
    )
    
    # Update store sync timestamp
    ecommerce_service.update_sync_status(request.store_id, "products")
    
    return result


@router.get("/products/mappings")
async def get_product_mappings(store_id: str = None):
    """Get product mappings"""
    mappings = product_sync_service.get_mappings(store_id)
    return {"mappings": mappings, "count": len(mappings)}


@router.get("/products/history")
async def get_sync_history(store_id: str = None, limit: int = 20):
    """Get product sync history"""
    history = product_sync_service.get_sync_history(store_id, limit)
    return {"history": history}


# Inventory Sync
@router.post("/inventory")
async def sync_inventory(request: SyncRequest):
    """Pull inventory from a store"""
    adapter = ecommerce_service.get_adapter(request.store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    result = await inventory_sync_service.pull_inventory(request.store_id, adapter)
    
    # Update store sync timestamp
    ecommerce_service.update_sync_status(request.store_id, "inventory")
    
    return result


@router.post("/inventory/push")
async def push_inventory(request: InventoryUpdateRequest):
    """Push inventory update to a store"""
    adapter = ecommerce_service.get_adapter(request.store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    result = await inventory_sync_service.push_inventory(
        request.store_id,
        adapter,
        request.product_id,
        request.quantity,
        request.reason
    )
    return result


@router.get("/inventory/alerts")
async def get_low_stock_alerts(store_id: str = None, severity: str = None):
    """Get low stock alerts"""
    alerts = inventory_sync_service.get_low_stock_alerts(store_id, severity)
    return {"alerts": alerts, "count": len(alerts)}


@router.delete("/inventory/alerts/{alert_id}")
async def clear_alert(alert_id: str):
    """Clear a low stock alert"""
    success = inventory_sync_service.clear_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"success": True}


@router.get("/inventory/log")
async def get_inventory_log(store_id: str = None, limit: int = 50):
    """Get inventory sync log"""
    log = inventory_sync_service.get_sync_log(store_id, limit)
    return {"log": log}


# Order Import
@router.post("/orders")
async def import_orders(request: SyncRequest):
    """Import orders from a store"""
    adapter = ecommerce_service.get_adapter(request.store_id)
    if not adapter:
        raise HTTPException(status_code=404, detail="Store not found")
    
    result = await order_import_service.import_orders(
        request.store_id,
        adapter
    )
    
    # Update store sync timestamp
    ecommerce_service.update_sync_status(request.store_id, "orders")
    
    return result


@router.get("/orders")
async def get_imported_orders(
    store_id: str = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0
):
    """Get imported orders"""
    orders = order_import_service.get_imported_orders(store_id, status, limit, offset)
    stats = order_import_service.get_stats(store_id)
    return {"orders": orders, "count": len(orders), "stats": stats}


@router.get("/orders/{transaction_id}")
async def get_imported_order(transaction_id: str):
    """Get a specific imported order"""
    order = order_import_service.get_order(transaction_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/orders/history")
async def get_import_history(store_id: str = None, limit: int = 20):
    """Get order import history"""
    history = order_import_service.get_import_history(store_id, limit)
    return {"history": history}
```

---

### 10.3 Create Webhook Routes

**File:** `backend/app/routes/ecommerce_webhooks.py`

```python
"""
E-commerce webhook handlers
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import hmac
import hashlib
import base64

from app.services.ecommerce.connection_service import ecommerce_service
from app.services.ecommerce.order_import_service import order_import_service
from app.services.ecommerce.inventory_sync_service import inventory_sync_service

router = APIRouter(prefix="/api/v1/webhooks", tags=["ecommerce-webhooks"])


def verify_shopify_signature(
    body: bytes,
    signature: str,
    secret: str = "demo_webhook_secret"
) -> bool:
    """Verify Shopify webhook signature"""
    computed = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(computed, signature)


def verify_woocommerce_signature(
    body: bytes,
    signature: str,
    secret: str = "demo_webhook_secret"
) -> bool:
    """Verify WooCommerce webhook signature"""
    computed = base64.b64encode(
        hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(computed, signature)


@router.post("/shopify")
async def shopify_webhook(
    request: Request,
    x_shopify_topic: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None),
    x_shopify_hmac_sha256: Optional[str] = Header(None)
):
    """Handle Shopify webhooks"""
    body = await request.body()
    
    # In production, verify signature
    # if not verify_shopify_signature(body, x_shopify_hmac_sha256):
    #     raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = await request.json()
    topic = x_shopify_topic or "unknown"
    
    # Find store by domain
    store = None
    for s in ecommerce_service.get_stores():
        if s["platform"] == "shopify":
            if s["credentials"].get("shop_domain") == x_shopify_shop_domain:
                store = s
                break
    
    if not store:
        # Demo mode - use first Shopify store
        for s in ecommerce_service.get_stores():
            if s["platform"] == "shopify":
                store = s
                break
    
    if store:
        await process_shopify_event(store["id"], topic, data)
    
    return {"received": True, "topic": topic}


async def process_shopify_event(store_id: str, topic: str, data: dict):
    """Process Shopify webhook event"""
    if topic == "orders/create" or topic == "orders/paid":
        # Import order
        adapter = ecommerce_service.get_adapter(store_id)
        if adapter:
            await order_import_service.import_orders(store_id, adapter)
    
    elif topic == "inventory_levels/update":
        # Sync inventory
        adapter = ecommerce_service.get_adapter(store_id)
        if adapter:
            await inventory_sync_service.pull_inventory(store_id, adapter)
    
    elif topic == "products/update":
        # Could trigger product sync
        pass


@router.post("/woocommerce")
async def woocommerce_webhook(
    request: Request,
    x_wc_webhook_topic: Optional[str] = Header(None),
    x_wc_webhook_source: Optional[str] = Header(None),
    x_wc_webhook_signature: Optional[str] = Header(None)
):
    """Handle WooCommerce webhooks"""
    body = await request.body()
    data = await request.json()
    topic = x_wc_webhook_topic or "unknown"
    
    # Find store by URL
    store = None
    for s in ecommerce_service.get_stores():
        if s["platform"] == "woocommerce":
            if x_wc_webhook_source and x_wc_webhook_source.startswith(
                s["credentials"].get("store_url", "")
            ):
                store = s
                break
    
    if not store:
        # Demo mode - use first WooCommerce store
        for s in ecommerce_service.get_stores():
            if s["platform"] == "woocommerce":
                store = s
                break
    
    if store:
        await process_woocommerce_event(store["id"], topic, data)
    
    return {"received": True, "topic": topic}


async def process_woocommerce_event(store_id: str, topic: str, data: dict):
    """Process WooCommerce webhook event"""
    if topic in ["order.created", "order.updated"]:
        adapter = ecommerce_service.get_adapter(store_id)
        if adapter:
            await order_import_service.import_orders(store_id, adapter)
    
    elif topic == "product.updated":
        pass


@router.post("/amazon")
async def amazon_webhook(request: Request):
    """Handle Amazon notifications (SNS)"""
    data = await request.json()
    notification_type = data.get("NotificationType", "unknown")
    
    # Find Amazon store
    store = None
    for s in ecommerce_service.get_stores():
        if s["platform"] == "amazon":
            store = s
            break
    
    if store:
        await process_amazon_event(store["id"], notification_type, data)
    
    return {"received": True, "type": notification_type}


async def process_amazon_event(store_id: str, notification_type: str, data: dict):
    """Process Amazon notification"""
    if notification_type == "ORDER_CHANGE":
        adapter = ecommerce_service.get_adapter(store_id)
        if adapter:
            await order_import_service.import_orders(store_id, adapter)
```

---

### 10.4 Create Analytics Routes

**File:** `backend/app/routes/ecommerce_analytics.py`

```python
"""
E-commerce analytics routes
"""

from fastapi import APIRouter

from app.services.ecommerce.connection_service import ecommerce_service
from app.services.ecommerce.product_sync_service import product_sync_service
from app.services.ecommerce.order_import_service import order_import_service
from app.services.ecommerce.analytics_service import analytics_service

router = APIRouter(prefix="/api/v1/ecommerce/analytics", tags=["ecommerce-analytics"])


@router.get("/summary")
async def get_dashboard_summary():
    """Get dashboard summary"""
    return analytics_service.get_dashboard_summary(
        ecommerce_service,
        order_import_service,
        product_sync_service
    )


@router.get("/revenue")
async def get_revenue_by_store():
    """Get revenue breakdown by store"""
    return analytics_service.get_revenue_by_store(
        order_import_service,
        ecommerce_service
    )


@router.get("/top-products")
async def get_top_products(limit: int = 10):
    """Get top selling products"""
    return analytics_service.get_top_products(order_import_service, limit)


@router.get("/sync-status")
async def get_sync_status():
    """Get sync status for all stores"""
    return analytics_service.get_sync_status(ecommerce_service)


@router.get("/platforms")
async def get_platform_distribution():
    """Get distribution of stores by platform"""
    return analytics_service.get_platform_distribution(ecommerce_service)
```

---

## TASK 11: UPDATE MAIN ROUTES

### 11.1 Update Main App Router

**File:** `backend/app/main.py` (add imports)

```python
# Add these imports
from app.routes import ecommerce
from app.routes import ecommerce_sync
from app.routes import ecommerce_webhooks
from app.routes import ecommerce_analytics

# Add these routers
app.include_router(ecommerce.router)
app.include_router(ecommerce_sync.router)
app.include_router(ecommerce_webhooks.router)
app.include_router(ecommerce_analytics.router)
```

---

## FILES CHECKLIST - PART 2

### Sync Services Created:
- [x] `backend/app/services/ecommerce/product_sync_service.py`
- [x] `backend/app/services/ecommerce/inventory_sync_service.py`
- [x] `backend/app/services/ecommerce/order_import_service.py`
- [x] `backend/app/services/ecommerce/analytics_service.py`

### Routes Created:
- [x] `backend/app/routes/ecommerce.py`
- [x] `backend/app/routes/ecommerce_sync.py`
- [x] `backend/app/routes/ecommerce_webhooks.py`
- [x] `backend/app/routes/ecommerce_analytics.py`

### API Endpoints Summary:
```
Store Management:
  GET    /api/v1/ecommerce/platforms
  GET    /api/v1/ecommerce/stores
  POST   /api/v1/ecommerce/stores
  GET    /api/v1/ecommerce/stores/{id}
  PUT    /api/v1/ecommerce/stores/{id}
  DELETE /api/v1/ecommerce/stores/{id}
  POST   /api/v1/ecommerce/stores/{id}/test

Products:
  GET    /api/v1/ecommerce/stores/{id}/products
  GET    /api/v1/ecommerce/stores/{id}/products/{pid}

Inventory:
  GET    /api/v1/ecommerce/stores/{id}/inventory
  PUT    /api/v1/ecommerce/stores/{id}/inventory/{pid}

Orders:
  GET    /api/v1/ecommerce/stores/{id}/orders
  GET    /api/v1/ecommerce/stores/{id}/orders/{oid}

Sync:
  POST   /api/v1/ecommerce/sync/products
  GET    /api/v1/ecommerce/sync/products/mappings
  POST   /api/v1/ecommerce/sync/inventory
  POST   /api/v1/ecommerce/sync/inventory/push
  GET    /api/v1/ecommerce/sync/inventory/alerts
  POST   /api/v1/ecommerce/sync/orders
  GET    /api/v1/ecommerce/sync/orders

Webhooks:
  POST   /api/v1/webhooks/shopify
  POST   /api/v1/webhooks/woocommerce
  POST   /api/v1/webhooks/amazon

Analytics:
  GET    /api/v1/ecommerce/analytics/summary
  GET    /api/v1/ecommerce/analytics/revenue
  GET    /api/v1/ecommerce/analytics/top-products
  GET    /api/v1/ecommerce/analytics/sync-status
```

---

*Continue to Part 3 for Frontend Components*
