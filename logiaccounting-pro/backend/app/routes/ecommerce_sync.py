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
