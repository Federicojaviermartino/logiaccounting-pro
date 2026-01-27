"""Supplier API Routes"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.purchasing.suppliers import (
    SupplierService, get_supplier_service,
    SupplierCreate, SupplierUpdate, SupplierFilter,
    ContactCreate, ContactUpdate,
    PriceListCreate, PriceListUpdate,
)

router = APIRouter(prefix="/suppliers", tags=["Purchasing - Suppliers"])


@router.get("")
def list_suppliers(
    search: Optional[str] = None,
    supplier_type: Optional[str] = None,
    category: Optional[str] = None,
    is_active: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    filters = SupplierFilter(
        search=search, supplier_type=supplier_type,
        category=category, is_active=is_active
    )
    suppliers, total = service.get_suppliers(user.customer_id, filters, page, page_size)
    return {
        "suppliers": [s.to_dict() for s in suppliers],
        "total": total,
        "page": page,
    }


@router.get("/summary")
def get_suppliers_summary(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    return {"suppliers": service.get_suppliers_summary(user.customer_id)}


@router.post("")
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    try:
        supplier = service.create_supplier(user.customer_id, data, user.id)
        return supplier.to_dict(include_contacts=True)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{supplier_id}")
def get_supplier(
    supplier_id: UUID,
    include_prices: bool = False,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    supplier = service.get_supplier_by_id(supplier_id)
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    return supplier.to_dict(include_contacts=True, include_prices=include_prices)


@router.put("/{supplier_id}")
def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    try:
        supplier = service.update_supplier(supplier_id, data)
        return supplier.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{supplier_id}/approve")
def approve_supplier(
    supplier_id: UUID,
    approve: bool = True,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    supplier = service.approve_supplier(supplier_id, user.id, approve)
    return supplier.to_dict()


# ============== Contacts ==============

@router.post("/{supplier_id}/contacts")
def add_contact(
    supplier_id: UUID,
    data: ContactCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    try:
        contact = service.add_contact(supplier_id, data)
        return contact.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/contacts/{contact_id}")
def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    try:
        contact = service.update_contact(contact_id, data)
        return contact.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    service.delete_contact(contact_id)
    return {"success": True}


# ============== Price Lists ==============

@router.get("/{supplier_id}/prices")
def get_supplier_prices(
    supplier_id: UUID,
    current_only: bool = True,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    prices = service.get_supplier_prices(supplier_id, current_only)
    return {"prices": [p.to_dict() for p in prices]}


@router.post("/{supplier_id}/prices")
def add_price(
    supplier_id: UUID,
    data: PriceListCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    service = get_supplier_service(db)
    try:
        price = service.add_price_list(supplier_id, data)
        return price.to_dict()
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/products/{product_id}/suppliers")
def get_product_suppliers(
    product_id: UUID,
    quantity: float = 1,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    from decimal import Decimal
    service = get_supplier_service(db)
    return {"suppliers": service.get_product_suppliers(
        user.customer_id, product_id, Decimal(str(quantity))
    )}
