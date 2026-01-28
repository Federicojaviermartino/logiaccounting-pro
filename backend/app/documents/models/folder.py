"""Document folder/directory models."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Boolean, Integer, ForeignKey, Text, DateTime, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Folder(Base):
    """Folder structure for organizing documents."""
    __tablename__ = "folders"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Hierarchy
    parent_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("folders.id"))
    path: Mapped[str] = mapped_column(String(1000), nullable=False)  # Full path like /root/subfolder/folder
    depth: Mapped[int] = mapped_column(Integer, default=0)
    
    # Metadata
    color: Mapped[Optional[str]] = mapped_column(String(7))
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Access
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Stats (denormalized for performance)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    total_size: Mapped[int] = mapped_column(Integer, default=0)  # bytes
    
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    children = relationship("Folder", backref="parent", remote_side=[id])
    
    __table_args__ = (
        UniqueConstraint("customer_id", "path", name="uq_folder_path"),
        Index("idx_folders_customer", "customer_id"),
        Index("idx_folders_parent", "parent_id"),
    )


class DocumentFolder(Base):
    """Many-to-many relationship between documents and folders."""
    __tablename__ = "document_folders"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    folder_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("folders.id"), nullable=False)
    
    added_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("document_id", "folder_id", name="uq_document_folder"),
        Index("idx_doc_folders_document", "document_id"),
        Index("idx_doc_folders_folder", "folder_id"),
    )
