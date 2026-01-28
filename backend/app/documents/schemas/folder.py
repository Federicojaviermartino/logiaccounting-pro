"""Folder schemas."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class FolderCreate(BaseModel):
    """Create folder request."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None


class FolderUpdate(BaseModel):
    """Update folder request."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class FolderResponse(BaseModel):
    """Folder response."""
    id: UUID
    name: str
    description: Optional[str]
    parent_id: Optional[UUID]
    path: str
    depth: int
    color: Optional[str]
    icon: Optional[str]
    is_public: bool
    document_count: int
    total_size: int
    created_by: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class FolderTree(BaseModel):
    """Folder tree structure."""
    id: UUID
    name: str
    path: str
    children: List["FolderTree"] = []
    document_count: int = 0


class FolderContents(BaseModel):
    """Folder contents response."""
    folder: FolderResponse
    subfolders: List[FolderResponse]
    documents: List[dict]  # DocumentResponse
    breadcrumbs: List[dict]


class DocumentStats(BaseModel):
    """Document statistics."""
    total_documents: int
    total_size: int  # bytes
    documents_by_type: dict
    documents_by_status: dict
    recent_uploads: int
    storage_used_percent: float
