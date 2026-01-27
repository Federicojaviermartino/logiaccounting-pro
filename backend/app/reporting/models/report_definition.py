"""Report definition and configuration models."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text,
    Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base


class ReportType(str, Enum):
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    TRIAL_BALANCE = "trial_balance"
    AR_AGING = "ar_aging"
    AP_AGING = "ap_aging"
    BUDGET_VS_ACTUAL = "budget_vs_actual"
    PAYROLL_SUMMARY = "payroll_summary"
    GENERAL_LEDGER = "general_ledger"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ReportDefinition(Base):
    """Saved report configuration."""
    __tablename__ = "report_definitions"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    report_type: Mapped[ReportType] = mapped_column(SQLEnum(ReportType), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    default_format: Mapped[ReportFormat] = mapped_column(SQLEnum(ReportFormat), default=ReportFormat.PDF)
    
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    schedules: Mapped[List["ReportSchedule"]] = relationship(
        "ReportSchedule", back_populates="report_definition", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint("customer_id", "code", name="uq_report_definition_code"),
        Index("idx_report_definitions_customer", "customer_id"),
    )


class ReportSchedule(Base):
    """Scheduled report execution."""
    __tablename__ = "report_schedules"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    report_definition_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("report_definitions.id", ondelete="CASCADE"), nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    frequency: Mapped[ReportFrequency] = mapped_column(SQLEnum(ReportFrequency), nullable=False)
    
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer)
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer)
    time_of_day: Mapped[str] = mapped_column(String(10), default="08:00")
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    output_format: Mapped[ReportFormat] = mapped_column(SQLEnum(ReportFormat), default=ReportFormat.PDF)
    email_recipients: Mapped[Optional[List]] = mapped_column(JSONB)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column()
    next_run_at: Mapped[Optional[datetime]] = mapped_column()
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    report_definition: Mapped["ReportDefinition"] = relationship("ReportDefinition", back_populates="schedules")
    
    __table_args__ = (
        Index("idx_report_schedules_definition", "report_definition_id"),
    )


class ReportExecution(Base):
    """Report execution history."""
    __tablename__ = "report_executions"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    report_definition_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("report_definitions.id"))
    
    report_type: Mapped[ReportType] = mapped_column(SQLEnum(ReportType), nullable=False)
    report_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column()
    
    status: Mapped[str] = mapped_column(String(20), default="running")
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    parameters: Mapped[Optional[dict]] = mapped_column(JSONB)
    output_format: Mapped[ReportFormat] = mapped_column(SQLEnum(ReportFormat))
    output_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    executed_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    __table_args__ = (
        Index("idx_report_executions_customer", "customer_id"),
    )
