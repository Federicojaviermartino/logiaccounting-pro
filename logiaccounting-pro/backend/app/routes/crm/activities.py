"""
CRM Activities API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.services.crm.activity_service import activity_service
from app.services.crm.email_template_service import email_template_service


router = APIRouter()


# ============================================
# PYDANTIC MODELS
# ============================================

class ActivityCreate(BaseModel):
    type: str
    subject: str
    description: Optional[str] = None
    lead_id: Optional[str] = None
    contact_id: Optional[str] = None
    company_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    due_date: Optional[str] = None
    duration_minutes: Optional[int] = None


class ActivityUpdate(BaseModel):
    subject: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    duration_minutes: Optional[int] = None


class CompleteActivity(BaseModel):
    outcome: Optional[str] = None
    notes: Optional[str] = None


class LogCall(BaseModel):
    subject: str
    outcome: str
    duration_minutes: Optional[int] = None
    contact_id: Optional[str] = None
    lead_id: Optional[str] = None
    company_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    notes: Optional[str] = None
    phone_number: Optional[str] = None
    direction: Optional[str] = "outbound"


class LogEmail(BaseModel):
    subject: str
    body: Optional[str] = None
    contact_id: Optional[str] = None
    lead_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    template_id: Optional[str] = None
    to_email: Optional[str] = None


class ScheduleMeeting(BaseModel):
    subject: str
    start_time: str
    end_time: str
    contact_id: Optional[str] = None
    lead_id: Optional[str] = None
    company_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    attendees: Optional[List[str]] = None
    description: Optional[str] = None


class CreateTask(BaseModel):
    subject: str
    due_date: str
    priority: Optional[str] = "medium"
    contact_id: Optional[str] = None
    lead_id: Optional[str] = None
    company_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    description: Optional[str] = None


class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    body: str
    category: Optional[str] = "general"
    is_shared: Optional[bool] = True


class RenderTemplate(BaseModel):
    template_id: str
    context: dict


# ============================================
# ACTIVITY ENDPOINTS
# ============================================

@router.get("")
async def list_activities(
    type: Optional[str] = None,
    lead_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    company_id: Optional[str] = None,
    opportunity_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List activities with filters"""
    return activity_service.list_activities(
        tenant_id=current_user.get("tenant_id"),
        type=type,
        lead_id=lead_id,
        contact_id=contact_id,
        company_id=company_id,
        opportunity_id=opportunity_id,
        owner_id=owner_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.post("")
async def create_activity(
    data: ActivityCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new activity"""
    return activity_service.create_activity(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.get("/upcoming")
async def get_upcoming_activities(
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
):
    """Get upcoming activities"""
    return activity_service.get_upcoming_activities(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        days=days,
    )


@router.get("/overdue")
async def get_overdue_tasks(
    current_user: dict = Depends(get_current_user),
):
    """Get overdue tasks"""
    return activity_service.get_overdue_tasks(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
    )


@router.get("/stats")
async def get_activity_stats(
    days: int = Query(30, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Get activity statistics"""
    return activity_service.get_activity_stats(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        days=days,
    )


@router.get("/types")
async def get_activity_types():
    """Get available activity types"""
    return activity_service.ACTIVITY_TYPES


@router.get("/call-outcomes")
async def get_call_outcomes():
    """Get available call outcomes"""
    return activity_service.CALL_OUTCOMES


@router.get("/{activity_id}")
async def get_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get activity by ID"""
    activity = activity_service.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.put("/{activity_id}")
async def update_activity(
    activity_id: str,
    data: ActivityUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update activity"""
    activity = activity_service.update_activity(
        activity_id=activity_id,
        user_id=current_user["id"],
        **data.dict(exclude_none=True),
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete activity"""
    if not activity_service.delete_activity(activity_id, current_user["id"]):
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"success": True}


@router.post("/{activity_id}/complete")
async def complete_activity(
    activity_id: str,
    data: CompleteActivity,
    current_user: dict = Depends(get_current_user),
):
    """Mark activity as completed"""
    return activity_service.complete_activity(
        activity_id=activity_id,
        user_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.post("/{activity_id}/cancel")
async def cancel_activity(
    activity_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Cancel activity"""
    return activity_service.cancel_activity(
        activity_id=activity_id,
        user_id=current_user["id"],
        reason=reason,
    )


@router.post("/{activity_id}/reschedule")
async def reschedule_activity(
    activity_id: str,
    new_date: str,
    current_user: dict = Depends(get_current_user),
):
    """Reschedule activity"""
    return activity_service.reschedule_activity(
        activity_id=activity_id,
        user_id=current_user["id"],
        new_date=new_date,
    )


# ============================================
# QUICK ACTIONS
# ============================================

@router.post("/log-call")
async def log_call(
    data: LogCall,
    current_user: dict = Depends(get_current_user),
):
    """Log a completed call"""
    return activity_service.log_call(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.post("/log-email")
async def log_email(
    data: LogEmail,
    current_user: dict = Depends(get_current_user),
):
    """Log a sent email"""
    return activity_service.log_email(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.post("/schedule-meeting")
async def schedule_meeting(
    data: ScheduleMeeting,
    current_user: dict = Depends(get_current_user),
):
    """Schedule a meeting"""
    return activity_service.schedule_meeting(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.post("/create-task")
async def create_task(
    data: CreateTask,
    current_user: dict = Depends(get_current_user),
):
    """Create a task"""
    return activity_service.create_task(
        tenant_id=current_user.get("tenant_id"),
        owner_id=current_user["id"],
        **data.dict(exclude_none=True),
    )


# ============================================
# EMAIL TEMPLATES
# ============================================

@router.get("/templates")
async def list_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """List email templates"""
    return email_template_service.list_templates(
        tenant_id=current_user.get("tenant_id"),
        category=category,
        search=search,
        user_id=current_user["id"],
    )


@router.post("/templates")
async def create_template(
    data: EmailTemplateCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create email template"""
    return email_template_service.create_template(
        tenant_id=current_user.get("tenant_id"),
        created_by=current_user["id"],
        **data.dict(exclude_none=True),
    )


@router.get("/templates/merge-fields")
async def get_merge_fields():
    """Get available merge fields"""
    return email_template_service.get_merge_fields()


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get template by ID"""
    template = email_template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/templates/render")
async def render_template(
    data: RenderTemplate,
    current_user: dict = Depends(get_current_user),
):
    """Render template with context"""
    return email_template_service.render_template(
        template_id=data.template_id,
        context=data.context,
    )
