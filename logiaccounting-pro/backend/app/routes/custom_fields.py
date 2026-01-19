"""
Custom Fields routes
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.custom_fields_service import custom_fields_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class CreateFieldRequest(BaseModel):
    entity: str
    name: str
    label: str
    type: str
    required: bool = False
    default_value: Any = None
    options: List[str] = []
    validation: dict = {}
    placeholder: str = ""
    help_text: str = ""
    position: int = 0
    group: str = "Custom Fields"
    searchable: bool = False
    show_in_list: bool = False


class UpdateFieldRequest(BaseModel):
    label: Optional[str] = None
    required: Optional[bool] = None
    default_value: Optional[Any] = None
    options: Optional[List[str]] = None
    validation: Optional[dict] = None
    position: Optional[int] = None
    active: Optional[bool] = None


class SetValueRequest(BaseModel):
    value: Any


class SetBulkValuesRequest(BaseModel):
    values: Dict[str, Any]


@router.get("/types")
async def get_field_types():
    """Get available field types"""
    return {"types": custom_fields_service.FIELD_TYPES}


@router.get("/entities")
async def get_supported_entities():
    """Get entities that support custom fields"""
    return {"entities": custom_fields_service.SUPPORTED_ENTITIES}


@router.get("/entity/{entity}")
async def get_entity_fields(
    entity: str,
    active_only: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Get custom fields for an entity"""
    return {"fields": custom_fields_service.get_entity_fields(entity, active_only)}


@router.post("")
async def create_field(
    request: CreateFieldRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a custom field"""
    result = custom_fields_service.create_field(**request.model_dump())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{field_id}")
async def get_field(
    field_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a custom field"""
    field = custom_fields_service.get_field(field_id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.put("/{field_id}")
async def update_field(
    field_id: str,
    request: UpdateFieldRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update a custom field"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    field = custom_fields_service.update_field(field_id, updates)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.delete("/{field_id}")
async def delete_field(
    field_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a custom field"""
    if custom_fields_service.delete_field(field_id):
        return {"message": "Field deleted"}
    raise HTTPException(status_code=404, detail="Field not found")


@router.get("/values/{entity}/{entity_id}")
async def get_entity_values(
    entity: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get custom field values for an entity instance"""
    return {"values": custom_fields_service.get_entity_values(entity, entity_id)}


@router.put("/values/{entity}/{entity_id}/{field_id}")
async def set_value(
    entity: str,
    entity_id: str,
    field_id: str,
    request: SetValueRequest,
    current_user: dict = Depends(get_current_user)
):
    """Set a custom field value"""
    result = custom_fields_service.set_value(entity, entity_id, field_id, request.value)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.put("/values/{entity}/{entity_id}")
async def set_bulk_values(
    entity: str,
    entity_id: str,
    request: SetBulkValuesRequest,
    current_user: dict = Depends(get_current_user)
):
    """Set multiple custom field values"""
    return custom_fields_service.set_bulk_values(entity, entity_id, request.values)
