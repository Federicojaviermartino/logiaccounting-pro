"""
Supplier Models
Supplier master data, contacts, and price lists
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, ForeignKey,
    Numeric, Integer, Text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base


class SupplierTypeEnum(str, Enum):
    """Supplier classification."""
    VENDOR = "vendor"
    CONTRACTOR = "contractor"
    SERVICE = "service"
    DISTRIBUTOR = "distributor"
    MANUFACTURER = "manufacturer"


class Supplier(Base):
    """Supplier master record."""

    __tablename__ = "suppliers"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    # Identification
    supplier_code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    legal_name = Column(String(200))
    tax_id = Column(String(50))

    # Classification
    supplier_type = Column(String(30), default=SupplierTypeEnum.VENDOR.value)
    category = Column(String(50))
    tags = Column(String(200))

    # Primary contact
    email = Column(String(100))
    phone = Column(String(30))
    website = Column(String(200))

    # Address
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(3), default="USA")

    # Payment settings
    payment_term_id = Column(PGUUID(as_uuid=True), ForeignKey("payment_terms.id"))
    currency = Column(String(3), default="USD")
    credit_limit = Column(Numeric(18, 4))

    # Banking
    bank_name = Column(String(100))
    bank_account = Column(String(50))
    bank_routing = Column(String(50))
    bank_swift = Column(String(20))
    bank_iban = Column(String(50))

    # Defaults
    default_warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))
    default_lead_time_days = Column(Integer, default=0)

    # Accounting
    payable_account_id = Column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))
    expense_account_id = Column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))

    # Status
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # Metadata
    notes = Column(Text)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contacts = relationship("SupplierContact", back_populates="supplier", cascade="all, delete-orphan")
    price_lists = relationship("SupplierPriceList", back_populates="supplier", cascade="all, delete-orphan")
    payment_term = relationship("PaymentTerm")
    default_warehouse = relationship("Warehouse")
    payable_account = relationship("ChartOfAccount", foreign_keys=[payable_account_id])
    expense_account = relationship("ChartOfAccount", foreign_keys=[expense_account_id])

    __table_args__ = (
        UniqueConstraint("customer_id", "supplier_code", name="uq_supplier_code"),
        Index("idx_supplier_name", "customer_id", "name"),
        Index("idx_supplier_active", "customer_id", "is_active"),
    )

    @property
    def primary_contact(self):
        """Get primary contact."""
        for contact in self.contacts:
            if contact.is_primary:
                return contact
        return self.contacts[0] if self.contacts else None

    @property
    def full_address(self) -> str:
        """Get formatted address."""
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.append(f"{self.city}, {self.state} {self.postal_code}")
        parts.append(self.country)
        return "\n".join(filter(None, parts))

    def to_dict(self, include_contacts: bool = False, include_prices: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "supplier_code": self.supplier_code,
            "name": self.name,
            "legal_name": self.legal_name,
            "tax_id": self.tax_id,
            "supplier_type": self.supplier_type,
            "category": self.category,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "address": {
                "line1": self.address_line1,
                "line2": self.address_line2,
                "city": self.city,
                "state": self.state,
                "postal_code": self.postal_code,
                "country": self.country,
            },
            "currency": self.currency,
            "payment_term_id": str(self.payment_term_id) if self.payment_term_id else None,
            "payment_term": self.payment_term.name if self.payment_term else None,
            "credit_limit": float(self.credit_limit) if self.credit_limit else None,
            "default_warehouse_id": str(self.default_warehouse_id) if self.default_warehouse_id else None,
            "default_lead_time_days": self.default_lead_time_days,
            "is_active": self.is_active,
            "is_approved": self.is_approved,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_contacts:
            result["contacts"] = [c.to_dict() for c in self.contacts]

        if include_prices:
            result["price_lists"] = [p.to_dict() for p in self.price_lists if p.is_current]

        return result


class SupplierContact(Base):
    """Supplier contact person."""

    __tablename__ = "supplier_contacts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(PGUUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)

    # Contact info
    name = Column(String(100), nullable=False)
    title = Column(String(50))
    department = Column(String(50))

    email = Column(String(100))
    phone = Column(String(30))
    mobile = Column(String(30))

    # Role flags
    is_primary = Column(Boolean, default=False)
    is_ordering = Column(Boolean, default=False)
    is_billing = Column(Boolean, default=False)
    is_technical = Column(Boolean, default=False)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="contacts")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "title": self.title,
            "department": self.department,
            "email": self.email,
            "phone": self.phone,
            "mobile": self.mobile,
            "is_primary": self.is_primary,
            "is_ordering": self.is_ordering,
            "is_billing": self.is_billing,
            "is_technical": self.is_technical,
            "notes": self.notes,
        }


class SupplierPriceList(Base):
    """Supplier product pricing."""

    __tablename__ = "supplier_price_lists"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(PGUUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # Supplier's product info
    supplier_sku = Column(String(50))
    supplier_description = Column(String(200))

    # Pricing
    unit_price = Column(Numeric(18, 6), nullable=False)
    currency = Column(String(3), default="USD")
    min_quantity = Column(Numeric(18, 4), default=1)

    # Lead time
    lead_time_days = Column(Integer, default=0)

    # Validity period
    valid_from = Column(Date)
    valid_to = Column(Date)

    # Preference
    is_preferred = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="price_lists")
    product = relationship("Product")

    __table_args__ = (
        UniqueConstraint("supplier_id", "product_id", "min_quantity", name="uq_supplier_product_qty"),
        Index("idx_supplier_price_product", "product_id"),
    )

    @property
    def is_current(self) -> bool:
        """Check if price is currently valid."""
        today = date.today()
        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_to and today > self.valid_to:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "supplier_id": str(self.supplier_id),
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "supplier_sku": self.supplier_sku,
            "supplier_description": self.supplier_description,
            "unit_price": float(self.unit_price),
            "currency": self.currency,
            "min_quantity": float(self.min_quantity),
            "lead_time_days": self.lead_time_days,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "is_preferred": self.is_preferred,
            "is_current": self.is_current,
        }
