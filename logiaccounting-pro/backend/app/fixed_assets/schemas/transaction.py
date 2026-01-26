"""
Asset transaction schemas.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class DisposalType(str, Enum):
    SOLD = "sold"
    SCRAPPED = "scrapped"
    DONATED = "donated"
    LOST = "lost"
    STOLEN = "stolen"
    TRADE_IN = "trade_in"
    WRITTEN_OFF = "written_off"


class DisposalCreate(BaseModel):
    """Create asset disposal."""
    asset_id: UUID
    disposal_date: date
    disposal_type: DisposalType

    proceeds: Decimal = Field(default=0, ge=0)
    buyer_name: Optional[str] = Field(None, max_length=200)
    buyer_contact: Optional[str] = Field(None, max_length=200)

    notes: Optional[str] = None


class TransferCreate(BaseModel):
    """Create asset transfer."""
    asset_id: UUID
    transfer_date: date

    to_location: Optional[str] = Field(None, max_length=200)
    to_department_id: Optional[UUID] = None
    to_responsible_id: Optional[UUID] = None

    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_destination(self):
        """At least one destination field required."""
        if not any([self.to_location, self.to_department_id, self.to_responsible_id]):
            raise ValueError("At least one destination (location, department, or responsible person) required")
        return self


class RevaluationCreate(BaseModel):
    """Create asset revaluation."""
    asset_id: UUID
    revaluation_date: date

    new_value: Decimal = Field(..., gt=0)
    new_useful_life_months: Optional[int] = Field(None, gt=0)

    revaluation_reason: str = Field(..., max_length=500)
    appraiser: Optional[str] = Field(None, max_length=200)
    appraisal_date: Optional[date] = None

    notes: Optional[str] = None


class ImprovementCreate(BaseModel):
    """Create asset improvement (capitalized expense)."""
    asset_id: UUID
    improvement_date: date

    amount: Decimal = Field(..., gt=0)
    description: str = Field(..., max_length=500)

    extends_useful_life: bool = False
    additional_life_months: Optional[int] = Field(None, gt=0)

    notes: Optional[str] = None


class TransactionResponse(BaseModel):
    """Asset transaction response."""
    id: UUID
    asset_id: UUID
    asset_number: Optional[str] = None
    asset_name: Optional[str] = None

    transaction_number: str
    transaction_type: str
    transaction_date: date
    amount: Decimal

    # Disposal
    disposal_type: Optional[str]
    proceeds: Optional[Decimal]
    gain_loss: Optional[Decimal]

    # Transfer
    from_location: Optional[str]
    to_location: Optional[str]

    # Revaluation
    old_value: Optional[Decimal]
    new_value: Optional[Decimal]

    status: str
    journal_entry_id: Optional[UUID]

    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MovementResponse(TransactionResponse):
    """Movement response - alias for TransactionResponse."""
    pass


class DisposalResponse(TransactionResponse):
    """Disposal response with additional fields."""
    book_value_at_disposal: Optional[Decimal] = None
    accumulated_at_disposal: Optional[Decimal] = None
    buyer_name: Optional[str] = None
