"""Budgeting module route registration."""
from fastapi import APIRouter

from app.budgeting.routes.budgets import router as budgets_router
from app.budgeting.routes.allocations import router as allocations_router

router = APIRouter(prefix="/budgeting", tags=["Budgeting"])

router.include_router(budgets_router)
router.include_router(allocations_router)

__all__ = ["router"]
