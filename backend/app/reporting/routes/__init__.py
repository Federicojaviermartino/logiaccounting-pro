"""Reporting module route registration."""
from fastapi import APIRouter

from app.reporting.routes.financial_statements import router as financial_statements_router
from app.reporting.routes.dashboard import router as dashboard_router
from app.reporting.routes.export import router as export_router

router = APIRouter(prefix="/reporting", tags=["Reporting"])

router.include_router(financial_statements_router)
router.include_router(dashboard_router)
router.include_router(export_router)

__all__ = ["router"]
