"""Document management models."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text, DateTime,
    Enum as SQLEnum, Index, UniqueConstraint, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentType(str, Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    PURCHASE_ORDER = "purchase_order"
    DELIVERY_NOTE = "delivery_note"
    QUOTE = "quote"
    REPORT = "report"
    STATEMENT = "statement"
    TAX_DOCUMENT = "tax_document"
    LEGAL = "legal"
    CORRESPONDENCE = "correspondence"
    OTHER = "other"


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Document(Base):
    """Main document entity."""
    __tablename__ = "documents"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    # Document identification
    document_number: Mapped[Optional[str]] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Classification
    document_type: Mapped[DocumentType] = mapped_column(SQLEnum(DocumentType), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(SQLEnum(DocumentStatus), default=DocumentStatus.DRAFT)
    
    # Categorization
    category_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("document_categories.id"))
    tags: Mapped[Optional[List]] = mapped_column(JSONB)
    
    # File information
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)  # bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA-256 hash
    
    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id"))
    
    # Related entities
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(100))  # invoice, project, etc.
    related_entity_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)  # Custom fields
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)  # OCR/extracted text
    
    # Document date (not upload date)
    document_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Access control
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Ownership
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("DocumentCategory", back_populates="documents")
    versions = relationship("Document", backref="parent", remote_side=[id])
    
    __table_args__ = (
        Index("idx_documents_customer", "customer_id"),
        Index("idx_documents_type", "document_type"),
        Index("idx_documents_status", "status"),
        Index("idx_documents_category", "category_id"),
        Index("idx_documents_related", "related_entity_type", "related_entity_id"),
        Index("idx_documents_created", "created_at"),
        UniqueConstraint("customer_id", "document_number", name="uq_document_number"),
    )


class DocumentCategory(Base):
    """Document categories for organization."""
    __tablename__ = "document_categories"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Hierarchy
    parent_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("document_categories.id"))
    path: Mapped[Optional[str]] = mapped_column(String(500))  # Materialized path
    
    # Settings
    default_retention_days: Mapped[Optional[int]] = mapped_column(Integer)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="category")
    children = relationship("DocumentCategory", backref="parent_category", remote_side=[id])
    
    __table_args__ = (
        UniqueConstraint("customer_id", "name", "parent_id", name="uq_category_name"),
        Index("idx_doc_categories_customer", "customer_id"),
    )


class DocumentVersion(Base):
    """Track document version history."""
    __tablename__ = "document_versions"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # File info at this version
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))
    
    # Changes
    change_summary: Mapped[Optional[str]] = mapped_column(Text)
    changes: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("document_id", "version", name="uq_document_version"),
        Index("idx_doc_versions_document", "document_id"),
    )
