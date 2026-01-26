"""
Banking API Routes
"""

from fastapi import APIRouter

from app.banking.routes.accounts import router as accounts_router
from app.banking.routes.transactions import router as transactions_router
from app.banking.routes.reconciliation import router as reconciliation_router
from app.banking.routes.payments import router as payments_router
from app.banking.routes.cashflow import router as cashflow_router

# Create main banking router
banking_router = APIRouter(prefix="/banking", tags=["Banking"])

# Include sub-routers
banking_router.include_router(accounts_router)
banking_router.include_router(transactions_router)
banking_router.include_router(reconciliation_router)
banking_router.include_router(payments_router)
banking_router.include_router(cashflow_router)

__all__ = ['banking_router']
