"""
Stock movements routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.models.store import db
from app.utils.auth import get_current_user, require_roles
from app.schemas.schemas import MovementCreate

router = APIRouter()


@router.get("")
async def get_movements(
    type: Optional[str] = None,
    material_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get all stock movements"""
    filters = {k: v for k, v in {"type": type, "material_id": material_id, "project_id": project_id}.items() if v}
    
    movements = db.movements.find_all(filters if filters else None)
    movements = sorted(movements, key=lambda x: x["created_at"], reverse=True)
    
    for m in movements:
        material = db.materials.find_by_id(m["material_id"])
        project = db.projects.find_by_id(m.get("project_id"))
        m["material_name"] = material["name"] if material else "Unknown"
        m["material_reference"] = material.get("reference", "N/A") if material else "N/A"
        m["project_code"] = project["code"] if project else None
    
    return {"movements": movements[:limit]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_movement(
    request: MovementCreate,
    current_user: dict = Depends(require_roles("admin", "supplier"))
):
    """Create a new stock movement"""
    material = db.materials.find_by_id(request.material_id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    
    if request.type == "exit" and material["quantity"] < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Available: {material['quantity']}"
        )
    
    movement = db.movements.create({
        **request.model_dump(),
        "created_by": current_user["id"]
    })
    
    delta = request.quantity if request.type == "entry" else -request.quantity
    db.materials.update_quantity(request.material_id, delta)
    
    return movement


@router.delete("/{movement_id}")
async def delete_movement(
    movement_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a movement and reverse stock change (admin only)"""
    movement = db.movements.find_by_id(movement_id)
    if not movement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movement not found")
    
    delta = -movement["quantity"] if movement["type"] == "entry" else movement["quantity"]
    db.materials.update_quantity(movement["material_id"], delta)
    db.movements.delete(movement_id)
    
    return {"success": True}
