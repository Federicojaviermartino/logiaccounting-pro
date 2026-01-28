"""Document schemas."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class DocumentUpload(BaseModel):
    """Document upload request."""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    document_type: str
    category_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    document_date: Optional[datetime] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None
    is_confidential: bool = False
    metadata: Optional[dict] = None


class DocumentUpdate(BaseModel):
    """Document update request."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    document_type: Optional[str] = None
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    document_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_confidential: Optional[bool] = None
    metadata: Optional[dict] = None


class DocumentResponse(BaseModel):
    """Document response."""
    id: UUID
    document_number: Optional[str]
    title: str
    description: Optional[str]
    document_type: str
    status: str
    category_id: Optional[UUID]
    tags: Optional[List[str]]
    file_name: str
    file_size: int
    mime_type: str
    version: int
    document_date: Optional[datetime]
    expiry_date: Optional[datetime]
    is_confidential: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentDetail(DocumentResponse):
    """Detailed document response."""
    file_path: str
    file_hash: Optional[str]
    is_latest: bool
    parent_id: Optional[UUID]
    related_entity_type: Optional[str]
    related_entity_id: Optional[UUID]
    metadata: Optional[dict]
    extracted_text: Optional[str]
    is_public: bool
    category_name: Optional[str] = None
    folder_names: Optional[List[str]] = None
    version_count: int = 1


class DocumentFilter(BaseModel):
    """Document filter parameters."""
    search: Optional[str] = None
    document_type: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    created_by: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_confidential: Optional[bool] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None


class DocumentVersionResponse(BaseModel):
    """Document version response."""
    id: UUID
    document_id: UUID
    version: int
    file_name: str
    file_size: int
    change_summary: Optional[str]
    created_by: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    """Create category request."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = None
    parent_id: Optional[UUID] = None
    default_retention_days: Optional[int] = Field(None, ge=1)


class CategoryResponse(BaseModel):
    """Category response."""
    id: UUID
    name: str
    description: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    parent_id: Optional[UUID]
    path: Optional[str]
    is_system: bool
    is_active: bool
    document_count: int = 0
    
    class Config:
        from_attributes = True
