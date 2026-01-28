"""
Document Management Store - Phase 13
Enhanced document models with categories, versions, shares, comments, and signatures
"""
import logging

logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import uuid4
from app.models.store import BaseStore
from app.utils.datetime_utils import utc_now
import secrets
import hashlib
import re


class DocumentCategoryStore(BaseStore):
    """Hierarchical document category (folder) store"""

    def find_by_organization(self, org_id: str) -> List[Dict]:
        return [c for c in self._data if c.get("organization_id") == org_id]

    def find_by_parent(self, org_id: str, parent_id: Optional[str]) -> List[Dict]:
        return [c for c in self._data
                if c.get("organization_id") == org_id and c.get("parent_id") == parent_id]

    def find_by_slug(self, org_id: str, slug: str, parent_id: Optional[str] = None) -> Optional[Dict]:
        for c in self._data:
            if (c.get("organization_id") == org_id and
                c.get("slug") == slug and
                c.get("parent_id") == parent_id):
                return c
        return None

    @staticmethod
    def generate_slug(name: str) -> str:
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

    def get_tree(self, org_id: str) -> List[Dict]:
        """Get full category tree for organization"""
        categories = self.find_by_organization(org_id)
        categories.sort(key=lambda x: x.get("path", ""))

        tree = []
        category_map = {}

        for cat in categories:
            node = {**cat, "children": []}
            category_map[cat["id"]] = node

            if cat.get("parent_id"):
                parent_node = category_map.get(cat["parent_id"])
                if parent_node:
                    parent_node["children"].append(node)
            else:
                tree.append(node)

        return tree

    def create(self, data: Dict) -> Dict:
        if not data.get("slug"):
            data["slug"] = self.generate_slug(data["name"])

        # Calculate path
        if data.get("parent_id"):
            parent = self.find_by_id(data["parent_id"])
            if parent:
                data["path"] = f"{parent.get('path', '')}/{data['slug']}"
                data["level"] = parent.get("level", 0) + 1
        else:
            data["path"] = f"/{data['slug']}"
            data["level"] = 0

        return super().create(data)


class DocumentTagStore(BaseStore):
    """Document tag store"""

    def find_by_organization(self, org_id: str) -> List[Dict]:
        return [t for t in self._data if t.get("organization_id") == org_id]

    def find_by_slug(self, org_id: str, slug: str) -> Optional[Dict]:
        return next((t for t in self._data
                    if t.get("organization_id") == org_id and t.get("slug") == slug), None)

    def create(self, data: Dict) -> Dict:
        if not data.get("slug"):
            data["slug"] = DocumentCategoryStore.generate_slug(data["name"])
        return super().create(data)


class EnhancedDocumentStore(BaseStore):
    """Enhanced document store with full Phase 13 features"""

    def find_by_organization(self, org_id: str, filters: Dict = None) -> List[Dict]:
        results = [d for d in self._data if d.get("organization_id") == org_id]

        if filters:
            if filters.get("category_id"):
                results = [d for d in results if d.get("category_id") == filters["category_id"]]
            if filters.get("document_type"):
                results = [d for d in results if d.get("document_type") == filters["document_type"]]
            if filters.get("status"):
                if filters["status"] == "all":
                    results = [d for d in results if d.get("status") != "deleted"]
                else:
                    results = [d for d in results if d.get("status") == filters["status"]]
            else:
                results = [d for d in results if d.get("status") != "deleted"]
            if filters.get("owner_id"):
                results = [d for d in results if d.get("owner_id") == filters["owner_id"]]
            if filters.get("search"):
                search = filters["search"].lower()
                results = [d for d in results if
                          search in d.get("name", "").lower() or
                          search in d.get("description", "").lower() or
                          search in d.get("original_filename", "").lower() or
                          search in d.get("ocr_text", "").lower()]
            if filters.get("related_entity_type"):
                results = [d for d in results
                          if d.get("related_entity_type") == filters["related_entity_type"]]
            if filters.get("related_entity_id"):
                results = [d for d in results
                          if d.get("related_entity_id") == filters["related_entity_id"]]

        # Sort by created_at descending by default
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results

    def find_by_hash(self, org_id: str, file_hash: str) -> Optional[Dict]:
        return next((d for d in self._data
                    if d.get("organization_id") == org_id and
                    d.get("file_hash") == file_hash and
                    d.get("status") != "deleted"), None)

    @staticmethod
    def calculate_hash(file_content: bytes) -> str:
        return hashlib.sha256(file_content).hexdigest()

    def soft_delete(self, doc_id: str) -> Optional[Dict]:
        doc = self.find_by_id(doc_id)
        if doc:
            doc["status"] = "deleted"
            doc["deleted_at"] = utc_now().isoformat()
            doc["updated_at"] = utc_now().isoformat()
            return doc
        return None

    def archive(self, doc_id: str) -> Optional[Dict]:
        doc = self.find_by_id(doc_id)
        if doc:
            doc["status"] = "archived"
            doc["archived_at"] = utc_now().isoformat()
            doc["updated_at"] = utc_now().isoformat()
            return doc
        return None

    def restore(self, doc_id: str) -> Optional[Dict]:
        doc = self.find_by_id(doc_id)
        if doc:
            doc["status"] = "active"
            doc["deleted_at"] = None
            doc["archived_at"] = None
            doc["updated_at"] = utc_now().isoformat()
            return doc
        return None


class DocumentVersionStore(BaseStore):
    """Document version history store"""

    def find_by_document(self, doc_id: str) -> List[Dict]:
        versions = [v for v in self._data if v.get("document_id") == doc_id]
        versions.sort(key=lambda x: x.get("version_number", 0), reverse=True)
        return versions

    def get_latest_version(self, doc_id: str) -> Optional[Dict]:
        versions = self.find_by_document(doc_id)
        return versions[0] if versions else None


class DocumentShareStore(BaseStore):
    """Document sharing store"""

    def find_by_document(self, doc_id: str) -> List[Dict]:
        return [s for s in self._data if s.get("document_id") == doc_id]

    def find_by_token(self, token: str) -> Optional[Dict]:
        return next((s for s in self._data if s.get("share_token") == token), None)

    def find_by_user(self, user_id: str) -> List[Dict]:
        return [s for s in self._data if s.get("shared_with_user_id") == user_id]

    def is_expired(self, share: Dict) -> bool:
        if not share.get("expires_at"):
            return False
        expires = datetime.fromisoformat(share["expires_at"].replace("Z", ""))
        return utc_now() > expires

    def record_access(self, share_id: str):
        share = self.find_by_id(share_id)
        if share:
            share["last_accessed_at"] = utc_now().isoformat()
            share["access_count"] = share.get("access_count", 0) + 1

    def create_link_share(
        self,
        document_id: str,
        shared_by: str,
        permission: str = "view",
        expires_days: int = None,
        can_download: bool = True
    ) -> Dict:
        data = {
            "document_id": document_id,
            "share_token": secrets.token_urlsafe(32),
            "is_link_share": True,
            "shared_by": shared_by,
            "permission": permission,
            "can_download": can_download,
            "access_count": 0,
        }

        if expires_days:
            data["expires_at"] = (utc_now() + timedelta(days=expires_days)).isoformat()

        return self.create(data)

    def create_user_share(
        self,
        document_id: str,
        shared_with_user_id: str,
        shared_by: str,
        permission: str = "view",
        can_download: bool = True,
        can_share: bool = False
    ) -> Dict:
        # Check if already shared
        existing = next((s for s in self._data
                        if s.get("document_id") == document_id and
                        s.get("shared_with_user_id") == shared_with_user_id), None)

        if existing:
            existing["permission"] = permission
            existing["can_download"] = can_download
            existing["can_share"] = can_share
            existing["updated_at"] = utc_now().isoformat()
            return existing

        return self.create({
            "document_id": document_id,
            "shared_with_user_id": shared_with_user_id,
            "shared_by": shared_by,
            "permission": permission,
            "can_download": can_download,
            "can_share": can_share,
            "is_link_share": False,
            "access_count": 0,
        })


class DocumentCommentStore(BaseStore):
    """Document comments and annotations store"""

    def find_by_document(self, doc_id: str, include_resolved: bool = True) -> List[Dict]:
        comments = [c for c in self._data if c.get("document_id") == doc_id]

        if not include_resolved:
            comments = [c for c in comments if not c.get("is_resolved")]

        # Get top-level comments first
        top_level = [c for c in comments if not c.get("parent_id")]

        # Add replies
        for comment in top_level:
            comment["replies"] = [c for c in comments if c.get("parent_id") == comment["id"]]
            comment["replies"].sort(key=lambda x: x.get("created_at", ""))

        top_level.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return top_level

    def resolve(self, comment_id: str, resolved_by: str) -> Optional[Dict]:
        comment = self.find_by_id(comment_id)
        if comment:
            comment["is_resolved"] = True
            comment["resolved_by"] = resolved_by
            comment["resolved_at"] = utc_now().isoformat()
            return comment
        return None


class DocumentActivityStore(BaseStore):
    """Document activity log store"""

    def find_by_document(self, doc_id: str, limit: int = 50) -> List[Dict]:
        logs = [l for l in self._data if l.get("document_id") == doc_id]
        logs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return logs[:limit]

    def find_by_user(self, user_id: str, limit: int = 50) -> List[Dict]:
        logs = [l for l in self._data if l.get("user_id") == user_id]
        logs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return logs[:limit]

    def log(
        self,
        document_id: str,
        action: str,
        user_id: str = None,
        details: Dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict:
        return self.create({
            "document_id": document_id,
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
        })


class SignatureRequestStore(BaseStore):
    """E-signature request store"""

    def find_by_organization(self, org_id: str) -> List[Dict]:
        return [r for r in self._data if r.get("organization_id") == org_id]

    def find_by_document(self, doc_id: str) -> List[Dict]:
        return [r for r in self._data if r.get("document_id") == doc_id]

    def find_pending_by_user(self, email: str) -> List[Dict]:
        return [r for r in self._data
                if r.get("status") in ["pending", "in_progress"] and
                any(rec.get("email") == email and rec.get("status") in ["pending", "sent"]
                    for rec in r.get("recipients", []))]


class SignatureRecipientStore(BaseStore):
    """Signature recipient store"""

    def find_by_request(self, request_id: str) -> List[Dict]:
        recipients = [r for r in self._data if r.get("request_id") == request_id]
        recipients.sort(key=lambda x: x.get("signing_order", 0))
        return recipients

    def find_by_token(self, token: str) -> Optional[Dict]:
        return next((r for r in self._data if r.get("access_token") == token), None)

    def find_pending_by_order(self, request_id: str, order: int) -> List[Dict]:
        return [r for r in self._data
                if r.get("request_id") == request_id and
                r.get("signing_order") == order and
                r.get("status") == "pending"]


# Document database instance
class DocumentDatabase:
    """Document management database container"""

    def __init__(self):
        self.categories = DocumentCategoryStore()
        self.tags = DocumentTagStore()
        self.documents = EnhancedDocumentStore()
        self.versions = DocumentVersionStore()
        self.shares = DocumentShareStore()
        self.comments = DocumentCommentStore()
        self.activity = DocumentActivityStore()
        self.signature_requests = SignatureRequestStore()
        self.signature_recipients = SignatureRecipientStore()


# Global document database instance
doc_db = DocumentDatabase()


def init_document_database():
    """Initialize document database with default categories"""

    # Default document categories
    default_categories = [
        {"name": "Invoices", "icon": "receipt", "color": "#3B82F6", "organization_id": "default"},
        {"name": "Receipts", "icon": "file-text", "color": "#10B981", "organization_id": "default"},
        {"name": "Contracts", "icon": "file-signature", "color": "#8B5CF6", "organization_id": "default"},
        {"name": "Reports", "icon": "chart-bar", "color": "#F59E0B", "organization_id": "default"},
        {"name": "Correspondence", "icon": "mail", "color": "#EC4899", "organization_id": "default"},
        {"name": "Other", "icon": "folder", "color": "#6B7280", "organization_id": "default"},
    ]

    for cat in default_categories:
        doc_db.categories.create(cat)

    # Default tags
    default_tags = [
        {"name": "Important", "color": "#EF4444", "organization_id": "default"},
        {"name": "Pending Review", "color": "#F59E0B", "organization_id": "default"},
        {"name": "Approved", "color": "#10B981", "organization_id": "default"},
        {"name": "Archived", "color": "#6B7280", "organization_id": "default"},
    ]

    for tag in default_tags:
        doc_db.tags.create(tag)

    logger.info("Document database initialized: %d categories, %d tags", len(doc_db.categories._data), len(doc_db.tags._data))
