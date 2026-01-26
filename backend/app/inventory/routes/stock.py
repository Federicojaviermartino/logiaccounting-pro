"""Stock API Routes"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.inventory.stock import get_stock_service, StockFilter

router = APIRouter(prefix="/stock", tags=["Inventory - Stock"])


@router.get("")
def list_stock_levels(
    product_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    has_stock_only: bool = True,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_stock_service(db)
    filters = StockFilter(
        product_id=product_id, warehouse_id=warehouse_id,
        has_stock_only=has_stock_only, search=search
    )
    stocks, total = service.get_stock_levels(user.customer_id, filters, page, page_size)
    return {
        "stock_levels": [s.to_dict() for s in stocks],
        "total": total,
    }


@router.get("/low")
def get_low_stock(
    warehouse_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_stock_service(db)
    return {"products": service.get_low_stock_products(user.customer_id, warehouse_id)}


@router.get("/valuation")
def get_valuation_report(
    warehouse_id: Optional[UUID] = None,
    category_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    from app.inventory.stock.valuation import get_valuation_service
    service = get_valuation_service(db)
    return service.get_inventory_valuation_report(user.customer_id, warehouse_id, category_id)
