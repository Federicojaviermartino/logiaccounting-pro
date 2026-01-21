"""
Document Management Service - Phase 13
Comprehensive document management with storage, versioning, sharing, and OCR
"""

from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime
from uuid import uuid4
import os
import base64
import hashlib
import mimetypes
import logging
from io import BytesIO

from app.models.document_store import doc_db, init_document_database
from app.services.storage import get_storage_provider

logger = logging.getLogger(__name__)


class DocumentManagementService:
    """Enhanced document management service"""

    # Supported file types
    SUPPORTED_TYPES = {
        'application/pdf': ['.pdf'],
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/tiff': ['.tiff', '.tif'],
        'image/webp': ['.webp'],
        'application/msword': ['.doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'application/vnd.ms-excel': ['.xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        'text/plain': ['.txt'],
        'text/csv': ['.csv'],
        'application/xml': ['.xml'],
        'application/json': ['.json'],
    }

    # Document types for classification
    DOCUMENT_TYPES = [
        'invoice', 'receipt', 'contract', 'proposal', 'report',
        'statement', 'certificate', 'id_document', 'correspondence', 'other'
    ]

    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    def __init__(self):
        self._storage = None

    @property
    def storage(self):
        if self._storage is None:
            self._storage = get_storage_provider()
        return self._storage

    def get_default_bucket(self) -> str:
        return os.getenv('STORAGE_BUCKET', 'logiaccounting-documents')

    def validate_file(
        self,
        filename: str,
        file_size: int,
        mime_type: str = None
    ) -> Dict[str, Any]:
        """Validate file before upload"""
        errors = []

        ext = os.path.splitext(filename)[1].lower()
        valid_extensions = []
        for exts in self.SUPPORTED_TYPES.values():
            valid_extensions.extend(exts)

        if ext not in valid_extensions:
            errors.append(f"Unsupported file type: {ext}")

        if mime_type and mime_type not in self.SUPPORTED_TYPES:
            guessed_type, _ = mimetypes.guess_type(filename)
            if guessed_type not in self.SUPPORTED_TYPES:
                errors.append(f"Unsupported MIME type: {mime_type}")

        if file_size > self.MAX_FILE_SIZE:
            errors.append(f"File too large. Maximum size: {self.MAX_FILE_SIZE / 1024 / 1024}MB")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def upload_document(
        self,
        file_data: BinaryIO,
        filename: str,
        organization_id: str,
        owner_id: str,
        mime_type: str = None,
        document_type: str = 'other',
        category_id: str = None,
        name: str = None,
        description: str = None,
        tags: List[str] = None,
        related_entity_type: str = None,
        related_entity_id: str = None,
        extract_text: bool = True,
        detect_type: bool = True,
    ) -> Dict[str, Any]:
        """Upload a document with full processing"""

        # Read file content
        content = file_data.read()
        file_size = len(content)

        # Validate
        validation = self.validate_file(filename, file_size, mime_type)
        if not validation['valid']:
            return {'success': False, 'errors': validation['errors']}

        # Guess mime type if not provided
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            mime_type = mime_type or 'application/octet-stream'

        # Calculate hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()

        # Check for duplicates
        existing = doc_db.documents.find_by_hash(organization_id, file_hash)
        if existing:
            return {
                'success': False,
                'error': 'duplicate',
                'existing_document_id': existing['id'],
                'message': 'A document with the same content already exists'
            }

        # Create document record
        document_id = str(uuid4())

        doc_data = {
            'id': document_id,
            'organization_id': organization_id,
            'owner_id': owner_id,
            'name': name or filename,
            'original_filename': filename,
            'mime_type': mime_type,
            'file_size': file_size,
            'file_hash': file_hash,
            'document_type': document_type,
            'description': description or '',
            'category_id': category_id,
            'status': 'processing',
            'storage_provider': self.storage.name,
            'storage_bucket': self.get_default_bucket(),
            'related_entity_type': related_entity_type,
            'related_entity_id': related_entity_id,
            'tags': tags or [],
            'ocr_text': None,
            'ocr_confidence': None,
            'extracted_data': None,
            'version_number': 1,
        }

        # Save to store first
        doc_db.documents.create(doc_data)

        try:
            # Upload to storage
            storage_key = self.storage.generate_key(
                organization_id=organization_id,
                document_id=document_id,
                filename=filename
            )

            storage_obj = self.storage.upload_bytes(
                content=content,
                key=storage_key,
                bucket=self.get_default_bucket(),
                content_type=mime_type,
                metadata={
                    'document_id': document_id,
                    'organization_id': organization_id,
                    'original_filename': filename,
                }
            )

            # Update document with storage info
            doc_db.documents.update(document_id, {
                'storage_key': storage_key,
                'status': 'active',
            })

            # Create version record
            doc_db.versions.create({
                'document_id': document_id,
                'version_number': 1,
                'storage_key': storage_key,
                'file_size': file_size,
                'file_hash': file_hash,
                'created_by': owner_id,
                'change_notes': 'Initial upload',
            })

            # Log activity
            doc_db.activity.log(
                document_id=document_id,
                action='upload',
                user_id=owner_id,
                details={'filename': filename, 'size': file_size}
            )

            # Get final document
            document = doc_db.documents.find_by_id(document_id)

            return {
                'success': True,
                'document': document
            }

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            doc_db.documents.soft_delete(document_id)
            return {
                'success': False,
                'error': str(e)
            }

    def upload_from_base64(
        self,
        content_base64: str,
        filename: str,
        organization_id: str,
        owner_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Upload document from base64 encoded content"""
        try:
            content = base64.b64decode(content_base64)
            return self.upload_document(
                file_data=BytesIO(content),
                filename=filename,
                organization_id=organization_id,
                owner_id=owner_id,
                **kwargs
            )
        except Exception as e:
            return {'success': False, 'error': f'Invalid base64 content: {e}'}

    def get_document(self, document_id: str, organization_id: str = None) -> Optional[Dict]:
        """Get document by ID"""
        doc = doc_db.documents.find_by_id(document_id)

        if not doc:
            return None

        if organization_id and doc.get('organization_id') != organization_id:
            return None

        return doc

    def list_documents(
        self,
        organization_id: str,
        page: int = 1,
        per_page: int = 20,
        **filters
    ) -> Dict[str, Any]:
        """List documents with pagination and filters"""
        documents = doc_db.documents.find_by_organization(organization_id, filters)

        total = len(documents)
        start = (page - 1) * per_page
        end = start + per_page

        return {
            'documents': documents[start:end],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        }

    def update_document(
        self,
        document_id: str,
        organization_id: str,
        user_id: str,
        **updates
    ) -> Optional[Dict]:
        """Update document metadata"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return None

        allowed_fields = [
            'name', 'description', 'document_type', 'category_id',
            'tags', 'related_entity_type', 'related_entity_id'
        ]

        update_data = {k: v for k, v in updates.items() if k in allowed_fields and v is not None}

        if update_data:
            doc_db.documents.update(document_id, update_data)

            doc_db.activity.log(
                document_id=document_id,
                action='update',
                user_id=user_id,
                details={'updated_fields': list(update_data.keys())}
            )

        return doc_db.documents.find_by_id(document_id)

    def delete_document(
        self,
        document_id: str,
        organization_id: str,
        user_id: str,
        permanent: bool = False
    ) -> bool:
        """Delete a document"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return False

        if permanent:
            # Delete from storage
            if doc.get('storage_key'):
                self.storage.delete(doc['storage_key'], doc.get('storage_bucket'))

            # Delete versions from storage
            versions = doc_db.versions.find_by_document(document_id)
            for version in versions:
                if version.get('storage_key'):
                    self.storage.delete(version['storage_key'], doc.get('storage_bucket'))

            # Delete records
            doc_db.documents.delete(document_id)

            doc_db.activity.log(
                document_id=document_id,
                action='permanent_delete',
                user_id=user_id,
            )
        else:
            doc_db.documents.soft_delete(document_id)

            doc_db.activity.log(
                document_id=document_id,
                action='delete',
                user_id=user_id,
            )

        return True

    def restore_document(
        self,
        document_id: str,
        organization_id: str,
        user_id: str
    ) -> Optional[Dict]:
        """Restore a soft-deleted document"""
        doc = doc_db.documents.find_by_id(document_id)

        if not doc or doc.get('organization_id') != organization_id:
            return None

        if doc.get('status') != 'deleted':
            return doc

        doc_db.documents.restore(document_id)

        doc_db.activity.log(
            document_id=document_id,
            action='restore',
            user_id=user_id,
        )

        return doc_db.documents.find_by_id(document_id)

    def download_document(
        self,
        document_id: str,
        organization_id: str,
        user_id: str = None,
        version: int = None
    ) -> Optional[Dict]:
        """Get document content for download"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return None

        storage_key = doc.get('storage_key')

        if version:
            ver = next(
                (v for v in doc_db.versions.find_by_document(document_id)
                 if v.get('version_number') == version),
                None
            )
            if ver:
                storage_key = ver.get('storage_key')

        if not storage_key:
            return None

        try:
            content = self.storage.download(storage_key, doc.get('storage_bucket'))

            if user_id:
                doc_db.activity.log(
                    document_id=document_id,
                    action='download',
                    user_id=user_id,
                    details={'version': version or doc.get('version_number')}
                )

            return {
                'content': content,
                'filename': doc.get('original_filename'),
                'mime_type': doc.get('mime_type'),
                'size': len(content)
            }

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None

    def get_download_url(
        self,
        document_id: str,
        organization_id: str,
        expires_in: int = 3600,
        version: int = None
    ) -> Optional[str]:
        """Get presigned download URL"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return None

        storage_key = doc.get('storage_key')

        if version:
            ver = next(
                (v for v in doc_db.versions.find_by_document(document_id)
                 if v.get('version_number') == version),
                None
            )
            if ver:
                storage_key = ver.get('storage_key')

        if not storage_key:
            return None

        return self.storage.get_signed_url(
            storage_key,
            doc.get('storage_bucket'),
            expires_in=expires_in
        )

    def upload_new_version(
        self,
        document_id: str,
        file_data: BinaryIO,
        filename: str,
        organization_id: str,
        user_id: str,
        change_notes: str = None
    ) -> Dict[str, Any]:
        """Upload a new version of an existing document"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return {'success': False, 'error': 'Document not found'}

        content = file_data.read()
        file_size = len(content)

        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or doc.get('mime_type')

        file_hash = hashlib.sha256(content).hexdigest()

        new_version = doc.get('version_number', 1) + 1

        try:
            storage_key = self.storage.generate_key(
                organization_id=organization_id,
                document_id=document_id,
                filename=filename,
                version=new_version
            )

            self.storage.upload_bytes(
                content=content,
                key=storage_key,
                bucket=doc.get('storage_bucket'),
                content_type=mime_type,
            )

            doc_db.versions.create({
                'document_id': document_id,
                'version_number': new_version,
                'storage_key': storage_key,
                'file_size': file_size,
                'file_hash': file_hash,
                'created_by': user_id,
                'change_notes': change_notes or f'Version {new_version}',
            })

            doc_db.documents.update(document_id, {
                'storage_key': storage_key,
                'file_size': file_size,
                'file_hash': file_hash,
                'version_number': new_version,
                'original_filename': filename,
                'mime_type': mime_type,
            })

            doc_db.activity.log(
                document_id=document_id,
                action='new_version',
                user_id=user_id,
                details={'version': new_version, 'filename': filename}
            )

            return {
                'success': True,
                'document': doc_db.documents.find_by_id(document_id),
                'version': new_version
            }

        except Exception as e:
            logger.error(f"Version upload failed: {e}")
            return {'success': False, 'error': str(e)}

    def get_versions(self, document_id: str, organization_id: str) -> List[Dict]:
        """Get all versions of a document"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return []

        return doc_db.versions.find_by_document(document_id)

    def create_share_link(
        self,
        document_id: str,
        organization_id: str,
        user_id: str,
        permission: str = 'view',
        expires_days: int = None,
        can_download: bool = True
    ) -> Optional[Dict]:
        """Create a shareable link for a document"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return None

        share = doc_db.shares.create_link_share(
            document_id=document_id,
            shared_by=user_id,
            permission=permission,
            expires_days=expires_days,
            can_download=can_download
        )

        doc_db.activity.log(
            document_id=document_id,
            action='share_link_created',
            user_id=user_id,
            details={'expires_days': expires_days}
        )

        base_url = os.getenv('APP_URL', 'http://localhost:5173')
        share['share_url'] = f"{base_url}/share/{share['share_token']}"

        return share

    def share_with_user(
        self,
        document_id: str,
        organization_id: str,
        user_id: str,
        share_with_user_id: str,
        permission: str = 'view',
        can_download: bool = True,
        can_share: bool = False
    ) -> Optional[Dict]:
        """Share document with another user"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return None

        share = doc_db.shares.create_user_share(
            document_id=document_id,
            shared_with_user_id=share_with_user_id,
            shared_by=user_id,
            permission=permission,
            can_download=can_download,
            can_share=can_share
        )

        doc_db.activity.log(
            document_id=document_id,
            action='shared_with_user',
            user_id=user_id,
            details={'shared_with': share_with_user_id, 'permission': permission}
        )

        return share

    def get_shares(self, document_id: str, organization_id: str) -> List[Dict]:
        """Get all shares for a document"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return []

        return doc_db.shares.find_by_document(document_id)

    def revoke_share(
        self,
        share_id: str,
        document_id: str,
        organization_id: str,
        user_id: str
    ) -> bool:
        """Revoke a share"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return False

        share = doc_db.shares.find_by_id(share_id)

        if not share or share.get('document_id') != document_id:
            return False

        doc_db.shares.delete(share_id)

        doc_db.activity.log(
            document_id=document_id,
            action='share_revoked',
            user_id=user_id,
            details={'share_id': share_id}
        )

        return True

    def access_shared_document(
        self,
        share_token: str,
        ip_address: str = None
    ) -> Optional[Dict]:
        """Access a document via share link"""
        share = doc_db.shares.find_by_token(share_token)

        if not share:
            return None

        if doc_db.shares.is_expired(share):
            return {'error': 'Share link has expired'}

        doc_db.shares.record_access(share['id'])

        doc = doc_db.documents.find_by_id(share['document_id'])

        if not doc or doc.get('status') == 'deleted':
            return None

        return {
            'document': {
                'id': doc['id'],
                'name': doc['name'],
                'mime_type': doc['mime_type'],
                'file_size': doc['file_size'],
                'created_at': doc['created_at'],
            },
            'permission': share['permission'],
            'can_download': share.get('can_download', True),
        }

    def add_comment(
        self,
        document_id: str,
        organization_id: str,
        user_id: str,
        content: str,
        parent_id: str = None,
        page_number: int = None,
        position_x: float = None,
        position_y: float = None
    ) -> Optional[Dict]:
        """Add a comment to a document"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return None

        comment = doc_db.comments.create({
            'document_id': document_id,
            'user_id': user_id,
            'content': content,
            'parent_id': parent_id,
            'page_number': page_number,
            'position_x': position_x,
            'position_y': position_y,
            'is_resolved': False,
        })

        doc_db.activity.log(
            document_id=document_id,
            action='comment_added',
            user_id=user_id,
            details={'comment_id': comment['id']}
        )

        return comment

    def get_comments(
        self,
        document_id: str,
        organization_id: str,
        include_resolved: bool = True
    ) -> List[Dict]:
        """Get comments for a document"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return []

        return doc_db.comments.find_by_document(document_id, include_resolved)

    def resolve_comment(
        self,
        comment_id: str,
        document_id: str,
        organization_id: str,
        user_id: str
    ) -> Optional[Dict]:
        """Resolve a comment"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return None

        comment = doc_db.comments.find_by_id(comment_id)

        if not comment or comment.get('document_id') != document_id:
            return None

        return doc_db.comments.resolve(comment_id, user_id)

    def get_activity(
        self,
        document_id: str,
        organization_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get activity log for a document"""
        doc = self.get_document(document_id, organization_id)

        if not doc:
            return []

        return doc_db.activity.find_by_document(document_id, limit)

    def update_ocr_text(
        self,
        document_id: str,
        ocr_text: str,
        ocr_confidence: float = None
    ):
        """Update document with OCR extracted text"""
        doc_db.documents.update(document_id, {
            'ocr_text': ocr_text,
            'ocr_confidence': ocr_confidence,
        })

    def update_extracted_data(
        self,
        document_id: str,
        extracted_data: Dict[str, Any]
    ):
        """Update document with AI extracted data"""
        doc_db.documents.update(document_id, {
            'extracted_data': extracted_data,
        })

    def get_categories(self, organization_id: str) -> List[Dict]:
        """Get document categories for organization"""
        cats = doc_db.categories.find_by_organization(organization_id)
        if not cats:
            cats = doc_db.categories.find_by_organization('default')
        return cats

    def get_category_tree(self, organization_id: str) -> List[Dict]:
        """Get category tree for organization"""
        return doc_db.categories.get_tree(organization_id)

    def create_category(
        self,
        organization_id: str,
        name: str,
        parent_id: str = None,
        icon: str = 'folder',
        color: str = '#6B7280'
    ) -> Dict:
        """Create a new category"""
        return doc_db.categories.create({
            'organization_id': organization_id,
            'name': name,
            'parent_id': parent_id,
            'icon': icon,
            'color': color,
        })

    def get_tags(self, organization_id: str) -> List[Dict]:
        """Get tags for organization"""
        tags = doc_db.tags.find_by_organization(organization_id)
        if not tags:
            tags = doc_db.tags.find_by_organization('default')
        return tags

    def create_tag(
        self,
        organization_id: str,
        name: str,
        color: str = '#6B7280'
    ) -> Dict:
        """Create a new tag"""
        return doc_db.tags.create({
            'organization_id': organization_id,
            'name': name,
            'color': color,
        })

    def get_storage_stats(self, organization_id: str) -> Dict[str, Any]:
        """Get storage statistics for organization"""
        documents = doc_db.documents.find_by_organization(organization_id)

        total_size = sum(d.get('file_size', 0) for d in documents)
        by_type = {}

        for doc in documents:
            doc_type = doc.get('document_type', 'other')
            if doc_type not in by_type:
                by_type[doc_type] = {'count': 0, 'size': 0}
            by_type[doc_type]['count'] += 1
            by_type[doc_type]['size'] += doc.get('file_size', 0)

        return {
            'total_documents': len(documents),
            'total_size': total_size,
            'total_size_formatted': self._format_size(total_size),
            'by_type': by_type,
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"


# Global service instance
document_management_service = DocumentManagementService()
