"""
Customer Service
Business logic for customer management
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session, joinedload

from app.sales.customers.models import (
    CustomerMaster, CustomerContact, CustomerShippingAddress, CustomerPriceList
)
from app.sales.customers.schemas import (
    CustomerCreate, CustomerUpdate, CustomerFilter,
    ContactCreate, ContactUpdate,
    ShippingAddressCreate, ShippingAddressUpdate,
    PriceListCreate, PriceListUpdate,
)

logger = logging.getLogger(__name__)


class CustomerService:
    """Service for customer management."""

    def __init__(self, db: Session):
        self.db = db

    def create_customer(
        self,
        customer_id: UUID,
        data: CustomerCreate,
        created_by: UUID = None,
    ) -> CustomerMaster:
        """Create a new customer."""
        existing = self.db.query(CustomerMaster).filter(
            CustomerMaster.customer_id == customer_id,
            CustomerMaster.customer_code == data.customer_code,
        ).first()

        if existing:
            raise ValueError(f"Customer code {data.customer_code} already exists")

        customer = CustomerMaster(
            customer_id=customer_id,
            customer_code=data.customer_code,
            name=data.name,
            legal_name=data.legal_name,
            tax_id=data.tax_id,
            customer_type=data.customer_type.value if data.customer_type else "business",
            category=data.category,
            segment=data.segment.value if data.segment else None,
            email=data.email,
            phone=data.phone,
            website=data.website,
            shipping_same_as_billing=data.shipping_same_as_billing,
            payment_term_id=data.payment_term_id,
            currency=data.currency,
            credit_limit=data.credit_limit,
            default_warehouse_id=data.default_warehouse_id,
            default_shipping_method=data.default_shipping_method,
            receivable_account_id=data.receivable_account_id,
            revenue_account_id=data.revenue_account_id,
            tax_exempt=data.tax_exempt,
            tax_exempt_number=data.tax_exempt_number,
            tax_exempt_expiry=data.tax_exempt_expiry,
            sales_rep_id=data.sales_rep_id,
            notes=data.notes,
            created_by=created_by,
        )

        if data.billing_address:
            customer.billing_address_line1 = data.billing_address.line1
            customer.billing_address_line2 = data.billing_address.line2
            customer.billing_city = data.billing_address.city
            customer.billing_state = data.billing_address.state
            customer.billing_postal_code = data.billing_address.postal_code
            customer.billing_country = data.billing_address.country

        self.db.add(customer)
        self.db.flush()

        if data.contacts:
            for contact_data in data.contacts:
                contact = CustomerContact(
                    customer_master_id=customer.id,
                    name=contact_data.name,
                    title=contact_data.title,
                    department=contact_data.department,
                    email=contact_data.email,
                    phone=contact_data.phone,
                    mobile=contact_data.mobile,
                    is_primary=contact_data.is_primary,
                    is_billing=contact_data.is_billing,
                    is_shipping=contact_data.is_shipping,
                    is_purchasing=contact_data.is_purchasing,
                    notes=contact_data.notes,
                )
                self.db.add(contact)

        if data.shipping_addresses:
            for addr_data in data.shipping_addresses:
                addr = CustomerShippingAddress(
                    customer_master_id=customer.id,
                    name=addr_data.name,
                    address_line1=addr_data.address_line1,
                    address_line2=addr_data.address_line2,
                    city=addr_data.city,
                    state=addr_data.state,
                    postal_code=addr_data.postal_code,
                    country=addr_data.country,
                    contact_name=addr_data.contact_name,
                    contact_phone=addr_data.contact_phone,
                    contact_email=addr_data.contact_email,
                    delivery_instructions=addr_data.delivery_instructions,
                    is_default=addr_data.is_default,
                )
                self.db.add(addr)

        self.db.commit()
        self.db.refresh(customer)

        logger.info(f"Created customer: {customer.customer_code}")
        return customer

    def update_customer(
        self,
        customer_master_id: UUID,
        data: CustomerUpdate,
    ) -> CustomerMaster:
        """Update customer."""
        customer = self.db.query(CustomerMaster).get(customer_master_id)
        if not customer:
            raise ValueError("Customer not found")

        update_fields = [
            "name", "legal_name", "tax_id", "category",
            "email", "phone", "website",
            "shipping_same_as_billing",
            "payment_term_id", "currency", "credit_limit",
            "default_warehouse_id", "default_shipping_method",
            "receivable_account_id", "revenue_account_id",
            "tax_exempt", "tax_exempt_number", "tax_exempt_expiry",
            "sales_rep_id", "is_active", "notes",
        ]

        for field in update_fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(customer, field, value)

        if data.customer_type:
            customer.customer_type = data.customer_type.value

        if data.segment:
            customer.segment = data.segment.value

        if data.billing_address:
            customer.billing_address_line1 = data.billing_address.line1
            customer.billing_address_line2 = data.billing_address.line2
            customer.billing_city = data.billing_address.city
            customer.billing_state = data.billing_address.state
            customer.billing_postal_code = data.billing_address.postal_code
            customer.billing_country = data.billing_address.country

        self.db.commit()
        self.db.refresh(customer)

        return customer

    def get_customer_by_id(self, customer_master_id: UUID) -> Optional[CustomerMaster]:
        """Get customer by ID."""
        return self.db.query(CustomerMaster).options(
            joinedload(CustomerMaster.contacts),
            joinedload(CustomerMaster.shipping_addresses),
            joinedload(CustomerMaster.payment_term),
            joinedload(CustomerMaster.sales_rep),
        ).get(customer_master_id)

    def get_customer_by_code(self, customer_id: UUID, code: str) -> Optional[CustomerMaster]:
        """Get customer by code."""
        return self.db.query(CustomerMaster).filter(
            CustomerMaster.customer_id == customer_id,
            CustomerMaster.customer_code == code,
        ).first()

    def get_customers(
        self,
        customer_id: UUID,
        filters: CustomerFilter = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[CustomerMaster], int]:
        """Get customers with filtering."""
        query = self.db.query(CustomerMaster).filter(
            CustomerMaster.customer_id == customer_id
        )

        if filters:
            if filters.search:
                search = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        CustomerMaster.customer_code.ilike(search),
                        CustomerMaster.name.ilike(search),
                        CustomerMaster.email.ilike(search),
                    )
                )

            if filters.customer_type:
                query = query.filter(CustomerMaster.customer_type == filters.customer_type.value)

            if filters.segment:
                query = query.filter(CustomerMaster.segment == filters.segment.value)

            if filters.category:
                query = query.filter(CustomerMaster.category == filters.category)

            if filters.sales_rep_id:
                query = query.filter(CustomerMaster.sales_rep_id == filters.sales_rep_id)

            if filters.is_active is not None:
                query = query.filter(CustomerMaster.is_active == filters.is_active)

            if filters.credit_hold is not None:
                query = query.filter(CustomerMaster.credit_hold == filters.credit_hold)

        total = query.count()

        customers = query.options(
            joinedload(CustomerMaster.payment_term),
            joinedload(CustomerMaster.sales_rep),
        ).order_by(
            CustomerMaster.name.asc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return customers, total

    def get_customers_summary(self, customer_id: UUID, active_only: bool = True) -> List[dict]:
        """Get customer list for dropdowns."""
        query = self.db.query(
            CustomerMaster.id,
            CustomerMaster.customer_code,
            CustomerMaster.name,
            CustomerMaster.currency,
            CustomerMaster.payment_term_id,
            CustomerMaster.credit_hold,
        ).filter(CustomerMaster.customer_id == customer_id)

        if active_only:
            query = query.filter(CustomerMaster.is_active == True)

        return [
            {
                "id": str(row.id),
                "customer_code": row.customer_code,
                "name": row.name,
                "currency": row.currency,
                "payment_term_id": str(row.payment_term_id) if row.payment_term_id else None,
                "credit_hold": row.credit_hold,
            }
            for row in query.order_by(CustomerMaster.name).all()
        ]

    def set_credit_hold(
        self,
        customer_master_id: UUID,
        hold: bool,
        reason: str = None,
        by_user: UUID = None,
    ) -> CustomerMaster:
        """Set or release credit hold."""
        customer = self.db.query(CustomerMaster).get(customer_master_id)
        if not customer:
            raise ValueError("Customer not found")

        customer.credit_hold = hold
        customer.credit_hold_reason = reason if hold else None

        self.db.commit()
        self.db.refresh(customer)

        return customer

    def update_credit_limit(
        self,
        customer_master_id: UUID,
        credit_limit: Decimal,
    ) -> CustomerMaster:
        """Update credit limit."""
        customer = self.db.query(CustomerMaster).get(customer_master_id)
        if not customer:
            raise ValueError("Customer not found")

        customer.credit_limit = credit_limit

        self.db.commit()
        self.db.refresh(customer)

        return customer

    def add_contact(
        self,
        customer_master_id: UUID,
        data: ContactCreate,
    ) -> CustomerContact:
        """Add contact to customer."""
        customer = self.db.query(CustomerMaster).get(customer_master_id)
        if not customer:
            raise ValueError("Customer not found")

        if data.is_primary:
            self.db.query(CustomerContact).filter(
                CustomerContact.customer_master_id == customer_master_id,
                CustomerContact.is_primary == True,
            ).update({"is_primary": False})

        contact = CustomerContact(
            customer_master_id=customer_master_id,
            name=data.name,
            title=data.title,
            department=data.department,
            email=data.email,
            phone=data.phone,
            mobile=data.mobile,
            is_primary=data.is_primary,
            is_billing=data.is_billing,
            is_shipping=data.is_shipping,
            is_purchasing=data.is_purchasing,
            notes=data.notes,
        )

        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)

        return contact

    def update_contact(self, contact_id: UUID, data: ContactUpdate) -> CustomerContact:
        """Update contact."""
        contact = self.db.query(CustomerContact).get(contact_id)
        if not contact:
            raise ValueError("Contact not found")

        if data.is_primary:
            self.db.query(CustomerContact).filter(
                CustomerContact.customer_master_id == contact.customer_master_id,
                CustomerContact.id != contact_id,
                CustomerContact.is_primary == True,
            ).update({"is_primary": False})

        for field, value in data.dict(exclude_unset=True).items():
            setattr(contact, field, value)

        self.db.commit()
        self.db.refresh(contact)

        return contact

    def delete_contact(self, contact_id: UUID) -> bool:
        """Delete contact."""
        contact = self.db.query(CustomerContact).get(contact_id)
        if contact:
            self.db.delete(contact)
            self.db.commit()
            return True
        return False

    def add_shipping_address(
        self,
        customer_master_id: UUID,
        data: ShippingAddressCreate,
    ) -> CustomerShippingAddress:
        """Add shipping address."""
        if data.is_default:
            self.db.query(CustomerShippingAddress).filter(
                CustomerShippingAddress.customer_master_id == customer_master_id,
                CustomerShippingAddress.is_default == True,
            ).update({"is_default": False})

        address = CustomerShippingAddress(
            customer_master_id=customer_master_id,
            name=data.name,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country=data.country,
            contact_name=data.contact_name,
            contact_phone=data.contact_phone,
            contact_email=data.contact_email,
            delivery_instructions=data.delivery_instructions,
            is_default=data.is_default,
        )

        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)

        return address

    def update_shipping_address(self, address_id: UUID, data: ShippingAddressUpdate) -> CustomerShippingAddress:
        """Update shipping address."""
        address = self.db.query(CustomerShippingAddress).get(address_id)
        if not address:
            raise ValueError("Address not found")

        if data.is_default:
            self.db.query(CustomerShippingAddress).filter(
                CustomerShippingAddress.customer_master_id == address.customer_master_id,
                CustomerShippingAddress.id != address_id,
                CustomerShippingAddress.is_default == True,
            ).update({"is_default": False})

        for field, value in data.dict(exclude_unset=True).items():
            setattr(address, field, value)

        self.db.commit()
        self.db.refresh(address)

        return address

    def delete_shipping_address(self, address_id: UUID) -> bool:
        """Delete shipping address."""
        address = self.db.query(CustomerShippingAddress).get(address_id)
        if address:
            self.db.delete(address)
            self.db.commit()
            return True
        return False

    def add_price_list(
        self,
        customer_master_id: UUID,
        data: PriceListCreate,
    ) -> CustomerPriceList:
        """Add customer-specific pricing."""
        existing = self.db.query(CustomerPriceList).filter(
            CustomerPriceList.customer_master_id == customer_master_id,
            CustomerPriceList.product_id == data.product_id,
            CustomerPriceList.min_quantity == data.min_quantity,
        ).first()

        if existing:
            raise ValueError("Price already exists for this product/quantity")

        price = CustomerPriceList(
            customer_master_id=customer_master_id,
            product_id=data.product_id,
            unit_price=data.unit_price,
            currency=data.currency,
            min_quantity=data.min_quantity,
            discount_percent=data.discount_percent,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
        )

        self.db.add(price)
        self.db.commit()
        self.db.refresh(price)

        return price

    def get_customer_price(
        self,
        customer_master_id: UUID,
        product_id: UUID,
        quantity: Decimal = Decimal("1"),
    ) -> Optional[CustomerPriceList]:
        """Get customer-specific price for a product."""
        today = date.today()

        return self.db.query(CustomerPriceList).filter(
            CustomerPriceList.customer_master_id == customer_master_id,
            CustomerPriceList.product_id == product_id,
            CustomerPriceList.min_quantity <= quantity,
            or_(CustomerPriceList.valid_from == None, CustomerPriceList.valid_from <= today),
            or_(CustomerPriceList.valid_to == None, CustomerPriceList.valid_to >= today),
        ).order_by(
            CustomerPriceList.min_quantity.desc()
        ).first()


def get_customer_service(db: Session) -> CustomerService:
    """Factory function."""
    return CustomerService(db)
