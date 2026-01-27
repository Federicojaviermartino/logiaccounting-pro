"""
Sales Order Routes
API endpoints for sales orders
"""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, get_customer_id
from app.sales.orders import (
    SalesOrderService,
    SalesOrderCreate,
    SalesOrderUpdate,
    SalesOrderResponse,
    SalesOrderFilter,
    SalesOrderSummary,
    OrderLineCreate,
    OrderLineUpdate,
    OrderLineResponse,
    OrderConfirmRequest,
    OrderHoldRequest,
    OrderCancelRequest,
    AllocationCreate,
    AllocationResponse,
    BulkLineUpdate,
    OrderDuplicateRequest,
    SOStatusEnum,
    PriorityEnum,
)

router = APIRouter(prefix="/orders", tags=["Sales Orders"])


def get_order_service(
    db: Session = Depends(get_db),
    customer_id: UUID = Depends(get_customer_id)
) -> SalesOrderService:
    return SalesOrderService(db, customer_id)


@router.post("", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: SalesOrderCreate,
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user)
):
    """Create a new sales order."""
    order = service.create_order(data, created_by=current_user.get("id"))
    return order.to_dict(include_lines=True)


@router.get("", response_model=dict)
async def list_orders(
    search: Optional[str] = None,
    customer_master_id: Optional[UUID] = None,
    status: Optional[SOStatusEnum] = None,
    priority: Optional[PriorityEnum] = None,
    warehouse_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    requested_date_from: Optional[date] = None,
    requested_date_to: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: SalesOrderService = Depends(get_order_service)
):
    """List sales orders with filters."""
    filters = SalesOrderFilter(
        search=search,
        customer_master_id=customer_master_id,
        status=status,
        priority=priority,
        warehouse_id=warehouse_id,
        date_from=date_from,
        date_to=date_to,
        requested_date_from=requested_date_from,
        requested_date_to=requested_date_to
    )
    orders, total = service.get_orders(filters, skip, limit)
    return {
        "items": [o.to_dict() for o in orders],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/stats", response_model=dict)
async def get_order_stats(
    service: SalesOrderService = Depends(get_order_service)
):
    """Get order statistics."""
    return service.get_order_stats()


@router.get("/pending", response_model=dict)
async def list_pending_orders(
    warehouse_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: SalesOrderService = Depends(get_order_service)
):
    """List orders pending fulfillment."""
    filters = SalesOrderFilter(
        statuses=[
            SOStatusEnum.CONFIRMED,
            SOStatusEnum.PROCESSING,
            SOStatusEnum.PARTIAL_SHIPPED
        ],
        warehouse_id=warehouse_id
    )
    orders, total = service.get_orders(filters, skip, limit)
    return {
        "items": [o.to_dict() for o in orders],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{order_id}", response_model=SalesOrderResponse)
async def get_order(
    order_id: UUID,
    service: SalesOrderService = Depends(get_order_service)
):
    """Get order by ID."""
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order.to_dict(include_lines=True)


@router.put("/{order_id}", response_model=SalesOrderResponse)
async def update_order(
    order_id: UUID,
    data: SalesOrderUpdate,
    service: SalesOrderService = Depends(get_order_service)
):
    """Update sales order."""
    order = service.update_order(order_id, data)
    return order.to_dict(include_lines=True)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: UUID,
    reason: Optional[str] = None,
    service: SalesOrderService = Depends(get_order_service)
):
    """Cancel sales order."""
    service.cancel_order(order_id, reason)
    return None


@router.post("/{order_id}/confirm", response_model=SalesOrderResponse)
async def confirm_order(
    order_id: UUID,
    data: OrderConfirmRequest = OrderConfirmRequest(),
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user)
):
    """Confirm sales order."""
    order = service.confirm_order(order_id, data, confirmed_by=current_user.get("id"))
    return order.to_dict(include_lines=True)


@router.post("/{order_id}/hold", response_model=SalesOrderResponse)
async def set_order_hold(
    order_id: UUID,
    data: OrderHoldRequest,
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user)
):
    """Set or release hold on order."""
    order = service.set_hold(order_id, data, user_id=current_user.get("id"))
    return order.to_dict(include_lines=True)


@router.post("/{order_id}/duplicate", response_model=SalesOrderResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_order(
    order_id: UUID,
    data: OrderDuplicateRequest = OrderDuplicateRequest(),
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user)
):
    """Duplicate an existing order."""
    order = service.duplicate_order(order_id, data, created_by=current_user.get("id"))
    return order.to_dict(include_lines=True)


@router.post("/{order_id}/lines", response_model=OrderLineResponse, status_code=status.HTTP_201_CREATED)
async def add_order_line(
    order_id: UUID,
    data: OrderLineCreate,
    service: SalesOrderService = Depends(get_order_service)
):
    """Add line to order."""
    line = service.add_line(order_id, data)
    return line.to_dict()


@router.put("/{order_id}/lines/{line_id}", response_model=OrderLineResponse)
async def update_order_line(
    order_id: UUID,
    line_id: UUID,
    data: OrderLineUpdate,
    service: SalesOrderService = Depends(get_order_service)
):
    """Update order line."""
    line = service.update_line(order_id, line_id, data)
    return line.to_dict()


@router.delete("/{order_id}/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order_line(
    order_id: UUID,
    line_id: UUID,
    service: SalesOrderService = Depends(get_order_service)
):
    """Delete order line."""
    service.delete_line(order_id, line_id)
    return None


@router.put("/{order_id}/lines/bulk", response_model=List[OrderLineResponse])
async def bulk_update_lines(
    order_id: UUID,
    data: BulkLineUpdate,
    service: SalesOrderService = Depends(get_order_service)
):
    """Bulk update order lines."""
    lines = service.bulk_update_lines(order_id, data)
    return [l.to_dict() for l in lines]


@router.get("/{order_id}/allocations", response_model=List[AllocationResponse])
async def get_allocations(
    order_id: UUID,
    service: SalesOrderService = Depends(get_order_service)
):
    """Get stock allocations for order."""
    allocations = service.get_allocations(order_id)
    return [a.to_dict() for a in allocations]


@router.post("/{order_id}/allocations", response_model=AllocationResponse, status_code=status.HTTP_201_CREATED)
async def allocate_stock(
    order_id: UUID,
    data: AllocationCreate,
    service: SalesOrderService = Depends(get_order_service),
    current_user: dict = Depends(get_current_user)
):
    """Allocate stock for order."""
    allocation = service.allocate_stock(order_id, data, allocated_by=current_user.get("id"))
    return allocation.to_dict()


@router.delete("/{order_id}/allocations/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deallocate_stock(
    order_id: UUID,
    allocation_id: UUID,
    service: SalesOrderService = Depends(get_order_service)
):
    """Remove stock allocation."""
    service.deallocate_stock(order_id, allocation_id)
    return None
