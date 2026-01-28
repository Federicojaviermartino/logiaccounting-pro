"""Document sharing schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ShareCreate(BaseModel):
    """Create share request."""
    shared_with_user_id: Optional[UUID] = None
    shared_with_email: Optional[str] = Field(None, max_length=255)
    permission: str = "view"
    expires_at: Optional[datetime] = None
    message: Optional[str] = None
    requires_password: bool = False
    password: Optional[str] = None
    allow_download: bool = True


class ShareResponse(BaseModel):
    """Share response."""
    id: UUID
    document_id: UUID
    shared_with_user_id: Optional[UUID]
    shared_with_email: Optional[str]
    permission: str
    expires_at: Optional[datetime]
    is_active: bool
    access_count: int
    last_accessed_at: Optional[datetime]
    shared_by: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class ShareLinkCreate(BaseModel):
    """Create share link request."""
    permission: str = "view"
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = Field(None, ge=1)
    requires_password: bool = False
    password: Optional[str] = None


class ShareLinkResponse(BaseModel):
    """Share link response."""
    id: UUID
    document_id: UUID
    token: str
    link: str
    permission: str
    expires_at: Optional[datetime]
    max_uses: Optional[int]
    use_count: int
    is_active: bool
    requires_password: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AccessLogResponse(BaseModel):
    """Access log response."""
    id: UUID
    document_id: UUID
    user_id: Optional[UUID]
    access_type: str
    ip_address: Optional[str]
    accessed_at: datetime
    
    class Config:
        from_attributes = True
