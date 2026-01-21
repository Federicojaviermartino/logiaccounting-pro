# LogiAccounting Pro - Phase 13 Tasks Part 2

## UPLOAD SERVICE, OCR & AI EXTRACTION

---

## TASK 3: DOCUMENT SERVICE

### 3.1 Document Service

**File:** `backend/app/documents/services/document_service.py`

```python
"""
Document Service
Main service for document operations
"""

from typing import Optional, List, Dict, Any, BinaryIO, Tuple
from datetime import datetime
from flask import current_app
import logging
import uuid
import os

from app.extensions import db
from app.documents.models.document import Document, document_tag_assignments
from app.documents.models.document_category import DocumentCategory, DocumentTag
from app.documents.models.document_version import DocumentVersion
from app.documents.models.document_share import DocumentShare
from app.documents.models.document_activity import DocumentActivityLog
from app.documents.services.storage import get_storage_provider
from app.documents.services.thumbnail_service import ThumbnailService

logger = logging.getLogger(__name__)


class DocumentService:
    """Main service for document operations"""
    
    ALLOWED_MIME_TYPES = {
        # Documents
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain',
        'text/csv',
        # Images
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'image/tiff',
        'image/bmp',
    }
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    
    def __init__(self):
        self.storage = get_storage_provider()
        self.thumbnail_service = ThumbnailService()
    
    # ==================== Document CRUD ====================
    
    def create_document(
        self,
        organization_id: str,
        name: str,
        file_data: BinaryIO,
        filename: str,
        mime_type: str,
        owner_id: str,
        category_id: str = None,
        document_type: str = None,
        description: str = None,
        tags: List[str] = None,
        related_entity_type: str = None,
        related_entity_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Document:
        """
        Create new document with file upload
        """
        # Validate mime type
        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise ValueError(f"File type not allowed: {mime_type}")
        
        # Read file content
        file_content = file_data.read()
        file_size = len(file_content)
        
        # Validate file size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})")
        
        # Calculate hash
        file_hash = Document.calculate_hash(file_content)
        
        # Check for duplicates
        existing = Document.query.filter(
            Document.organization_id == organization_id,
            Document.file_hash == file_hash,
            Document.status != 'deleted'
        ).first()
        
        if existing:
            logger.info(f"Duplicate document found: {existing.id}")
            # Return existing or raise error based on config
            # For now, we'll allow duplicates but log it
        
        # Create document record
        document = Document(
            id=uuid.uuid4(),
            organization_id=organization_id,
            name=name or filename,
            description=description,
            original_filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            file_hash=file_hash,
            storage_provider=self.storage.name,
            storage_bucket=os.getenv('STORAGE_BUCKET', 'documents'),
            category_id=category_id,
            document_type=document_type,
            owner_id=owner_id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            status='processing',
        )
        
        # Generate storage key
        storage_key = self.storage.generate_key(
            organization_id=str(organization_id),
            document_id=str(document.id),
            filename=filename
        )
        document.storage_key = storage_key
        
        # Upload file
        from io import BytesIO
        storage_result = self.storage.upload(
            file_data=BytesIO(file_content),
            key=storage_key,
            bucket=document.storage_bucket,
            content_type=mime_type,
            metadata={'document_id': str(document.id), 'organization_id': str(organization_id)}
        )
        
        document.storage_url = storage_result.url
        
        # Save document
        db.session.add(document)
        db.session.flush()
        
        # Add tags
        if tags:
            self._assign_tags(document, tags, organization_id)
        
        # Log activity
        DocumentActivityLog.log(
            document_id=str(document.id),
            action='created',
            user_id=owner_id,
            details={'filename': filename, 'size': file_size}
        )
        
        db.session.commit()
        
        # Queue background tasks
        self._queue_processing_tasks(document, file_content)
        
        logger.info(f"Document created: {document.id}")
        
        return document
    
    def get_document(
        self,
        document_id: str,
        organization_id: str = None,
        include_deleted: bool = False
    ) -> Optional[Document]:
        """Get document by ID"""
        query = Document.query.filter(Document.id == document_id)
        
        if organization_id:
            query = query.filter(Document.organization_id == organization_id)
        
        if not include_deleted:
            query = query.filter(Document.status != 'deleted')
        
        return query.first()
    
    def list_documents(
        self,
        organization_id: str,
        category_id: str = None,
        document_type: str = None,
        status: str = 'active',
        owner_id: str = None,
        tag_ids: List[str] = None,
        search_query: str = None,
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Document], int]:
        """List documents with filters and pagination"""
        query = Document.query.filter(Document.organization_id == organization_id)
        
        # Apply filters
        if category_id:
            query = query.filter(Document.category_id == category_id)
        
        if document_type:
            query = query.filter(Document.document_type == document_type)
        
        if status:
            if status == 'all':
                query = query.filter(Document.status != 'deleted')
            else:
                query = query.filter(Document.status == status)
        
        if owner_id:
            query = query.filter(Document.owner_id == owner_id)
        
        if tag_ids:
            query = query.join(document_tag_assignments).filter(
                document_tag_assignments.c.tag_id.in_(tag_ids)
            )
        
        if search_query:
            # Full-text search
            from sqlalchemy import func
            search_vector = func.to_tsquery('english', search_query.replace(' ', ' & '))
            query = query.filter(Document.search_vector.op('@@')(search_vector))
        
        # Get total count
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(Document, sort_by, Document.created_at)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        offset = (page - 1) * per_page
        documents = query.offset(offset).limit(per_page).all()
        
        return documents, total
    
    def update_document(
        self,
        document_id: str,
        organization_id: str,
        updated_by: str,
        name: str = None,
        description: str = None,
        category_id: str = None,
        document_type: str = None,
        tags: List[str] = None,
        related_entity_type: str = None,
        related_entity_id: str = None
    ) -> Optional[Document]:
        """Update document metadata"""
        document = self.get_document(document_id, organization_id)
        
        if not document:
            return None
        
        # Track changes
        changes = {}
        
        if name is not None and name != document.name:
            changes['name'] = {'from': document.name, 'to': name}
            document.name = name
        
        if description is not None:
            document.description = description
        
        if category_id is not None:
            changes['category_id'] = {'from': str(document.category_id), 'to': category_id}
            document.category_id = category_id
        
        if document_type is not None:
            document.document_type = document_type
        
        if related_entity_type is not None:
            document.related_entity_type = related_entity_type
            document.related_entity_id = related_entity_id
        
        if tags is not None:
            self._assign_tags(document, tags, organization_id)
        
        document.updated_at = datetime.utcnow()
        document.update_search_vector()
        
        # Log activity
        if changes:
            DocumentActivityLog.log(
                document_id=str(document.id),
                action='updated',
                user_id=updated_by,
                details={'changes': changes}
            )
        
        db.session.commit()
        
        return document
    
    def update_document_file(
        self,
        document_id: str,
        organization_id: str,
        file_data: BinaryIO,
        filename: str,
        mime_type: str,
        updated_by: str,
        change_summary: str = None
    ) -> Optional[Document]:
        """Update document file (creates new version)"""
        document = self.get_document(document_id, organization_id)
        
        if not document:
            return None
        
        # Create version of current state
        document.create_version(updated_by, change_summary)
        
        # Read new file
        file_content = file_data.read()
        file_size = len(file_content)
        file_hash = Document.calculate_hash(file_content)
        
        # Generate new storage key
        new_storage_key = self.storage.generate_key(
            organization_id=str(organization_id),
            document_id=str(document.id),
            filename=filename,
            version=document.current_version
        )
        
        # Upload new file
        from io import BytesIO
        storage_result = self.storage.upload(
            file_data=BytesIO(file_content),
            key=new_storage_key,
            bucket=document.storage_bucket,
            content_type=mime_type
        )
        
        # Update document
        document.original_filename = filename
        document.mime_type = mime_type
        document.file_size = file_size
        document.file_hash = file_hash
        document.storage_key = new_storage_key
        document.storage_url = storage_result.url
        document.updated_at = datetime.utcnow()
        
        # Reset processing status
        document.ocr_status = 'pending'
        document.extraction_status = 'pending'
        
        # Log activity
        DocumentActivityLog.log(
            document_id=str(document.id),
            action='versioned',
            user_id=updated_by,
            details={
                'version': document.current_version,
                'change_summary': change_summary
            }
        )
        
        db.session.commit()
        
        # Queue processing
        self._queue_processing_tasks(document, file_content)
        
        return document
    
    def delete_document(
        self,
        document_id: str,
        organization_id: str,
        deleted_by: str,
        permanent: bool = False
    ) -> bool:
        """Delete document (soft or permanent)"""
        document = self.get_document(document_id, organization_id, include_deleted=True)
        
        if not document:
            return False
        
        if permanent:
            # Delete from storage
            self.storage.delete(document.storage_key, document.storage_bucket)
            
            # Delete all versions
            for version in document.versions:
                self.storage.delete(version.storage_key, document.storage_bucket)
            
            # Delete record
            db.session.delete(document)
            
            logger.info(f"Document permanently deleted: {document_id}")
        else:
            # Soft delete
            document.soft_delete(deleted_by)
            
            logger.info(f"Document soft deleted: {document_id}")
        
        db.session.commit()
        return True
    
    def restore_document(
        self,
        document_id: str,
        organization_id: str,
        restored_by: str
    ) -> Optional[Document]:
        """Restore deleted document"""
        document = self.get_document(document_id, organization_id, include_deleted=True)
        
        if not document or document.status != 'deleted':
            return None
        
        document.restore(restored_by)
        db.session.commit()
        
        return document
    
    # ==================== Helper Methods ====================
    
    def _assign_tags(
        self,
        document: Document,
        tag_names: List[str],
        organization_id: str
    ):
        """Assign tags to document"""
        # Clear existing tags
        document.tags = []
        
        for tag_name in tag_names:
            tag_slug = DocumentCategory.generate_slug(tag_name)
            
            # Find or create tag
            tag = DocumentTag.query.filter(
                DocumentTag.organization_id == organization_id,
                DocumentTag.slug == tag_slug
            ).first()
            
            if not tag:
                tag = DocumentTag(
                    organization_id=organization_id,
                    name=tag_name,
                    slug=tag_slug
                )
                db.session.add(tag)
            
            document.tags.append(tag)
    
    def _queue_processing_tasks(self, document: Document, file_content: bytes = None):
        """Queue background processing tasks"""
        from app.workers.tasks.document_tasks import (
            process_document_ocr,
            generate_document_thumbnail,
            index_document_search
        )
        
        # Generate thumbnail
        generate_document_thumbnail.delay(str(document.id))
        
        # OCR processing (for PDFs and images)
        if document.mime_type in ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']:
            process_document_ocr.delay(str(document.id))
        else:
            # Skip OCR for other file types
            document.ocr_status = 'skipped'
            document.extraction_status = 'skipped'
            document.status = 'active'
            db.session.commit()
        
        # Index for search
        index_document_search.delay(str(document.id))
    
    # ==================== Download & Preview ====================
    
    def get_download_url(
        self,
        document_id: str,
        organization_id: str,
        user_id: str,
        version: int = None,
        expires_in: int = 3600
    ) -> Optional[str]:
        """Get signed download URL"""
        document = self.get_document(document_id, organization_id)
        
        if not document:
            return None
        
        # Log download
        DocumentActivityLog.log(
            document_id=str(document.id),
            action='downloaded',
            user_id=user_id,
            details={'version': version}
        )
        
        if version:
            doc_version = DocumentVersion.query.filter(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == version
            ).first()
            
            if doc_version:
                return self.storage.get_signed_url(
                    key=doc_version.storage_key,
                    bucket=document.storage_bucket,
                    expires_in=expires_in
                )
        
        return self.storage.get_signed_url(
            key=document.storage_key,
            bucket=document.storage_bucket,
            expires_in=expires_in
        )
    
    def record_view(
        self,
        document_id: str,
        user_id: str,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Record document view"""
        DocumentActivityLog.log(
            document_id=document_id,
            action='viewed',
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
```

---

## TASK 4: UPLOAD ROUTES

### 4.1 Upload Endpoints

**File:** `backend/app/documents/routes/upload.py`

```python
"""
Document Upload Routes
Handles file uploads with chunking support
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import magic
import os
import tempfile
import logging

from app.documents.services.document_service import DocumentService
from app.documents.services.virus_scan_service import VirusScanService

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__, url_prefix='/api/v1/documents')


@upload_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    """
    Upload a single document
    
    Form data:
    - file: The file to upload
    - name: Document name (optional, defaults to filename)
    - category_id: Category ID (optional)
    - document_type: Document type (optional)
    - description: Description (optional)
    - tags: Comma-separated tags (optional)
    """
    user_id = get_jwt_identity()
    organization_id = g.current_user.organization_id
    
    # Check for file
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Secure filename
    filename = secure_filename(file.filename)
    
    # Detect mime type from content
    file_content = file.read()
    mime_type = magic.from_buffer(file_content, mime=True)
    file.seek(0)  # Reset file pointer
    
    # Validate mime type
    if mime_type not in DocumentService.ALLOWED_MIME_TYPES:
        return jsonify({
            'error': f'File type not allowed: {mime_type}',
            'allowed_types': list(DocumentService.ALLOWED_MIME_TYPES)
        }), 400
    
    # Validate file size
    file_size = len(file_content)
    if file_size > DocumentService.MAX_FILE_SIZE:
        return jsonify({
            'error': f'File too large: {file_size} bytes',
            'max_size': DocumentService.MAX_FILE_SIZE
        }), 400
    
    # Virus scan
    try:
        virus_scan = VirusScanService()
        scan_result = virus_scan.scan_content(file_content)
        
        if not scan_result['clean']:
            logger.warning(f"Virus detected in upload from user {user_id}: {scan_result.get('threat')}")
            return jsonify({
                'error': 'File contains malware',
                'threat': scan_result.get('threat')
            }), 400
    except Exception as e:
        logger.warning(f"Virus scan failed, proceeding with upload: {e}")
    
    # Parse optional fields
    name = request.form.get('name') or filename
    category_id = request.form.get('category_id')
    document_type = request.form.get('document_type')
    description = request.form.get('description')
    tags = request.form.get('tags')
    related_entity_type = request.form.get('related_entity_type')
    related_entity_id = request.form.get('related_entity_id')
    
    tag_list = [t.strip() for t in tags.split(',')] if tags else None
    
    # Create document
    try:
        from io import BytesIO
        service = DocumentService()
        
        document = service.create_document(
            organization_id=str(organization_id),
            name=name,
            file_data=BytesIO(file_content),
            filename=filename,
            mime_type=mime_type,
            owner_id=user_id,
            category_id=category_id,
            document_type=document_type,
            description=description,
            tags=tag_list,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )
        
        return jsonify({
            'success': True,
            'document': document.to_dict(include_url=True)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception(f"Upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500


@upload_bp.route('/upload/bulk', methods=['POST'])
@jwt_required()
def upload_bulk():
    """
    Upload multiple documents
    
    Form data:
    - files[]: Multiple files
    - category_id: Category ID for all files (optional)
    """
    user_id = get_jwt_identity()
    organization_id = g.current_user.organization_id
    
    files = request.files.getlist('files[]')
    
    if not files or len(files) == 0:
        return jsonify({'error': 'No files provided'}), 400
    
    if len(files) > 50:
        return jsonify({'error': 'Too many files (max 50)'}), 400
    
    category_id = request.form.get('category_id')
    
    results = []
    service = DocumentService()
    virus_scan = VirusScanService()
    
    for file in files:
        filename = secure_filename(file.filename)
        
        try:
            file_content = file.read()
            mime_type = magic.from_buffer(file_content, mime=True)
            
            # Skip invalid files
            if mime_type not in DocumentService.ALLOWED_MIME_TYPES:
                results.append({
                    'filename': filename,
                    'success': False,
                    'error': f'File type not allowed: {mime_type}'
                })
                continue
            
            # Virus scan
            try:
                scan_result = virus_scan.scan_content(file_content)
                if not scan_result['clean']:
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': 'File contains malware'
                    })
                    continue
            except:
                pass
            
            # Upload
            from io import BytesIO
            document = service.create_document(
                organization_id=str(organization_id),
                name=filename,
                file_data=BytesIO(file_content),
                filename=filename,
                mime_type=mime_type,
                owner_id=user_id,
                category_id=category_id
            )
            
            results.append({
                'filename': filename,
                'success': True,
                'document': document.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Bulk upload error for {filename}: {e}")
            results.append({
                'filename': filename,
                'success': False,
                'error': str(e)
            })
    
    successful = sum(1 for r in results if r['success'])
    
    return jsonify({
        'success': True,
        'total': len(files),
        'successful': successful,
        'failed': len(files) - successful,
        'results': results
    })


@upload_bp.route('/upload/chunk/init', methods=['POST'])
@jwt_required()
def init_chunked_upload():
    """
    Initialize chunked upload for large files
    
    JSON body:
    - filename: Original filename
    - file_size: Total file size
    - mime_type: MIME type
    - chunk_size: Size of each chunk
    """
    user_id = get_jwt_identity()
    organization_id = g.current_user.organization_id
    
    data = request.get_json()
    
    filename = data.get('filename')
    file_size = data.get('file_size')
    mime_type = data.get('mime_type')
    chunk_size = data.get('chunk_size', 5 * 1024 * 1024)  # Default 5MB
    
    if not all([filename, file_size, mime_type]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if mime_type not in DocumentService.ALLOWED_MIME_TYPES:
        return jsonify({'error': f'File type not allowed: {mime_type}'}), 400
    
    if file_size > DocumentService.MAX_FILE_SIZE:
        return jsonify({'error': f'File too large: {file_size} bytes'}), 400
    
    # Generate upload ID
    import uuid
    upload_id = str(uuid.uuid4())
    
    # Calculate chunks
    total_chunks = (file_size + chunk_size - 1) // chunk_size
    
    # Store upload session in Redis
    from app.extensions import redis_client
    import json
    
    session_data = {
        'upload_id': upload_id,
        'filename': filename,
        'file_size': file_size,
        'mime_type': mime_type,
        'chunk_size': chunk_size,
        'total_chunks': total_chunks,
        'uploaded_chunks': [],
        'organization_id': str(organization_id),
        'user_id': user_id,
        'created_at': datetime.utcnow().isoformat(),
    }
    
    redis_client.setex(
        f"chunked_upload:{upload_id}",
        3600 * 24,  # 24 hour expiry
        json.dumps(session_data)
    )
    
    return jsonify({
        'upload_id': upload_id,
        'chunk_size': chunk_size,
        'total_chunks': total_chunks
    })


@upload_bp.route('/upload/chunk/<upload_id>', methods=['POST'])
@jwt_required()
def upload_chunk(upload_id: str):
    """
    Upload a chunk of a large file
    
    Form data:
    - chunk: The chunk data
    - chunk_number: Chunk index (0-based)
    """
    from app.extensions import redis_client
    import json
    
    # Get session
    session_data = redis_client.get(f"chunked_upload:{upload_id}")
    
    if not session_data:
        return jsonify({'error': 'Upload session not found or expired'}), 404
    
    session = json.loads(session_data)
    
    # Verify user
    user_id = get_jwt_identity()
    if session['user_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get chunk
    if 'chunk' not in request.files:
        return jsonify({'error': 'No chunk data'}), 400
    
    chunk = request.files['chunk']
    chunk_number = int(request.form.get('chunk_number', 0))
    
    if chunk_number >= session['total_chunks']:
        return jsonify({'error': 'Invalid chunk number'}), 400
    
    # Save chunk to temp storage
    chunk_path = os.path.join(
        tempfile.gettempdir(),
        f"chunk_{upload_id}_{chunk_number}"
    )
    
    chunk.save(chunk_path)
    
    # Update session
    session['uploaded_chunks'].append(chunk_number)
    session['uploaded_chunks'] = sorted(list(set(session['uploaded_chunks'])))
    
    redis_client.setex(
        f"chunked_upload:{upload_id}",
        3600 * 24,
        json.dumps(session)
    )
    
    return jsonify({
        'success': True,
        'chunk_number': chunk_number,
        'uploaded_chunks': len(session['uploaded_chunks']),
        'total_chunks': session['total_chunks']
    })


@upload_bp.route('/upload/chunk/<upload_id>/complete', methods=['POST'])
@jwt_required()
def complete_chunked_upload(upload_id: str):
    """
    Complete chunked upload by assembling chunks
    """
    from app.extensions import redis_client
    import json
    
    # Get session
    session_data = redis_client.get(f"chunked_upload:{upload_id}")
    
    if not session_data:
        return jsonify({'error': 'Upload session not found or expired'}), 404
    
    session = json.loads(session_data)
    
    # Verify all chunks uploaded
    if len(session['uploaded_chunks']) != session['total_chunks']:
        return jsonify({
            'error': 'Not all chunks uploaded',
            'uploaded': len(session['uploaded_chunks']),
            'required': session['total_chunks']
        }), 400
    
    # Assemble file
    assembled_path = os.path.join(
        tempfile.gettempdir(),
        f"assembled_{upload_id}"
    )
    
    try:
        with open(assembled_path, 'wb') as assembled:
            for i in range(session['total_chunks']):
                chunk_path = os.path.join(
                    tempfile.gettempdir(),
                    f"chunk_{upload_id}_{i}"
                )
                
                with open(chunk_path, 'rb') as chunk:
                    assembled.write(chunk.read())
                
                # Cleanup chunk
                os.remove(chunk_path)
        
        # Virus scan
        with open(assembled_path, 'rb') as f:
            file_content = f.read()
        
        virus_scan = VirusScanService()
        try:
            scan_result = virus_scan.scan_content(file_content)
            if not scan_result['clean']:
                os.remove(assembled_path)
                return jsonify({
                    'error': 'File contains malware',
                    'threat': scan_result.get('threat')
                }), 400
        except:
            pass
        
        # Get additional metadata from request
        data = request.get_json() or {}
        
        # Create document
        from io import BytesIO
        service = DocumentService()
        
        document = service.create_document(
            organization_id=session['organization_id'],
            name=data.get('name') or session['filename'],
            file_data=BytesIO(file_content),
            filename=session['filename'],
            mime_type=session['mime_type'],
            owner_id=session['user_id'],
            category_id=data.get('category_id'),
            document_type=data.get('document_type'),
            description=data.get('description'),
            tags=data.get('tags')
        )
        
        # Cleanup
        os.remove(assembled_path)
        redis_client.delete(f"chunked_upload:{upload_id}")
        
        return jsonify({
            'success': True,
            'document': document.to_dict(include_url=True)
        }), 201
        
    except Exception as e:
        logger.exception(f"Chunked upload completion error: {e}")
        # Cleanup on error
        if os.path.exists(assembled_path):
            os.remove(assembled_path)
        return jsonify({'error': 'Upload completion failed'}), 500
```

---

## TASK 5: OCR SERVICE

### 5.1 OCR Service

**File:** `backend/app/documents/services/ocr_service.py`

```python
"""
OCR Service
Optical Character Recognition for documents
"""

from typing import Optional, Dict, Any, Tuple
from io import BytesIO
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


class OCRService:
    """OCR processing service using Tesseract"""
    
    # Supported languages
    LANGUAGES = {
        'en': 'eng',
        'es': 'spa',
        'fr': 'fra',
        'de': 'deu',
        'it': 'ita',
        'pt': 'por',
        'nl': 'nld',
    }
    
    def __init__(self):
        import pytesseract
        
        # Configure Tesseract path if needed
        tesseract_cmd = os.getenv('TESSERACT_CMD')
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self.pytesseract = pytesseract
    
    def process_document(
        self,
        file_content: bytes,
        mime_type: str,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Process document and extract text
        
        Args:
            file_content: File bytes
            mime_type: File MIME type
            language: Language code
            
        Returns:
            Dict with 'text', 'confidence', 'pages', 'language'
        """
        lang_code = self.LANGUAGES.get(language, 'eng')
        
        if mime_type == 'application/pdf':
            return self._process_pdf(file_content, lang_code)
        elif mime_type.startswith('image/'):
            return self._process_image(file_content, lang_code)
        else:
            return {
                'text': '',
                'confidence': 0,
                'pages': 0,
                'language': language,
                'error': f'Unsupported mime type: {mime_type}'
            }
    
    def _process_pdf(
        self,
        file_content: bytes,
        lang_code: str
    ) -> Dict[str, Any]:
        """Process PDF document"""
        from pdf2image import convert_from_bytes
        from PIL import Image
        
        try:
            # Convert PDF to images
            images = convert_from_bytes(
                file_content,
                dpi=300,
                fmt='png'
            )
            
            all_text = []
            all_confidence = []
            
            for i, image in enumerate(images):
                # OCR each page
                page_result = self._ocr_image(image, lang_code)
                all_text.append(f"--- Page {i + 1} ---\n{page_result['text']}")
                all_confidence.append(page_result['confidence'])
            
            # Calculate average confidence
            avg_confidence = sum(all_confidence) / len(all_confidence) if all_confidence else 0
            
            return {
                'text': '\n\n'.join(all_text),
                'confidence': round(avg_confidence, 2),
                'pages': len(images),
                'language': lang_code,
            }
            
        except Exception as e:
            logger.error(f"PDF OCR error: {e}")
            return {
                'text': '',
                'confidence': 0,
                'pages': 0,
                'language': lang_code,
                'error': str(e)
            }
    
    def _process_image(
        self,
        file_content: bytes,
        lang_code: str
    ) -> Dict[str, Any]:
        """Process image file"""
        from PIL import Image
        
        try:
            image = Image.open(BytesIO(file_content))
            result = self._ocr_image(image, lang_code)
            
            return {
                'text': result['text'],
                'confidence': result['confidence'],
                'pages': 1,
                'language': lang_code,
            }
            
        except Exception as e:
            logger.error(f"Image OCR error: {e}")
            return {
                'text': '',
                'confidence': 0,
                'pages': 0,
                'language': lang_code,
                'error': str(e)
            }
    
    def _ocr_image(
        self,
        image,
        lang_code: str
    ) -> Dict[str, Any]:
        """OCR a single image"""
        from PIL import Image, ImageEnhance, ImageFilter
        
        # Preprocess image for better OCR
        image = self._preprocess_image(image)
        
        # Get OCR data with confidence
        ocr_data = self.pytesseract.image_to_data(
            image,
            lang=lang_code,
            output_type=self.pytesseract.Output.DICT
        )
        
        # Extract text
        text = self.pytesseract.image_to_string(image, lang=lang_code)
        
        # Calculate confidence
        confidences = [
            int(conf) for conf in ocr_data['conf']
            if conf != '-1'
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'text': text.strip(),
            'confidence': round(avg_confidence, 2),
        }
    
    def _preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        from PIL import Image, ImageEnhance, ImageFilter
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to grayscale
        image = image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)
        
        # Apply sharpening
        image = image.filter(ImageFilter.SHARPEN)
        
        # Binarization (threshold)
        threshold = 128
        image = image.point(lambda x: 0 if x < threshold else 255, '1')
        
        return image
    
    def detect_language(self, file_content: bytes, mime_type: str) -> str:
        """Detect document language"""
        # Simple approach: try OCR with English and check results
        # For production, use langdetect library
        try:
            from langdetect import detect
            
            # Get sample text
            if mime_type == 'application/pdf':
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(file_content, dpi=150, first_page=1, last_page=1)
                if images:
                    text = self.pytesseract.image_to_string(images[0])
            else:
                from PIL import Image
                image = Image.open(BytesIO(file_content))
                text = self.pytesseract.image_to_string(image)
            
            if text and len(text.strip()) > 20:
                return detect(text)
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
        
        return 'en'  # Default to English
    
    def extract_tables(
        self,
        file_content: bytes,
        mime_type: str
    ) -> list:
        """Extract tables from document"""
        # For basic implementation, use image processing
        # For production, consider Camelot or Tabula for PDFs
        
        tables = []
        
        try:
            if mime_type == 'application/pdf':
                import camelot
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                    f.write(file_content)
                    temp_path = f.name
                
                try:
                    extracted = camelot.read_pdf(temp_path, pages='all')
                    
                    for table in extracted:
                        tables.append({
                            'page': table.page,
                            'data': table.df.values.tolist(),
                            'columns': table.df.columns.tolist(),
                            'accuracy': table.accuracy
                        })
                finally:
                    os.remove(temp_path)
        
        except ImportError:
            logger.warning("Camelot not installed, table extraction skipped")
        except Exception as e:
            logger.error(f"Table extraction error: {e}")
        
        return tables
```

---

## TASK 6: AI EXTRACTION SERVICE

### 6.1 AI Data Extraction Service

**File:** `backend/app/documents/services/extraction_service.py`

```python
"""
AI Extraction Service
Extract structured data from documents using AI
"""

from typing import Optional, Dict, Any, List
import json
import logging
import os

logger = logging.getLogger(__name__)


class ExtractionService:
    """AI-powered data extraction from documents"""
    
    # Document type schemas
    EXTRACTION_SCHEMAS = {
        'invoice': {
            'vendor_name': 'string',
            'vendor_address': 'string',
            'vendor_tax_id': 'string',
            'invoice_number': 'string',
            'invoice_date': 'date',
            'due_date': 'date',
            'currency': 'string',
            'subtotal': 'number',
            'tax_amount': 'number',
            'total_amount': 'number',
            'line_items': [{
                'description': 'string',
                'quantity': 'number',
                'unit_price': 'number',
                'amount': 'number'
            }],
            'payment_terms': 'string',
            'bank_details': 'string'
        },
        'receipt': {
            'merchant_name': 'string',
            'merchant_address': 'string',
            'date': 'date',
            'time': 'string',
            'items': [{
                'name': 'string',
                'quantity': 'number',
                'price': 'number'
            }],
            'subtotal': 'number',
            'tax': 'number',
            'total': 'number',
            'payment_method': 'string',
            'card_last_four': 'string'
        },
        'contract': {
            'contract_type': 'string',
            'parties': ['string'],
            'effective_date': 'date',
            'expiration_date': 'date',
            'contract_value': 'number',
            'key_terms': ['string'],
            'signatures_required': 'number'
        },
        'purchase_order': {
            'po_number': 'string',
            'date': 'date',
            'vendor': 'string',
            'ship_to': 'string',
            'line_items': [{
                'item_number': 'string',
                'description': 'string',
                'quantity': 'number',
                'unit_price': 'number'
            }],
            'total': 'number',
            'delivery_date': 'date'
        },
        'shipping_label': {
            'carrier': 'string',
            'tracking_number': 'string',
            'ship_from': {
                'name': 'string',
                'address': 'string',
                'city': 'string',
                'postal_code': 'string',
                'country': 'string'
            },
            'ship_to': {
                'name': 'string',
                'address': 'string',
                'city': 'string',
                'postal_code': 'string',
                'country': 'string'
            },
            'weight': 'string',
            'service_type': 'string'
        }
    }
    
    def __init__(self):
        self.provider = os.getenv('AI_PROVIDER', 'openai')  # openai, anthropic
        self.client = self._init_client()
    
    def _init_client(self):
        """Initialize AI client"""
        if self.provider == 'openai':
            from openai import OpenAI
            return OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        elif self.provider == 'anthropic':
            from anthropic import Anthropic
            return Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")
    
    def extract_data(
        self,
        ocr_text: str,
        document_type: str = None,
        hints: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from OCR text
        
        Args:
            ocr_text: Text from OCR
            document_type: Type of document (invoice, receipt, etc.)
            hints: Additional hints for extraction
            
        Returns:
            Dict with extracted data and confidence
        """
        if not ocr_text or len(ocr_text.strip()) < 10:
            return {
                'success': False,
                'error': 'Insufficient text for extraction',
                'data': {}
            }
        
        # Auto-detect document type if not provided
        if not document_type:
            document_type = self.classify_document(ocr_text)
        
        # Get schema for document type
        schema = self.EXTRACTION_SCHEMAS.get(document_type)
        
        if not schema:
            # Generic extraction
            return self._generic_extraction(ocr_text)
        
        # Extract with schema
        return self._extract_with_schema(ocr_text, document_type, schema, hints)
    
    def classify_document(self, ocr_text: str) -> str:
        """Classify document type from text"""
        prompt = f"""Classify this document into one of these categories:
- invoice
- receipt
- contract
- purchase_order
- shipping_label
- other

Document text:
{ocr_text[:2000]}

Respond with only the category name, nothing else."""

        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=20,
                    temperature=0
                )
                result = response.choices[0].message.content.strip().lower()
            else:
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=20,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text.strip().lower()
            
            # Validate result
            valid_types = list(self.EXTRACTION_SCHEMAS.keys()) + ['other']
            return result if result in valid_types else 'other'
            
        except Exception as e:
            logger.error(f"Document classification error: {e}")
            return 'other'
    
    def _extract_with_schema(
        self,
        ocr_text: str,
        document_type: str,
        schema: Dict,
        hints: Dict = None
    ) -> Dict[str, Any]:
        """Extract data using schema"""
        schema_json = json.dumps(schema, indent=2)
        hints_text = f"\nAdditional context: {json.dumps(hints)}" if hints else ""
        
        prompt = f"""Extract structured data from this {document_type} document.

Expected data schema:
{schema_json}

Document text:
{ocr_text}
{hints_text}

Instructions:
1. Extract all fields that match the schema
2. Use null for missing fields
3. Parse dates as ISO format (YYYY-MM-DD)
4. Parse numbers without currency symbols
5. Be precise with amounts and numbers

Respond with valid JSON only, no explanations."""

        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content
            else:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
            
            # Parse JSON
            extracted_data = json.loads(result_text)
            
            # Validate and clean data
            cleaned_data = self._validate_extracted_data(extracted_data, schema)
            
            return {
                'success': True,
                'document_type': document_type,
                'data': cleaned_data,
                'confidence': self._calculate_confidence(cleaned_data, schema)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in extraction: {e}")
            return {
                'success': False,
                'error': 'Failed to parse extraction result',
                'data': {}
            }
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }
    
    def _generic_extraction(self, ocr_text: str) -> Dict[str, Any]:
        """Generic extraction without schema"""
        prompt = f"""Extract any structured data from this document.
Look for:
- Dates
- Amounts/prices
- Names (people, companies)
- Addresses
- Reference numbers
- Key-value pairs

Document text:
{ocr_text}

Respond with valid JSON containing the extracted data."""

        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content
            else:
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
            
            extracted_data = json.loads(result_text)
            
            return {
                'success': True,
                'document_type': 'other',
                'data': extracted_data,
                'confidence': 0.7  # Lower confidence for generic extraction
            }
            
        except Exception as e:
            logger.error(f"Generic extraction error: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }
    
    def _validate_extracted_data(
        self,
        data: Dict,
        schema: Dict
    ) -> Dict:
        """Validate and clean extracted data"""
        cleaned = {}
        
        for key, expected_type in schema.items():
            if key not in data:
                cleaned[key] = None
                continue
            
            value = data[key]
            
            if expected_type == 'string':
                cleaned[key] = str(value) if value else None
            elif expected_type == 'number':
                cleaned[key] = self._parse_number(value)
            elif expected_type == 'date':
                cleaned[key] = self._parse_date(value)
            elif isinstance(expected_type, list):
                if isinstance(value, list):
                    cleaned[key] = value
                else:
                    cleaned[key] = [value] if value else []
            elif isinstance(expected_type, dict):
                cleaned[key] = value if isinstance(value, dict) else {}
            else:
                cleaned[key] = value
        
        return cleaned
    
    def _parse_number(self, value) -> Optional[float]:
        """Parse number from various formats"""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove currency symbols and whitespace
            import re
            cleaned = re.sub(r'[^\d.,\-]', '', value)
            cleaned = cleaned.replace(',', '')
            
            try:
                return float(cleaned)
            except:
                return None
        
        return None
    
    def _parse_date(self, value) -> Optional[str]:
        """Parse date to ISO format"""
        if value is None:
            return None
        
        if isinstance(value, str):
            from dateutil import parser
            try:
                parsed = parser.parse(value)
                return parsed.strftime('%Y-%m-%d')
            except:
                return value  # Return as-is if parsing fails
        
        return str(value)
    
    def _calculate_confidence(
        self,
        data: Dict,
        schema: Dict
    ) -> float:
        """Calculate extraction confidence score"""
        if not schema:
            return 0.5
        
        total_fields = len(schema)
        filled_fields = sum(
            1 for key in schema
            if key in data and data[key] is not None
        )
        
        return round(filled_fields / total_fields, 2)
    
    def suggest_tags(self, ocr_text: str, document_type: str) -> List[str]:
        """Suggest tags for document"""
        prompt = f"""Suggest 3-5 relevant tags for this {document_type} document.
Tags should be single words or short phrases, lowercase.

Document text:
{ocr_text[:1000]}

Respond with a JSON array of tag strings only."""

        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.5
                )
                result = response.choices[0].message.content
            else:
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text
            
            tags = json.loads(result)
            return tags if isinstance(tags, list) else []
            
        except Exception as e:
            logger.error(f"Tag suggestion error: {e}")
            return []
```

---

## TASK 7: CELERY TASKS

### 7.1 Document Processing Tasks

**File:** `backend/app/workers/tasks/document_tasks.py`

```python
"""
Document Processing Celery Tasks
Background tasks for OCR, extraction, and indexing
"""

from celery import shared_task
from datetime import datetime
import logging

from app.extensions import db
from app.documents.models.document import Document
from app.documents.services.ocr_service import OCRService
from app.documents.services.extraction_service import ExtractionService
from app.documents.services.storage import get_storage_provider
from app.documents.services.thumbnail_service import ThumbnailService
from app.documents.services.search_service import SearchService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document_ocr(self, document_id: str):
    """
    Process document OCR
    
    Args:
        document_id: Document ID to process
    """
    try:
        document = Document.query.get(document_id)
        
        if not document:
            logger.error(f"Document not found: {document_id}")
            return
        
        if document.ocr_status == 'completed':
            logger.info(f"OCR already completed for document: {document_id}")
            return
        
        # Update status
        document.ocr_status = 'processing'
        db.session.commit()
        
        # Download file
        storage = get_storage_provider(document.storage_provider)
        file_content = storage.download(document.storage_key, document.storage_bucket)
        
        # Detect language
        ocr_service = OCRService()
        language = ocr_service.detect_language(file_content, document.mime_type)
        
        # Process OCR
        result = ocr_service.process_document(
            file_content=file_content,
            mime_type=document.mime_type,
            language=language
        )
        
        if result.get('error'):
            document.ocr_status = 'failed'
            logger.error(f"OCR failed for document {document_id}: {result['error']}")
        else:
            document.ocr_status = 'completed'
            document.ocr_text = result['text']
            document.ocr_confidence = result['confidence']
            document.ocr_language = language
            document.ocr_completed_at = datetime.utcnow()
            
            logger.info(f"OCR completed for document {document_id}, confidence: {result['confidence']}")
        
        db.session.commit()
        
        # Trigger extraction if OCR successful
        if document.ocr_status == 'completed' and document.ocr_text:
            process_document_extraction.delay(document_id)
        else:
            # Mark document as active if no extraction needed
            document.status = 'active'
            db.session.commit()
        
    except Exception as e:
        logger.exception(f"OCR task error for document {document_id}: {e}")
        
        try:
            document = Document.query.get(document_id)
            if document:
                document.ocr_status = 'failed'
                db.session.commit()
        except:
            pass
        
        # Retry
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def process_document_extraction(self, document_id: str):
    """
    Extract structured data from document using AI
    
    Args:
        document_id: Document ID to process
    """
    try:
        document = Document.query.get(document_id)
        
        if not document:
            logger.error(f"Document not found: {document_id}")
            return
        
        if not document.ocr_text:
            logger.info(f"No OCR text available for document: {document_id}")
            document.extraction_status = 'skipped'
            document.status = 'active'
            db.session.commit()
            return
        
        # Update status
        document.extraction_status = 'processing'
        db.session.commit()
        
        # Extract data
        extraction_service = ExtractionService()
        result = extraction_service.extract_data(
            ocr_text=document.ocr_text,
            document_type=document.document_type
        )
        
        if result['success']:
            document.extraction_status = 'completed'
            document.extracted_data = result['data']
            document.extraction_confidence = result.get('confidence', 0)
            document.extraction_completed_at = datetime.utcnow()
            
            # Update document type if detected
            if result.get('document_type') and not document.document_type:
                document.document_type = result['document_type']
                document.ai_type_suggestion = result['document_type']
            
            # Get tag suggestions
            tags = extraction_service.suggest_tags(
                document.ocr_text,
                document.document_type or 'document'
            )
            document.ai_tags = tags
            
            logger.info(f"Extraction completed for document {document_id}")
        else:
            document.extraction_status = 'failed'
            logger.error(f"Extraction failed for document {document_id}: {result.get('error')}")
        
        # Mark document as active
        document.status = 'active'
        
        # Update search vector
        document.update_search_vector()
        
        db.session.commit()
        
        # Index for search
        index_document_search.delay(document_id)
        
    except Exception as e:
        logger.exception(f"Extraction task error for document {document_id}: {e}")
        
        try:
            document = Document.query.get(document_id)
            if document:
                document.extraction_status = 'failed'
                document.status = 'active'  # Still mark as active
                db.session.commit()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def generate_document_thumbnail(self, document_id: str):
    """
    Generate thumbnail and preview for document
    
    Args:
        document_id: Document ID to process
    """
    try:
        document = Document.query.get(document_id)
        
        if not document:
            logger.error(f"Document not found: {document_id}")
            return
        
        # Download file
        storage = get_storage_provider(document.storage_provider)
        file_content = storage.download(document.storage_key, document.storage_bucket)
        
        # Generate thumbnail
        thumbnail_service = ThumbnailService()
        
        thumbnail_result = thumbnail_service.generate_thumbnail(
            file_content=file_content,
            mime_type=document.mime_type,
            document_id=str(document.id),
            organization_id=str(document.organization_id)
        )
        
        if thumbnail_result:
            document.thumbnail_url = thumbnail_result.get('thumbnail_url')
            document.preview_url = thumbnail_result.get('preview_url')
            db.session.commit()
            
            logger.info(f"Thumbnail generated for document {document_id}")
        
    except Exception as e:
        logger.exception(f"Thumbnail task error for document {document_id}: {e}")
        raise self.retry(exc=e, countdown=30)


@shared_task(bind=True, max_retries=3)
def index_document_search(self, document_id: str):
    """
    Index document for full-text search
    
    Args:
        document_id: Document ID to index
    """
    try:
        document = Document.query.get(document_id)
        
        if not document:
            logger.error(f"Document not found: {document_id}")
            return
        
        # Index in Elasticsearch
        search_service = SearchService()
        search_service.index_document(document)
        
        logger.info(f"Document indexed for search: {document_id}")
        
    except Exception as e:
        logger.exception(f"Search index task error for document {document_id}: {e}")
        raise self.retry(exc=e, countdown=30)


@shared_task
def cleanup_expired_documents():
    """
    Cleanup expired/deleted documents
    Runs daily via Celery Beat
    """
    from datetime import timedelta
    
    # Permanently delete documents marked as deleted > 30 days ago
    cutoff = datetime.utcnow() - timedelta(days=30)
    
    expired = Document.query.filter(
        Document.status == 'deleted',
        Document.deleted_at < cutoff
    ).all()
    
    storage = get_storage_provider()
    deleted_count = 0
    
    for document in expired:
        try:
            # Delete from storage
            storage.delete(document.storage_key, document.storage_bucket)
            
            # Delete versions
            for version in document.versions:
                storage.delete(version.storage_key, document.storage_bucket)
            
            # Delete record
            db.session.delete(document)
            deleted_count += 1
            
        except Exception as e:
            logger.error(f"Failed to cleanup document {document.id}: {e}")
    
    db.session.commit()
    
    logger.info(f"Cleanup completed: {deleted_count} documents permanently deleted")
```

---

## Continue to Part 3 for Search, Signatures, and Frontend

---

*Phase 13 Tasks Part 2 - LogiAccounting Pro*
*Upload Service, OCR & AI Extraction*
