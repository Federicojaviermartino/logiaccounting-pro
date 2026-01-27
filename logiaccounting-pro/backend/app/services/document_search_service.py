"""
Document Search Service - Phase 13
Full-text search with optional Elasticsearch support
"""

from typing import Optional, List, Dict, Any, Tuple
import os
import logging
import re
from datetime import datetime

from app.models.document_store import doc_db

logger = logging.getLogger(__name__)


class DocumentSearchService:
    """Document search service with full-text search capabilities"""

    def __init__(self):
        self._es_client = None
        self._es_available = None
        self.index_name = 'documents'

    @property
    def es_available(self) -> bool:
        """Check if Elasticsearch is available"""
        if self._es_available is None:
            self._es_available = self._init_elasticsearch()
        return self._es_available

    def _init_elasticsearch(self) -> bool:
        """Initialize Elasticsearch client"""
        es_url = os.getenv('ELASTICSEARCH_URL')

        if not es_url:
            return False

        try:
            from elasticsearch import Elasticsearch

            self._es_client = Elasticsearch(
                hosts=[es_url],
                basic_auth=(
                    os.getenv('ELASTICSEARCH_USER', 'elastic'),
                    os.getenv('ELASTICSEARCH_PASSWORD', '')
                ) if os.getenv('ELASTICSEARCH_PASSWORD') else None,
                verify_certs=os.getenv('ELASTICSEARCH_VERIFY_CERTS', 'false').lower() == 'true'
            )

            # Check connection
            if self._es_client.ping():
                self._ensure_index()
                return True

        except ImportError:
            logger.info("Elasticsearch not installed, using in-memory search")
        except Exception as e:
            logger.warning(f"Elasticsearch not available: {e}")

        return False

    def _ensure_index(self):
        """Create Elasticsearch index if not exists"""
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "document_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "asciifolding"]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "organization_id": {"type": "keyword"},
                    "category_id": {"type": "keyword"},
                    "name": {
                        "type": "text",
                        "analyzer": "document_analyzer",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "description": {"type": "text", "analyzer": "document_analyzer"},
                    "content": {"type": "text", "analyzer": "document_analyzer"},
                    "document_type": {"type": "keyword"},
                    "mime_type": {"type": "keyword"},
                    "file_size": {"type": "long"},
                    "status": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "owner_id": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "extracted_data_flat": {"type": "text", "analyzer": "document_analyzer"},
                    "related_entity_type": {"type": "keyword"},
                    "related_entity_id": {"type": "keyword"}
                }
            }
        }

        try:
            if not self._es_client.indices.exists(index=self.index_name):
                self._es_client.indices.create(index=self.index_name, body=mapping)
                logger.info(f"Created Elasticsearch index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to create index: {e}")

    def index_document(self, document: Dict):
        """Index a document for search"""
        if not self.es_available:
            return

        doc_body = self._document_to_index(document)

        try:
            self._es_client.index(
                index=self.index_name,
                id=document['id'],
                body=doc_body,
                refresh=True
            )
            logger.debug(f"Indexed document: {document['id']}")
        except Exception as e:
            logger.error(f"Failed to index document {document['id']}: {e}")

    def delete_from_index(self, document_id: str):
        """Remove document from index"""
        if not self.es_available:
            return

        try:
            self._es_client.delete(
                index=self.index_name,
                id=document_id,
                refresh=True
            )
        except Exception as e:
            logger.warning(f"Failed to delete document {document_id} from index: {e}")

    def search(
        self,
        organization_id: str,
        query: str = None,
        filters: Dict[str, Any] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """
        Search documents

        Args:
            organization_id: Organization ID
            query: Search query string
            filters: Filter conditions
            page: Page number
            per_page: Results per page
            sort_by: Sort field
            sort_order: Sort direction

        Returns:
            Dict with results, total, and facets
        """
        if self.es_available:
            return self._search_elasticsearch(
                organization_id, query, filters, page, per_page, sort_by, sort_order
            )
        else:
            return self._search_inmemory(
                organization_id, query, filters, page, per_page, sort_by, sort_order
            )

    def _search_elasticsearch(
        self,
        organization_id: str,
        query: str = None,
        filters: Dict[str, Any] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """Search using Elasticsearch"""
        filters = filters or {}

        must_conditions = [
            {"term": {"organization_id": organization_id}}
        ]

        filter_conditions = [
            {"terms": {"status": ["active", "processing"]}}
        ]

        # Full-text search
        if query:
            must_conditions.append({
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "name.keyword^2", "description^2", "content", "extracted_data_flat"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })

        # Apply filters
        if filters.get('category_id'):
            filter_conditions.append({"term": {"category_id": filters['category_id']}})

        if filters.get('document_type'):
            filter_conditions.append({"term": {"document_type": filters['document_type']}})

        if filters.get('mime_type'):
            filter_conditions.append({"term": {"mime_type": filters['mime_type']}})

        if filters.get('status'):
            filter_conditions = [{"term": {"status": filters['status']}}]

        if filters.get('tags'):
            filter_conditions.append({"terms": {"tags": filters['tags']}})

        if filters.get('owner_id'):
            filter_conditions.append({"term": {"owner_id": filters['owner_id']}})

        if filters.get('date_from') or filters.get('date_to'):
            date_range = {}
            if filters.get('date_from'):
                date_range['gte'] = filters['date_from']
            if filters.get('date_to'):
                date_range['lte'] = filters['date_to']
            filter_conditions.append({"range": {"created_at": date_range}})

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
                "document_types": {"terms": {"field": "document_type", "size": 20}},
                "mime_types": {"terms": {"field": "mime_type", "size": 20}},
                "tags": {"terms": {"field": "tags", "size": 50}}
            }
        }

        # Apply sorting
        if sort_by != '_score' or not query:
            search_body["sort"] = [{sort_by: {"order": sort_order}}]

        try:
            response = self._es_client.search(index=self.index_name, body=search_body)

            hits = response['hits']['hits']
            total = response['hits']['total']['value']
            aggregations = response.get('aggregations', {})

            results = []
            for hit in hits:
                result = hit['_source']
                result['_score'] = hit['_score']
                result['_highlights'] = hit.get('highlight', {})
                results.append(result)

            return {
                'results': results,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page,
                'page': page,
                'facets': {
                    'document_types': [
                        {'value': b['key'], 'count': b['doc_count']}
                        for b in aggregations.get('document_types', {}).get('buckets', [])
                    ],
                    'mime_types': [
                        {'value': b['key'], 'count': b['doc_count']}
                        for b in aggregations.get('mime_types', {}).get('buckets', [])
                    ],
                    'tags': [
                        {'value': b['key'], 'count': b['doc_count']}
                        for b in aggregations.get('tags', {}).get('buckets', [])
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Elasticsearch search failed: {e}")
            return self._search_inmemory(
                organization_id, query, filters, page, per_page, sort_by, sort_order
            )

    def _search_inmemory(
        self,
        organization_id: str,
        query: str = None,
        filters: Dict[str, Any] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """Search using in-memory store"""
        filters = filters or {}

        # Get all documents for organization
        documents = doc_db.documents.find_by_organization(organization_id, {
            'status': filters.get('status', 'all'),
            'category_id': filters.get('category_id'),
            'document_type': filters.get('document_type'),
            'owner_id': filters.get('owner_id'),
        })

        # Apply text search
        if query:
            query_lower = query.lower()
            query_terms = query_lower.split()

            scored_results = []

            for doc in documents:
                score = 0
                highlights = {}

                # Search in name (highest weight)
                name = doc.get('name', '').lower()
                if query_lower in name:
                    score += 10
                    highlights['name'] = [self._highlight_text(doc.get('name', ''), query)]
                elif any(term in name for term in query_terms):
                    score += 5
                    highlights['name'] = [self._highlight_text(doc.get('name', ''), query)]

                # Search in description
                description = doc.get('description', '').lower()
                if query_lower in description:
                    score += 3
                    highlights['description'] = [self._highlight_text(doc.get('description', ''), query)]

                # Search in OCR text
                ocr_text = doc.get('ocr_text', '').lower()
                if query_lower in ocr_text:
                    score += 2
                    highlights['content'] = [self._extract_snippet(doc.get('ocr_text', ''), query)]

                # Search in filename
                filename = doc.get('original_filename', '').lower()
                if query_lower in filename:
                    score += 4

                if score > 0:
                    result = {**doc, '_score': score, '_highlights': highlights}
                    scored_results.append(result)

            # Sort by score
            documents = sorted(scored_results, key=lambda x: x['_score'], reverse=True)
        else:
            # No query, just add empty highlights
            documents = [{**doc, '_score': 0, '_highlights': {}} for doc in documents]

        # Apply additional filters
        if filters.get('mime_type'):
            documents = [d for d in documents if d.get('mime_type') == filters['mime_type']]

        if filters.get('tags'):
            filter_tags = filters['tags']
            documents = [d for d in documents
                        if any(t in d.get('tags', []) for t in filter_tags)]

        if filters.get('date_from'):
            documents = [d for d in documents
                        if d.get('created_at', '') >= filters['date_from']]

        if filters.get('date_to'):
            documents = [d for d in documents
                        if d.get('created_at', '') <= filters['date_to']]

        # Sort
        if sort_by != '_score' or not query:
            reverse = sort_order == 'desc'
            documents.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)

        # Calculate facets
        facets = self._calculate_facets(documents)

        # Paginate
        total = len(documents)
        start = (page - 1) * per_page
        end = start + per_page
        results = documents[start:end]

        return {
            'results': results,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page,
            'page': page,
            'facets': facets
        }

    def _highlight_text(self, text: str, query: str, max_length: int = 200) -> str:
        """Add highlight marks to matching text"""
        if not text:
            return ''

        pattern = re.compile(f'({re.escape(query)})', re.IGNORECASE)
        highlighted = pattern.sub(r'<mark>\1</mark>', text)

        if len(highlighted) > max_length:
            match = pattern.search(highlighted)
            if match:
                start = max(0, match.start() - 50)
                end = min(len(highlighted), match.end() + 150)
                highlighted = ('...' if start > 0 else '') + highlighted[start:end] + ('...' if end < len(highlighted) else '')

        return highlighted

    def _extract_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """Extract snippet around query match"""
        if not text:
            return ''

        query_lower = query.lower()
        text_lower = text.lower()

        pos = text_lower.find(query_lower)

        if pos == -1:
            return text[:max_length] + ('...' if len(text) > max_length else '')

        start = max(0, pos - 50)
        end = min(len(text), pos + len(query) + 150)

        snippet = text[start:end]

        if start > 0:
            snippet = '...' + snippet
        if end < len(text):
            snippet = snippet + '...'

        return self._highlight_text(snippet, query)

    def _calculate_facets(self, documents: List[Dict]) -> Dict[str, List[Dict]]:
        """Calculate facet counts from documents"""
        type_counts = {}
        mime_counts = {}
        tag_counts = {}

        for doc in documents:
            # Document type
            doc_type = doc.get('document_type', 'other')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

            # MIME type
            mime_type = doc.get('mime_type', 'unknown')
            mime_counts[mime_type] = mime_counts.get(mime_type, 0) + 1

            # Tags
            for tag in doc.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            'document_types': [
                {'value': k, 'count': v}
                for k, v in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
            ],
            'mime_types': [
                {'value': k, 'count': v}
                for k, v in sorted(mime_counts.items(), key=lambda x: x[1], reverse=True)
            ],
            'tags': [
                {'value': k, 'count': v}
                for k, v in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            ]
        }

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
        if len(prefix) < 2:
            return []

        # Get documents
        documents = doc_db.documents.find_by_organization(organization_id)

        prefix_lower = prefix.lower()
        suggestions = set()

        for doc in documents:
            if doc.get('status') == 'deleted':
                continue

            name = doc.get('name', '')
            if name.lower().startswith(prefix_lower):
                suggestions.add(name)
            elif prefix_lower in name.lower():
                suggestions.add(name)

            if len(suggestions) >= limit:
                break

        return list(suggestions)[:limit]

    def _document_to_index(self, document: Dict) -> Dict[str, Any]:
        """Convert document to Elasticsearch index format"""
        # Flatten extracted data for search
        extracted_flat = ""
        if document.get('extracted_data'):
            extracted_flat = self._flatten_dict(document['extracted_data'])

        return {
            "id": document['id'],
            "organization_id": document.get('organization_id'),
            "category_id": document.get('category_id'),
            "name": document.get('name'),
            "description": document.get('description'),
            "content": document.get('ocr_text', ''),
            "document_type": document.get('document_type'),
            "mime_type": document.get('mime_type'),
            "file_size": document.get('file_size'),
            "status": document.get('status'),
            "tags": document.get('tags', []),
            "owner_id": document.get('owner_id'),
            "created_at": document.get('created_at'),
            "extracted_data_flat": extracted_flat,
            "related_entity_type": document.get('related_entity_type'),
            "related_entity_id": document.get('related_entity_id')
        }

    def _flatten_dict(self, d: Dict, parent_key: str = '') -> str:
        """Flatten nested dict values to searchable string"""
        items = []

        for k, v in d.items():
            if isinstance(v, dict):
                items.append(self._flatten_dict(v, f"{parent_key}{k}_"))
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        items.append(self._flatten_dict(item))
                    else:
                        items.append(str(item))
            else:
                items.append(str(v))

        return ' '.join(items)


# Global service instance
document_search_service = DocumentSearchService()
