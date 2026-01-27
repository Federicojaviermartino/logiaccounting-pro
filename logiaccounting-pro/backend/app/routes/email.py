"""
Email notification routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from app.services.email_service import email_service
from app.utils.auth import require_roles

router = APIRouter()


class TestEmailRequest(BaseModel):
    to: str
    template: str
    data: dict = {}


@router.get("/logs")
async def get_email_logs(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    template: Optional[str] = None,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get email logs (admin only)"""
    logs, total = email_service.get_logs(
        limit=limit,
        offset=offset,
        status=status,
        template=template
    )

    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/templates")
async def get_email_templates(
    current_user: dict = Depends(require_roles("admin"))
):
    """Get available email templates (admin only)"""
    return {"templates": email_service.get_templates()}


@router.post("/test")
async def send_test_email(
    request: TestEmailRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Send a test email (admin only)"""
    # Add default data
    data = {
        "user_name": current_user["first_name"],
        "login_url": "https://logiaccounting-pro.onrender.com/login",
        **request.data
    }

    log = email_service.send(
        to=request.to,
        template=request.template,
        data=data
    )

    return {
        "success": log.status == "sent",
        "log": {
            "id": log.id,
            "to": log.to,
            "subject": log.subject,
            "status": log.status,
            "sent_at": log.sent_at,
            "error": log.error
        }
    }
