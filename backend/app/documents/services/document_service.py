"""Document management service."""
import os
import hashlib
import logging
from datetime import datetime
from typing import Optional, List, BinaryIO
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import Session

from app.documents.models.document import (
    Document, DocumentCategory, DocumentVersion,
    DocumentType, DocumentStatus
)
from app.documents.models.folder import Folder, DocumentFolder
from app.documents.schemas.document import (
    DocumentUpload, DocumentUpdate, DocumentFilter,
    DocumentResponse, CategoryCreate
)


class DocumentService:
    """Service for document management."""
    
    UPLOAD_DIR = "uploads/documents"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    ALLOWED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.txt', '.csv', '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.zip', '.rar', '.7z', '.xml', '.json'
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    async def upload_document(
        self,
        customer_id: UUID,
        user_id: UUID,
        file: BinaryIO,
        file_name: str,
        file_size: int,
        mime_type: str,
        data: DocumentUpload
    ) -> Document:
        """Upload a new document."""
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {ext} not allowed")
        
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum of {self.MAX_FILE_SIZE} bytes")
        
        file_content = file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        doc_number = await self._generate_document_number(customer_id)
        
        year_month = datetime.utcnow().strftime("%Y/%m")
        relative_path = f"{customer_id}/{year_month}/{uuid4()}{ext}"
        full_path = os.path.join(self.UPLOAD_DIR, relative_path)
        
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(file_content)
        except OSError as exc:
            logger.error("Failed to write document file %s: %s", full_path, exc)
            raise ValueError(f"Failed to store file: {exc}") from exc

        document = Document(
            id=uuid4(),
            customer_id=customer_id,
            document_number=doc_number,
            title=data.title,
            description=data.description,
            document_type=DocumentType(data.document_type),
            status=DocumentStatus.DRAFT,
            category_id=data.category_id,
            tags=data.tags,
            file_name=file_name,
            file_path=relative_path,
            file_size=file_size,
            mime_type=mime_type,
            file_hash=file_hash,
            version=1,
            is_latest=True,
            related_entity_type=data.related_entity_type,
            related_entity_id=data.related_entity_id,
            document_date=data.document_date,
            is_confidential=data.is_confidential,
            metadata=data.metadata,
            created_by=user_id
        )
        
        self.db.add(document)
        
        if data.folder_id:
            doc_folder = DocumentFolder(
                id=uuid4(),
                document_id=document.id,
                folder_id=data.folder_id,
                added_by=user_id
            )
            self.db.add(doc_folder)
            
            await self._update_folder_stats(data.folder_id, 1, file_size)
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    async def update_document(
        self,
        customer_id: UUID,
        document_id: UUID,
        user_id: UUID,
        data: DocumentUpdate
    ) -> Optional[Document]:
        """Update document metadata."""
        document = await self.get_document_by_id(customer_id, document_id)
        if not document:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        if 'document_type' in update_data:
            update_data['document_type'] = DocumentType(update_data['document_type'])
        
        _UPDATABLE_FIELDS = frozenset({
            'title', 'description', 'document_type', 'category_id',
            'tags', 'document_date', 'is_confidential', 'metadata',
            'related_entity_type', 'related_entity_id', 'status',
        })
        for field, value in update_data.items():
            if field not in _UPDATABLE_FIELDS:
                continue
            setattr(document, field, value)
        
        document.updated_by = user_id
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    async def upload_new_version(
        self,
        customer_id: UUID,
        document_id: UUID,
        user_id: UUID,
        file: BinaryIO,
        file_name: str,
        file_size: int,
        mime_type: str,
        change_summary: Optional[str] = None
    ) -> Document:
        """Upload a new version of a document."""
        document = await self.get_document_by_id(customer_id, document_id)
        if not document:
            raise ValueError("Document not found")
        
        version_record = DocumentVersion(
            id=uuid4(),
            document_id=document.id,
            version=document.version,
            file_name=document.file_name,
            file_path=document.file_path,
            file_size=document.file_size,
            file_hash=document.file_hash,
            change_summary=change_summary,
            created_by=user_id
        )
        self.db.add(version_record)
        
        file_content = file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        ext = os.path.splitext(file_name)[1].lower()
        year_month = datetime.utcnow().strftime("%Y/%m")
        relative_path = f"{customer_id}/{year_month}/{uuid4()}{ext}"
        full_path = os.path.join(self.UPLOAD_DIR, relative_path)
        
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(file_content)
        except OSError as exc:
            logger.error("Failed to write version file %s: %s", full_path, exc)
            raise ValueError(f"Failed to store file version: {exc}") from exc

        document.file_name = file_name
        document.file_path = relative_path
        document.file_size = file_size
        document.mime_type = mime_type
        document.file_hash = file_hash
        document.version += 1
        document.updated_by = user_id
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(document)
        
        return document
    
    async def get_document_by_id(
        self,
        customer_id: UUID,
        document_id: UUID
    ) -> Optional[Document]:
        """Get document by ID."""
        query = select(Document).where(
            Document.id == document_id,
            Document.customer_id == customer_id,
            Document.status != DocumentStatus.DELETED
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_documents(
        self,
        customer_id: UUID,
        filters: DocumentFilter,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[Document], int]:
        """Get documents with filtering."""
        query = select(Document).where(
            Document.customer_id == customer_id,
            Document.status != DocumentStatus.DELETED,
            Document.is_latest.is_(True)
        )
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Document.title.ilike(search_term),
                    Document.description.ilike(search_term),
                    Document.file_name.ilike(search_term),
                    Document.document_number.ilike(search_term)
                )
            )
        
        if filters.document_type:
            query = query.where(Document.document_type == filters.document_type)
        if filters.status:
            query = query.where(Document.status == filters.status)
        if filters.category_id:
            query = query.where(Document.category_id == filters.category_id)
        if filters.created_by:
            query = query.where(Document.created_by == filters.created_by)
        if filters.is_confidential is not None:
            query = query.where(Document.is_confidential == filters.is_confidential)
        if filters.start_date:
            query = query.where(Document.created_at >= filters.start_date)
        if filters.end_date:
            query = query.where(Document.created_at <= filters.end_date)
        if filters.related_entity_type:
            query = query.where(Document.related_entity_type == filters.related_entity_type)
        if filters.related_entity_id:
            query = query.where(Document.related_entity_id == filters.related_entity_id)
        if filters.tags:
            for tag in filters.tags:
                query = query.where(Document.tags.contains([tag]))
        
        if filters.folder_id:
            subquery = select(DocumentFolder.document_id).where(
                DocumentFolder.folder_id == filters.folder_id
            )
            query = query.where(Document.id.in_(subquery))
        
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()
        
        query = query.order_by(desc(Document.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = self.db.execute(query)
        documents = result.scalars().all()
        
        return documents, total
    
    async def delete_document(
        self,
        customer_id: UUID,
        document_id: UUID,
        user_id: UUID,
        permanent: bool = False
    ) -> bool:
        """Delete or soft-delete a document."""
        document = await self.get_document_by_id(customer_id, document_id)
        if not document:
            return False
        
        if permanent:
            full_path = os.path.join(self.UPLOAD_DIR, document.file_path)
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
            except OSError as exc:
                logger.warning("Failed to delete file %s: %s", full_path, exc)
            self.db.delete(document)
        else:
            document.status = DocumentStatus.DELETED
            document.updated_by = user_id
            document.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    async def get_document_versions(
        self,
        customer_id: UUID,
        document_id: UUID
    ) -> List[DocumentVersion]:
        """Get all versions of a document."""
        document = await self.get_document_by_id(customer_id, document_id)
        if not document:
            return []
        
        query = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.version))
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    async def get_file_path(
        self,
        customer_id: UUID,
        document_id: UUID
    ) -> Optional[str]:
        """Get the full file path for download."""
        document = await self.get_document_by_id(customer_id, document_id)
        if not document:
            return None
        return os.path.join(self.UPLOAD_DIR, document.file_path)
    
    # ==========================================
    # CATEGORIES
    # ==========================================
    
    async def create_category(
        self,
        customer_id: UUID,
        data: CategoryCreate
    ) -> DocumentCategory:
        """Create a document category."""
        path = data.name
        if data.parent_id:
            parent = self.db.execute(
                select(DocumentCategory).where(DocumentCategory.id == data.parent_id)
            ).scalar_one_or_none()
            if parent:
                path = f"{parent.path}/{data.name}"
        
        category = DocumentCategory(
            id=uuid4(),
            customer_id=customer_id,
            name=data.name,
            description=data.description,
            color=data.color,
            icon=data.icon,
            parent_id=data.parent_id,
            path=path,
            default_retention_days=data.default_retention_days
        )
        
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        
        return category
    
    async def get_categories(
        self,
        customer_id: UUID,
        include_inactive: bool = False
    ) -> List[DocumentCategory]:
        """Get all categories."""
        query = select(DocumentCategory).where(
            DocumentCategory.customer_id == customer_id
        )
        if not include_inactive:
            query = query.where(DocumentCategory.is_active.is_(True))
        
        query = query.order_by(DocumentCategory.path)
        result = self.db.execute(query)
        return result.scalars().all()
    
    # ==========================================
    # HELPERS
    # ==========================================
    
    async def _generate_document_number(self, customer_id: UUID) -> str:
        """Generate unique document number."""
        year = datetime.utcnow().strftime("%Y")
        
        count = self.db.execute(
            select(func.count()).where(
                Document.customer_id == customer_id,
                Document.document_number.like(f"DOC-{year}-%")
            )
        ).scalar()
        
        return f"DOC-{year}-{(count or 0) + 1:06d}"
    
    async def _update_folder_stats(
        self,
        folder_id: UUID,
        doc_count_delta: int,
        size_delta: int
    ):
        """Update folder statistics."""
        folder = self.db.execute(
            select(Folder).where(Folder.id == folder_id)
        ).scalar_one_or_none()
        
        if folder:
            folder.document_count += doc_count_delta
            folder.total_size += size_delta
