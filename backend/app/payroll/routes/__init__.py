"""Payroll module route registration."""
from fastapi import APIRouter

from app.payroll.routes.employees import router as employees_router
from app.payroll.routes.payroll import router as payroll_router
from app.payroll.routes.deductions import router as deductions_router
from app.payroll.routes.time_off import router as time_off_router

router = APIRouter(prefix="/payroll", tags=["Payroll & HR"])

router.include_router(employees_router)
router.include_router(payroll_router)
router.include_router(deductions_router)
router.include_router(time_off_router)

__all__ = ["router"]
