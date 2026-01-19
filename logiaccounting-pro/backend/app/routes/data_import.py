"""
Data Import Wizard routes
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.import_service import import_service
from app.utils.auth import require_roles

router = APIRouter()


class ParseRequest(BaseModel):
    content: str
    delimiter: str = ","


class CreateImportRequest(BaseModel):
    entity: str
    headers: List[str]
    rows: List[dict]
    mapping: Dict[str, str]


@router.get("/entities")
async def get_supported_entities():
    """Get supported entity types for import"""
    return {"entities": import_service.get_supported_entities()}


@router.get("/entities/{entity}/config")
async def get_entity_config(entity: str):
    """Get import configuration for an entity"""
    config = import_service.get_entity_config(entity)
    if not config:
        raise HTTPException(status_code=404, detail="Entity not supported")
    return config


@router.post("/parse")
async def parse_csv(
    request: ParseRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Parse CSV content"""
    try:
        headers, rows = import_service.parse_csv(request.content, request.delimiter)
        return {
            "headers": headers,
            "rows": rows[:100],  # Limit preview
            "total_rows": len(rows)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")


@router.post("/suggest-mapping")
async def suggest_mapping(
    entity: str,
    headers: List[str],
    current_user: dict = Depends(require_roles("admin"))
):
    """Get suggested column mappings"""
    return {"suggestions": import_service.suggest_mappings(headers, entity)}


@router.post("")
async def create_import(
    request: CreateImportRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create and validate an import job"""
    return import_service.create_import(
        entity=request.entity,
        headers=request.headers,
        rows=request.rows,
        mapping=request.mapping,
        created_by=current_user["id"]
    )


@router.get("")
async def list_imports(
    limit: int = 20,
    current_user: dict = Depends(require_roles("admin"))
):
    """List recent imports"""
    return {"imports": import_service.list_imports(limit)}


@router.get("/{import_id}")
async def get_import(
    import_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get import details"""
    import_job = import_service.get_import(import_id)
    if not import_job:
        raise HTTPException(status_code=404, detail="Import not found")
    return import_job


@router.post("/{import_id}/execute")
async def execute_import(
    import_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Execute the import"""
    result = import_service.execute_import(import_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{import_id}/rollback")
async def rollback_import(
    import_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Rollback a completed import"""
    result = import_service.rollback_import(import_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
