"""
Accounting API Routes
"""

from fastapi import APIRouter

from app.accounting.routes.accounts import router as accounts_router
from app.accounting.routes.journal import router as journal_router
from app.accounting.routes.ledger import router as ledger_router
from app.accounting.routes.periods import router as periods_router

# Create main accounting router
accounting_router = APIRouter(prefix="/accounting", tags=["Accounting"])

# Include sub-routers
accounting_router.include_router(accounts_router)
accounting_router.include_router(journal_router)
accounting_router.include_router(ledger_router)
accounting_router.include_router(periods_router)

__all__ = ['accounting_router']
