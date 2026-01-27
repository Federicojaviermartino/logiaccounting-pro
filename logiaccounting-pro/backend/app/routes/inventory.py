"""
Inventory routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.models.store import db
from app.utils.auth import get_current_user, require_roles
from app.schemas.schemas import MaterialCreate, MaterialUpdate, CategoryCreate, LocationCreate

router = APIRouter()


@router.get("/materials")
async def get_materials(
    category_id: Optional[str] = None,
    location_id: Optional[str] = None,
    state: Optional[str] = None,
    low_stock: bool = False,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all materials with optional filters"""
    filters = {
        "category_id": category_id,
        "location_id": location_id,
        "state": state,
        "low_stock": low_stock if low_stock else None,
        "search": search
    }
    filters = {k: v for k, v in filters.items() if v}
    
    materials = db.materials.find_all(filters if filters else None)
    
    for m in materials:
        cat = db.categories.find_by_id(m.get("category_id"))
        loc = db.locations.find_by_id(m.get("location_id"))
        m["category_name"] = cat["name"] if cat else None
        m["location_name"] = loc["name"] if loc else None
        m["is_low_stock"] = m["quantity"] <= m.get("min_stock", 0)
    
    return {"materials": materials}


@router.get("/materials/{material_id}")
async def get_material(
    material_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific material"""
    material = db.materials.find_by_id(material_id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return material


@router.post("/materials", status_code=status.HTTP_201_CREATED)
async def create_material(
    request: MaterialCreate,
    current_user: dict = Depends(require_roles("admin", "supplier"))
):
    """Create a new material"""
    if db.materials.find_by_reference(request.reference):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reference already exists"
        )
    
    material = db.materials.create(request.model_dump())
    return material


@router.put("/materials/{material_id}")
async def update_material(
    material_id: str,
    request: MaterialUpdate,
    current_user: dict = Depends(require_roles("admin", "supplier"))
):
    """Update a material"""
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    updated = db.materials.update(material_id, update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return updated


@router.delete("/materials/{material_id}")
async def delete_material(
    material_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete a material (admin only)"""
    if not db.materials.delete(material_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return {"success": True}


@router.get("/categories")
async def get_categories(
    type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all categories"""
    if type:
        return [c for c in db.categories._data if c.get("type") == type]
    return db.categories._data


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    request: CategoryCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new category (admin only)"""
    return db.categories.create(request.model_dump())


@router.get("/locations")
async def get_locations(current_user: dict = Depends(get_current_user)):
    """Get all locations"""
    return db.locations._data


@router.post("/locations", status_code=status.HTTP_201_CREATED)
async def create_location(
    request: LocationCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new location (admin only)"""
    return db.locations.create(request.model_dump())
