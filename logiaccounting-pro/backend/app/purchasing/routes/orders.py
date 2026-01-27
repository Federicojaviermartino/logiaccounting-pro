"""Purchase Order API Routes"""

from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.purchasing.orders import (
    PurchaseOrderService, get_purchase_order_service,
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderFilter,
    AddLineRequest, OrderLineUpdate, OrderApprovalAction, CancelOrderRequest,
)

router = APIRouter(prefix="/purchase-orders", tags=["Purchasing - Orders"])


@router.get("")
def list_orders(
    supplier_id: Optional[UUID] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    has_pending_receipt: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    filters = PurchaseOrderFilter(
        supplier_id=supplier_id, status=status,
        date_from=date_from, date_to=date_to,
        search=search, has_pending_receipt=has_pending_receipt
    )
    orders, total = service.get_orders(user.customer_id, filters, page, page_size)
    return {
        "orders": [o.to_dict() for o in orders],
        "total": total,
        "page": page,
    }


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    return service.get_dashboard_stats(user.customer_id)


@router.post("")
def create_order(
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    try:
        order = service.create_order(user.customer_id, data, user.id)
        return order.to_dict(include_lines=True)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{order_id}")
def get_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    order = service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order.to_dict(include_lines=True)


@router.put("/{order_id}")
def update_order(
    order_id: UUID,
    data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    try:
        order = service.update_order(order_id, data)
        return order.to_dict(include_lines=True)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{order_id}/lines")
def add_line(
    order_id: UUID,
    data: AddLineRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    try:
        line = service.add_line(order_id, data)
        return line.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/lines/{line_id}")
def update_line(
    line_id: UUID,
    data: OrderLineUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    try:
        line = service.update_line(line_id, data)
        return line.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/lines/{line_id}")
def delete_line(
    line_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    try:
        service.delete_line(line_id)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{order_id}/submit")
def submit_for_approval(
    order_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    try:
        order = service.submit_for_approval(order_id)
        return order.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{order_id}/approve")
def approve_order(
    order_id: UUID,
    data: OrderApprovalAction,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    try:
        order = service.approve_order(order_id, user.id, data.action, data.comments)
        return order.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{order_id}/send")
def send_order(
    order_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    try:
        order = service.send_order(order_id)
        return order.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: UUID,
    data: CancelOrderRequest,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_purchase_order_service(db)
    try:
        order = service.cancel_order(order_id, data.reason)
        return order.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))
