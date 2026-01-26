"""
Invoice Schemas
Pydantic schemas for invoices and payments
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, EmailStr


class InvoiceStatusEnum(str, Enum):
    """Invoice status."""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PARTIAL_PAID = "partial_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    VOID = "void"


class PaymentMethodEnum(str, Enum):
    """Payment method."""
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    ACH = "ach"
    WIRE = "wire"
    OTHER = "other"


class InvoiceLineCreate(BaseModel):
    """Schema for creating invoice line."""
    order_id: Optional[UUID] = None
    order_line_id: Optional[UUID] = None
    shipment_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    uom_id: Optional[UUID] = None
    unit_price: Decimal = Field(..., ge=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    revenue_account_id: Optional[UUID] = None


class InvoiceLineUpdate(BaseModel):
    """Schema for updating invoice line."""
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    uom_id: Optional[UUID] = None
    unit_price: Optional[Decimal] = Field(None, ge=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    revenue_account_id: Optional[UUID] = None


class InvoiceLineResponse(BaseModel):
    """Response schema for invoice line."""
    id: UUID
    line_number: int
    order_id: Optional[UUID]
    order_number: Optional[str]
    shipment_id: Optional[UUID]
    product_id: Optional[UUID]
    product_sku: Optional[str]
    product_name: Optional[str]
    description: str
    quantity: float
    uom: Optional[str]
    unit_price: float
    discount_percent: float
    tax_rate: float
    line_subtotal: float
    line_discount: float
    line_tax: float
    line_total: float

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    """Schema for creating invoice."""
    customer_master_id: UUID
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_term_id: Optional[UUID] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    currency: str = "USD"
    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    shipping_amount: Decimal = Field(default=Decimal("0"), ge=0)
    po_number: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    footer_text: Optional[str] = None
    receivable_account_id: Optional[UUID] = None
    revenue_account_id: Optional[UUID] = None
    lines: Optional[List[InvoiceLineCreate]] = None


class InvoiceUpdate(BaseModel):
    """Schema for updating invoice."""
    due_date: Optional[date] = None
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = Field(None, gt=0)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    shipping_amount: Optional[Decimal] = Field(None, ge=0)
    po_number: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    footer_text: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Response schema for invoice."""
    id: UUID
    invoice_number: str
    customer_master_id: UUID
    customer_code: Optional[str]
    customer_name: Optional[str]
    invoice_date: Optional[date]
    due_date: Optional[date]
    billing_address: Optional[str]
    currency: str
    subtotal: float
    discount_percent: float
    discount_amount: float
    tax_amount: float
    shipping_amount: float
    total_amount: float
    paid_amount: float
    balance_due: float
    status: str
    po_number: Optional[str]
    reference: Optional[str]
    notes: Optional[str]
    is_overdue: bool
    days_overdue: int
    line_count: int
    payment_count: int
    sent_at: Optional[datetime]
    created_at: Optional[datetime]
    lines: Optional[List[InvoiceLineResponse]] = None
    payments: Optional[List["InvoicePaymentResponse"]] = None

    class Config:
        from_attributes = True


class InvoiceFilter(BaseModel):
    """Filter for listing invoices."""
    search: Optional[str] = None
    customer_master_id: Optional[UUID] = None
    status: Optional[InvoiceStatusEnum] = None
    statuses: Optional[List[InvoiceStatusEnum]] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None
    is_overdue: Optional[bool] = None
    order_id: Optional[UUID] = None


class InvoiceSummary(BaseModel):
    """Summary for dropdowns."""
    id: UUID
    invoice_number: str
    customer_name: str
    invoice_date: date
    total_amount: float
    balance_due: float
    status: str


class SendInvoiceRequest(BaseModel):
    """Request to send invoice."""
    email_to: EmailStr
    cc: Optional[List[EmailStr]] = None
    subject: Optional[str] = None
    message: Optional[str] = None
    attach_pdf: bool = True


class VoidInvoiceRequest(BaseModel):
    """Request to void invoice."""
    reason: str = Field(..., min_length=1)


class CreateFromOrderRequest(BaseModel):
    """Request to create invoice from order."""
    order_id: UUID
    invoice_shipped_only: bool = True


class CreateFromShipmentRequest(BaseModel):
    """Request to create invoice from shipment."""
    shipment_id: UUID


class InvoicePaymentCreate(BaseModel):
    """Schema for creating invoice payment."""
    invoice_id: UUID
    amount: Decimal = Field(..., gt=0)
    payment_date: Optional[date] = None
    payment_method: PaymentMethodEnum = PaymentMethodEnum.BANK_TRANSFER
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class InvoicePaymentResponse(BaseModel):
    """Response schema for invoice payment."""
    id: UUID
    invoice_id: UUID
    payment_id: Optional[UUID]
    amount: float
    payment_date: Optional[date]
    payment_method: str
    reference_number: Optional[str]
    notes: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class CustomerPaymentCreate(BaseModel):
    """Schema for creating customer payment."""
    customer_master_id: UUID
    payment_date: Optional[date] = None
    payment_method: PaymentMethodEnum = PaymentMethodEnum.BANK_TRANSFER
    amount: Decimal = Field(..., gt=0)
    currency: str = "USD"
    exchange_rate: Decimal = Field(default=Decimal("1"), gt=0)
    reference_number: Optional[str] = None
    bank_account_id: Optional[UUID] = None
    deposit_to_account_id: Optional[UUID] = None
    notes: Optional[str] = None
    memo: Optional[str] = None
    invoice_applications: Optional[List["PaymentApplicationCreate"]] = None


class CustomerPaymentUpdate(BaseModel):
    """Schema for updating customer payment."""
    payment_date: Optional[date] = None
    payment_method: Optional[PaymentMethodEnum] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    memo: Optional[str] = None


class CustomerPaymentResponse(BaseModel):
    """Response schema for customer payment."""
    id: UUID
    payment_number: str
    customer_master_id: UUID
    customer_code: Optional[str]
    customer_name: Optional[str]
    payment_date: Optional[date]
    payment_method: str
    amount: float
    applied_amount: float
    unapplied_amount: float
    currency: str
    reference_number: Optional[str]
    notes: Optional[str]
    memo: Optional[str]
    is_void: bool
    is_fully_applied: bool
    created_at: Optional[datetime]
    applications: Optional[List[InvoicePaymentResponse]] = None

    class Config:
        from_attributes = True


class CustomerPaymentFilter(BaseModel):
    """Filter for listing customer payments."""
    search: Optional[str] = None
    customer_master_id: Optional[UUID] = None
    payment_method: Optional[PaymentMethodEnum] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    has_unapplied: Optional[bool] = None
    is_void: Optional[bool] = False


class PaymentApplicationCreate(BaseModel):
    """Schema for applying payment to invoice."""
    invoice_id: UUID
    amount: Decimal = Field(..., gt=0)


class ApplyPaymentRequest(BaseModel):
    """Request to apply payment to invoices."""
    applications: List[PaymentApplicationCreate]


class VoidPaymentRequest(BaseModel):
    """Request to void payment."""
    reason: str = Field(..., min_length=1)


class AgingBucket(BaseModel):
    """Aging bucket summary."""
    current: float = 0
    days_1_30: float = 0
    days_31_60: float = 0
    days_61_90: float = 0
    over_90: float = 0
    total: float = 0


class CustomerAgingReport(BaseModel):
    """Customer aging report."""
    customer_id: UUID
    customer_code: str
    customer_name: str
    aging: AgingBucket
    invoice_count: int


class AgingReportFilter(BaseModel):
    """Filter for aging report."""
    as_of_date: Optional[date] = None
    customer_master_id: Optional[UUID] = None
    min_balance: Optional[Decimal] = None
