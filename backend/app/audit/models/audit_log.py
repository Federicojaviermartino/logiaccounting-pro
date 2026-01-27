"""Audit log models for tracking all system changes."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import String, Boolean, Integer, ForeignKey, Text, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    VOID = "void"
    ARCHIVE = "archive"
    RESTORE = "restore"
    DOWNLOAD = "download"


class AuditSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base):
    """Immutable audit log entry."""
    __tablename__ = "audit_logs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"))
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    user_email: Mapped[Optional[str]] = mapped_column(String(255))
    user_name: Mapped[Optional[str]] = mapped_column(String(200))
    user_role: Mapped[Optional[str]] = mapped_column(String(50))
    
    action: Mapped[AuditAction] = mapped_column(SQLEnum(AuditAction), nullable=False)
    severity: Mapped[AuditSeverity] = mapped_column(SQLEnum(AuditSeverity), default=AuditSeverity.LOW)
    
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))
    resource_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    description: Mapped[Optional[str]] = mapped_column(Text)
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    changed_fields: Mapped[Optional[list]] = mapped_column(JSONB)
    
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    request_id: Mapped[Optional[str]] = mapped_column(String(100))
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    
    endpoint: Mapped[Optional[str]] = mapped_column(String(255))
    http_method: Mapped[Optional[str]] = mapped_column(String(10))
    
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    
    __table_args__ = (
        Index("idx_audit_logs_customer", "customer_id"),
        Index("idx_audit_logs_timestamp", "timestamp"),
        Index("idx_audit_logs_user", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_severity", "severity"),
    )


class DataChangeLog(Base):
    """Field-level change tracking."""
    __tablename__ = "data_change_logs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    audit_log_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("audit_logs.id"), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    field_type: Mapped[Optional[str]] = mapped_column(String(50))
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_data_change_audit", "audit_log_id"),
        Index("idx_data_change_customer", "customer_id"),
        Index("idx_data_change_table", "table_name", "record_id"),
    )


class EntitySnapshot(Base):
    """Complete entity snapshots for point-in-time recovery."""
    __tablename__ = "entity_snapshots"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    audit_log_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("audit_logs.id"))
    
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(100))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    __table_args__ = (
        Index("idx_entity_snapshots_customer", "customer_id"),
        Index("idx_entity_snapshots_entity", "entity_type", "entity_id"),
    )
