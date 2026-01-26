"""
Fulfillment Routes
API endpoints for pick lists and shipments
"""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, get_customer_id
from app.sales.fulfillment import (
    PickListService,
    ShipmentService,
    PickListCreate,
    PickListUpdate,
    PickListResponse,
    PickListFilter,
    PickLineCreate,
    PickLineUpdate,
    PickLineResponse,
    PickConfirmRequest,
    GeneratePickListRequest,
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentResponse,
    ShipmentFilter,
    ShipmentLineCreate,
    ShipmentLineResponse,
    ShipConfirmRequest,
    DeliveryConfirmRequest,
    CreateShipmentFromPickRequest,
    PickListStatusEnum,
    ShipmentStatusEnum,
)

router = APIRouter(tags=["Fulfillment"])


def get_pick_list_service(
    db: Session = Depends(get_db),
    customer_id: UUID = Depends(get_customer_id)
) -> PickListService:
    return PickListService(db, customer_id)


def get_shipment_service(
    db: Session = Depends(get_db),
    customer_id: UUID = Depends(get_customer_id)
) -> ShipmentService:
    return ShipmentService(db, customer_id)


# Pick List Routes

@router.post("/pick-lists", response_model=PickListResponse, status_code=status.HTTP_201_CREATED)
async def create_pick_list(
    data: PickListCreate,
    service: PickListService = Depends(get_pick_list_service),
    current_user: dict = Depends(get_current_user)
):
    """Create a new pick list."""
    pick_list = service.create_pick_list(data, created_by=current_user.get("id"))
    return pick_list.to_dict(include_lines=True)


@router.post("/pick-lists/generate", response_model=PickListResponse, status_code=status.HTTP_201_CREATED)
async def generate_pick_list(
    data: GeneratePickListRequest,
    service: PickListService = Depends(get_pick_list_service),
    current_user: dict = Depends(get_current_user)
):
    """Generate pick list from orders."""
    pick_list = service.generate_from_orders(data, created_by=current_user.get("id"))
    return pick_list.to_dict(include_lines=True)


@router.get("/pick-lists", response_model=dict)
async def list_pick_lists(
    warehouse_id: Optional[UUID] = None,
    status: Optional[PickListStatusEnum] = None,
    assigned_to: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    due_date_from: Optional[date] = None,
    due_date_to: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: PickListService = Depends(get_pick_list_service)
):
    """List pick lists with filters."""
    filters = PickListFilter(
        warehouse_id=warehouse_id,
        status=status,
        assigned_to=assigned_to,
        date_from=date_from,
        date_to=date_to,
        due_date_from=due_date_from,
        due_date_to=due_date_to
    )
    pick_lists, total = service.get_pick_lists(filters, skip, limit)
    return {
        "items": [p.to_dict() for p in pick_lists],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/pick-lists/active", response_model=dict)
async def list_active_pick_lists(
    warehouse_id: Optional[UUID] = None,
    assigned_to: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: PickListService = Depends(get_pick_list_service)
):
    """List active pick lists."""
    filters = PickListFilter(
        warehouse_id=warehouse_id,
        assigned_to=assigned_to,
        statuses=[PickListStatusEnum.RELEASED, PickListStatusEnum.IN_PROGRESS]
    )
    pick_lists, total = service.get_pick_lists(filters, skip, limit)
    return {
        "items": [p.to_dict(include_lines=True) for p in pick_lists],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/pick-lists/{pick_list_id}", response_model=PickListResponse)
async def get_pick_list(
    pick_list_id: UUID,
    service: PickListService = Depends(get_pick_list_service)
):
    """Get pick list by ID."""
    pick_list = service.get_pick_list(pick_list_id)
    if not pick_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pick list not found"
        )
    return pick_list.to_dict(include_lines=True)


@router.put("/pick-lists/{pick_list_id}", response_model=PickListResponse)
async def update_pick_list(
    pick_list_id: UUID,
    data: PickListUpdate,
    service: PickListService = Depends(get_pick_list_service)
):
    """Update pick list."""
    pick_list = service.update_pick_list(pick_list_id, data)
    return pick_list.to_dict(include_lines=True)


@router.post("/pick-lists/{pick_list_id}/release", response_model=PickListResponse)
async def release_pick_list(
    pick_list_id: UUID,
    service: PickListService = Depends(get_pick_list_service)
):
    """Release pick list for picking."""
    pick_list = service.release_pick_list(pick_list_id)
    return pick_list.to_dict(include_lines=True)


@router.post("/pick-lists/{pick_list_id}/start", response_model=PickListResponse)
async def start_picking(
    pick_list_id: UUID,
    service: PickListService = Depends(get_pick_list_service),
    current_user: dict = Depends(get_current_user)
):
    """Start picking process."""
    pick_list = service.start_picking(pick_list_id, user_id=current_user.get("id"))
    return pick_list.to_dict(include_lines=True)


@router.post("/pick-lists/{pick_list_id}/confirm", response_model=PickListResponse)
async def confirm_picks(
    pick_list_id: UUID,
    data: PickConfirmRequest,
    service: PickListService = Depends(get_pick_list_service),
    current_user: dict = Depends(get_current_user)
):
    """Confirm picked quantities."""
    pick_list = service.confirm_picks(pick_list_id, data, picked_by=current_user.get("id"))
    return pick_list.to_dict(include_lines=True)


@router.post("/pick-lists/{pick_list_id}/complete", response_model=PickListResponse)
async def complete_pick_list(
    pick_list_id: UUID,
    service: PickListService = Depends(get_pick_list_service)
):
    """Complete pick list."""
    pick_list = service.complete_pick_list(pick_list_id)
    return pick_list.to_dict(include_lines=True)


@router.post("/pick-lists/{pick_list_id}/cancel", response_model=PickListResponse)
async def cancel_pick_list(
    pick_list_id: UUID,
    reason: Optional[str] = None,
    service: PickListService = Depends(get_pick_list_service)
):
    """Cancel pick list."""
    pick_list = service.cancel_pick_list(pick_list_id, reason)
    return pick_list.to_dict(include_lines=True)


# Shipment Routes

@router.post("/shipments", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    data: ShipmentCreate,
    service: ShipmentService = Depends(get_shipment_service),
    current_user: dict = Depends(get_current_user)
):
    """Create a new shipment."""
    shipment = service.create_shipment(data, created_by=current_user.get("id"))
    return shipment.to_dict(include_lines=True)


@router.post("/shipments/from-pick-list", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment_from_pick_list(
    data: CreateShipmentFromPickRequest,
    service: ShipmentService = Depends(get_shipment_service),
    current_user: dict = Depends(get_current_user)
):
    """Create shipment from completed pick list."""
    shipment = service.create_from_pick_list(data, created_by=current_user.get("id"))
    return shipment.to_dict(include_lines=True)


@router.get("/shipments", response_model=dict)
async def list_shipments(
    warehouse_id: Optional[UUID] = None,
    status: Optional[ShipmentStatusEnum] = None,
    carrier: Optional[str] = None,
    tracking_number: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    order_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ShipmentService = Depends(get_shipment_service)
):
    """List shipments with filters."""
    filters = ShipmentFilter(
        warehouse_id=warehouse_id,
        status=status,
        carrier=carrier,
        tracking_number=tracking_number,
        date_from=date_from,
        date_to=date_to,
        order_id=order_id
    )
    shipments, total = service.get_shipments(filters, skip, limit)
    return {
        "items": [s.to_dict() for s in shipments],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/shipments/pending", response_model=dict)
async def list_pending_shipments(
    warehouse_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ShipmentService = Depends(get_shipment_service)
):
    """List pending shipments."""
    filters = ShipmentFilter(
        warehouse_id=warehouse_id,
        statuses=[ShipmentStatusEnum.DRAFT, ShipmentStatusEnum.PACKED]
    )
    shipments, total = service.get_shipments(filters, skip, limit)
    return {
        "items": [s.to_dict(include_lines=True) for s in shipments],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/shipments/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(
    shipment_id: UUID,
    service: ShipmentService = Depends(get_shipment_service)
):
    """Get shipment by ID."""
    shipment = service.get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    return shipment.to_dict(include_lines=True)


@router.put("/shipments/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(
    shipment_id: UUID,
    data: ShipmentUpdate,
    service: ShipmentService = Depends(get_shipment_service)
):
    """Update shipment."""
    shipment = service.update_shipment(shipment_id, data)
    return shipment.to_dict(include_lines=True)


@router.post("/shipments/{shipment_id}/pack", response_model=ShipmentResponse)
async def pack_shipment(
    shipment_id: UUID,
    service: ShipmentService = Depends(get_shipment_service)
):
    """Mark shipment as packed."""
    shipment = service.pack_shipment(shipment_id)
    return shipment.to_dict(include_lines=True)


@router.post("/shipments/{shipment_id}/ship", response_model=ShipmentResponse)
async def ship(
    shipment_id: UUID,
    data: ShipConfirmRequest = ShipConfirmRequest(),
    service: ShipmentService = Depends(get_shipment_service),
    current_user: dict = Depends(get_current_user)
):
    """Confirm shipment shipped."""
    shipment = service.ship(shipment_id, data, shipped_by=current_user.get("id"))
    return shipment.to_dict(include_lines=True)


@router.post("/shipments/{shipment_id}/deliver", response_model=ShipmentResponse)
async def confirm_delivery(
    shipment_id: UUID,
    data: DeliveryConfirmRequest,
    service: ShipmentService = Depends(get_shipment_service)
):
    """Confirm shipment delivered."""
    shipment = service.confirm_delivery(shipment_id, data)
    return shipment.to_dict(include_lines=True)


@router.post("/shipments/{shipment_id}/cancel", response_model=ShipmentResponse)
async def cancel_shipment(
    shipment_id: UUID,
    reason: Optional[str] = None,
    service: ShipmentService = Depends(get_shipment_service)
):
    """Cancel shipment."""
    shipment = service.cancel_shipment(shipment_id, reason)
    return shipment.to_dict(include_lines=True)
