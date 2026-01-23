"""
Knowledge Base Service
Self-service knowledge articles and FAQ
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging
import re


logger = logging.getLogger(__name__)


class KBCategory:
    """Knowledge base category"""

    def __init__(self, tenant_id: str, name: str, slug: str, description: str = None, icon: str = None):
        self.id = f"kbc_{uuid4().hex[:12]}"
        self.tenant_id = tenant_id
        self.name = name
        self.slug = slug
        self.description = description
        self.icon = icon
        self.sort_order = 0
        self.is_public = True
        self.article_count = 0
        self.created_at = datetime.utcnow()


class KBArticle:
    """Knowledge base article"""

    def __init__(self, tenant_id: str, category_id: str, title: str, content: str, excerpt: str = None):
        self.id = f"kba_{uuid4().hex[:12]}"
        self.tenant_id = tenant_id
        self.category_id = category_id
        self.title = title
        self.slug = self._generate_slug(title)
        self.content = content
        self.excerpt = excerpt or content[:200]
        self.status = "published"
        self.tags = []
        self.view_count = 0
        self.helpful_yes = 0
        self.helpful_no = 0
        self.published_at = datetime.utcnow()
        self.created_at = datetime.utcnow()

    def _generate_slug(self, title: str) -> str:
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug)
        return slug[:100]


class KnowledgeService:
    """Manages knowledge base articles."""

    def __init__(self):
        self._categories: Dict[str, KBCategory] = {}
        self._articles: Dict[str, KBArticle] = {}
        self._view_history: Dict[str, List[str]] = {}
        self._load_sample_content()

    def _load_sample_content(self):
        """Load sample KB content."""
        tenant_id = "default"

        categories = [
            {"name": "Getting Started", "slug": "getting-started", "icon": "rocket", "description": "Learn the basics"},
            {"name": "Billing & Payments", "slug": "billing", "icon": "credit-card", "description": "Payment questions"},
            {"name": "Account Management", "slug": "account", "icon": "user", "description": "Manage your account"},
            {"name": "Projects", "slug": "projects", "icon": "folder", "description": "Working with projects"},
            {"name": "Troubleshooting", "slug": "troubleshooting", "icon": "tool", "description": "Common issues"},
        ]

        for cat_data in categories:
            cat = KBCategory(tenant_id=tenant_id, **cat_data)
            self._categories[cat.id] = cat

        cat_ids = list(self._categories.keys())

        articles = [
            {"category_id": cat_ids[0], "title": "Welcome to Customer Portal", "content": "# Welcome\n\nYour portal hub for projects, payments, and support.", "tags": ["welcome"]},
            {"category_id": cat_ids[0], "title": "Portal Navigation Guide", "content": "# Navigation\n\nUse the sidebar to access all features.", "tags": ["navigation"]},
            {"category_id": cat_ids[1], "title": "How to Pay an Invoice", "content": "# Paying Invoices\n\n1. Go to Payments\n2. Select invoice\n3. Click Pay Now", "tags": ["payment"]},
            {"category_id": cat_ids[1], "title": "Understanding Your Invoice", "content": "# Invoice Details\n\nEach invoice shows line items, taxes, and totals.", "tags": ["invoice"]},
            {"category_id": cat_ids[2], "title": "Updating Your Profile", "content": "# Profile Settings\n\nUpdate your name, email, and password.", "tags": ["profile"]},
            {"category_id": cat_ids[3], "title": "Tracking Project Progress", "content": "# Projects\n\nView milestones, progress, and deliverables.", "tags": ["projects"]},
            {"category_id": cat_ids[4], "title": "Login Troubleshooting", "content": "# Login Issues\n\nReset password or contact support.", "tags": ["login"]},
        ]

        for art_data in articles:
            article = KBArticle(tenant_id=tenant_id, **art_data)
            article.tags = art_data.get("tags", [])
            self._articles[article.id] = article
            if article.category_id in self._categories:
                self._categories[article.category_id].article_count += 1

    def list_categories(self, tenant_id: str = None) -> List[Dict]:
        categories = [c for c in self._categories.values() if c.is_public]
        categories.sort(key=lambda c: c.sort_order)
        return [{"id": c.id, "name": c.name, "slug": c.slug, "description": c.description, "icon": c.icon, "article_count": c.article_count} for c in categories]

    def get_category_by_slug(self, slug: str) -> Optional[Dict]:
        for cat in self._categories.values():
            if cat.slug == slug:
                return {"id": cat.id, "name": cat.name, "slug": cat.slug, "description": cat.description, "icon": cat.icon, "article_count": cat.article_count}
        return None

    def list_articles(self, category_id: str = None, search: str = None, tags: List[str] = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        articles = [a for a in self._articles.values() if a.status == "published"]

        if category_id:
            articles = [a for a in articles if a.category_id == category_id]

        if search:
            search_lower = search.lower()
            articles = [a for a in articles if search_lower in a.title.lower() or search_lower in a.content.lower()]

        if tags:
            articles = [a for a in articles if any(t in a.tags for t in tags)]

        articles.sort(key=lambda a: a.view_count, reverse=True)
        total = len(articles)
        skip = (page - 1) * page_size
        articles = articles[skip:skip + page_size]

        return {"items": [self._article_to_dict(a) for a in articles], "total": total, "page": page, "page_size": page_size}

    def get_article_by_slug(self, slug: str, customer_id: str = None) -> Optional[Dict]:
        for article in self._articles.values():
            if article.slug == slug and article.status == "published":
                article.view_count += 1
                if customer_id:
                    if customer_id not in self._view_history:
                        self._view_history[customer_id] = []
                    if article.id not in self._view_history[customer_id]:
                        self._view_history[customer_id].insert(0, article.id)
                        self._view_history[customer_id] = self._view_history[customer_id][:20]
                return self._article_to_dict(article, include_content=True)
        return None

    def search_articles(self, query: str, limit: int = 10) -> List[Dict]:
        if not query:
            return []
        query_lower = query.lower()
        results = []
        for article in self._articles.values():
            if article.status != "published":
                continue
            score = 0
            if query_lower in article.title.lower():
                score += 10
            if query_lower in article.content.lower():
                score += 1
            if score > 0:
                results.append((article, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return [self._article_to_dict(a) for a, _ in results[:limit]]

    def get_popular_articles(self, limit: int = 5) -> List[Dict]:
        articles = [a for a in self._articles.values() if a.status == "published"]
        articles.sort(key=lambda a: a.view_count, reverse=True)
        return [self._article_to_dict(a) for a in articles[:limit]]

    def get_recent_articles(self, customer_id: str, limit: int = 5) -> List[Dict]:
        article_ids = self._view_history.get(customer_id, [])
        articles = []
        for aid in article_ids[:limit]:
            article = self._articles.get(aid)
            if article and article.status == "published":
                articles.append(self._article_to_dict(article))
        return articles

    def vote_helpful(self, article_id: str, helpful: bool, customer_id: str) -> Dict:
        article = self._articles.get(article_id)
        if not article:
            raise ValueError("Article not found")
        if helpful:
            article.helpful_yes += 1
        else:
            article.helpful_no += 1
        return {"helpful_yes": article.helpful_yes, "helpful_no": article.helpful_no}

    def get_faq(self, limit: int = 10) -> List[Dict]:
        articles = [a for a in self._articles.values() if a.status == "published"]
        articles.sort(key=lambda a: a.helpful_yes, reverse=True)
        return [self._article_to_dict(a, include_content=True) for a in articles[:limit]]

    def _article_to_dict(self, article: KBArticle, include_content: bool = False) -> Dict:
        result = {"id": article.id, "title": article.title, "slug": article.slug, "excerpt": article.excerpt, "category_id": article.category_id, "tags": article.tags, "view_count": article.view_count, "helpful_yes": article.helpful_yes, "helpful_no": article.helpful_no}
        if include_content:
            result["content"] = article.content
        cat = self._categories.get(article.category_id)
        if cat:
            result["category_name"] = cat.name
            result["category_slug"] = cat.slug
        return result


knowledge_service = KnowledgeService()
