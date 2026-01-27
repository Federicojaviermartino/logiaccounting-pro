"""Time off and leave management models."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text, Date,
    Numeric, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TimeOffType(str, Enum):
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    BEREAVEMENT = "bereavement"
    JURY_DUTY = "jury_duty"
    MILITARY = "military"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    UNPAID = "unpaid"
    OTHER = "other"


class TimeOffStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class TimeOffRequest(Base):
    """Employee time off request."""
    __tablename__ = "time_off_requests"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    employee_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)

    request_number: Mapped[str] = mapped_column(String(30), nullable=False)

    time_off_type: Mapped[TimeOffType] = mapped_column(SQLEnum(TimeOffType), nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Hours requested
    hours_requested: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    # For partial days
    start_time: Mapped[Optional[str]] = mapped_column(String(10))  # HH:MM format
    end_time: Mapped[Optional[str]] = mapped_column(String(10))

    reason: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[TimeOffStatus] = mapped_column(
        SQLEnum(TimeOffStatus), default=TimeOffStatus.PENDING
    )

    # Approval
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column()
    review_notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("customer_id", "request_number", name="uq_time_off_request_number"),
        Index("idx_time_off_requests_customer", "customer_id"),
        Index("idx_time_off_requests_employee", "employee_id"),
        Index("idx_time_off_requests_dates", "start_date", "end_date"),
        Index("idx_time_off_requests_status", "customer_id", "status"),
    )


class TimeOffBalance(Base):
    """Employee time off balance tracking."""
    __tablename__ = "time_off_balances"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time_off_type: Mapped[TimeOffType] = mapped_column(SQLEnum(TimeOffType), nullable=False)

    # Entitlements
    annual_entitlement: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    carryover_from_previous: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)

    # Usage
    hours_used: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    hours_pending: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)  # Approved but not yet taken

    # Adjustments
    adjustments: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)  # Manual adjustments

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("employee_id", "year", "time_off_type", name="uq_time_off_balance"),
        Index("idx_time_off_balances_employee", "employee_id"),
    )

    @property
    def available_balance(self) -> Decimal:
        """Calculate available balance."""
        return (
            self.annual_entitlement +
            self.carryover_from_previous +
            self.adjustments -
            self.hours_used -
            self.hours_pending
        )
