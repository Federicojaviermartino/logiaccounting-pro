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
