# LogiAccounting Pro - Phase 13 Tasks Part 1

## DATABASE MODELS & STORAGE SERVICE

---

## TASK 1: DATABASE MODELS

### 1.1 Document Category Model

**File:** `backend/app/documents/models/document_category.py`

```python
"""
Document Category Model
Hierarchical folder structure for documents
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid
import re


class DocumentCategory(db.Model):
    """Hierarchical document category (folder)"""
    
    __tablename__ = 'document_categories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    parent_id = Column(UUID(as_uuid=True), db.ForeignKey('document_categories.id'), nullable=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    description = Column(Text)
    color = Column(String(7), default='#3B82F6')
    icon = Column(String(50), default='folder')
    
    # Settings
    auto_categorize = Column(Boolean, default=False)
    retention_days = Column(Integer, nullable=True)  # NULL = forever
    
    # Hierarchy (materialized path)
    path = Column(String(1000))  # /parent-slug/child-slug/grandchild-slug
    level = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = relationship('DocumentCategory', remote_side=[id], backref='children')
    documents = relationship('Document', back_populates='category')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'parent_id', 'slug', name='uq_category_slug'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.slug:
            self.slug = self.generate_slug(self.name)
    
    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-safe slug from name"""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')
    
    def update_path(self):
        """Update materialized path based on parent"""
        if self.parent:
            self.path = f"{self.parent.path}/{self.slug}"
            self.level = self.parent.level + 1
        else:
            self.path = f"/{self.slug}"
            self.level = 0
    
    def get_ancestors(self) -> List['DocumentCategory']:
        """Get all ancestor categories"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
    
    def get_descendants(self) -> List['DocumentCategory']:
        """Get all descendant categories"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def get_document_count(self, include_descendants: bool = False) -> int:
        """Count documents in this category"""
        from app.documents.models.document import Document
        
        if include_descendants:
            # Count documents in this category and all descendants
            category_ids = [self.id] + [d.id for d in self.get_descendants()]
            return Document.query.filter(
                Document.category_id.in_(category_ids),
                Document.status != 'deleted'
            ).count()
        else:
            return Document.query.filter(
                Document.category_id == self.id,
                Document.status != 'deleted'
            ).count()
    
    @classmethod
    def get_tree(cls, organization_id: str) -> List[Dict[str, Any]]:
        """Get full category tree for organization"""
        categories = cls.query.filter(
            cls.organization_id == organization_id
        ).order_by(cls.path).all()
        
        # Build tree structure
        tree = []
        category_map = {}
        
        for cat in categories:
            node = cat.to_dict()
            node['children'] = []
            category_map[str(cat.id)] = node
            
            if cat.parent_id:
                parent_node = category_map.get(str(cat.parent_id))
                if parent_node:
                    parent_node['children'].append(node)
            else:
                tree.append(node)
        
        return tree
    
    def to_dict(self, include_counts: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'path': self.path,
            'level': self.level,
            'auto_categorize': self.auto_categorize,
            'retention_days': self.retention_days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_counts:
            data['document_count'] = self.get_document_count()
            data['total_count'] = self.get_document_count(include_descendants=True)
        
        return data
    
    def save(self):
        """Save with path update"""
        self.update_path()
        db.session.add(self)
        db.session.commit()
        
        # Update children paths if needed
        for child in self.children:
            child.save()
        
        return self


class DocumentTag(db.Model):
    """Document tag for classification"""
    
    __tablename__ = 'document_tags'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    color = Column(String(7), default='#6B7280')
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'slug', name='uq_tag_slug'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.slug:
            self.slug = DocumentCategory.generate_slug(self.name)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'name': self.name,
            'slug': self.slug,
            'color': self.color,
        }
```

### 1.2 Main Document Model

**File:** `backend/app/documents/models/document.py`

```python
"""
Document Model
Core document entity with metadata and relationships
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy import Index
from app.extensions import db
import uuid
import hashlib


class Document(db.Model):
    """Main document entity"""
    
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    
    # Basic Info
    name = Column(String(500), nullable=False)
    description = Column(Text)
    
    # File Info
    original_filename = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    
    # Storage
    storage_provider = Column(String(20), nullable=False)  # 's3', 'azure', 'gcs', 'local'
    storage_bucket = Column(String(255), nullable=False)
    storage_key = Column(String(500), nullable=False)
    storage_url = Column(Text)
    
    # Thumbnails
    thumbnail_url = Column(Text)
    preview_url = Column(Text)
    
    # Classification
    category_id = Column(UUID(as_uuid=True), db.ForeignKey('document_categories.id'))
    document_type = Column(String(50))  # 'invoice', 'receipt', 'contract', etc.
    
    # OCR & Extraction
    ocr_status = Column(String(20), default='pending')  # pending, processing, completed, failed, skipped
    ocr_text = Column(Text)
    ocr_confidence = Column(db.Numeric(5, 2))
    ocr_language = Column(String(10))
    ocr_completed_at = Column(db.DateTime)
    
    # AI Extraction
    extraction_status = Column(String(20), default='pending')
    extracted_data = Column(JSONB, default=dict)
    extraction_confidence = Column(db.Numeric(5, 2))
    extraction_completed_at = Column(db.DateTime)
    
    # AI Classification
    ai_category_suggestion = Column(String(100))
    ai_type_suggestion = Column(String(50))
    ai_confidence = Column(db.Numeric(5, 2))
    ai_tags = Column(ARRAY(String))
    
    # Relationships to other entities
    related_entity_type = Column(String(50))  # 'invoice', 'transaction', 'project', etc.
    related_entity_id = Column(UUID(as_uuid=True))
    
    # Status
    status = Column(String(20), default='processing')  # uploading, processing, active, archived, deleted
    
    # Versioning
    current_version = Column(Integer, default=1)
    version_count = Column(Integer, default=1)
    
    # Permissions
    visibility = Column(String(20), default='private')  # private, organization, public
    owner_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Signatures
    requires_signature = Column(Boolean, default=False)
    signature_status = Column(String(20))  # pending, partial, completed
    
    # Timestamps
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived_at = Column(db.DateTime)
    deleted_at = Column(db.DateTime)
    
    # Full-text search vector
    search_vector = Column(TSVECTOR)
    
    # Relationships
    category = relationship('DocumentCategory', back_populates='documents')
    owner = relationship('User', backref='documents')
    versions = relationship('DocumentVersion', back_populates='document', order_by='DocumentVersion.version_number.desc()')
    shares = relationship('DocumentShare', back_populates='document', cascade='all, delete-orphan')
    comments = relationship('DocumentComment', back_populates='document', cascade='all, delete-orphan')
    signatures = relationship('DocumentSignature', back_populates='document', cascade='all, delete-orphan')
    tags = relationship('DocumentTag', secondary='document_tag_assignments', backref='documents')
    activity_logs = relationship('DocumentActivityLog', back_populates='document', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_documents_org', 'organization_id'),
        Index('idx_documents_category', 'category_id'),
        Index('idx_documents_status', 'status'),
        Index('idx_documents_type', 'document_type'),
        Index('idx_documents_entity', 'related_entity_type', 'related_entity_id'),
        Index('idx_documents_owner', 'owner_id'),
        Index('idx_documents_search', 'search_vector', postgresql_using='gin'),
    )
    
    @staticmethod
    def calculate_hash(file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def update_search_vector(self):
        """Update full-text search vector"""
        # Combine searchable fields
        searchable_parts = [
            self.name or '',
            self.description or '',
            self.original_filename or '',
            self.ocr_text or '',
        ]
        
        # Add tags
        if self.ai_tags:
            searchable_parts.extend(self.ai_tags)
        
        searchable_text = ' '.join(searchable_parts)
        
        # Update using PostgreSQL to_tsvector
        from sqlalchemy import func
        self.search_vector = func.to_tsvector('english', searchable_text)
    
    def get_download_url(self, expires_in: int = 3600) -> str:
        """Get signed download URL"""
        from app.documents.services.storage_service import StorageService
        
        storage = StorageService.get_provider(self.storage_provider)
        return storage.get_signed_url(
            bucket=self.storage_bucket,
            key=self.storage_key,
            expires_in=expires_in
        )
    
    def create_version(self, changed_by_id: str, change_summary: str = None):
        """Create a new version from current state"""
        from app.documents.models.document_version import DocumentVersion
        
        version = DocumentVersion(
            document_id=self.id,
            version_number=self.current_version,
            original_filename=self.original_filename,
            mime_type=self.mime_type,
            file_size=self.file_size,
            file_hash=self.file_hash,
            storage_key=self.storage_key,
            storage_url=self.storage_url,
            change_summary=change_summary,
            changed_by=changed_by_id,
        )
        
        db.session.add(version)
        
        self.current_version += 1
        self.version_count += 1
        
        return version
    
    def soft_delete(self, deleted_by_id: str = None):
        """Soft delete document"""
        self.status = 'deleted'
        self.deleted_at = datetime.utcnow()
        
        self.log_activity('deleted', deleted_by_id)
    
    def archive(self, archived_by_id: str = None):
        """Archive document"""
        self.status = 'archived'
        self.archived_at = datetime.utcnow()
        
        self.log_activity('archived', archived_by_id)
    
    def restore(self, restored_by_id: str = None):
        """Restore deleted/archived document"""
        self.status = 'active'
        self.deleted_at = None
        self.archived_at = None
        
        self.log_activity('restored', restored_by_id)
    
    def log_activity(
        self, 
        action: str, 
        user_id: str = None,
        details: Dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Log document activity"""
        from app.documents.models.document_activity import DocumentActivityLog
        
        log = DocumentActivityLog(
            document_id=self.id,
            user_id=user_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        db.session.add(log)
    
    def to_dict(self, include_url: bool = False, include_details: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'organization_id': str(self.organization_id),
            'name': self.name,
            'description': self.description,
            'original_filename': self.original_filename,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'document_type': self.document_type,
            'status': self.status,
            'visibility': self.visibility,
            'current_version': self.current_version,
            'version_count': self.version_count,
            'thumbnail_url': self.thumbnail_url,
            'category_id': str(self.category_id) if self.category_id else None,
            'category': self.category.to_dict() if self.category else None,
            'owner_id': str(self.owner_id) if self.owner_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Include tags
        if self.tags:
            data['tags'] = [t.to_dict() for t in self.tags]
        
        # Include download URL if requested
        if include_url:
            data['download_url'] = self.get_download_url()
            data['preview_url'] = self.preview_url
        
        # Include detailed info
        if include_details:
            data['file_hash'] = self.file_hash
            data['ocr_status'] = self.ocr_status
            data['ocr_text'] = self.ocr_text[:500] if self.ocr_text else None  # Truncate
            data['extraction_status'] = self.extraction_status
            data['extracted_data'] = self.extracted_data
            data['ai_category_suggestion'] = self.ai_category_suggestion
            data['ai_type_suggestion'] = self.ai_type_suggestion
            data['ai_tags'] = self.ai_tags
            data['requires_signature'] = self.requires_signature
            data['signature_status'] = self.signature_status
            data['related_entity_type'] = self.related_entity_type
            data['related_entity_id'] = str(self.related_entity_id) if self.related_entity_id else None
        
        return data
    
    def __repr__(self):
        return f'<Document {self.name}>'


# Tag assignment junction table
document_tag_assignments = db.Table(
    'document_tag_assignments',
    Column('document_id', UUID(as_uuid=True), db.ForeignKey('documents.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), db.ForeignKey('document_tags.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_by', UUID(as_uuid=True), db.ForeignKey('users.id')),
    Column('assigned_at', db.DateTime, default=datetime.utcnow),
)
```

### 1.3 Document Version Model

**File:** `backend/app/documents/models/document_version.py`

```python
"""
Document Version Model
Version history for documents
"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, String, Integer, BigInteger, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class DocumentVersion(db.Model):
    """Document version for history tracking"""
    
    __tablename__ = 'document_versions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    
    version_number = Column(Integer, nullable=False)
    
    # File info snapshot
    original_filename = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(64), nullable=False)
    
    # Storage location
    storage_key = Column(String(500), nullable=False)
    storage_url = Column(Text)
    
    # Change info
    change_summary = Column(Text)
    changed_by = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Timestamp
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship('Document', back_populates='versions')
    changed_by_user = relationship('User', foreign_keys=[changed_by])
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('document_id', 'version_number', name='uq_document_version'),
    )
    
    def get_download_url(self, expires_in: int = 3600) -> str:
        """Get signed download URL for this version"""
        from app.documents.services.storage_service import StorageService
        
        document = self.document
        storage = StorageService.get_provider(document.storage_provider)
        
        return storage.get_signed_url(
            bucket=document.storage_bucket,
            key=self.storage_key,
            expires_in=expires_in
        )
    
    def to_dict(self, include_url: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'version_number': self.version_number,
            'original_filename': self.original_filename,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'change_summary': self.change_summary,
            'changed_by': str(self.changed_by) if self.changed_by else None,
            'changed_by_name': self.changed_by_user.name if self.changed_by_user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_url:
            data['download_url'] = self.get_download_url()
        
        return data
```

### 1.4 Document Share Model

**File:** `backend/app/documents/models/document_share.py`

```python
"""
Document Share Model
Sharing and permissions
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid
import secrets


class DocumentShare(db.Model):
    """Document sharing permissions"""
    
    __tablename__ = 'document_shares'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    
    # Share target (one of these)
    shared_with_user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    shared_with_email = Column(String(255))  # External share
    
    # Permissions
    permission = Column(String(20), nullable=False, default='view')  # view, comment, edit, admin
    can_download = Column(Boolean, default=True)
    can_share = Column(Boolean, default=False)
    
    # Link sharing
    share_token = Column(String(64), unique=True)
    is_link_share = Column(Boolean, default=False)
    link_password_hash = Column(String(255))
    
    # Expiration
    expires_at = Column(db.DateTime)
    
    # Metadata
    shared_by = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    created_at = Column(db.DateTime, default=datetime.utcnow)
    last_accessed_at = Column(db.DateTime)
    access_count = Column(Integer, default=0)
    
    # Relationships
    document = relationship('Document', back_populates='shares')
    shared_with_user = relationship('User', foreign_keys=[shared_with_user_id])
    shared_by_user = relationship('User', foreign_keys=[shared_by])
    
    @classmethod
    def create_link_share(
        cls,
        document_id: str,
        shared_by: str,
        permission: str = 'view',
        password: str = None,
        expires_at: datetime = None,
        can_download: bool = True
    ) -> 'DocumentShare':
        """Create a link-based share"""
        share = cls(
            document_id=document_id,
            share_token=secrets.token_urlsafe(32),
            is_link_share=True,
            shared_by=shared_by,
            permission=permission,
            can_download=can_download,
            expires_at=expires_at,
        )
        
        if password:
            from werkzeug.security import generate_password_hash
            share.link_password_hash = generate_password_hash(password)
        
        db.session.add(share)
        db.session.commit()
        
        return share
    
    @classmethod
    def create_user_share(
        cls,
        document_id: str,
        shared_with_user_id: str,
        shared_by: str,
        permission: str = 'view',
        can_download: bool = True,
        can_share: bool = False
    ) -> 'DocumentShare':
        """Create a user-based share"""
        # Check if share already exists
        existing = cls.query.filter(
            cls.document_id == document_id,
            cls.shared_with_user_id == shared_with_user_id
        ).first()
        
        if existing:
            existing.permission = permission
            existing.can_download = can_download
            existing.can_share = can_share
            db.session.commit()
            return existing
        
        share = cls(
            document_id=document_id,
            shared_with_user_id=shared_with_user_id,
            shared_by=shared_by,
            permission=permission,
            can_download=can_download,
            can_share=can_share,
        )
        
        db.session.add(share)
        db.session.commit()
        
        return share
    
    def verify_password(self, password: str) -> bool:
        """Verify link password"""
        if not self.link_password_hash:
            return True
        
        from werkzeug.security import check_password_hash
        return check_password_hash(self.link_password_hash, password)
    
    def is_expired(self) -> bool:
        """Check if share has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def record_access(self):
        """Record access to shared document"""
        self.last_accessed_at = datetime.utcnow()
        self.access_count += 1
        db.session.commit()
    
    def get_share_url(self) -> Optional[str]:
        """Get shareable URL"""
        if not self.share_token:
            return None
        
        import os
        base_url = os.getenv('FRONTEND_URL', '')
        return f"{base_url}/share/{self.share_token}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'permission': self.permission,
            'can_download': self.can_download,
            'can_share': self.can_share,
            'is_link_share': self.is_link_share,
            'has_password': bool(self.link_password_hash),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'access_count': self.access_count,
        }
        
        if self.shared_with_user_id:
            data['shared_with'] = {
                'type': 'user',
                'user_id': str(self.shared_with_user_id),
                'user_name': self.shared_with_user.name if self.shared_with_user else None,
                'user_email': self.shared_with_user.email if self.shared_with_user else None,
            }
        elif self.shared_with_email:
            data['shared_with'] = {
                'type': 'email',
                'email': self.shared_with_email,
            }
        elif self.is_link_share:
            data['shared_with'] = {
                'type': 'link',
            }
            data['share_url'] = self.get_share_url()
        
        if self.shared_by_user:
            data['shared_by'] = {
                'user_id': str(self.shared_by),
                'user_name': self.shared_by_user.name,
            }
        
        return data
```

### 1.5 Document Comment Model

**File:** `backend/app/documents/models/document_comment.py`

```python
"""
Document Comment Model
Comments and annotations on documents
"""

from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class DocumentComment(db.Model):
    """Comment on a document"""
    
    __tablename__ = 'document_comments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    parent_id = Column(UUID(as_uuid=True), db.ForeignKey('document_comments.id'))  # For replies
    
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    
    # Position for annotations
    page_number = Column(Integer)
    position_x = Column(Numeric(10, 4))
    position_y = Column(Numeric(10, 4))
    annotation_type = Column(String(20))  # highlight, note, drawing
    annotation_data = Column(JSONB)  # Additional annotation data
    
    # Status
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    resolved_at = Column(db.DateTime)
    
    # Timestamps
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship('Document', back_populates='comments')
    user = relationship('User', foreign_keys=[user_id], backref='document_comments')
    resolved_by_user = relationship('User', foreign_keys=[resolved_by])
    parent = relationship('DocumentComment', remote_side=[id], backref='replies')
    
    def resolve(self, resolved_by_id: str):
        """Mark comment as resolved"""
        self.is_resolved = True
        self.resolved_by = resolved_by_id
        self.resolved_at = datetime.utcnow()
        db.session.commit()
    
    def unresolve(self):
        """Mark comment as unresolved"""
        self.is_resolved = False
        self.resolved_by = None
        self.resolved_at = None
        db.session.commit()
    
    def get_replies(self) -> List['DocumentComment']:
        """Get all replies to this comment"""
        return DocumentComment.query.filter(
            DocumentComment.parent_id == self.id
        ).order_by(DocumentComment.created_at.asc()).all()
    
    def to_dict(self, include_replies: bool = True) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'user': {
                'id': str(self.user_id),
                'name': self.user.name if self.user else None,
                'avatar_url': self.user.avatar_url if self.user else None,
            },
            'content': self.content,
            'page_number': self.page_number,
            'position': {
                'x': float(self.position_x) if self.position_x else None,
                'y': float(self.position_y) if self.position_y else None,
            } if self.position_x else None,
            'annotation_type': self.annotation_type,
            'annotation_data': self.annotation_data,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if self.resolved_by_user:
            data['resolved_by'] = {
                'id': str(self.resolved_by),
                'name': self.resolved_by_user.name,
            }
        
        if include_replies and not self.parent_id:
            data['replies'] = [r.to_dict(include_replies=False) for r in self.get_replies()]
        
        return data
```

### 1.6 Document Activity Log Model

**File:** `backend/app/documents/models/document_activity.py`

```python
"""
Document Activity Log Model
Audit trail for document actions
"""

from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class DocumentActivityLog(db.Model):
    """Activity log for document audit trail"""
    
    __tablename__ = 'document_activity_log'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), db.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    action = Column(String(50), nullable=False)
    # Actions: created, viewed, downloaded, updated, versioned, shared, unshared,
    #          commented, signed, archived, deleted, restored, processed
    
    details = Column(JSONB, default=dict)
    
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship('Document', back_populates='activity_logs')
    user = relationship('User', backref='document_activities')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_activity_document', 'document_id'),
        db.Index('idx_activity_created', 'created_at'),
        db.Index('idx_activity_user', 'user_id'),
        db.Index('idx_activity_action', 'action'),
    )
    
    @classmethod
    def log(
        cls,
        document_id: str,
        action: str,
        user_id: str = None,
        details: Dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> 'DocumentActivityLog':
        """Create activity log entry"""
        log = cls(
            document_id=document_id,
            user_id=user_id,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        db.session.add(log)
        db.session.commit()
        
        return log
    
    @classmethod
    def get_document_history(
        cls,
        document_id: str,
        limit: int = 50,
        actions: List[str] = None
    ) -> List['DocumentActivityLog']:
        """Get activity history for a document"""
        query = cls.query.filter(cls.document_id == document_id)
        
        if actions:
            query = query.filter(cls.action.in_(actions))
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_user_activity(
        cls,
        user_id: str,
        limit: int = 50
    ) -> List['DocumentActivityLog']:
        """Get activity history for a user"""
        return cls.query.filter(
            cls.user_id == user_id
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'user': {
                'id': str(self.user_id) if self.user_id else None,
                'name': self.user.name if self.user else 'System',
            },
            'action': self.action,
            'details': self.details,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
```

---

## TASK 2: STORAGE SERVICE ABSTRACTION

### 2.1 Base Storage Provider

**File:** `backend/app/documents/services/storage/__init__.py`

```python
"""
Storage Service Module
Cloud storage abstraction layer
"""

from .base import StorageProvider, StorageConfig
from .s3_provider import S3StorageProvider
from .azure_provider import AzureStorageProvider
from .gcs_provider import GCSStorageProvider
from .local_provider import LocalStorageProvider

__all__ = [
    'StorageProvider',
    'StorageConfig',
    'S3StorageProvider',
    'AzureStorageProvider',
    'GCSStorageProvider',
    'LocalStorageProvider',
    'get_storage_provider',
]


def get_storage_provider(provider_name: str = None) -> StorageProvider:
    """Factory function to get storage provider"""
    import os
    
    provider_name = provider_name or os.getenv('STORAGE_PROVIDER', 'local')
    
    providers = {
        's3': S3StorageProvider,
        'azure': AzureStorageProvider,
        'gcs': GCSStorageProvider,
        'local': LocalStorageProvider,
    }
    
    provider_class = providers.get(provider_name.lower())
    
    if not provider_class:
        raise ValueError(f"Unknown storage provider: {provider_name}")
    
    return provider_class()
```

**File:** `backend/app/documents/services/storage/base.py`

```python
"""
Base Storage Provider
Abstract base class for storage implementations
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, BinaryIO, List
from dataclasses import dataclass
from datetime import datetime
import mimetypes


@dataclass
class StorageConfig:
    """Storage configuration"""
    provider: str
    bucket: str
    region: Optional[str] = None
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    
    # Azure specific
    connection_string: Optional[str] = None
    account_name: Optional[str] = None
    
    # GCS specific
    project_id: Optional[str] = None
    credentials_path: Optional[str] = None


@dataclass
class StorageObject:
    """Represents a stored object"""
    key: str
    bucket: str
    size: int
    content_type: str
    etag: Optional[str] = None
    last_modified: Optional[datetime] = None
    metadata: Optional[Dict[str, str]] = None
    url: Optional[str] = None


class StorageProvider(ABC):
    """Abstract base class for storage providers"""
    
    name: str = "base"
    
    @abstractmethod
    def upload(
        self,
        file_data: BinaryIO,
        key: str,
        bucket: str,
        content_type: str = None,
        metadata: Dict[str, str] = None,
        acl: str = 'private'
    ) -> StorageObject:
        """
        Upload file to storage
        
        Args:
            file_data: File-like object
            key: Storage key/path
            bucket: Bucket name
            content_type: MIME type
            metadata: Custom metadata
            acl: Access control (private, public-read)
            
        Returns:
            StorageObject with upload result
        """
        pass
    
    @abstractmethod
    def download(
        self,
        key: str,
        bucket: str
    ) -> bytes:
        """
        Download file from storage
        
        Args:
            key: Storage key/path
            bucket: Bucket name
            
        Returns:
            File content as bytes
        """
        pass
    
    @abstractmethod
    def download_to_file(
        self,
        key: str,
        bucket: str,
        file_path: str
    ) -> str:
        """
        Download file to local path
        
        Args:
            key: Storage key/path
            bucket: Bucket name
            file_path: Local file path
            
        Returns:
            Local file path
        """
        pass
    
    @abstractmethod
    def delete(
        self,
        key: str,
        bucket: str
    ) -> bool:
        """
        Delete file from storage
        
        Args:
            key: Storage key/path
            bucket: Bucket name
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    def exists(
        self,
        key: str,
        bucket: str
    ) -> bool:
        """
        Check if file exists
        
        Args:
            key: Storage key/path
            bucket: Bucket name
            
        Returns:
            True if file exists
        """
        pass
    
    @abstractmethod
    def get_metadata(
        self,
        key: str,
        bucket: str
    ) -> Optional[StorageObject]:
        """
        Get file metadata
        
        Args:
            key: Storage key/path
            bucket: Bucket name
            
        Returns:
            StorageObject with metadata
        """
        pass
    
    @abstractmethod
    def get_signed_url(
        self,
        key: str,
        bucket: str,
        expires_in: int = 3600,
        method: str = 'GET'
    ) -> str:
        """
        Generate signed URL for temporary access
        
        Args:
            key: Storage key/path
            bucket: Bucket name
            expires_in: URL validity in seconds
            method: HTTP method (GET, PUT)
            
        Returns:
            Signed URL string
        """
        pass
    
    @abstractmethod
    def copy(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: str,
        dest_bucket: str = None
    ) -> StorageObject:
        """
        Copy file within storage
        
        Args:
            source_key: Source key/path
            dest_key: Destination key/path
            source_bucket: Source bucket
            dest_bucket: Destination bucket (same if None)
            
        Returns:
            StorageObject for copied file
        """
        pass
    
    @abstractmethod
    def list_objects(
        self,
        prefix: str,
        bucket: str,
        max_keys: int = 1000,
        continuation_token: str = None
    ) -> Dict[str, Any]:
        """
        List objects with prefix
        
        Args:
            prefix: Key prefix
            bucket: Bucket name
            max_keys: Maximum results
            continuation_token: Pagination token
            
        Returns:
            Dict with 'objects' list and optional 'continuation_token'
        """
        pass
    
    def generate_key(
        self,
        organization_id: str,
        document_id: str,
        filename: str,
        version: int = None
    ) -> str:
        """Generate storage key with organization namespace"""
        import os
        from datetime import datetime
        
        # Clean filename
        safe_filename = self._safe_filename(filename)
        
        # Date-based partitioning
        date_path = datetime.utcnow().strftime('%Y/%m')
        
        if version:
            return f"{organization_id}/documents/{date_path}/{document_id}/v{version}/{safe_filename}"
        else:
            return f"{organization_id}/documents/{date_path}/{document_id}/{safe_filename}"
    
    def _safe_filename(self, filename: str) -> str:
        """Generate safe filename"""
        import re
        # Remove path separators and null bytes
        safe = re.sub(r'[/\\:\x00]', '_', filename)
        # Limit length
        if len(safe) > 200:
            name, ext = os.path.splitext(safe)
            safe = name[:200-len(ext)] + ext
        return safe
    
    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
```

### 2.2 AWS S3 Storage Provider

**File:** `backend/app/documents/services/storage/s3_provider.py`

```python
"""
AWS S3 Storage Provider
"""

from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
import os
import logging

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from .base import StorageProvider, StorageObject

logger = logging.getLogger(__name__)


class S3StorageProvider(StorageProvider):
    """AWS S3 Storage Provider"""
    
    name = "s3"
    
    def __init__(self):
        self.client = self._create_client()
        self.default_bucket = os.getenv('S3_BUCKET', 'logiaccounting-documents')
    
    def _create_client(self):
        """Create S3 client"""
        config = Config(
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        
        # Support custom endpoint (MinIO, DigitalOcean Spaces, etc.)
        endpoint_url = os.getenv('S3_ENDPOINT_URL')
        
        return boto3.client(
            's3',
            region_name=os.getenv('S3_REGION', 'us-east-1'),
            endpoint_url=endpoint_url,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            config=config
        )
    
    def upload(
        self,
        file_data: BinaryIO,
        key: str,
        bucket: str = None,
        content_type: str = None,
        metadata: Dict[str, str] = None,
        acl: str = 'private'
    ) -> StorageObject:
        """Upload file to S3"""
        bucket = bucket or self.default_bucket
        
        # Prepare extra args
        extra_args = {
            'ContentType': content_type or self._guess_content_type(key),
        }
        
        if acl:
            extra_args['ACL'] = acl
        
        if metadata:
            extra_args['Metadata'] = metadata
        
        # Upload
        try:
            self.client.upload_fileobj(
                file_data,
                bucket,
                key,
                ExtraArgs=extra_args
            )
            
            # Get metadata
            response = self.client.head_object(Bucket=bucket, Key=key)
            
            return StorageObject(
                key=key,
                bucket=bucket,
                size=response['ContentLength'],
                content_type=response['ContentType'],
                etag=response.get('ETag', '').strip('"'),
                last_modified=response.get('LastModified'),
                metadata=response.get('Metadata', {}),
            )
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise
    
    def download(self, key: str, bucket: str = None) -> bytes:
        """Download file from S3"""
        bucket = bucket or self.default_bucket
        
        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"S3 download error: {e}")
            raise
    
    def download_to_file(
        self,
        key: str,
        bucket: str = None,
        file_path: str = None
    ) -> str:
        """Download file to local path"""
        bucket = bucket or self.default_bucket
        
        try:
            self.client.download_file(bucket, key, file_path)
            return file_path
        except ClientError as e:
            logger.error(f"S3 download to file error: {e}")
            raise
    
    def delete(self, key: str, bucket: str = None) -> bool:
        """Delete file from S3"""
        bucket = bucket or self.default_bucket
        
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
    
    def exists(self, key: str, bucket: str = None) -> bool:
        """Check if file exists in S3"""
        bucket = bucket or self.default_bucket
        
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    def get_metadata(self, key: str, bucket: str = None) -> Optional[StorageObject]:
        """Get file metadata from S3"""
        bucket = bucket or self.default_bucket
        
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            
            return StorageObject(
                key=key,
                bucket=bucket,
                size=response['ContentLength'],
                content_type=response['ContentType'],
                etag=response.get('ETag', '').strip('"'),
                last_modified=response.get('LastModified'),
                metadata=response.get('Metadata', {}),
            )
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            raise
    
    def get_signed_url(
        self,
        key: str,
        bucket: str = None,
        expires_in: int = 3600,
        method: str = 'GET'
    ) -> str:
        """Generate presigned URL"""
        bucket = bucket or self.default_bucket
        
        client_method = 'get_object' if method == 'GET' else 'put_object'
        
        try:
            url = self.client.generate_presigned_url(
                client_method,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"S3 presigned URL error: {e}")
            raise
    
    def copy(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: str = None,
        dest_bucket: str = None
    ) -> StorageObject:
        """Copy file within S3"""
        source_bucket = source_bucket or self.default_bucket
        dest_bucket = dest_bucket or source_bucket
        
        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            
            self.client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key
            )
            
            return self.get_metadata(dest_key, dest_bucket)
            
        except ClientError as e:
            logger.error(f"S3 copy error: {e}")
            raise
    
    def list_objects(
        self,
        prefix: str,
        bucket: str = None,
        max_keys: int = 1000,
        continuation_token: str = None
    ) -> Dict[str, Any]:
        """List objects with prefix"""
        bucket = bucket or self.default_bucket
        
        params = {
            'Bucket': bucket,
            'Prefix': prefix,
            'MaxKeys': max_keys,
        }
        
        if continuation_token:
            params['ContinuationToken'] = continuation_token
        
        try:
            response = self.client.list_objects_v2(**params)
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append(StorageObject(
                    key=obj['Key'],
                    bucket=bucket,
                    size=obj['Size'],
                    content_type='',  # Not included in list
                    etag=obj.get('ETag', '').strip('"'),
                    last_modified=obj.get('LastModified'),
                ))
            
            result = {'objects': objects}
            
            if response.get('IsTruncated'):
                result['continuation_token'] = response.get('NextContinuationToken')
            
            return result
            
        except ClientError as e:
            logger.error(f"S3 list error: {e}")
            raise
    
    def create_multipart_upload(
        self,
        key: str,
        bucket: str = None,
        content_type: str = None
    ) -> str:
        """Create multipart upload for large files"""
        bucket = bucket or self.default_bucket
        
        response = self.client.create_multipart_upload(
            Bucket=bucket,
            Key=key,
            ContentType=content_type or 'application/octet-stream'
        )
        
        return response['UploadId']
    
    def upload_part(
        self,
        key: str,
        upload_id: str,
        part_number: int,
        data: bytes,
        bucket: str = None
    ) -> Dict[str, Any]:
        """Upload a part of multipart upload"""
        bucket = bucket or self.default_bucket
        
        response = self.client.upload_part(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            PartNumber=part_number,
            Body=data
        )
        
        return {
            'PartNumber': part_number,
            'ETag': response['ETag']
        }
    
    def complete_multipart_upload(
        self,
        key: str,
        upload_id: str,
        parts: list,
        bucket: str = None
    ) -> StorageObject:
        """Complete multipart upload"""
        bucket = bucket or self.default_bucket
        
        self.client.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        
        return self.get_metadata(key, bucket)
    
    def abort_multipart_upload(
        self,
        key: str,
        upload_id: str,
        bucket: str = None
    ):
        """Abort multipart upload"""
        bucket = bucket or self.default_bucket
        
        self.client.abort_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id
        )
```

### 2.3 Local Storage Provider (Development)

**File:** `backend/app/documents/services/storage/local_provider.py`

```python
"""
Local File System Storage Provider
For development and testing
"""

from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
import os
import shutil
import hashlib
import logging
from pathlib import Path

from .base import StorageProvider, StorageObject

logger = logging.getLogger(__name__)


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider"""
    
    name = "local"
    
    def __init__(self):
        self.base_path = os.getenv('LOCAL_STORAGE_PATH', '/tmp/logiaccounting-documents')
        self.base_url = os.getenv('LOCAL_STORAGE_URL', 'http://localhost:5000/files')
        
        # Ensure base directory exists
        os.makedirs(self.base_path, exist_ok=True)
    
    def _get_full_path(self, bucket: str, key: str) -> str:
        """Get full filesystem path"""
        return os.path.join(self.base_path, bucket, key)
    
    def _ensure_directory(self, file_path: str):
        """Ensure parent directory exists"""
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)
    
    def upload(
        self,
        file_data: BinaryIO,
        key: str,
        bucket: str = 'default',
        content_type: str = None,
        metadata: Dict[str, str] = None,
        acl: str = 'private'
    ) -> StorageObject:
        """Upload file to local storage"""
        full_path = self._get_full_path(bucket, key)
        self._ensure_directory(full_path)
        
        # Write file
        content = file_data.read()
        with open(full_path, 'wb') as f:
            f.write(content)
        
        # Calculate hash
        file_hash = hashlib.md5(content).hexdigest()
        
        # Store metadata
        meta_path = full_path + '.meta'
        import json
        with open(meta_path, 'w') as f:
            json.dump({
                'content_type': content_type or self._guess_content_type(key),
                'metadata': metadata or {},
                'size': len(content),
                'etag': file_hash,
                'created_at': datetime.utcnow().isoformat(),
            }, f)
        
        return StorageObject(
            key=key,
            bucket=bucket,
            size=len(content),
            content_type=content_type or self._guess_content_type(key),
            etag=file_hash,
            last_modified=datetime.utcnow(),
            metadata=metadata,
            url=f"{self.base_url}/{bucket}/{key}",
        )
    
    def download(self, key: str, bucket: str = 'default') -> bytes:
        """Download file from local storage"""
        full_path = self._get_full_path(bucket, key)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {key}")
        
        with open(full_path, 'rb') as f:
            return f.read()
    
    def download_to_file(
        self,
        key: str,
        bucket: str = 'default',
        file_path: str = None
    ) -> str:
        """Download file to local path"""
        full_path = self._get_full_path(bucket, key)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {key}")
        
        shutil.copy2(full_path, file_path)
        return file_path
    
    def delete(self, key: str, bucket: str = 'default') -> bool:
        """Delete file from local storage"""
        full_path = self._get_full_path(bucket, key)
        meta_path = full_path + '.meta'
        
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
            return True
        except Exception as e:
            logger.error(f"Local delete error: {e}")
            return False
    
    def exists(self, key: str, bucket: str = 'default') -> bool:
        """Check if file exists"""
        full_path = self._get_full_path(bucket, key)
        return os.path.exists(full_path)
    
    def get_metadata(self, key: str, bucket: str = 'default') -> Optional[StorageObject]:
        """Get file metadata"""
        full_path = self._get_full_path(bucket, key)
        meta_path = full_path + '.meta'
        
        if not os.path.exists(full_path):
            return None
        
        # Get file stats
        stats = os.stat(full_path)
        
        # Read metadata
        metadata = {}
        content_type = self._guess_content_type(key)
        etag = None
        
        if os.path.exists(meta_path):
            import json
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                content_type = meta.get('content_type', content_type)
                metadata = meta.get('metadata', {})
                etag = meta.get('etag')
        
        return StorageObject(
            key=key,
            bucket=bucket,
            size=stats.st_size,
            content_type=content_type,
            etag=etag,
            last_modified=datetime.fromtimestamp(stats.st_mtime),
            metadata=metadata,
            url=f"{self.base_url}/{bucket}/{key}",
        )
    
    def get_signed_url(
        self,
        key: str,
        bucket: str = 'default',
        expires_in: int = 3600,
        method: str = 'GET'
    ) -> str:
        """Generate URL (not actually signed for local storage)"""
        # In local mode, just return direct URL
        return f"{self.base_url}/{bucket}/{key}"
    
    def copy(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: str = 'default',
        dest_bucket: str = None
    ) -> StorageObject:
        """Copy file"""
        dest_bucket = dest_bucket or source_bucket
        
        source_path = self._get_full_path(source_bucket, source_key)
        dest_path = self._get_full_path(dest_bucket, dest_key)
        
        self._ensure_directory(dest_path)
        
        shutil.copy2(source_path, dest_path)
        
        # Copy metadata
        source_meta = source_path + '.meta'
        dest_meta = dest_path + '.meta'
        if os.path.exists(source_meta):
            shutil.copy2(source_meta, dest_meta)
        
        return self.get_metadata(dest_key, dest_bucket)
    
    def list_objects(
        self,
        prefix: str,
        bucket: str = 'default',
        max_keys: int = 1000,
        continuation_token: str = None
    ) -> Dict[str, Any]:
        """List objects with prefix"""
        bucket_path = os.path.join(self.base_path, bucket)
        
        if not os.path.exists(bucket_path):
            return {'objects': []}
        
        objects = []
        
        for root, dirs, files in os.walk(bucket_path):
            for file in files:
                if file.endswith('.meta'):
                    continue
                
                full_path = os.path.join(root, file)
                key = os.path.relpath(full_path, bucket_path)
                
                if prefix and not key.startswith(prefix):
                    continue
                
                stats = os.stat(full_path)
                
                objects.append(StorageObject(
                    key=key,
                    bucket=bucket,
                    size=stats.st_size,
                    content_type=self._guess_content_type(key),
                    last_modified=datetime.fromtimestamp(stats.st_mtime),
                ))
                
                if len(objects) >= max_keys:
                    break
        
        return {'objects': objects}
```

---

## Continue to Part 2 for Upload Service and OCR Integration

---

*Phase 13 Tasks Part 1 - LogiAccounting Pro*
*Database Models & Storage Service*
