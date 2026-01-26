"""Product API Routes"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.inventory.products import (
    ProductService, get_product_service,
    ProductCreate, ProductUpdate, ProductFilter, ProductResponse
)

router = APIRouter(prefix="/products", tags=["Inventory - Products"])


@router.get("")
def list_products(
    search: Optional[str] = None,
    category_id: Optional[UUID] = None,
    is_active: Optional[bool] = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_product_service(db)
    filters = ProductFilter(search=search, category_id=category_id, is_active=is_active)
    products, total = service.get_products(user.customer_id, filters, page, page_size)
    return {
        "products": [p.to_dict() for p in products],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("")
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_product_service(db)
    try:
        product = service.create_product(user.customer_id, data, user.id)
        return product.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{product_id}")
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_product_service(db)
    product = service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product.to_dict()


@router.put("/{product_id}")
def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_product_service(db)
    try:
        product = service.update_product(product_id, data)
        return product.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{product_id}")
def deactivate_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_product_service(db)
    try:
        service.deactivate_product(product_id)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{product_id}/stock")
def get_product_stock(
    product_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    from app.inventory.stock.service import get_stock_service
    service = get_stock_service(db)
    return service.get_product_stock_summary(user.customer_id, product_id)
