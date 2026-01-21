# LogiAccounting Pro - Phase 13 Tasks Part 3

## SEARCH SERVICE, SIGNATURES & FRONTEND UI

---

## TASK 8: ELASTICSEARCH SEARCH SERVICE

### 8.1 Search Service

**File:** `backend/app/documents/services/search_service.py`

```python
"""
Search Service
Elasticsearch integration for document search
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import os
import logging

from app.documents.models.document import Document

logger = logging.getLogger(__name__)


class SearchService:
    """Elasticsearch search service for documents"""
    
    INDEX_NAME = 'documents'
    
    # Index mapping
    INDEX_MAPPING = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "document_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding", "snowball"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "organization_id": {"type": "keyword"},
                "folder_id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "analyzer": "document_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {"type": "completion"}
                    }
                },
                "original_name": {"type": "keyword"},
                "description": {
                    "type": "text",
                    "analyzer": "document_analyzer"
                },
                "content": {
                    "type": "text",
                    "analyzer": "document_analyzer"
                },
                "document_type": {"type": "keyword"},
                "mime_type": {"type": "keyword"},
                "file_extension": {"type": "keyword"},
                "file_size": {"type": "long"},
                "status": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "created_by": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "extracted_data": {
                    "type": "object",
                    "enabled": True
                },
                "extracted_data_flat": {
                    "type": "text",
                    "analyzer": "document_analyzer"
                },
                "related_entity_type": {"type": "keyword"},
                "related_entity_id": {"type": "keyword"}
            }
        }
    }
    
    def __init__(self):
        self.es = self._create_client()
        self._ensure_index()
    
    def _create_client(self) -> Elasticsearch:
        """Create Elasticsearch client"""
        host = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
        
        return Elasticsearch(
            hosts=[host],
            basic_auth=(
                os.getenv('ELASTICSEARCH_USER', 'elastic'),
                os.getenv('ELASTICSEARCH_PASSWORD', '')
            ) if os.getenv('ELASTICSEARCH_PASSWORD') else None,
            verify_certs=os.getenv('ELASTICSEARCH_VERIFY_CERTS', 'false').lower() == 'true'
        )
    
    def _ensure_index(self):
        """Ensure index exists with proper mapping"""
        try:
            if not self.es.indices.exists(index=self.INDEX_NAME):
                self.es.indices.create(
                    index=self.INDEX_NAME,
                    body=self.INDEX_MAPPING
                )
                logger.info(f"Created Elasticsearch index: {self.INDEX_NAME}")
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
    
    def index_document(self, document: Document):
        """
        Index a single document
        
        Args:
            document: Document model instance
        """
        doc_body = self._document_to_index(document)
        
        try:
            self.es.index(
                index=self.INDEX_NAME,
                id=str(document.id),
                body=doc_body,
                refresh=True
            )
            logger.debug(f"Indexed document: {document.id}")
        except Exception as e:
            logger.error(f"Failed to index document {document.id}: {e}")
            raise
    
    def bulk_index(self, documents: List[Document]):
        """
        Bulk index multiple documents
        
        Args:
            documents: List of Document model instances
        """
        actions = []
        
        for doc in documents:
            actions.append({
                "_index": self.INDEX_NAME,
                "_id": str(doc.id),
                "_source": self._document_to_index(doc)
            })
        
        try:
            success, failed = bulk(self.es, actions, refresh=True)
            logger.info(f"Bulk indexed {success} documents, {len(failed)} failed")
        except Exception as e:
            logger.error(f"Bulk index failed: {e}")
            raise
    
    def delete_document(self, document_id: str):
        """Remove document from index"""
        try:
            self.es.delete(
                index=self.INDEX_NAME,
                id=document_id,
                refresh=True
            )
            logger.debug(f"Deleted document from index: {document_id}")
        except Exception as e:
            logger.warning(f"Failed to delete document {document_id} from index: {e}")
    
    def search(
        self,
        organization_id: str,
        query: str = None,
        filters: Dict[str, Any] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = '_score',
        sort_order: str = 'desc'
    ) -> Tuple[List[Dict], int, Dict]:
        """
        Search documents
        
        Args:
            organization_id: Organization ID to scope search
            query: Search query string
            filters: Filter conditions
            page: Page number (1-indexed)
            per_page: Results per page
            sort_by: Sort field
            sort_order: Sort direction
            
        Returns:
            Tuple of (results, total_count, aggregations)
        """
        filters = filters or {}
        
        # Build query
        must_conditions = [
            {"term": {"organization_id": organization_id}}
        ]
        
        filter_conditions = []
        
        # Full-text search
        if query:
            must_conditions.append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "name^3",
                        "name.keyword^2",
                        "description^2",
                        "content",
                        "extracted_data_flat"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        
        # Apply filters
        if filters.get('folder_id'):
            filter_conditions.append({"term": {"folder_id": filters['folder_id']}})
        
        if filters.get('document_type'):
            filter_conditions.append({"term": {"document_type": filters['document_type']}})
        
        if filters.get('mime_type'):
            filter_conditions.append({"term": {"mime_type": filters['mime_type']}})
        
        if filters.get('status'):
            filter_conditions.append({"term": {"status": filters['status']}})
        else:
            # Default: exclude deleted
            filter_conditions.append({"terms": {"status": ["ready", "processing"]}})
        
        if filters.get('tags'):
            filter_conditions.append({"terms": {"tags": filters['tags']}})
        
        if filters.get('created_by'):
            filter_conditions.append({"term": {"created_by": filters['created_by']}})
        
        if filters.get('date_from') or filters.get('date_to'):
            date_range = {}
            if filters.get('date_from'):
                date_range['gte'] = filters['date_from']
            if filters.get('date_to'):
                date_range['lte'] = filters['date_to']
            filter_conditions.append({"range": {"created_at": date_range}})
        
        if filters.get('file_size_min') or filters.get('file_size_max'):
            size_range = {}
            if filters.get('file_size_min'):
                size_range['gte'] = filters['file_size_min']
            if filters.get('file_size_max'):
                size_range['lte'] = filters['file_size_max']
            filter_conditions.append({"range": {"file_size": size_range}})
        
        if filters.get('related_entity_type'):
            filter_conditions.append({"term": {"related_entity_type": filters['related_entity_type']}})
        
        if filters.get('related_entity_id'):
            filter_conditions.append({"term": {"related_entity_id": filters['related_entity_id']}})
        
        # Build search body
        search_body = {
            "query": {
                "bool": {
                    "must": must_conditions,
                    "filter": filter_conditions
                }
            },
            "from": (page - 1) * per_page,
            "size": per_page,
            "highlight": {
                "fields": {
                    "name": {},
                    "content": {"fragment_size": 200, "number_of_fragments": 3},
                    "description": {}
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            },
            "aggs": {
                "document_types": {
                    "terms": {"field": "document_type", "size": 20}
                },
                "mime_types": {
                    "terms": {"field": "mime_type", "size": 20}
                },
                "tags": {
                    "terms": {"field": "tags", "size": 50}
                },
                "date_histogram": {
                    "date_histogram": {
                        "field": "created_at",
                        "calendar_interval": "month"
                    }
                }
            }
        }
        
        # Apply sorting
        if sort_by != '_score' or not query:
            search_body["sort"] = [
                {sort_by: {"order": sort_order}}
            ]
        
        try:
            response = self.es.search(
                index=self.INDEX_NAME,
                body=search_body
            )
            
            # Parse results
            hits = response['hits']['hits']
            total = response['hits']['total']['value']
            aggregations = response.get('aggregations', {})
            
            results = []
            for hit in hits:
                result = hit['_source']
                result['_score'] = hit['_score']
                result['_highlights'] = hit.get('highlight', {})
                results.append(result)
            
            return results, total, aggregations
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [], 0, {}
    
    def suggest(
        self,
        organization_id: str,
        prefix: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get search suggestions (autocomplete)
        
        Args:
            organization_id: Organization ID
            prefix: Search prefix
            limit: Max suggestions
            
        Returns:
            List of suggestions
        """
        try:
            response = self.es.search(
                index=self.INDEX_NAME,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"organization_id": organization_id}},
                                {
                                    "bool": {
                                        "should": [
                                            {"prefix": {"name.keyword": {"value": prefix, "boost": 2}}},
                                            {"match_phrase_prefix": {"name": prefix}}
                                        ]
                                    }
                                }
                            ],
                            "filter": [
                                {"terms": {"status": ["ready", "processing"]}}
                            ]
                        }
                    },
                    "size": limit,
                    "_source": ["name"]
                }
            )
            
            suggestions = []
            for hit in response['hits']['hits']:
                name = hit['_source'].get('name')
                if name and name not in suggestions:
                    suggestions.append(name)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Suggestion failed: {e}")
            return []
    
    def get_facets(
        self,
        organization_id: str,
        query: str = None
    ) -> Dict[str, List[Dict]]:
        """
        Get facet counts for filtering
        
        Args:
            organization_id: Organization ID
            query: Optional search query
            
        Returns:
            Dict of facet name to list of {value, count}
        """
        must_conditions = [
            {"term": {"organization_id": organization_id}}
        ]
        
        if query:
            must_conditions.append({
                "multi_match": {
                    "query": query,
                    "fields": ["name", "content", "description"]
                }
            })
        
        try:
            response = self.es.search(
                index=self.INDEX_NAME,
                body={
                    "query": {
                        "bool": {
                            "must": must_conditions,
                            "filter": [
                                {"terms": {"status": ["ready", "processing"]}}
                            ]
                        }
                    },
                    "size": 0,
                    "aggs": {
                        "document_types": {
                            "terms": {"field": "document_type", "size": 50}
                        },
                        "mime_types": {
                            "terms": {"field": "mime_type", "size": 50}
                        },
                        "tags": {
                            "terms": {"field": "tags", "size": 100}
                        },
                        "folders": {
                            "terms": {"field": "folder_id", "size": 100}
                        }
                    }
                }
            )
            
            facets = {}
            aggs = response.get('aggregations', {})
            
            for facet_name, facet_data in aggs.items():
                facets[facet_name] = [
                    {"value": bucket['key'], "count": bucket['doc_count']}
                    for bucket in facet_data.get('buckets', [])
                ]
            
            return facets
            
        except Exception as e:
            logger.error(f"Facets failed: {e}")
            return {}
    
    def _document_to_index(self, document: Document) -> Dict[str, Any]:
        """Convert Document model to index document"""
        # Flatten extracted data for search
        extracted_flat = ""
        if document.extracted_data:
            extracted_flat = " ".join(
                str(v) for v in self._flatten_dict(document.extracted_data)
            )
        
        return {
            "id": str(document.id),
            "organization_id": str(document.organization_id),
            "folder_id": str(document.category_id) if document.category_id else None,
            "name": document.name,
            "original_name": document.original_filename,
            "description": document.description,
            "content": document.ocr_text or "",
            "document_type": document.document_type,
            "mime_type": document.mime_type,
            "file_extension": document.mime_type.split('/')[-1] if document.mime_type else None,
            "file_size": document.file_size,
            "status": document.status,
            "tags": [t.name for t in document.tags] if document.tags else [],
            "created_by": str(document.owner_id) if document.owner_id else None,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            "extracted_data": document.extracted_data or {},
            "extracted_data_flat": extracted_flat,
            "related_entity_type": document.related_entity_type,
            "related_entity_id": str(document.related_entity_id) if document.related_entity_id else None
        }
    
    def _flatten_dict(self, d: Dict, parent_key: str = '') -> List:
        """Flatten nested dict values for search"""
        items = []
        for k, v in d.items():
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, f"{parent_key}{k}_"))
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item))
                    else:
                        items.append(str(item))
            else:
                items.append(str(v))
        return items
```

### 8.2 Search Routes

**File:** `backend/app/documents/routes/search.py`

```python
"""
Search Routes
Document search API endpoints
"""

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from app.documents.services.search_service import SearchService

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__, url_prefix='/api/v1/documents')


@search_bp.route('/search', methods=['GET'])
@jwt_required()
def search_documents():
    """
    Search documents with filters
    
    Query params:
    - q: Search query
    - folder_id: Filter by folder
    - document_type: Filter by type
    - mime_type: Filter by MIME type
    - tags: Filter by tags (comma-separated)
    - status: Filter by status
    - date_from: Filter by created date (ISO)
    - date_to: Filter by created date (ISO)
    - created_by: Filter by creator
    - related_entity_type: Filter by related entity type
    - related_entity_id: Filter by related entity ID
    - page: Page number
    - per_page: Results per page
    - sort_by: Sort field
    - sort_order: Sort direction (asc/desc)
    """
    organization_id = str(g.current_user.organization_id)
    
    # Parse query params
    query = request.args.get('q', '').strip()
    
    filters = {}
    
    if request.args.get('folder_id'):
        filters['folder_id'] = request.args.get('folder_id')
    
    if request.args.get('document_type'):
        filters['document_type'] = request.args.get('document_type')
    
    if request.args.get('mime_type'):
        filters['mime_type'] = request.args.get('mime_type')
    
    if request.args.get('tags'):
        filters['tags'] = request.args.get('tags').split(',')
    
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    
    if request.args.get('date_from'):
        filters['date_from'] = request.args.get('date_from')
    
    if request.args.get('date_to'):
        filters['date_to'] = request.args.get('date_to')
    
    if request.args.get('created_by'):
        filters['created_by'] = request.args.get('created_by')
    
    if request.args.get('related_entity_type'):
        filters['related_entity_type'] = request.args.get('related_entity_type')
    
    if request.args.get('related_entity_id'):
        filters['related_entity_id'] = request.args.get('related_entity_id')
    
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)
    sort_by = request.args.get('sort_by', '_score' if query else 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Execute search
    search_service = SearchService()
    
    results, total, aggregations = search_service.search(
        organization_id=organization_id,
        query=query or None,
        filters=filters,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Format response
    return jsonify({
        'success': True,
        'data': {
            'results': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            },
            'facets': {
                'document_types': aggregations.get('document_types', {}).get('buckets', []),
                'mime_types': aggregations.get('mime_types', {}).get('buckets', []),
                'tags': aggregations.get('tags', {}).get('buckets', [])
            }
        }
    })


@search_bp.route('/search/suggest', methods=['GET'])
@jwt_required()
def search_suggestions():
    """
    Get search suggestions (autocomplete)
    
    Query params:
    - q: Search prefix
    - limit: Max suggestions (default 10)
    """
    organization_id = str(g.current_user.organization_id)
    
    prefix = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 20)
    
    if len(prefix) < 2:
        return jsonify({'success': True, 'suggestions': []})
    
    search_service = SearchService()
    suggestions = search_service.suggest(
        organization_id=organization_id,
        prefix=prefix,
        limit=limit
    )
    
    return jsonify({
        'success': True,
        'suggestions': suggestions
    })


@search_bp.route('/search/facets', methods=['GET'])
@jwt_required()
def get_facets():
    """
    Get facet counts for filtering
    
    Query params:
    - q: Optional search query to scope facets
    """
    organization_id = str(g.current_user.organization_id)
    query = request.args.get('q', '').strip() or None
    
    search_service = SearchService()
    facets = search_service.get_facets(
        organization_id=organization_id,
        query=query
    )
    
    return jsonify({
        'success': True,
        'facets': facets
    })
```

---

## TASK 9: DIGITAL SIGNATURE SERVICE

### 9.1 Signature Service

**File:** `backend/app/documents/services/signature_service.py`

```python
"""
Digital Signature Service
E-signature functionality for documents
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from flask import current_app
import secrets
import hashlib
import logging
import base64

from app.extensions import db
from app.documents.models.document import Document
from app.documents.models.signature_request import SignatureRequest, SignatureRecipient

logger = logging.getLogger(__name__)


class SignatureService:
    """Service for document signing workflows"""
    
    def create_request(
        self,
        document_id: str,
        organization_id: str,
        created_by: str,
        title: str,
        recipients: List[Dict[str, Any]],
        message: str = None,
        signing_order: str = 'parallel',
        expires_in_days: int = 30,
        reminder_frequency: int = 3
    ) -> SignatureRequest:
        """
        Create a signature request
        
        Args:
            document_id: Document to sign
            organization_id: Organization ID
            created_by: User creating request
            title: Request title
            recipients: List of {email, name, role, order}
            message: Optional message to signers
            signing_order: 'sequential' or 'parallel'
            expires_in_days: Days until expiration
            reminder_frequency: Days between reminders
            
        Returns:
            SignatureRequest instance
        """
        # Verify document exists
        document = Document.query.filter(
            Document.id == document_id,
            Document.organization_id == organization_id
        ).first()
        
        if not document:
            raise ValueError("Document not found")
        
        # Create request
        request = SignatureRequest(
            organization_id=organization_id,
            document_id=document_id,
            title=title,
            message=message,
            signing_order=signing_order,
            status='draft',
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            reminder_frequency_days=reminder_frequency,
            created_by=created_by
        )
        
        db.session.add(request)
        db.session.flush()
        
        # Add recipients
        for i, recipient_data in enumerate(recipients):
            recipient = SignatureRecipient(
                request_id=request.id,
                email=recipient_data['email'],
                name=recipient_data.get('name'),
                role=recipient_data.get('role', 'signer'),
                signing_order=recipient_data.get('order', i + 1) if signing_order == 'sequential' else 1,
                access_token=secrets.token_urlsafe(32),
                status='pending'
            )
            db.session.add(recipient)
        
        db.session.commit()
        
        logger.info(f"Created signature request {request.id} for document {document_id}")
        
        return request
    
    def send_request(self, request_id: str) -> bool:
        """
        Send signature request to recipients
        
        Args:
            request_id: Signature request ID
            
        Returns:
            True if sent successfully
        """
        request = SignatureRequest.query.get(request_id)
        
        if not request:
            raise ValueError("Request not found")
        
        if request.status not in ['draft', 'pending']:
            raise ValueError(f"Cannot send request in {request.status} status")
        
        # Get recipients to notify
        if request.signing_order == 'sequential':
            # Only notify first signer(s)
            recipients = SignatureRecipient.query.filter(
                SignatureRecipient.request_id == request_id,
                SignatureRecipient.signing_order == 1,
                SignatureRecipient.status == 'pending'
            ).all()
        else:
            # Notify all pending signers
            recipients = SignatureRecipient.query.filter(
                SignatureRecipient.request_id == request_id,
                SignatureRecipient.status == 'pending'
            ).all()
        
        # Send notifications
        from app.services.email_service import EmailService
        email_service = EmailService()
        
        for recipient in recipients:
            try:
                email_service.send_signature_request(
                    to_email=recipient.email,
                    to_name=recipient.name,
                    request_title=request.title,
                    message=request.message,
                    access_token=recipient.access_token,
                    expires_at=request.expires_at
                )
                
                recipient.status = 'sent'
                
            except Exception as e:
                logger.error(f"Failed to send signature request to {recipient.email}: {e}")
        
        request.status = 'pending'
        request.sent_at = datetime.utcnow()
        
        db.session.commit()
        
        return True
    
    def sign_document(
        self,
        access_token: str,
        signature_data: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        Sign a document
        
        Args:
            access_token: Recipient's access token
            signature_data: Base64 encoded signature image
            ip_address: Signer's IP address
            user_agent: Signer's user agent
            
        Returns:
            Dict with signing result
        """
        # Find recipient
        recipient = SignatureRecipient.query.filter(
            SignatureRecipient.access_token == access_token
        ).first()
        
        if not recipient:
            raise ValueError("Invalid access token")
        
        request = recipient.request
        
        # Validate request
        if request.status == 'completed':
            raise ValueError("This document has already been signed")
        
        if request.status == 'expired' or (request.expires_at and datetime.utcnow() > request.expires_at):
            raise ValueError("This signature request has expired")
        
        if request.status == 'cancelled':
            raise ValueError("This signature request has been cancelled")
        
        if recipient.status == 'signed':
            raise ValueError("You have already signed this document")
        
        # Check signing order
        if request.signing_order == 'sequential':
            # Check if previous signers have signed
            previous = SignatureRecipient.query.filter(
                SignatureRecipient.request_id == request.id,
                SignatureRecipient.signing_order < recipient.signing_order,
                SignatureRecipient.status != 'signed'
            ).first()
            
            if previous:
                raise ValueError("Waiting for previous signers")
        
        # Record signature
        recipient.signature_data = signature_data
        recipient.signed_at = datetime.utcnow()
        recipient.status = 'signed'
        recipient.ip_address = ip_address
        recipient.user_agent = user_agent
        
        # Generate new access token (invalidate old one)
        recipient.access_token = secrets.token_urlsafe(32)
        
        # Check if all signers have signed
        pending_count = SignatureRecipient.query.filter(
            SignatureRecipient.request_id == request.id,
            SignatureRecipient.role == 'signer',
            SignatureRecipient.status != 'signed'
        ).count()
        
        if pending_count == 0:
            # All signed - complete request
            request.status = 'completed'
            request.completed_at = datetime.utcnow()
            
            # Generate signed document
            signed_document = self._generate_signed_document(request)
            request.signed_document_id = signed_document.id
            
            logger.info(f"Signature request {request.id} completed")
        else:
            request.status = 'in_progress'
            
            # Notify next signer if sequential
            if request.signing_order == 'sequential':
                next_recipients = SignatureRecipient.query.filter(
                    SignatureRecipient.request_id == request.id,
                    SignatureRecipient.signing_order == recipient.signing_order + 1,
                    SignatureRecipient.status == 'pending'
                ).all()
                
                from app.services.email_service import EmailService
                email_service = EmailService()
                
                for next_recipient in next_recipients:
                    email_service.send_signature_request(
                        to_email=next_recipient.email,
                        to_name=next_recipient.name,
                        request_title=request.title,
                        message=request.message,
                        access_token=next_recipient.access_token,
                        expires_at=request.expires_at
                    )
                    next_recipient.status = 'sent'
        
        db.session.commit()
        
        return {
            'success': True,
            'request_status': request.status,
            'pending_signatures': pending_count,
            'signed_at': recipient.signed_at.isoformat()
        }
    
    def decline_signature(
        self,
        access_token: str,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Decline to sign a document
        
        Args:
            access_token: Recipient's access token
            reason: Optional decline reason
            
        Returns:
            Dict with decline result
        """
        recipient = SignatureRecipient.query.filter(
            SignatureRecipient.access_token == access_token
        ).first()
        
        if not recipient:
            raise ValueError("Invalid access token")
        
        request = recipient.request
        
        if request.status in ['completed', 'cancelled', 'expired']:
            raise ValueError(f"Cannot decline: request is {request.status}")
        
        # Record decline
        recipient.status = 'declined'
        recipient.decline_reason = reason
        recipient.declined_at = datetime.utcnow()
        
        # Mark request as declined
        request.status = 'declined'
        
        # Notify creator
        # TODO: Send notification
        
        db.session.commit()
        
        logger.info(f"Signature request {request.id} declined by {recipient.email}")
        
        return {
            'success': True,
            'request_status': 'declined'
        }
    
    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get signature request status"""
        request = SignatureRequest.query.get(request_id)
        
        if not request:
            return None
        
        recipients = SignatureRecipient.query.filter(
            SignatureRecipient.request_id == request_id
        ).order_by(SignatureRecipient.signing_order).all()
        
        return {
            'id': str(request.id),
            'title': request.title,
            'status': request.status,
            'document_id': str(request.document_id),
            'signing_order': request.signing_order,
            'created_at': request.created_at.isoformat(),
            'sent_at': request.sent_at.isoformat() if request.sent_at else None,
            'completed_at': request.completed_at.isoformat() if request.completed_at else None,
            'expires_at': request.expires_at.isoformat() if request.expires_at else None,
            'signed_document_id': str(request.signed_document_id) if request.signed_document_id else None,
            'recipients': [
                {
                    'email': r.email,
                    'name': r.name,
                    'role': r.role,
                    'order': r.signing_order,
                    'status': r.status,
                    'signed_at': r.signed_at.isoformat() if r.signed_at else None
                }
                for r in recipients
            ]
        }
    
    def verify_signatures(self, request_id: str) -> Dict[str, Any]:
        """
        Verify all signatures on a request
        
        Args:
            request_id: Signature request ID
            
        Returns:
            Verification result
        """
        request = SignatureRequest.query.get(request_id)
        
        if not request:
            raise ValueError("Request not found")
        
        if request.status != 'completed':
            return {
                'valid': False,
                'reason': f'Request is not completed (status: {request.status})'
            }
        
        recipients = SignatureRecipient.query.filter(
            SignatureRecipient.request_id == request_id,
            SignatureRecipient.role == 'signer'
        ).all()
        
        signatures = []
        for recipient in recipients:
            if recipient.status == 'signed':
                signatures.append({
                    'signer': recipient.email,
                    'name': recipient.name,
                    'signed_at': recipient.signed_at.isoformat(),
                    'ip_address': str(recipient.ip_address) if recipient.ip_address else None,
                    'valid': True
                })
        
        return {
            'valid': True,
            'document_id': str(request.document_id),
            'completed_at': request.completed_at.isoformat(),
            'signatures': signatures
        }
    
    def _generate_signed_document(self, request: SignatureRequest) -> Document:
        """Generate PDF with embedded signatures"""
        from app.documents.services.storage import get_storage_provider
        from PyPDF2 import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from io import BytesIO
        import uuid
        
        # Get original document
        original = Document.query.get(request.document_id)
        storage = get_storage_provider()
        
        original_content = storage.download(
            original.storage_key,
            original.storage_bucket
        )
        
        # Read PDF
        reader = PdfReader(BytesIO(original_content))
        writer = PdfWriter()
        
        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)
        
        # Add signature page
        signature_page = self._create_signature_page(request)
        writer.add_page(signature_page)
        
        # Write to bytes
        output = BytesIO()
        writer.write(output)
        output.seek(0)
        
        # Create new document record
        signed_doc = Document(
            organization_id=original.organization_id,
            name=f"{original.name} (Signed)",
            original_filename=f"{original.original_filename.rsplit('.', 1)[0]}_signed.pdf",
            mime_type='application/pdf',
            file_size=len(output.getvalue()),
            file_hash=hashlib.sha256(output.getvalue()).hexdigest(),
            storage_provider=original.storage_provider,
            storage_bucket=original.storage_bucket,
            status='ready',
            document_type='signed_document',
            owner_id=request.created_by
        )
        
        # Upload
        storage_key = storage.generate_key(
            organization_id=str(original.organization_id),
            document_id=str(signed_doc.id),
            filename=signed_doc.original_filename
        )
        
        storage.upload(
            file_data=output,
            key=storage_key,
            bucket=original.storage_bucket,
            content_type='application/pdf'
        )
        
        signed_doc.storage_key = storage_key
        
        db.session.add(signed_doc)
        db.session.commit()
        
        return signed_doc
    
    def _create_signature_page(self, request: SignatureRequest):
        """Create PDF page with signature details"""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        from io import BytesIO
        from PyPDF2 import PdfReader
        
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        width, height = letter
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Digital Signature Certificate")
        
        # Horizontal line
        c.line(50, height - 60, width - 50, height - 60)
        
        y = height - 100
        
        # Document info
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Document Information")
        y -= 20
        
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Title: {request.title}")
        y -= 15
        c.drawString(50, y, f"Request ID: {request.id}")
        y -= 15
        c.drawString(50, y, f"Completed: {request.completed_at.strftime('%Y-%m-%d %H:%M UTC')}")
        y -= 30
        
        # Signatures
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Signatures")
        y -= 20
        
        recipients = SignatureRecipient.query.filter(
            SignatureRecipient.request_id == request.id,
            SignatureRecipient.status == 'signed'
        ).all()
        
        for recipient in recipients:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, f"{recipient.name or recipient.email}")
            y -= 15
            
            c.setFont("Helvetica", 9)
            c.drawString(70, y, f"Email: {recipient.email}")
            y -= 12
            c.drawString(70, y, f"Signed: {recipient.signed_at.strftime('%Y-%m-%d %H:%M UTC')}")
            y -= 12
            c.drawString(70, y, f"IP: {recipient.ip_address or 'N/A'}")
            y -= 12
            
            # Draw signature image if available
            if recipient.signature_data:
                try:
                    sig_data = base64.b64decode(recipient.signature_data.split(',')[-1])
                    sig_image = ImageReader(BytesIO(sig_data))
                    c.drawImage(sig_image, 70, y - 50, width=150, height=50, preserveAspectRatio=True)
                    y -= 60
                except:
                    pass
            
            y -= 20
        
        # Footer
        c.setFont("Helvetica", 8)
        c.drawString(50, 50, "This document was electronically signed using LogiAccounting Pro.")
        c.drawString(50, 40, "The signatures above are legally binding.")
        
        c.save()
        
        packet.seek(0)
        return PdfReader(packet).pages[0]
```

### 9.2 Signature Request Model

**File:** `backend/app/documents/models/signature_request.py`

```python
"""
Signature Request Models
E-signature request and recipient tracking
"""

from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.extensions import db
import uuid


class SignatureRequest(db.Model):
    """Signature request for a document"""
    
    __tablename__ = 'signature_requests'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    document_id = Column(UUID(as_uuid=True), db.ForeignKey('documents.id'), nullable=False)
    
    # Request info
    title = Column(String(255), nullable=False)
    message = Column(Text)
    status = Column(String(50), default='draft')
    # draft, pending, in_progress, completed, declined, cancelled, expired
    
    # Workflow
    signing_order = Column(String(20), default='parallel')  # sequential, parallel
    
    # Expiration
    expires_at = Column(db.DateTime)
    reminder_frequency_days = Column(Integer, default=3)
    last_reminder_at = Column(db.DateTime)
    
    # Completion
    sent_at = Column(db.DateTime)
    completed_at = Column(db.DateTime)
    signed_document_id = Column(UUID(as_uuid=True), db.ForeignKey('documents.id'))
    
    created_by = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    created_at = Column(db.DateTime, default=datetime.utcnow)
    updated_at = Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship('Document', foreign_keys=[document_id])
    signed_document = relationship('Document', foreign_keys=[signed_document_id])
    recipients = relationship('SignatureRecipient', back_populates='request', cascade='all, delete-orphan')
    creator = relationship('User', foreign_keys=[created_by])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'title': self.title,
            'message': self.message,
            'status': self.status,
            'signing_order': self.signing_order,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'signed_document_id': str(self.signed_document_id) if self.signed_document_id else None,
            'created_at': self.created_at.isoformat(),
            'recipients': [r.to_dict() for r in self.recipients]
        }


class SignatureRecipient(db.Model):
    """Recipient of a signature request"""
    
    __tablename__ = 'signature_recipients'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), db.ForeignKey('signature_requests.id', ondelete='CASCADE'), nullable=False)
    
    # Recipient info
    user_id = Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    email = Column(String(255), nullable=False)
    name = Column(String(255))
    
    # Role and order
    role = Column(String(50), default='signer')  # signer, approver, viewer
    signing_order = Column(Integer, default=1)
    
    # Status
    status = Column(String(50), default='pending')
    # pending, sent, viewed, signed, declined
    
    # Signature
    signature_data = Column(Text)  # Base64 signature image
    signed_at = Column(db.DateTime)
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Decline
    decline_reason = Column(Text)
    declined_at = Column(db.DateTime)
    
    # Access
    access_token = Column(String(64), unique=True)
    viewed_at = Column(db.DateTime)
    
    created_at = Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    request = relationship('SignatureRequest', back_populates='recipients')
    user = relationship('User')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'signing_order': self.signing_order,
            'status': self.status,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'viewed_at': self.viewed_at.isoformat() if self.viewed_at else None
        }
```

---

## TASK 10: FRONTEND COMPONENTS

### 10.1 Document Uploader Component

**File:** `frontend/src/features/documents/components/DocumentUploader.jsx`

```jsx
/**
 * Document Uploader Component
 * Drag & drop file upload with progress tracking
 */

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useTranslation } from 'react-i18next';
import { documentsApi } from '../api/documentsApi';

// Allowed file types
const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/tiff': ['.tiff', '.tif'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/vnd.ms-excel': ['.xls'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'text/plain': ['.txt'],
  'text/csv': ['.csv'],
};

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

const DocumentUploader = ({
  folderId,
  onUploadComplete,
  onUploadError,
  allowMultiple = true,
  className = '',
}) => {
  const { t } = useTranslation();
  
  const [uploads, setUploads] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  
  const onDrop = useCallback(async (acceptedFiles, rejectedFiles) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      rejectedFiles.forEach(rejection => {
        const error = rejection.errors[0];
        onUploadError?.({
          file: rejection.file,
          error: error.code === 'file-too-large' 
            ? t('documents.upload.fileTooLarge')
            : t('documents.upload.invalidType')
        });
      });
    }
    
    if (acceptedFiles.length === 0) return;
    
    // Initialize upload state
    const newUploads = acceptedFiles.map(file => ({
      id: `${file.name}-${Date.now()}`,
      file,
      name: file.name,
      size: file.size,
      progress: 0,
      status: 'pending',
      error: null,
    }));
    
    setUploads(prev => [...prev, ...newUploads]);
    setIsUploading(true);
    
    // Upload files
    for (const upload of newUploads) {
      try {
        // Update status
        setUploads(prev => 
          prev.map(u => u.id === upload.id ? { ...u, status: 'uploading' } : u)
        );
        
        // Upload file
        const result = await documentsApi.upload(upload.file, {
          folderId,
          onProgress: (progress) => {
            setUploads(prev =>
              prev.map(u => u.id === upload.id ? { ...u, progress } : u)
            );
          },
        });
        
        // Update status
        setUploads(prev =>
          prev.map(u => u.id === upload.id 
            ? { ...u, status: 'complete', progress: 100, documentId: result.document.id }
            : u
          )
        );
        
        onUploadComplete?.(result.document);
        
      } catch (error) {
        setUploads(prev =>
          prev.map(u => u.id === upload.id
            ? { ...u, status: 'error', error: error.message }
            : u
          )
        );
        
        onUploadError?.({ file: upload.file, error: error.message });
      }
    }
    
    setIsUploading(false);
  }, [folderId, onUploadComplete, onUploadError, t]);
  
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: allowMultiple,
  });
  
  const removeUpload = (uploadId) => {
    setUploads(prev => prev.filter(u => u.id !== uploadId));
  };
  
  const clearCompleted = () => {
    setUploads(prev => prev.filter(u => u.status !== 'complete'));
  };
  
  return (
    <div className={className}>
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors duration-200
          ${isDragActive && !isDragReject ? 'border-blue-500 bg-blue-50' : ''}
          ${isDragReject ? 'border-red-500 bg-red-50' : ''}
          ${!isDragActive ? 'border-gray-300 hover:border-gray-400' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center">
          <svg 
            className={`w-12 h-12 mb-4 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`}
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
            />
          </svg>
          
          {isDragActive ? (
            <p className="text-blue-600 font-medium">
              {t('documents.upload.dropHere', 'Drop files here...')}
            </p>
          ) : (
            <>
              <p className="text-gray-700 font-medium mb-1">
                {t('documents.upload.dragDrop', 'Drag & drop files here')}
              </p>
              <p className="text-gray-500 text-sm">
                {t('documents.upload.or', 'or')} 
                <span className="text-blue-600 hover:underline ml-1">
                  {t('documents.upload.browse', 'browse to upload')}
                </span>
              </p>
              <p className="text-gray-400 text-xs mt-2">
                {t('documents.upload.maxSize', 'Max file size: 100MB')}
              </p>
            </>
          )}
        </div>
      </div>
      
      {/* Upload List */}
      {uploads.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">
              {t('documents.upload.uploads', 'Uploads')} ({uploads.length})
            </span>
            {uploads.some(u => u.status === 'complete') && (
              <button
                onClick={clearCompleted}
                className="text-sm text-blue-600 hover:underline"
              >
                {t('documents.upload.clearCompleted', 'Clear completed')}
              </button>
            )}
          </div>
          
          {uploads.map(upload => (
            <UploadItem
              key={upload.id}
              upload={upload}
              onRemove={() => removeUpload(upload.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const UploadItem = ({ upload, onRemove }) => {
  const { t } = useTranslation();
  
  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  
  const getStatusIcon = () => {
    switch (upload.status) {
      case 'complete':
        return (
          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };
  
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
      {/* File Icon */}
      <div className="flex-shrink-0">
        <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
        </svg>
      </div>
      
      {/* File Info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-700 truncate">
          {upload.name}
        </p>
        <p className="text-xs text-gray-500">
          {formatSize(upload.size)}
        </p>
        
        {/* Progress Bar */}
        {upload.status === 'uploading' && (
          <div className="mt-1">
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                style={{ width: `${upload.progress}%` }}
              />
            </div>
          </div>
        )}
        
        {/* Error Message */}
        {upload.error && (
          <p className="text-xs text-red-600 mt-1">{upload.error}</p>
        )}
      </div>
      
      {/* Status/Actions */}
      <div className="flex-shrink-0 flex items-center gap-2">
        {getStatusIcon()}
        
        {upload.status !== 'uploading' && (
          <button
            onClick={onRemove}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default DocumentUploader;
```

### 10.2 Document List Component

**File:** `frontend/src/features/documents/components/DocumentList.jsx`

```jsx
/**
 * Document List Component
 * Grid/list view of documents with actions
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import DocumentCard from './DocumentCard';

const DocumentList = ({
  documents,
  isLoading,
  viewMode = 'grid',
  selectedIds = [],
  onSelect,
  onSelectAll,
  onDelete,
  onDownload,
  onShare,
  emptyMessage,
}) => {
  const { t } = useTranslation();
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }
  
  if (!documents || documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-lg font-medium">
          {emptyMessage || t('documents.list.empty', 'No documents found')}
        </p>
        <p className="text-sm mt-1">
          {t('documents.list.uploadFirst', 'Upload your first document to get started')}
        </p>
      </div>
    );
  }
  
  const isAllSelected = documents.length > 0 && selectedIds.length === documents.length;
  
  return (
    <div>
      {/* Bulk Selection Header */}
      {selectedIds.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg flex items-center justify-between">
          <span className="text-sm text-blue-700">
            {t('documents.list.selected', '{{count}} selected', { count: selectedIds.length })}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => onDownload?.(selectedIds)}
              className="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              {t('common.download', 'Download')}
            </button>
            <button
              onClick={() => onDelete?.(selectedIds)}
              className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
            >
              {t('common.delete', 'Delete')}
            </button>
          </div>
        </div>
      )}
      
      {/* Grid View */}
      {viewMode === 'grid' && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {documents.map(doc => (
            <DocumentCard
              key={doc.id}
              document={doc}
              isSelected={selectedIds.includes(doc.id)}
              onSelect={() => onSelect?.(doc.id)}
              onDelete={() => onDelete?.([doc.id])}
              onDownload={() => onDownload?.([doc.id])}
              onShare={() => onShare?.(doc.id)}
            />
          ))}
        </div>
      )}
      
      {/* List View */}
      {viewMode === 'list' && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="w-10 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    onChange={onSelectAll}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('documents.list.name', 'Name')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('documents.list.type', 'Type')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('documents.list.size', 'Size')}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  {t('documents.list.modified', 'Modified')}
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  {t('documents.list.actions', 'Actions')}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {documents.map(doc => (
                <DocumentRow
                  key={doc.id}
                  document={doc}
                  isSelected={selectedIds.includes(doc.id)}
                  onSelect={() => onSelect?.(doc.id)}
                  onDelete={() => onDelete?.([doc.id])}
                  onDownload={() => onDownload?.([doc.id])}
                  onShare={() => onShare?.(doc.id)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const DocumentRow = ({
  document,
  isSelected,
  onSelect,
  onDelete,
  onDownload,
  onShare,
}) => {
  const { t } = useTranslation();
  
  const formatSize = (bytes) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString();
  };
  
  const getTypeLabel = (mimeType) => {
    const types = {
      'application/pdf': 'PDF',
      'image/jpeg': 'Image',
      'image/png': 'Image',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel',
    };
    return types[mimeType] || mimeType?.split('/')[1]?.toUpperCase() || 'File';
  };
  
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onSelect}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
      </td>
      <td className="px-4 py-3">
        <Link
          to={`/documents/${document.id}`}
          className="flex items-center gap-3 hover:text-blue-600"
        >
          {document.thumbnail_url ? (
            <img
              src={document.thumbnail_url}
              alt=""
              className="w-10 h-10 object-cover rounded"
            />
          ) : (
            <div className="w-10 h-10 bg-gray-100 rounded flex items-center justify-center">
              <svg className="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
              </svg>
            </div>
          )}
          <div>
            <p className="font-medium text-gray-900 truncate max-w-xs">
              {document.name}
            </p>
            {document.document_type && (
              <span className="text-xs text-gray-500 capitalize">
                {document.document_type}
              </span>
            )}
          </div>
        </Link>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {getTypeLabel(document.mime_type)}
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {formatSize(document.file_size)}
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {formatDate(document.updated_at)}
      </td>
      <td className="px-4 py-3 text-right">
        <div className="flex items-center justify-end gap-2">
          <button
            onClick={onDownload}
            className="p-1 text-gray-400 hover:text-gray-600"
            title={t('common.download', 'Download')}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
          <button
            onClick={onShare}
            className="p-1 text-gray-400 hover:text-gray-600"
            title={t('common.share', 'Share')}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
          </button>
          <button
            onClick={onDelete}
            className="p-1 text-gray-400 hover:text-red-600"
            title={t('common.delete', 'Delete')}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </td>
    </tr>
  );
};

export default DocumentList;
```

### 10.3 Documents API Service

**File:** `frontend/src/features/documents/api/documentsApi.js`

```javascript
/**
 * Documents API Service
 * Client for document management endpoints
 */

import api from '../../../services/api';

export const documentsApi = {
  /**
   * Upload a document
   * @param {File} file - File to upload
   * @param {Object} options - Upload options
   * @returns {Promise<Object>} Upload result
   */
  async upload(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options.folderId) {
      formData.append('folder_id', options.folderId);
    }
    if (options.name) {
      formData.append('name', options.name);
    }
    if (options.documentType) {
      formData.append('document_type', options.documentType);
    }
    if (options.tags) {
      formData.append('tags', options.tags.join(','));
    }
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const progress = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        options.onProgress?.(progress);
      },
    });
    
    return response.data;
  },
  
  /**
   * List documents
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Documents list with pagination
   */
  async list(params = {}) {
    const response = await api.get('/documents', { params });
    return response.data;
  },
  
  /**
   * Get document by ID
   * @param {string} documentId - Document ID
   * @returns {Promise<Object>} Document details
   */
  async get(documentId) {
    const response = await api.get(`/documents/${documentId}`);
    return response.data.document;
  },
  
  /**
   * Update document metadata
   * @param {string} documentId - Document ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>} Updated document
   */
  async update(documentId, data) {
    const response = await api.put(`/documents/${documentId}`, data);
    return response.data.document;
  },
  
  /**
   * Delete document
   * @param {string} documentId - Document ID
   * @param {boolean} permanent - Permanent deletion
   * @returns {Promise<void>}
   */
  async delete(documentId, permanent = false) {
    await api.delete(`/documents/${documentId}`, {
      params: { permanent },
    });
  },
  
  /**
   * Get download URL
   * @param {string} documentId - Document ID
   * @param {number} version - Version number (optional)
   * @returns {Promise<string>} Download URL
   */
  async getDownloadUrl(documentId, version = null) {
    const params = version ? { version } : {};
    const response = await api.get(`/documents/${documentId}/download`, { params });
    return response.data.download_url;
  },
  
  /**
   * Search documents
   * @param {Object} params - Search parameters
   * @returns {Promise<Object>} Search results
   */
  async search(params) {
    const response = await api.get('/documents/search', { params });
    return response.data.data;
  },
  
  /**
   * Get search suggestions
   * @param {string} query - Search prefix
   * @returns {Promise<string[]>} Suggestions
   */
  async suggest(query) {
    const response = await api.get('/documents/search/suggest', {
      params: { q: query },
    });
    return response.data.suggestions;
  },
  
  /**
   * Share document
   * @param {string} documentId - Document ID
   * @param {Object} data - Share configuration
   * @returns {Promise<Object>} Share details
   */
  async share(documentId, data) {
    const response = await api.post(`/documents/${documentId}/share`, data);
    return response.data.share;
  },
  
  /**
   * List document versions
   * @param {string} documentId - Document ID
   * @returns {Promise<Object[]>} Version list
   */
  async getVersions(documentId) {
    const response = await api.get(`/documents/${documentId}/versions`);
    return response.data.versions;
  },
  
  /**
   * Create signature request
   * @param {Object} data - Request data
   * @returns {Promise<Object>} Signature request
   */
  async createSignatureRequest(data) {
    const response = await api.post('/signatures/request', data);
    return response.data.request;
  },
  
  /**
   * Get signature request status
   * @param {string} requestId - Request ID
   * @returns {Promise<Object>} Request status
   */
  async getSignatureRequest(requestId) {
    const response = await api.get(`/signatures/requests/${requestId}`);
    return response.data;
  },
  
  /**
   * List folders
   * @param {string} parentId - Parent folder ID (optional)
   * @returns {Promise<Object[]>} Folder list
   */
  async listFolders(parentId = null) {
    const params = parentId ? { parent_id: parentId } : {};
    const response = await api.get('/folders', { params });
    return response.data.folders;
  },
  
  /**
   * Create folder
   * @param {Object} data - Folder data
   * @returns {Promise<Object>} Created folder
   */
  async createFolder(data) {
    const response = await api.post('/folders', data);
    return response.data.folder;
  },
  
  /**
   * Get folder tree
   * @returns {Promise<Object[]>} Folder tree structure
   */
  async getFolderTree() {
    const response = await api.get('/folders/tree');
    return response.data.tree;
  },
};

export default documentsApi;
```

---

## SUMMARY

### Phase 13 Complete File List

| Part | Files |
|------|-------|
| **Part 1** | Database models, Storage service (S3/Local) |
| **Part 2** | Document service, Upload routes, OCR service, AI extraction, Celery tasks |
| **Part 3** | Search service (Elasticsearch), Signature service, Frontend components |

### Implementation Statistics

| Metric | Value |
|--------|-------|
| Total Files | ~35 |
| Backend Code | ~5,000 lines |
| Frontend Code | ~2,000 lines |
| Estimated Hours | ~170h |

### Key Technologies

| Component | Technology |
|-----------|------------|
| Storage | S3/MinIO |
| OCR | Tesseract |
| AI Extraction | OpenAI/Anthropic |
| Search | Elasticsearch |
| Tasks | Celery + Redis |
| Signatures | PDF manipulation |

---

*Phase 13 Tasks Part 3 - LogiAccounting Pro*
*Search, Signatures & Frontend UI*
