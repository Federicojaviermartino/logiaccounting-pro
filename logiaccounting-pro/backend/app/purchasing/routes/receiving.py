"""Goods Receipt API Routes"""

from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.purchasing.receiving.service import (
    GoodsReceiptService, get_goods_receipt_service
)

router = APIRouter(prefix="/goods-receipts", tags=["Purchasing - Receiving"])


class ReceiptLineInput(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    location_id: Optional[UUID] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[date] = None
    serial_numbers: Optional[List[str]] = None


class CreateReceiptFromPO(BaseModel):
    purchase_order_id: UUID
    warehouse_id: UUID
    receipt_date: Optional[date] = None
    supplier_delivery_note: Optional[str] = None


class CreateDirectReceipt(BaseModel):
    supplier_id: UUID
    warehouse_id: UUID
    lines: List[ReceiptLineInput]
    receipt_date: Optional[date] = None
    supplier_delivery_note: Optional[str] = None


class UpdateReceiptLine(BaseModel):
    quantity_received: Optional[Decimal] = None
    location_id: Optional[UUID] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[date] = None
    serial_numbers: Optional[List[str]] = None
    quality_status: Optional[str] = None
    rejection_reason: Optional[str] = None


@router.get("")
def list_receipts(
    supplier_id: Optional[UUID] = None,
    purchase_order_id: Optional[UUID] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_goods_receipt_service(db)
    receipts, total = service.get_receipts(
        user.customer_id, supplier_id, purchase_order_id, status, page, page_size
    )
    return {
        "receipts": [r.to_dict() for r in receipts],
        "total": total,
    }


@router.post("/from-po")
def create_from_po(
    data: CreateReceiptFromPO,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_goods_receipt_service(db)
    try:
        receipt = service.create_receipt_from_po(
            user.customer_id,
            data.purchase_order_id,
            data.warehouse_id,
            data.receipt_date,
            data.supplier_delivery_note,
            user.id,
        )
        return receipt.to_dict(include_lines=True)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/direct")
def create_direct(
    data: CreateDirectReceipt,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_goods_receipt_service(db)
    try:
        lines = [l.dict() for l in data.lines]
        receipt = service.create_receipt_direct(
            user.customer_id,
            data.supplier_id,
            data.warehouse_id,
            lines,
            data.receipt_date,
            data.supplier_delivery_note,
            user.id,
        )
        return receipt.to_dict(include_lines=True)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{receipt_id}")
def get_receipt(
    receipt_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_goods_receipt_service(db)
    receipt = service.get_receipt_by_id(receipt_id)
    if not receipt:
        raise HTTPException(404, "Receipt not found")
    return receipt.to_dict(include_lines=True)


@router.put("/lines/{line_id}")
def update_line(
    line_id: UUID,
    data: UpdateReceiptLine,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_goods_receipt_service(db)
    try:
        line = service.update_receipt_line(
            line_id, **data.dict(exclude_unset=True)
        )
        return line.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{receipt_id}/post")
def post_receipt(
    receipt_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_goods_receipt_service(db)
    try:
        receipt = service.post_receipt(receipt_id, user.id)
        return receipt.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{receipt_id}/cancel")
def cancel_receipt(
    receipt_id: UUID,
    reason: str = Query(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_goods_receipt_service(db)
    try:
        receipt = service.cancel_receipt(receipt_id, reason)
        return receipt.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))
