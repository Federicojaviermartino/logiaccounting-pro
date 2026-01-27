"""
Security Routes Module
Provides security-related API endpoints.
"""

from fastapi import APIRouter
from .mfa import router as mfa_router
from .sessions import router as sessions_router
from .audit import router as audit_router

router = APIRouter()

router.include_router(mfa_router, prefix="/mfa", tags=["MFA"])
router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
router.include_router(audit_router, prefix="/audit", tags=["Audit"])

__all__ = ["router", "mfa_router", "sessions_router", "audit_router"]
