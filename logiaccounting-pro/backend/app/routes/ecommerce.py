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
