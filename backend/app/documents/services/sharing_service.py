"""Document sharing service."""
import secrets
import hashlib
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.documents.models.sharing import (
    DocumentShare, DocumentShareLink, DocumentAccessLog, SharePermission
)
from app.documents.schemas.sharing import (
    ShareCreate, ShareLinkCreate, ShareResponse, ShareLinkResponse
)


class SharingService:
    """Service for document sharing."""
    
    BASE_URL = "https://app.example.com"  # Configure in settings
    
    def __init__(self, db: Session):
        self.db = db
    
    async def share_document(
        self,
        document_id: UUID,
        user_id: UUID,
        data: ShareCreate
    ) -> DocumentShare:
        """Share document with user or email."""
        password_hash = None
        if data.requires_password and data.password:
            password_hash = hashlib.sha256(data.password.encode()).hexdigest()
        
        share = DocumentShare(
            id=uuid4(),
            document_id=document_id,
            shared_with_user_id=data.shared_with_user_id,
            shared_with_email=data.shared_with_email,
            permission=SharePermission(data.permission),
            expires_at=data.expires_at,
            requires_password=data.requires_password,
            password_hash=password_hash,
            allow_download=data.allow_download,
            shared_by=user_id,
            message=data.message
        )
        
        self.db.add(share)
        self.db.commit()
        self.db.refresh(share)
        
        return share
    
    async def create_share_link(
        self,
        document_id: UUID,
        user_id: UUID,
        data: ShareLinkCreate
    ) -> DocumentShareLink:
        """Create a public share link."""
        token = secrets.token_urlsafe(32)
        
        password_hash = None
        if data.requires_password and data.password:
            password_hash = hashlib.sha256(data.password.encode()).hexdigest()
        
        share_link = DocumentShareLink(
            id=uuid4(),
            document_id=document_id,
            token=token,
            permission=SharePermission(data.permission),
            expires_at=data.expires_at,
            max_uses=data.max_uses,
            requires_password=data.requires_password,
            password_hash=password_hash,
            created_by=user_id
        )
        
        self.db.add(share_link)
        self.db.commit()
        self.db.refresh(share_link)
        
        return share_link
    
    async def get_document_shares(
        self,
        document_id: UUID
    ) -> List[DocumentShare]:
        """Get all shares for a document."""
        query = select(DocumentShare).where(
            DocumentShare.document_id == document_id,
            DocumentShare.is_active == True
        ).order_by(desc(DocumentShare.created_at))
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    async def get_document_share_links(
        self,
        document_id: UUID
    ) -> List[DocumentShareLink]:
        """Get all share links for a document."""
        query = select(DocumentShareLink).where(
            DocumentShareLink.document_id == document_id,
            DocumentShareLink.is_active == True
        ).order_by(desc(DocumentShareLink.created_at))
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    async def get_share_link_by_token(
        self,
        token: str
    ) -> Optional[DocumentShareLink]:
        """Get share link by token."""
        query = select(DocumentShareLink).where(
            DocumentShareLink.token == token,
            DocumentShareLink.is_active == True
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def validate_share_link(
        self,
        token: str,
        password: Optional[str] = None
    ) -> tuple[bool, Optional[DocumentShareLink], str]:
        """Validate share link and return status."""
        share_link = await self.get_share_link_by_token(token)
        
        if not share_link:
            return False, None, "Share link not found"
        
        if share_link.expires_at and share_link.expires_at < datetime.utcnow():
            return False, share_link, "Share link has expired"
        
        if share_link.max_uses and share_link.use_count >= share_link.max_uses:
            return False, share_link, "Share link has reached maximum uses"
        
        if share_link.requires_password:
            if not password:
                return False, share_link, "Password required"
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != share_link.password_hash:
                return False, share_link, "Invalid password"
        
        return True, share_link, "Valid"
    
    async def record_link_access(
        self,
        share_link: DocumentShareLink
    ):
        """Record share link access."""
        share_link.use_count += 1
        self.db.commit()
    
    async def revoke_share(
        self,
        share_id: UUID
    ) -> bool:
        """Revoke a document share."""
        share = self.db.execute(
            select(DocumentShare).where(DocumentShare.id == share_id)
        ).scalar_one_or_none()
        
        if share:
            share.is_active = False
            self.db.commit()
            return True
        return False
    
    async def revoke_share_link(
        self,
        link_id: UUID
    ) -> bool:
        """Revoke a share link."""
        link = self.db.execute(
            select(DocumentShareLink).where(DocumentShareLink.id == link_id)
        ).scalar_one_or_none()
        
        if link:
            link.is_active = False
            self.db.commit()
            return True
        return False
    
    async def log_access(
        self,
        document_id: UUID,
        access_type: str,
        user_id: Optional[UUID] = None,
        share_link_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> DocumentAccessLog:
        """Log document access."""
        log = DocumentAccessLog(
            id=uuid4(),
            document_id=document_id,
            user_id=user_id,
            share_link_id=share_link_id,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log)
        self.db.commit()
        
        return log
    
    async def get_access_logs(
        self,
        document_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[DocumentAccessLog], int]:
        """Get access logs for a document."""
        query = select(DocumentAccessLog).where(
            DocumentAccessLog.document_id == document_id
        )
        
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()
        
        query = query.order_by(desc(DocumentAccessLog.accessed_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = self.db.execute(query)
        logs = result.scalars().all()
        
        return logs, total
    
    def get_share_link_url(self, token: str) -> str:
        """Generate full share link URL."""
        return f"{self.BASE_URL}/shared/{token}"
