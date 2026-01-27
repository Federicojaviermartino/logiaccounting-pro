"""Audit module route registration."""
from fastapi import APIRouter

from app.audit.routes.audit import router as audit_router
from app.audit.routes.compliance import router as compliance_router

router = APIRouter()

router.include_router(audit_router)
router.include_router(compliance_router)

__all__ = ["router"]
