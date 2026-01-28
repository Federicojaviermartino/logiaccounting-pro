"""Document sharing and access models."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text, DateTime,
    Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SharePermission(str, Enum):
    VIEW = "view"
    DOWNLOAD = "download"
    EDIT = "edit"
    FULL = "full"


class DocumentShare(Base):
    """Document sharing with users."""
    __tablename__ = "document_shares"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Share with user
    shared_with_user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    shared_with_email: Mapped[Optional[str]] = mapped_column(String(255))  # External share
    
    # Permissions
    permission: Mapped[SharePermission] = mapped_column(SQLEnum(SharePermission), default=SharePermission.VIEW)
    
    # Validity
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Access tracking
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Share settings
    requires_password: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    allow_download: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Sharing info
    shared_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_doc_shares_document", "document_id"),
        Index("idx_doc_shares_user", "shared_with_user_id"),
    )


class DocumentShareLink(Base):
    """Public share links for documents."""
    __tablename__ = "document_share_links"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Link token
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    # Permissions
    permission: Mapped[SharePermission] = mapped_column(SQLEnum(SharePermission), default=SharePermission.VIEW)
    
    # Validity
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    max_uses: Mapped[Optional[int]] = mapped_column(Integer)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Security
    requires_password: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_share_links_document", "document_id"),
        Index("idx_share_links_token", "token"),
    )


class DocumentAccessLog(Base):
    """Log document access for audit."""
    __tablename__ = "document_access_logs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Who accessed
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    share_link_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("document_share_links.id"))
    
    # Access type
    access_type: Mapped[str] = mapped_column(String(20), nullable=False)  # view, download, edit, share
    
    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    accessed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_doc_access_document", "document_id"),
        Index("idx_doc_access_user", "user_id"),
        Index("idx_doc_access_date", "accessed_at"),
    )
