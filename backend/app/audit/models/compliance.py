"""Compliance rules and retention policies."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import String, Boolean, Integer, ForeignKey, Text, DateTime, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ComplianceStandard(str, Enum):
    SOX = "sox"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    CUSTOM = "custom"


class RetentionPolicy(Base):
    """Data retention policies."""
    __tablename__ = "retention_policies"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"))
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    archive_after_days: Mapped[Optional[int]] = mapped_column(Integer)
    action_on_expiry: Mapped[str] = mapped_column(String(20), default="archive")
    
    compliance_standard: Mapped[Optional[ComplianceStandard]] = mapped_column(SQLEnum(ComplianceStandard))
    regulation_reference: Mapped[Optional[str]] = mapped_column(String(200))
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("customer_id", "name", name="uq_retention_policy_name"),
        Index("idx_retention_policies_customer", "customer_id"),
    )


class ComplianceRule(Base):
    """Compliance rules and checks."""
    __tablename__ = "compliance_rules"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"))
    
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    compliance_standard: Mapped[ComplianceStandard] = mapped_column(SQLEnum(ComplianceStandard), nullable=False)
    category: Mapped[str] = mapped_column(String(50))
    
    rule_type: Mapped[str] = mapped_column(String(30), nullable=False)
    rule_config: Mapped[Optional[dict]] = mapped_column(JSONB)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    
    alert_on_violation: Mapped[bool] = mapped_column(Boolean, default=True)
    block_on_violation: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_users: Mapped[Optional[List]] = mapped_column(JSONB)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("customer_id", "code", name="uq_compliance_rule_code"),
        Index("idx_compliance_rules_customer", "customer_id"),
        Index("idx_compliance_rules_standard", "compliance_standard"),
    )


class ComplianceViolation(Base):
    """Recorded compliance violations."""
    __tablename__ = "compliance_violations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    rule_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("compliance_rules.id"), nullable=False)
    
    violation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    resource_type: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    audit_log_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("audit_logs.id"))
    
    status: Mapped[str] = mapped_column(String(20), default="open")
    
    resolved_at: Mapped[Optional[datetime]] = mapped_column()
    resolved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    
    detected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_compliance_violations_customer", "customer_id"),
        Index("idx_compliance_violations_rule", "rule_id"),
        Index("idx_compliance_violations_status", "status"),
    )


class AccessLog(Base):
    """Sensitive data access logging."""
    __tablename__ = "access_logs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    access_type: Mapped[str] = mapped_column(String(20), nullable=False)
    data_classification: Mapped[str] = mapped_column(String(30), default="internal")
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_financial: Mapped[bool] = mapped_column(Boolean, default=False)
    
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    access_reason: Mapped[Optional[str]] = mapped_column(String(500))
    
    accessed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_access_logs_customer", "customer_id"),
        Index("idx_access_logs_user", "user_id"),
        Index("idx_access_logs_resource", "resource_type", "resource_id"),
        Index("idx_access_logs_accessed", "accessed_at"),
    )
