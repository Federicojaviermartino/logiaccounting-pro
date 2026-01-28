"""Document module route registration."""
from fastapi import APIRouter

from app.documents.routes.documents import router as documents_router
from app.documents.routes.folders import router as folders_router
from app.documents.routes.sharing import router as sharing_router, public_router

router = APIRouter()

router.include_router(documents_router)
router.include_router(folders_router)
router.include_router(sharing_router)

__all__ = ["router", "public_router"]
