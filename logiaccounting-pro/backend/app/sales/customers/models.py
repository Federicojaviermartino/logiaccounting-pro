"""
Customer Models
Customer master data, contacts, addresses, and pricing
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


class CustomerTypeEnum(str, Enum):
    """Customer classification."""
    BUSINESS = "business"
    INDIVIDUAL = "individual"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"


class CustomerSegmentEnum(str, Enum):
    """Customer segment."""
    ENTERPRISE = "enterprise"
    MID_MARKET = "mid_market"
    SMB = "smb"
    RETAIL = "retail"


class CustomerMaster(Base):
    """Customer master record."""

    __tablename__ = "customers_master"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    customer_code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    legal_name = Column(String(200))
    tax_id = Column(String(50))

    customer_type = Column(String(30), default=CustomerTypeEnum.BUSINESS.value)
    category = Column(String(50))
    segment = Column(String(30))
    tags = Column(String(200))

    email = Column(String(100))
    phone = Column(String(30))
    website = Column(String(200))

    billing_address_line1 = Column(String(200))
    billing_address_line2 = Column(String(200))
    billing_city = Column(String(100))
    billing_state = Column(String(100))
    billing_postal_code = Column(String(20))
    billing_country = Column(String(3), default="USA")

    shipping_address_line1 = Column(String(200))
    shipping_address_line2 = Column(String(200))
    shipping_city = Column(String(100))
    shipping_state = Column(String(100))
    shipping_postal_code = Column(String(20))
    shipping_country = Column(String(3), default="USA")
    shipping_same_as_billing = Column(Boolean, default=True)

    payment_term_id = Column(PGUUID(as_uuid=True), ForeignKey("payment_terms.id"))
    currency = Column(String(3), default="USD")
    credit_limit = Column(Numeric(18, 4), default=0)
    credit_hold = Column(Boolean, default=False)
    credit_hold_reason = Column(String(200))

    default_warehouse_id = Column(PGUUID(as_uuid=True), ForeignKey("warehouses.id"))
    default_shipping_method = Column(String(50))

    receivable_account_id = Column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))
    revenue_account_id = Column(PGUUID(as_uuid=True), ForeignKey("chart_of_accounts.id"))

    tax_exempt = Column(Boolean, default=False)
    tax_exempt_number = Column(String(50))
    tax_exempt_expiry = Column(Date)

    is_active = Column(Boolean, default=True)

    sales_rep_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    notes = Column(Text)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contacts = relationship("CustomerContact", back_populates="customer", cascade="all, delete-orphan")
    shipping_addresses = relationship("CustomerShippingAddress", back_populates="customer", cascade="all, delete-orphan")
    price_lists = relationship("CustomerPriceList", back_populates="customer", cascade="all, delete-orphan")
    payment_term = relationship("PaymentTerm")
    default_warehouse = relationship("Warehouse")
    sales_rep = relationship("User", foreign_keys=[sales_rep_id])

    __table_args__ = (
        UniqueConstraint("customer_id", "customer_code", name="uq_customer_code"),
        Index("idx_customer_name", "customer_id", "name"),
        Index("idx_customer_active", "customer_id", "is_active"),
    )

    @property
    def primary_contact(self):
        """Get primary contact."""
        for contact in self.contacts:
            if contact.is_primary:
                return contact
        return self.contacts[0] if self.contacts else None

    @property
    def default_shipping_address(self):
        """Get default shipping address."""
        for addr in self.shipping_addresses:
            if addr.is_default:
                return addr
        return self.shipping_addresses[0] if self.shipping_addresses else None

    @property
    def billing_address_formatted(self) -> str:
        """Get formatted billing address."""
        parts = [self.billing_address_line1]
        if self.billing_address_line2:
            parts.append(self.billing_address_line2)
        parts.append(f"{self.billing_city}, {self.billing_state} {self.billing_postal_code}")
        parts.append(self.billing_country)
        return "\n".join(filter(None, parts))

    @property
    def available_credit(self) -> Decimal:
        """Calculate available credit."""
        if not self.credit_limit:
            return Decimal("999999999")
        return self.credit_limit

    def to_dict(self, include_contacts: bool = False, include_addresses: bool = False) -> dict:
        result = {
            "id": str(self.id),
            "customer_code": self.customer_code,
            "name": self.name,
            "legal_name": self.legal_name,
            "tax_id": self.tax_id,
            "customer_type": self.customer_type,
            "category": self.category,
            "segment": self.segment,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "billing_address": {
                "line1": self.billing_address_line1,
                "line2": self.billing_address_line2,
                "city": self.billing_city,
                "state": self.billing_state,
                "postal_code": self.billing_postal_code,
                "country": self.billing_country,
            },
            "shipping_same_as_billing": self.shipping_same_as_billing,
            "currency": self.currency,
            "payment_term_id": str(self.payment_term_id) if self.payment_term_id else None,
            "payment_term": self.payment_term.name if self.payment_term else None,
            "credit_limit": float(self.credit_limit) if self.credit_limit else 0,
            "credit_hold": self.credit_hold,
            "credit_hold_reason": self.credit_hold_reason,
            "tax_exempt": self.tax_exempt,
            "tax_exempt_number": self.tax_exempt_number,
            "default_warehouse_id": str(self.default_warehouse_id) if self.default_warehouse_id else None,
            "default_shipping_method": self.default_shipping_method,
            "sales_rep_id": str(self.sales_rep_id) if self.sales_rep_id else None,
            "sales_rep_name": self.sales_rep.full_name if self.sales_rep else None,
            "is_active": self.is_active,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_contacts:
            result["contacts"] = [c.to_dict() for c in self.contacts]

        if include_addresses:
            result["shipping_addresses"] = [a.to_dict() for a in self.shipping_addresses]

        return result


class CustomerContact(Base):
    """Customer contact person."""

    __tablename__ = "customer_contacts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_master_id = Column(PGUUID(as_uuid=True), ForeignKey("customers_master.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(100), nullable=False)
    title = Column(String(50))
    department = Column(String(50))

    email = Column(String(100))
    phone = Column(String(30))
    mobile = Column(String(30))

    is_primary = Column(Boolean, default=False)
    is_billing = Column(Boolean, default=False)
    is_shipping = Column(Boolean, default=False)
    is_purchasing = Column(Boolean, default=False)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("CustomerMaster", back_populates="contacts")

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
            "is_billing": self.is_billing,
            "is_shipping": self.is_shipping,
            "is_purchasing": self.is_purchasing,
            "notes": self.notes,
        }


class CustomerShippingAddress(Base):
    """Customer shipping address (multiple allowed)."""

    __tablename__ = "customer_shipping_addresses"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_master_id = Column(PGUUID(as_uuid=True), ForeignKey("customers_master.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(100), nullable=False)

    address_line1 = Column(String(200), nullable=False)
    address_line2 = Column(String(200))
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    postal_code = Column(String(20), nullable=False)
    country = Column(String(3), default="USA")

    contact_name = Column(String(100))
    contact_phone = Column(String(30))
    contact_email = Column(String(100))

    delivery_instructions = Column(Text)

    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("CustomerMaster", back_populates="shipping_addresses")

    @property
    def formatted_address(self) -> str:
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.append(f"{self.city}, {self.state} {self.postal_code}")
        parts.append(self.country)
        return "\n".join(filter(None, parts))

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "delivery_instructions": self.delivery_instructions,
            "is_default": self.is_default,
            "formatted_address": self.formatted_address,
        }


class CustomerPriceList(Base):
    """Customer-specific product pricing."""

    __tablename__ = "customer_price_lists"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_master_id = Column(PGUUID(as_uuid=True), ForeignKey("customers_master.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    unit_price = Column(Numeric(18, 6), nullable=False)
    currency = Column(String(3), default="USD")
    min_quantity = Column(Numeric(18, 4), default=1)
    discount_percent = Column(Numeric(5, 2), default=0)

    valid_from = Column(Date)
    valid_to = Column(Date)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("CustomerMaster", back_populates="price_lists")
    product = relationship("Product")

    __table_args__ = (
        UniqueConstraint("customer_master_id", "product_id", "min_quantity", name="uq_customer_product_qty"),
        Index("idx_customer_price_product", "product_id"),
    )

    @property
    def is_current(self) -> bool:
        today = date.today()
        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_to and today > self.valid_to:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "product_sku": self.product.sku if self.product else None,
            "product_name": self.product.name if self.product else None,
            "unit_price": float(self.unit_price),
            "currency": self.currency,
            "min_quantity": float(self.min_quantity),
            "discount_percent": float(self.discount_percent) if self.discount_percent else 0,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "is_current": self.is_current,
        }
