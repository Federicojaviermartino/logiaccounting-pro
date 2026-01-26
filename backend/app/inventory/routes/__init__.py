"""Inventory Routes"""

from fastapi import APIRouter
from app.inventory.routes.products import router as products_router
from app.inventory.routes.warehouses import router as warehouses_router
from app.inventory.routes.stock import router as stock_router
from app.inventory.routes.movements import router as movements_router

router = APIRouter(prefix="/inventory")

router.include_router(products_router)
router.include_router(warehouses_router)
router.include_router(stock_router)
router.include_router(movements_router)
