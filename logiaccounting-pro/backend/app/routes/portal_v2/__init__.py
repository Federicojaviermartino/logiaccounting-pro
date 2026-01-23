"""
Portal v2 Routes
Customer Self-Service Hub API
"""

from fastapi import APIRouter

from . import auth, dashboard, account, tickets, knowledge, payments, projects, quotes, messages

router = APIRouter(prefix="/portal/v2", tags=["portal-v2"])

router.include_router(auth.router, prefix="/auth", tags=["portal-auth"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["portal-dashboard"])
router.include_router(account.router, prefix="/account", tags=["portal-account"])
router.include_router(tickets.router, prefix="/tickets", tags=["portal-tickets"])
router.include_router(knowledge.router, prefix="/kb", tags=["portal-knowledge"])
router.include_router(payments.router, prefix="/payments", tags=["portal-payments"])
router.include_router(projects.router, prefix="/projects", tags=["portal-projects"])
router.include_router(quotes.router, prefix="/quotes", tags=["portal-quotes"])
router.include_router(messages.router, prefix="/messages", tags=["portal-messages"])
