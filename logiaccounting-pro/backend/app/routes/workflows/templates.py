"""
Workflow Template Marketplace API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.workflows.services.template_service import template_service
from app.workflows.services.ai_suggestion_service import ai_suggestion_service


router = APIRouter()


@router.get("")
async def list_templates(category: Optional[str] = None, search: Optional[str] = None, tags: Optional[str] = None, is_official: Optional[bool] = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50), current_user: dict = Depends(get_current_user)):
    tag_list = tags.split(",") if tags else None
    return template_service.list_templates(category=category, search=search, tags=tag_list, is_official=is_official, tenant_id=current_user.get("tenant_id"), page=page, page_size=page_size)


@router.get("/categories")
async def get_categories(current_user: dict = Depends(get_current_user)):
    return template_service.get_categories()


@router.get("/{template_id}")
async def get_template(template_id: str, current_user: dict = Depends(get_current_user)):
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template_service._template_to_dict(template)


@router.get("/{template_id}/preview")
async def preview_template(template_id: str, current_user: dict = Depends(get_current_user)):
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"id": template.id, "name": template.name, "definition": template.definition, "parameters": template.parameters}


class InstallRequest(BaseModel):
    parameters: Optional[dict] = None

@router.post("/{template_id}/install")
async def install_template(template_id: str, data: InstallRequest, current_user: dict = Depends(get_current_user)):
    return template_service.install_template(template_id=template_id, tenant_id=current_user.get("tenant_id"), user_id=current_user["id"], parameters=data.parameters)


class PublishRequest(BaseModel):
    workflow_id: str
    name: str
    description: str
    category: str
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = True

@router.post("/publish")
async def publish_template(data: PublishRequest, current_user: dict = Depends(get_current_user)):
    template = template_service.publish_template(workflow_id=data.workflow_id, tenant_id=current_user.get("tenant_id"), user_id=current_user["id"], name=data.name, description=data.description, category=data.category, tags=data.tags, is_public=data.is_public)
    return template_service._template_to_dict(template)


class RateRequest(BaseModel):
    rating: int

@router.post("/{template_id}/rate")
async def rate_template(template_id: str, data: RateRequest, current_user: dict = Depends(get_current_user)):
    template = template_service.rate_template(template_id=template_id, user_id=current_user["id"], rating=data.rating)
    return {"rating": template.rating, "rating_count": template.rating_count}


# AI Suggestions
@router.get("/suggestions")
async def get_suggestions(current_user: dict = Depends(get_current_user)):
    suggestions = await ai_suggestion_service.get_suggestions(tenant_id=current_user.get("tenant_id"), context={"user_role": current_user.get("role")})
    return {"suggestions": [{"name": s.name, "description": s.description, "trigger": s.trigger, "actions": s.actions, "confidence": s.confidence, "reasoning": s.reasoning} for s in suggestions]}


class NLRequest(BaseModel):
    description: str

@router.post("/from-description")
async def from_description(data: NLRequest, current_user: dict = Depends(get_current_user)):
    return await ai_suggestion_service.natural_language_to_workflow(description=data.description, tenant_id=current_user.get("tenant_id"))


class ExplainRequest(BaseModel):
    workflow: dict

@router.post("/explain")
async def explain_workflow(data: ExplainRequest, current_user: dict = Depends(get_current_user)):
    explanation = await ai_suggestion_service.explain_workflow(data.workflow)
    return {"explanation": explanation}
