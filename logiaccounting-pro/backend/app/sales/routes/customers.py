"""
Customer Routes
API endpoints for customer management
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, get_customer_id
from app.sales.customers import (
    CustomerService,
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerFilter,
    CustomerSummary,
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ShippingAddressCreate,
    ShippingAddressUpdate,
    ShippingAddressResponse,
    PriceListCreate,
    PriceListUpdate,
    PriceListResponse,
    CreditHoldRequest,
    CreditLimitUpdate,
)

router = APIRouter(prefix="/customers", tags=["Customers"])


def get_customer_service(
    db: Session = Depends(get_db),
    customer_id: UUID = Depends(get_customer_id)
) -> CustomerService:
    return CustomerService(db, customer_id)


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user)
):
    """Create a new customer."""
    customer = service.create_customer(data, created_by=current_user.get("id"))
    return customer.to_dict(include_contacts=True, include_addresses=True)


@router.get("", response_model=dict)
async def list_customers(
    search: Optional[str] = None,
    customer_type: Optional[str] = None,
    segment: Optional[str] = None,
    category: Optional[str] = None,
    sales_rep_id: Optional[UUID] = None,
    is_active: Optional[bool] = True,
    credit_hold: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: CustomerService = Depends(get_customer_service)
):
    """List customers with filters."""
    filters = CustomerFilter(
        search=search,
        customer_type=customer_type,
        segment=segment,
        category=category,
        sales_rep_id=sales_rep_id,
        is_active=is_active,
        credit_hold=credit_hold
    )
    customers, total = service.get_customers(filters, skip, limit)
    return {
        "items": [c.to_dict() for c in customers],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/summary", response_model=List[CustomerSummary])
async def list_customers_summary(
    is_active: bool = True,
    service: CustomerService = Depends(get_customer_service)
):
    """List customers summary for dropdowns."""
    filters = CustomerFilter(is_active=is_active)
    customers, _ = service.get_customers(filters, 0, 1000)
    return [
        CustomerSummary(
            id=c.id,
            customer_code=c.customer_code,
            name=c.name,
            currency=c.currency,
            payment_term_id=c.payment_term_id,
            credit_hold=c.credit_hold
        )
        for c in customers
    ]


@router.get("/{customer_master_id}", response_model=CustomerResponse)
async def get_customer(
    customer_master_id: UUID,
    service: CustomerService = Depends(get_customer_service)
):
    """Get customer by ID."""
    customer = service.get_customer(customer_master_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return customer.to_dict(include_contacts=True, include_addresses=True)


@router.put("/{customer_master_id}", response_model=CustomerResponse)
async def update_customer(
    customer_master_id: UUID,
    data: CustomerUpdate,
    service: CustomerService = Depends(get_customer_service)
):
    """Update customer."""
    customer = service.update_customer(customer_master_id, data)
    return customer.to_dict(include_contacts=True, include_addresses=True)


@router.delete("/{customer_master_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_customer(
    customer_master_id: UUID,
    service: CustomerService = Depends(get_customer_service)
):
    """Deactivate customer."""
    service.update_customer(customer_master_id, CustomerUpdate(is_active=False))
    return None


@router.post("/{customer_master_id}/credit-hold", response_model=CustomerResponse)
async def set_credit_hold(
    customer_master_id: UUID,
    data: CreditHoldRequest,
    service: CustomerService = Depends(get_customer_service)
):
    """Set or release credit hold."""
    customer = service.set_credit_hold(customer_master_id, data.hold, data.reason)
    return customer.to_dict()


@router.put("/{customer_master_id}/credit-limit", response_model=CustomerResponse)
async def update_credit_limit(
    customer_master_id: UUID,
    data: CreditLimitUpdate,
    service: CustomerService = Depends(get_customer_service)
):
    """Update credit limit."""
    customer = service.update_customer(
        customer_master_id,
        CustomerUpdate(credit_limit=data.credit_limit)
    )
    return customer.to_dict()


@router.post("/{customer_master_id}/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def add_contact(
    customer_master_id: UUID,
    data: ContactCreate,
    service: CustomerService = Depends(get_customer_service)
):
    """Add contact to customer."""
    contact = service.add_contact(customer_master_id, data)
    return contact.to_dict()


@router.put("/{customer_master_id}/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    customer_master_id: UUID,
    contact_id: UUID,
    data: ContactUpdate,
    service: CustomerService = Depends(get_customer_service)
):
    """Update customer contact."""
    contact = service.update_contact(customer_master_id, contact_id, data)
    return contact.to_dict()


@router.delete("/{customer_master_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    customer_master_id: UUID,
    contact_id: UUID,
    service: CustomerService = Depends(get_customer_service)
):
    """Delete customer contact."""
    service.delete_contact(customer_master_id, contact_id)
    return None


@router.post("/{customer_master_id}/addresses", response_model=ShippingAddressResponse, status_code=status.HTTP_201_CREATED)
async def add_shipping_address(
    customer_master_id: UUID,
    data: ShippingAddressCreate,
    service: CustomerService = Depends(get_customer_service)
):
    """Add shipping address to customer."""
    address = service.add_shipping_address(customer_master_id, data)
    return address.to_dict()


@router.put("/{customer_master_id}/addresses/{address_id}", response_model=ShippingAddressResponse)
async def update_shipping_address(
    customer_master_id: UUID,
    address_id: UUID,
    data: ShippingAddressUpdate,
    service: CustomerService = Depends(get_customer_service)
):
    """Update shipping address."""
    address = service.update_shipping_address(customer_master_id, address_id, data)
    return address.to_dict()


@router.delete("/{customer_master_id}/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipping_address(
    customer_master_id: UUID,
    address_id: UUID,
    service: CustomerService = Depends(get_customer_service)
):
    """Delete shipping address."""
    service.delete_shipping_address(customer_master_id, address_id)
    return None


@router.get("/{customer_master_id}/price-list", response_model=List[PriceListResponse])
async def get_price_list(
    customer_master_id: UUID,
    product_id: Optional[UUID] = None,
    current_only: bool = True,
    service: CustomerService = Depends(get_customer_service)
):
    """Get customer price list."""
    prices = service.get_price_list(customer_master_id, product_id, current_only)
    return [p.to_dict() for p in prices]


@router.post("/{customer_master_id}/price-list", response_model=PriceListResponse, status_code=status.HTTP_201_CREATED)
async def add_price_list_item(
    customer_master_id: UUID,
    data: PriceListCreate,
    service: CustomerService = Depends(get_customer_service)
):
    """Add item to customer price list."""
    price = service.add_price_list_item(customer_master_id, data)
    return price.to_dict()


@router.put("/{customer_master_id}/price-list/{price_id}", response_model=PriceListResponse)
async def update_price_list_item(
    customer_master_id: UUID,
    price_id: UUID,
    data: PriceListUpdate,
    service: CustomerService = Depends(get_customer_service)
):
    """Update price list item."""
    price = service.update_price_list_item(customer_master_id, price_id, data)
    return price.to_dict()


@router.delete("/{customer_master_id}/price-list/{price_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price_list_item(
    customer_master_id: UUID,
    price_id: UUID,
    service: CustomerService = Depends(get_customer_service)
):
    """Delete price list item."""
    service.delete_price_list_item(customer_master_id, price_id)
    return None
