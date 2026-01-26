"""Purchasing Routes"""

from fastapi import APIRouter
from app.purchasing.routes.suppliers import router as suppliers_router
from app.purchasing.routes.orders import router as orders_router
from app.purchasing.routes.receiving import router as receiving_router
from app.purchasing.routes.invoices import router as invoices_router

router = APIRouter(prefix="/purchasing")

router.include_router(suppliers_router)
router.include_router(orders_router)
router.include_router(receiving_router)
router.include_router(invoices_router)
