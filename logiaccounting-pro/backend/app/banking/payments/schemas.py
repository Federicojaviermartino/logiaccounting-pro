"""
Payment Processing Schemas
Pydantic schemas for payments
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.banking.payments.models import BatchStatus, PaymentMethod, BatchType, InstructionStatus


class PayeeAddressSchema(BaseModel):
    """Payee address details"""
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=3)


class PaymentInstructionCreate(BaseModel):
    """Schema for creating a payment instruction"""
    source_type: str = Field(..., pattern="^(supplier_invoice|customer_refund|manual)$")
    source_id: Optional[UUID] = None

    payee_type: Optional[str] = Field(None, pattern="^(supplier|customer|employee|other)$")
    payee_id: Optional[UUID] = None
    payee_name: str = Field(..., max_length=200)

    payee_bank_name: Optional[str] = Field(None, max_length=200)
    payee_account_number: Optional[str] = Field(None, max_length=50)
    payee_routing_number: Optional[str] = Field(None, max_length=50)
    payee_iban: Optional[str] = Field(None, max_length=50)
    payee_swift: Optional[str] = Field(None, max_length=20)

    payee_address: Optional[PayeeAddressSchema] = None

    currency: str = Field("USD", max_length=3)
    amount: Decimal = Field(..., gt=0)

    payment_reference: Optional[str] = Field(None, max_length=100)
    remittance_info: Optional[str] = None
    notes: Optional[str] = None


class PaymentInstructionResponse(BaseModel):
    """Schema for payment instruction response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID
    line_number: int

    source_type: str
    source_id: Optional[UUID] = None

    payee_type: Optional[str] = None
    payee_id: Optional[UUID] = None
    payee_name: str

    payee_bank_name: Optional[str] = None
    payee_account_number: Optional[str] = None

    currency: str
    amount: Decimal
    exchange_rate: Decimal
    base_amount: Optional[Decimal] = None

    payment_reference: Optional[str] = None
    remittance_info: Optional[str] = None
    check_number: Optional[str] = None

    status: str
    processed_at: Optional[datetime] = None
    confirmation_number: Optional[str] = None
    error_message: Optional[str] = None


class PaymentBatchCreate(BaseModel):
    """Schema for creating a payment batch"""
    batch_name: Optional[str] = Field(None, max_length=200)
    bank_account_id: UUID
    payment_method: PaymentMethod
    batch_type: BatchType = BatchType.AP
    currency: str = Field("USD", max_length=3)
    payment_date: date
    value_date: Optional[date] = None
    requires_approval: bool = True
    approval_threshold: Optional[Decimal] = None
    notes: Optional[str] = None


class PaymentBatchUpdate(BaseModel):
    """Schema for updating a payment batch"""
    batch_name: Optional[str] = Field(None, max_length=200)
    payment_date: Optional[date] = None
    value_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentBatchResponse(BaseModel):
    """Schema for payment batch response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_number: str
    batch_name: Optional[str] = None
    bank_account_id: UUID

    payment_method: str
    batch_type: str
    currency: str

    payment_count: int
    total_amount: Decimal

    payment_date: date
    value_date: Optional[date] = None

    status: str
    requires_approval: bool
    approval_threshold: Optional[Decimal] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None

    file_format: Optional[str] = None
    file_generated_at: Optional[datetime] = None
    file_reference: Optional[str] = None

    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    error_count: int
    error_message: Optional[str] = None

    notes: Optional[str] = None
    created_at: datetime


class PaymentBatchDetailResponse(PaymentBatchResponse):
    """Batch with instructions"""
    instructions: List[PaymentInstructionResponse] = []


class PaymentBatchSummary(BaseModel):
    """Brief batch summary"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_number: str
    payment_date: date
    payment_count: int
    total_amount: Decimal
    status: str


class ApprovalRequest(BaseModel):
    """Request for batch approval"""
    approved: bool = True
    notes: Optional[str] = None


class PaymentHistoryResponse(BaseModel):
    """Schema for payment history response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_type: str
    document_id: UUID
    payment_instruction_id: Optional[UUID] = None
    bank_transaction_id: Optional[UUID] = None
    payment_date: date
    amount: Decimal
    currency: str
    payment_method: Optional[str] = None
    reference: Optional[str] = None
    allocated_amount: Decimal
    created_at: datetime
