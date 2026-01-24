"""
Mobile API Routes - Router initialization
"""

from fastapi import APIRouter

from app.routes.mobile import home, notifications, devices, sync


router = APIRouter(prefix="/api/mobile/v1", tags=["Mobile API"])

# Include sub-routers
router.include_router(home.router, tags=["Mobile Home"])
router.include_router(notifications.router, prefix="/notifications", tags=["Mobile Notifications"])
router.include_router(devices.router, prefix="/devices", tags=["Mobile Devices"])
router.include_router(sync.router, prefix="/sync", tags=["Mobile Sync"])


def setup_mobile_routes(app):
    """Setup mobile routes on the FastAPI app."""
    app.include_router(router)
