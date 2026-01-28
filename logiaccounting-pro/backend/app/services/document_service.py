"""
Document Management Service
Handle file attachments for entities
"""

import base64
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from app.utils.datetime_utils import utc_now


class DocumentService:
    """Manages document attachments"""

    _instance = None
    _documents: Dict[str, dict] = {}
    _counter = 0

    ALLOWED_TYPES = {
        "application/pdf": "pdf",
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx"
    }

    CATEGORIES = ["invoice", "receipt", "contract", "quote", "report", "other"]

    MAX_SIZE_MB = 10

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._documents = {}
            cls._counter = 0
        return cls._instance

    def upload_document(
        self,
        filename: str,
        content_base64: str,
        mime_type: str,
        entity_type: str,
        entity_id: str,
        category: str = "other",
        description: str = "",
        uploaded_by: str = None
    ) -> dict:
        """Upload and store a document"""
        if mime_type not in self.ALLOWED_TYPES:
            return {"error": f"File type not allowed: {mime_type}"}

        try:
            content = base64.b64decode(content_base64)
            size_bytes = len(content)

            if size_bytes > self.MAX_SIZE_MB * 1024 * 1024:
                return {"error": f"File too large. Max size: {self.MAX_SIZE_MB}MB"}

        except Exception as e:
            return {"error": f"Invalid file content: {str(e)}"}

        self._counter += 1
        doc_id = f"DOC-{self._counter:06d}"

        content_hash = hashlib.sha256(content).hexdigest()[:16]

        document = {
            "id": doc_id,
            "filename": filename,
            "mime_type": mime_type,
            "extension": self.ALLOWED_TYPES[mime_type],
            "size_bytes": size_bytes,
            "content_hash": content_hash,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "category": category,
            "description": description,
            "content": content_base64,
            "uploaded_by": uploaded_by,
            "uploaded_at": utc_now().isoformat(),
            "version": 1
        }

        self._documents[doc_id] = document

        return {k: v for k, v in document.items() if k != "content"}

    def get_document(self, doc_id: str, include_content: bool = False) -> Optional[dict]:
        """Get a document by ID"""
        doc = self._documents.get(doc_id)
        if not doc:
            return None

        if include_content:
            return doc

        return {k: v for k, v in doc.items() if k != "content"}

    def get_document_content(self, doc_id: str) -> Optional[bytes]:
        """Get document content as bytes"""
        doc = self._documents.get(doc_id)
        if not doc:
            return None

        return base64.b64decode(doc["content"])

    def list_documents(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[dict]:
        """List documents with optional filters"""
        docs = list(self._documents.values())

        if entity_type:
            docs = [d for d in docs if d["entity_type"] == entity_type]

        if entity_id:
            docs = [d for d in docs if d["entity_id"] == entity_id]

        if category:
            docs = [d for d in docs if d["category"] == category]

        return [
            {k: v for k, v in d.items() if k != "content"}
            for d in sorted(docs, key=lambda x: x["uploaded_at"], reverse=True)
        ]

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False

    def update_document(
        self,
        doc_id: str,
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[dict]:
        """Update document metadata"""
        if doc_id not in self._documents:
            return None

        doc = self._documents[doc_id]

        if category:
            doc["category"] = category
        if description is not None:
            doc["description"] = description

        return {k: v for k, v in doc.items() if k != "content"}

    def get_entity_documents(self, entity_type: str, entity_id: str) -> List[dict]:
        """Get all documents for a specific entity"""
        return self.list_documents(entity_type=entity_type, entity_id=entity_id)

    def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        total_size = sum(d["size_bytes"] for d in self._documents.values())
        by_category = {}
        by_type = {}

        for doc in self._documents.values():
            cat = doc["category"]
            by_category[cat] = by_category.get(cat, 0) + 1

            ext = doc["extension"]
            by_type[ext] = by_type.get(ext, 0) + 1

        return {
            "total_documents": len(self._documents),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_category": by_category,
            "by_type": by_type
        }


document_service = DocumentService()
