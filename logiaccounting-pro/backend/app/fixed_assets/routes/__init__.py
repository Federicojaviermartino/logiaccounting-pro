"""
Fixed assets module route registration.
"""
from fastapi import APIRouter

from app.fixed_assets.routes.categories import router as categories_router
from app.fixed_assets.routes.assets import router as assets_router
from app.fixed_assets.routes.depreciation import router as depreciation_router
from app.fixed_assets.routes.movements import router as movements_router
from app.fixed_assets.routes.reports import router as reports_router

# Main fixed assets router
router = APIRouter(prefix="/fixed-assets", tags=["Fixed Assets"])

# Include sub-routers
router.include_router(categories_router)
router.include_router(assets_router)
router.include_router(depreciation_router)
router.include_router(movements_router)
router.include_router(reports_router)


__all__ = ["router"]
