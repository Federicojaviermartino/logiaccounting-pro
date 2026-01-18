"""
Recurring Transactions routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.recurring_service import recurring_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class CreateTemplateRequest(BaseModel):
    name: str
    entity_type: str
    template_data: dict
    frequency: str
    start_date: str
    end_date: Optional[str] = None
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    auto_create: bool = False


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    template_data: Optional[dict] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    day_of_month: Optional[int] = None
    day_of_week: Optional[int] = None
    auto_create: Optional[bool] = None


@router.get("/frequencies")
async def get_frequencies():
    """Get available frequencies"""
    return {
        "frequencies": [
            {"value": "daily", "label": "Daily"},
            {"value": "weekly", "label": "Weekly"},
            {"value": "biweekly", "label": "Bi-weekly"},
            {"value": "monthly", "label": "Monthly"},
            {"value": "quarterly", "label": "Quarterly"},
            {"value": "yearly", "label": "Yearly"}
        ]
    }


@router.get("")
async def list_templates(
    active_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """List recurring templates"""
    return {"templates": recurring_service.list_templates(active_only=active_only)}


@router.post("")
async def create_template(
    request: CreateTemplateRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a recurring template"""
    if request.frequency not in recurring_service.FREQUENCIES:
        raise HTTPException(status_code=400, detail="Invalid frequency")

    return recurring_service.create_template(
        name=request.name,
        entity_type=request.entity_type,
        template_data=request.template_data,
        frequency=request.frequency,
        start_date=request.start_date,
        end_date=request.end_date,
        day_of_month=request.day_of_month,
        day_of_week=request.day_of_week,
        auto_create=request.auto_create,
        created_by=current_user["id"]
    )


@router.get("/due/list")
async def get_due(current_user: dict = Depends(require_roles("admin"))):
    """Get templates due for generation"""
    return {"templates": recurring_service.get_due_templates()}


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific template"""
    template = recurring_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a template"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    template = recurring_service.update_template(template_id, updates)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a template"""
    if recurring_service.delete_template(template_id):
        return {"message": "Template deleted"}
    raise HTTPException(status_code=404, detail="Template not found")


@router.post("/{template_id}/toggle")
async def toggle_template(
    template_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Toggle template active status"""
    template = recurring_service.toggle_active(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/{template_id}/generate")
async def generate_now(
    template_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Manually generate from template"""
    result = recurring_service.generate_from_template(template_id)
    if not result:
        raise HTTPException(status_code=400, detail="Failed to generate")
    return {"generated": result}


@router.get("/{template_id}/preview")
async def preview_occurrences(
    template_id: str,
    count: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """Preview next occurrences"""
    occurrences = recurring_service.preview_occurrences(template_id, count)
    return {"occurrences": occurrences}
