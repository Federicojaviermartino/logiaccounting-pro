"""Budgeting module route registration."""
from fastapi import APIRouter

from app.budgeting.routes.budgets import router as budgets_router
from app.budgeting.routes.allocations import router as allocations_router
from app.budgeting.routes.variance import router as variance_router
from app.budgeting.routes.forecasts import router as forecasts_router
from app.budgeting.routes.reports import router as reports_router

router = APIRouter(prefix="/budgeting", tags=["Budgeting"])

router.include_router(budgets_router)
router.include_router(allocations_router)
router.include_router(variance_router)
router.include_router(forecasts_router)
router.include_router(reports_router)

__all__ = ["router"]
