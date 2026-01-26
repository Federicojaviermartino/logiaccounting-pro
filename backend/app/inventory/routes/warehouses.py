"""Warehouse API Routes"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.inventory.warehouses import (
    WarehouseService, get_warehouse_service,
    WarehouseCreate, WarehouseUpdate,
    ZoneCreate, LocationCreate, BulkLocationCreate
)

router = APIRouter(prefix="/warehouses", tags=["Inventory - Warehouses"])


@router.get("")
def list_warehouses(
    active_only: bool = True,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_warehouse_service(db)
    warehouses = service.get_warehouses(user.customer_id, active_only)
    return {"warehouses": [w.to_dict() for w in warehouses]}


@router.post("")
def create_warehouse(
    data: WarehouseCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_warehouse_service(db)
    try:
        warehouse = service.create_warehouse(user.customer_id, data, user.id)
        return warehouse.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{warehouse_id}")
def get_warehouse(
    warehouse_id: UUID,
    include_locations: bool = False,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_warehouse_service(db)
    warehouse = service.get_warehouse_by_id(warehouse_id)
    if not warehouse:
        raise HTTPException(404, "Warehouse not found")
    return warehouse.to_dict(include_locations=include_locations)


@router.get("/{warehouse_id}/locations")
def list_locations(
    warehouse_id: UUID,
    zone_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_warehouse_service(db)
    locations, total = service.get_locations(warehouse_id, zone_id, page=page, page_size=page_size)
    return {
        "locations": [l.to_dict() for l in locations],
        "total": total,
    }


@router.post("/{warehouse_id}/locations")
def create_location(
    warehouse_id: UUID,
    data: LocationCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_warehouse_service(db)
    try:
        location = service.create_location(warehouse_id, data)
        return location.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{warehouse_id}/locations/bulk")
def bulk_create_locations(
    warehouse_id: UUID,
    data: BulkLocationCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_warehouse_service(db)
    result = service.bulk_create_locations(warehouse_id, data)
    return result


@router.get("/{warehouse_id}/zones")
def list_zones(
    warehouse_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_warehouse_service(db)
    zones = service.get_zones(warehouse_id)
    return {"zones": [z.to_dict() for z in zones]}
