"""Payroll run and pay period models."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text, Date,
    Numeric, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class PayPeriodStatus(str, Enum):
    OPEN = "open"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CLOSED = "closed"


class PayrollRunStatus(str, Enum):
    DRAFT = "draft"
    CALCULATING = "calculating"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PROCESSING_PAYMENTS = "processing_payments"
    COMPLETED = "completed"
    VOIDED = "voided"


class PayPeriod(Base):
    """Pay period definition."""
    __tablename__ = "pay_periods"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)

    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    pay_date: Mapped[date] = mapped_column(Date, nullable=False)

    frequency: Mapped[str] = mapped_column(String(20), nullable=False)

    status: Mapped[PayPeriodStatus] = mapped_column(
        SQLEnum(PayPeriodStatus), default=PayPeriodStatus.OPEN
    )

    total_gross: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_net: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_employer_taxes: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    employee_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    payroll_runs: Mapped[List["PayrollRun"]] = relationship("PayrollRun", back_populates="pay_period")

    __table_args__ = (
        UniqueConstraint("customer_id", "period_year", "period_number", "frequency", name="uq_pay_period"),
        Index("idx_pay_periods_customer", "customer_id"),
        Index("idx_pay_periods_dates", "start_date", "end_date"),
    )


class PayrollRun(Base):
    """Payroll run execution."""
    __tablename__ = "payroll_runs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    pay_period_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pay_periods.id"), nullable=False)

    run_number: Mapped[str] = mapped_column(String(30), nullable=False)
    run_type: Mapped[str] = mapped_column(String(20), default="regular")  # regular, bonus, correction, final

    status: Mapped[PayrollRunStatus] = mapped_column(
        SQLEnum(PayrollRunStatus), default=PayrollRunStatus.DRAFT
    )

    run_date: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    calculated_at: Mapped[Optional[datetime]] = mapped_column()
    approved_at: Mapped[Optional[datetime]] = mapped_column()
    completed_at: Mapped[Optional[datetime]] = mapped_column()

    total_gross_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_net_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_employer_taxes: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_employer_benefits: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)

    employee_count: Mapped[int] = mapped_column(Integer, default=0)

    approved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))

    journal_entry_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    pay_period: Mapped["PayPeriod"] = relationship("PayPeriod", back_populates="payroll_runs")
    payroll_lines: Mapped[List["PayrollLine"]] = relationship("PayrollLine", back_populates="payroll_run", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("customer_id", "run_number", name="uq_payroll_run_number"),
        Index("idx_payroll_runs_customer", "customer_id"),
        Index("idx_payroll_runs_period", "pay_period_id"),
        Index("idx_payroll_runs_status", "customer_id", "status"),
    )


class PayrollLine(Base):
    """Individual employee payroll line."""
    __tablename__ = "payroll_lines"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    payroll_run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    contract_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("employee_contracts.id"), nullable=False)

    employee_number: Mapped[str] = mapped_column(String(20), nullable=False)
    employee_name: Mapped[str] = mapped_column(String(200), nullable=False)

    regular_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    holiday_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    pto_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    sick_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)

    regular_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    overtime_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)

    regular_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    overtime_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    holiday_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    pto_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    sick_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    bonus: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    commission: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    other_earnings: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    gross_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    total_deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    federal_tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    state_tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    local_tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    social_security: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    medicare: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    net_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    employer_social_security: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    employer_medicare: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    employer_futa: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    employer_suta: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    employer_benefits: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    total_employer_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    ytd_gross: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    ytd_federal_tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    ytd_state_tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    ytd_social_security: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    ytd_medicare: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    ytd_net: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)

    payment_method: Mapped[str] = mapped_column(String(20), default="direct_deposit")  # direct_deposit, check
    payment_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processed, failed
    check_number: Mapped[Optional[str]] = mapped_column(String(20))

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    payroll_run: Mapped["PayrollRun"] = relationship("PayrollRun", back_populates="payroll_lines")
    deductions: Mapped[List["PayrollLineDeduction"]] = relationship("PayrollLineDeduction", back_populates="payroll_line", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("payroll_run_id", "employee_id", name="uq_payroll_line_employee"),
        Index("idx_payroll_lines_run", "payroll_run_id"),
        Index("idx_payroll_lines_employee", "employee_id"),
    )

    def calculate_gross(self) -> Decimal:
        """Calculate gross pay from components."""
        self.gross_pay = (
            self.regular_pay + self.overtime_pay + self.holiday_pay +
            self.pto_pay + self.sick_pay + self.bonus +
            self.commission + self.other_earnings
        )
        return self.gross_pay

    def calculate_net(self) -> Decimal:
        """Calculate net pay."""
        self.net_pay = self.gross_pay - self.total_deductions
        return self.net_pay


class PayrollLineDeduction(Base):
    """Individual deduction on a payroll line."""
    __tablename__ = "payroll_line_deductions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    payroll_line_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("payroll_lines.id", ondelete="CASCADE"), nullable=False)
    deduction_type_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("deduction_types.id"), nullable=False)

    deduction_code: Mapped[str] = mapped_column(String(20), nullable=False)
    deduction_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)

    employee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    employer_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    ytd_employee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    ytd_employer: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    payroll_line: Mapped["PayrollLine"] = relationship("PayrollLine", back_populates="deductions")

    __table_args__ = (
        Index("idx_payroll_line_deductions_line", "payroll_line_id"),
    )
