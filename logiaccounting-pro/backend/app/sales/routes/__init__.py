"""
Sales Routes Module
API endpoints for sales management
"""

from fastapi import APIRouter

from app.sales.routes.customers import router as customers_router
from app.sales.routes.orders import router as orders_router
from app.sales.routes.fulfillment import router as fulfillment_router
from app.sales.routes.invoices import router as invoices_router


router = APIRouter(prefix="/sales")

router.include_router(customers_router)
router.include_router(orders_router)
router.include_router(fulfillment_router)
router.include_router(invoices_router)


__all__ = [
    'router',
    'customers_router',
    'orders_router',
    'fulfillment_router',
    'invoices_router',
]
