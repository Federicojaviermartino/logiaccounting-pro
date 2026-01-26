"""
Supplier Service
Business logic for supplier management
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session, joinedload

from app.purchasing.suppliers.models import (
    Supplier, SupplierContact, SupplierPriceList, SupplierTypeEnum
)
from app.purchasing.suppliers.schemas import (
    SupplierCreate, SupplierUpdate, SupplierFilter,
    ContactCreate, ContactUpdate,
    PriceListCreate, PriceListUpdate,
)

logger = logging.getLogger(__name__)


class SupplierService:
    """Service for supplier management."""

    def __init__(self, db: Session):
        self.db = db

    def create_supplier(
        self,
        customer_id: UUID,
        data: SupplierCreate,
        created_by: UUID = None,
    ) -> Supplier:
        """Create a new supplier."""
        existing = self.db.query(Supplier).filter(
            Supplier.customer_id == customer_id,
            Supplier.supplier_code == data.supplier_code,
        ).first()

        if existing:
            raise ValueError(f"Supplier code {data.supplier_code} already exists")

        supplier = Supplier(
            customer_id=customer_id,
            supplier_code=data.supplier_code,
            name=data.name,
            legal_name=data.legal_name,
            tax_id=data.tax_id,
            supplier_type=data.supplier_type.value if data.supplier_type else SupplierTypeEnum.VENDOR.value,
            category=data.category,
            email=data.email,
            phone=data.phone,
            website=data.website,
            payment_term_id=data.payment_term_id,
            currency=data.currency,
            credit_limit=data.credit_limit,
            bank_name=data.bank_name,
            bank_account=data.bank_account,
            bank_routing=data.bank_routing,
            bank_swift=data.bank_swift,
            bank_iban=data.bank_iban,
            default_warehouse_id=data.default_warehouse_id,
            default_lead_time_days=data.default_lead_time_days,
            payable_account_id=data.payable_account_id,
            expense_account_id=data.expense_account_id,
            notes=data.notes,
            created_by=created_by,
        )

        if data.address:
            supplier.address_line1 = data.address.line1
            supplier.address_line2 = data.address.line2
            supplier.city = data.address.city
            supplier.state = data.address.state
            supplier.postal_code = data.address.postal_code
            supplier.country = data.address.country

        self.db.add(supplier)
        self.db.flush()

        if data.contacts:
            for contact_data in data.contacts:
                contact = SupplierContact(
                    supplier_id=supplier.id,
                    name=contact_data.name,
                    title=contact_data.title,
                    department=contact_data.department,
                    email=contact_data.email,
                    phone=contact_data.phone,
                    mobile=contact_data.mobile,
                    is_primary=contact_data.is_primary,
                    is_ordering=contact_data.is_ordering,
                    is_billing=contact_data.is_billing,
                    is_technical=contact_data.is_technical,
                    notes=contact_data.notes,
                )
                self.db.add(contact)

        self.db.commit()
        self.db.refresh(supplier)

        logger.info(f"Created supplier: {supplier.supplier_code}")
        return supplier

    def update_supplier(
        self,
        supplier_id: UUID,
        data: SupplierUpdate,
    ) -> Supplier:
        """Update supplier."""
        supplier = self.db.query(Supplier).get(supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")

        update_fields = [
            "name", "legal_name", "tax_id", "category",
            "email", "phone", "website",
            "payment_term_id", "currency", "credit_limit",
            "bank_name", "bank_account", "bank_routing", "bank_swift", "bank_iban",
            "default_warehouse_id", "default_lead_time_days",
            "payable_account_id", "expense_account_id",
            "is_active", "notes",
        ]

        for field in update_fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(supplier, field, value)

        if data.supplier_type:
            supplier.supplier_type = data.supplier_type.value

        if data.address:
            supplier.address_line1 = data.address.line1
            supplier.address_line2 = data.address.line2
            supplier.city = data.address.city
            supplier.state = data.address.state
            supplier.postal_code = data.address.postal_code
            supplier.country = data.address.country

        self.db.commit()
        self.db.refresh(supplier)

        return supplier

    def get_supplier_by_id(self, supplier_id: UUID) -> Optional[Supplier]:
        """Get supplier by ID."""
        return self.db.query(Supplier).options(
            joinedload(Supplier.contacts),
            joinedload(Supplier.payment_term),
            joinedload(Supplier.default_warehouse),
        ).get(supplier_id)

    def get_supplier_by_code(self, customer_id: UUID, code: str) -> Optional[Supplier]:
        """Get supplier by code."""
        return self.db.query(Supplier).filter(
            Supplier.customer_id == customer_id,
            Supplier.supplier_code == code,
        ).first()

    def get_suppliers(
        self,
        customer_id: UUID,
        filters: SupplierFilter = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Supplier], int]:
        """Get suppliers with filtering."""
        query = self.db.query(Supplier).filter(
            Supplier.customer_id == customer_id
        )

        if filters:
            if filters.search:
                search = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Supplier.supplier_code.ilike(search),
                        Supplier.name.ilike(search),
                        Supplier.email.ilike(search),
                    )
                )

            if filters.supplier_type:
                query = query.filter(Supplier.supplier_type == filters.supplier_type.value)

            if filters.category:
                query = query.filter(Supplier.category == filters.category)

            if filters.is_active is not None:
                query = query.filter(Supplier.is_active == filters.is_active)

            if filters.is_approved is not None:
                query = query.filter(Supplier.is_approved == filters.is_approved)

        total = query.count()

        suppliers = query.options(
            joinedload(Supplier.payment_term),
        ).order_by(
            Supplier.name.asc()
        ).offset((page - 1) * page_size).limit(page_size).all()

        return suppliers, total

    def get_suppliers_summary(self, customer_id: UUID, active_only: bool = True) -> List[dict]:
        """Get supplier list for dropdowns."""
        query = self.db.query(
            Supplier.id,
            Supplier.supplier_code,
            Supplier.name,
            Supplier.currency,
            Supplier.payment_term_id,
        ).filter(Supplier.customer_id == customer_id)

        if active_only:
            query = query.filter(Supplier.is_active == True)

        return [
            {
                "id": str(row.id),
                "supplier_code": row.supplier_code,
                "name": row.name,
                "currency": row.currency,
                "payment_term_id": str(row.payment_term_id) if row.payment_term_id else None,
            }
            for row in query.order_by(Supplier.name).all()
        ]

    def approve_supplier(
        self,
        supplier_id: UUID,
        approved_by: UUID,
        approve: bool = True,
    ) -> Supplier:
        """Approve or reject supplier."""
        supplier = self.db.query(Supplier).get(supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")

        supplier.is_approved = approve
        supplier.approved_by = approved_by if approve else None
        supplier.approved_at = datetime.utcnow() if approve else None

        self.db.commit()
        self.db.refresh(supplier)

        return supplier

    def add_contact(
        self,
        supplier_id: UUID,
        data: ContactCreate,
    ) -> SupplierContact:
        """Add contact to supplier."""
        supplier = self.db.query(Supplier).get(supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")

        if data.is_primary:
            self.db.query(SupplierContact).filter(
                SupplierContact.supplier_id == supplier_id,
                SupplierContact.is_primary == True,
            ).update({"is_primary": False})

        contact = SupplierContact(
            supplier_id=supplier_id,
            name=data.name,
            title=data.title,
            department=data.department,
            email=data.email,
            phone=data.phone,
            mobile=data.mobile,
            is_primary=data.is_primary,
            is_ordering=data.is_ordering,
            is_billing=data.is_billing,
            is_technical=data.is_technical,
            notes=data.notes,
        )

        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)

        return contact

    def update_contact(
        self,
        contact_id: UUID,
        data: ContactUpdate,
    ) -> SupplierContact:
        """Update contact."""
        contact = self.db.query(SupplierContact).get(contact_id)
        if not contact:
            raise ValueError("Contact not found")

        if data.is_primary:
            self.db.query(SupplierContact).filter(
                SupplierContact.supplier_id == contact.supplier_id,
                SupplierContact.id != contact_id,
                SupplierContact.is_primary == True,
            ).update({"is_primary": False})

        for field, value in data.dict(exclude_unset=True).items():
            setattr(contact, field, value)

        self.db.commit()
        self.db.refresh(contact)

        return contact

    def delete_contact(self, contact_id: UUID) -> bool:
        """Delete contact."""
        contact = self.db.query(SupplierContact).get(contact_id)
        if contact:
            self.db.delete(contact)
            self.db.commit()
            return True
        return False

    def add_price_list(
        self,
        supplier_id: UUID,
        data: PriceListCreate,
    ) -> SupplierPriceList:
        """Add product price to supplier."""
        supplier = self.db.query(Supplier).get(supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")

        existing = self.db.query(SupplierPriceList).filter(
            SupplierPriceList.supplier_id == supplier_id,
            SupplierPriceList.product_id == data.product_id,
            SupplierPriceList.min_quantity == data.min_quantity,
        ).first()

        if existing:
            raise ValueError("Price already exists for this product/quantity")

        if data.is_preferred:
            self.db.query(SupplierPriceList).filter(
                SupplierPriceList.product_id == data.product_id,
                SupplierPriceList.is_preferred == True,
            ).update({"is_preferred": False})

        price = SupplierPriceList(
            supplier_id=supplier_id,
            product_id=data.product_id,
            supplier_sku=data.supplier_sku,
            supplier_description=data.supplier_description,
            unit_price=data.unit_price,
            currency=data.currency,
            min_quantity=data.min_quantity,
            lead_time_days=data.lead_time_days,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
            is_preferred=data.is_preferred,
        )

        self.db.add(price)
        self.db.commit()
        self.db.refresh(price)

        return price

    def update_price_list(
        self,
        price_id: UUID,
        data: PriceListUpdate,
    ) -> SupplierPriceList:
        """Update price list entry."""
        price = self.db.query(SupplierPriceList).get(price_id)
        if not price:
            raise ValueError("Price not found")

        if data.is_preferred:
            self.db.query(SupplierPriceList).filter(
                SupplierPriceList.product_id == price.product_id,
                SupplierPriceList.id != price_id,
                SupplierPriceList.is_preferred == True,
            ).update({"is_preferred": False})

        for field, value in data.dict(exclude_unset=True).items():
            setattr(price, field, value)

        self.db.commit()
        self.db.refresh(price)

        return price

    def delete_price_list(self, price_id: UUID) -> bool:
        """Delete price list entry."""
        price = self.db.query(SupplierPriceList).get(price_id)
        if price:
            self.db.delete(price)
            self.db.commit()
            return True
        return False

    def get_supplier_prices(
        self,
        supplier_id: UUID,
        current_only: bool = True,
    ) -> List[SupplierPriceList]:
        """Get all prices for a supplier."""
        query = self.db.query(SupplierPriceList).filter(
            SupplierPriceList.supplier_id == supplier_id
        )

        if current_only:
            today = date.today()
            query = query.filter(
                or_(
                    SupplierPriceList.valid_from == None,
                    SupplierPriceList.valid_from <= today,
                ),
                or_(
                    SupplierPriceList.valid_to == None,
                    SupplierPriceList.valid_to >= today,
                ),
            )

        return query.options(
            joinedload(SupplierPriceList.product)
        ).all()

    def get_product_suppliers(
        self,
        customer_id: UUID,
        product_id: UUID,
        quantity: Decimal = Decimal("1"),
    ) -> List[dict]:
        """Get suppliers for a product with pricing."""
        today = date.today()

        prices = self.db.query(SupplierPriceList).join(
            Supplier
        ).filter(
            Supplier.customer_id == customer_id,
            Supplier.is_active == True,
            SupplierPriceList.product_id == product_id,
            SupplierPriceList.min_quantity <= quantity,
            or_(
                SupplierPriceList.valid_from == None,
                SupplierPriceList.valid_from <= today,
            ),
            or_(
                SupplierPriceList.valid_to == None,
                SupplierPriceList.valid_to >= today,
            ),
        ).options(
            joinedload(SupplierPriceList.supplier)
        ).order_by(
            SupplierPriceList.is_preferred.desc(),
            SupplierPriceList.unit_price.asc(),
        ).all()

        return [
            {
                "supplier_id": str(p.supplier_id),
                "supplier_code": p.supplier.supplier_code,
                "supplier_name": p.supplier.name,
                "supplier_sku": p.supplier_sku,
                "unit_price": float(p.unit_price),
                "currency": p.currency,
                "min_quantity": float(p.min_quantity),
                "lead_time_days": p.lead_time_days,
                "is_preferred": p.is_preferred,
            }
            for p in prices
        ]

    def get_preferred_supplier(
        self,
        customer_id: UUID,
        product_id: UUID,
    ) -> Optional[dict]:
        """Get preferred supplier for a product."""
        suppliers = self.get_product_suppliers(customer_id, product_id)
        return suppliers[0] if suppliers else None


def get_supplier_service(db: Session) -> SupplierService:
    """Factory function."""
    return SupplierService(db)
