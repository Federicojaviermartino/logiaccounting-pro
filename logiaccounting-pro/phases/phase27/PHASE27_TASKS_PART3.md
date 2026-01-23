# Phase 27: Customer Portal v2 - Part 3
## Knowledge Base & Payment Portal

---

## Task 13: Knowledge Base Service

**File: `backend/app/services/portal/knowledge_service.py`**

```python
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
```

---

## Task 14: Knowledge Base API Routes

**File: `backend/app/routes/portal_v2/knowledge.py`**

```python
"""
Portal v2 Knowledge Base Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.services.portal.knowledge_service import knowledge_service
from app.utils.auth import get_current_user

router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("/categories")
async def list_categories(current_user: dict = Depends(get_portal_user)):
    return knowledge_service.list_categories()


@router.get("/articles")
async def list_articles(category: Optional[str] = None, search: Optional[str] = None, page: int = Query(1, ge=1), current_user: dict = Depends(get_portal_user)):
    category_id = None
    if category:
        cat = knowledge_service.get_category_by_slug(category)
        if cat:
            category_id = cat["id"]
    return knowledge_service.list_articles(category_id=category_id, search=search, page=page)


@router.get("/articles/popular")
async def get_popular(limit: int = Query(5, ge=1, le=20), current_user: dict = Depends(get_portal_user)):
    return knowledge_service.get_popular_articles(limit)


@router.get("/articles/recent")
async def get_recent(limit: int = Query(5, ge=1, le=20), current_user: dict = Depends(get_portal_user)):
    return knowledge_service.get_recent_articles(current_user.get("customer_id"), limit)


@router.get("/search")
async def search(q: str, limit: int = Query(10, ge=1, le=50), current_user: dict = Depends(get_portal_user)):
    return knowledge_service.search_articles(query=q, limit=limit)


@router.get("/faq")
async def get_faq(limit: int = Query(10, ge=1, le=30), current_user: dict = Depends(get_portal_user)):
    return knowledge_service.get_faq(limit)


@router.get("/articles/{slug}")
async def get_article(slug: str, current_user: dict = Depends(get_portal_user)):
    article = knowledge_service.get_article_by_slug(slug, current_user.get("customer_id"))
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/articles/{article_id}/helpful")
async def vote_helpful(article_id: str, helpful: bool = True, current_user: dict = Depends(get_portal_user)):
    try:
        return knowledge_service.vote_helpful(article_id, helpful, current_user.get("customer_id"))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## Task 15: Payment Portal Service

**File: `backend/app/services/portal/payment_service.py`**

```python
"""
Payment Portal Service
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging

from app.models.store import db

logger = logging.getLogger(__name__)


class PortalPaymentService:
    def __init__(self):
        self._saved_methods: Dict[str, List[Dict]] = {}
        self._auto_pay: Dict[str, Dict] = {}
    
    def get_invoices(self, customer_id: str, status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        invoices = [i for i in db.invoices.find_all() if i.get("client_id") == customer_id]
        if status:
            if status == "unpaid":
                invoices = [i for i in invoices if i.get("status") in ["pending", "overdue"]]
            else:
                invoices = [i for i in invoices if i.get("status") == status]
        invoices.sort(key=lambda i: i.get("created_at", ""), reverse=True)
        total = len(invoices)
        skip = (page - 1) * page_size
        invoices = invoices[skip:skip + page_size]
        return {"items": [self._invoice_to_dict(i) for i in invoices], "total": total, "page": page, "page_size": page_size}
    
    def get_invoice(self, invoice_id: str, customer_id: str) -> Optional[Dict]:
        invoice = db.invoices.find_by_id(invoice_id)
        if not invoice or invoice.get("client_id") != customer_id:
            return None
        return self._invoice_to_dict(invoice, include_items=True)
    
    def get_invoice_stats(self, customer_id: str) -> Dict[str, Any]:
        invoices = [i for i in db.invoices.find_all() if i.get("client_id") == customer_id]
        total_paid = sum(i.get("total", 0) for i in invoices if i.get("status") == "paid")
        total_pending = sum(i.get("total", 0) for i in invoices if i.get("status") == "pending")
        total_overdue = sum(i.get("total", 0) for i in invoices if i.get("status") == "overdue")
        pending_count = len([i for i in invoices if i.get("status") in ["pending", "overdue"]])
        return {"total_paid": total_paid, "total_pending": total_pending, "total_overdue": total_overdue, "pending_count": pending_count}
    
    def get_payment_history(self, customer_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        payments = [p for p in db.payments.find_all() if p.get("client_id") == customer_id]
        payments.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        total = len(payments)
        skip = (page - 1) * page_size
        payments = payments[skip:skip + page_size]
        return {"items": [self._payment_to_dict(p) for p in payments], "total": total, "page": page, "page_size": page_size}
    
    def initiate_payment(self, invoice_id: str, customer_id: str, payment_method: str, amount: float = None) -> Dict[str, Any]:
        invoice = db.invoices.find_by_id(invoice_id)
        if not invoice or invoice.get("client_id") != customer_id:
            raise ValueError("Invoice not found")
        if invoice.get("status") == "paid":
            raise ValueError("Invoice already paid")
        
        pay_amount = amount or invoice.get("total", 0) - invoice.get("amount_paid", 0)
        payment = {"id": f"pay_{uuid4().hex[:12]}", "invoice_id": invoice_id, "client_id": customer_id, "amount": pay_amount, "payment_method": payment_method, "status": "completed", "paid_at": datetime.utcnow().isoformat(), "transaction_id": f"txn_{uuid4().hex[:12]}", "created_at": datetime.utcnow().isoformat()}
        db.payments.create(payment)
        
        current_paid = invoice.get("amount_paid", 0) + pay_amount
        if current_paid >= invoice.get("total", 0):
            invoice["status"] = "paid"
            invoice["paid_at"] = datetime.utcnow().isoformat()
        invoice["amount_paid"] = current_paid
        db.invoices.update(invoice_id, invoice)
        
        return {"payment_id": payment["id"], "status": payment["status"], "amount": pay_amount, "transaction_id": payment["transaction_id"]}
    
    def get_payment_receipt(self, payment_id: str, customer_id: str) -> Optional[Dict]:
        payments = db.payments.find_all()
        payment = next((p for p in payments if p["id"] == payment_id and p.get("client_id") == customer_id), None)
        if not payment:
            return None
        invoice = db.invoices.find_by_id(payment.get("invoice_id"))
        return {"receipt_number": f"RCP-{payment['id'][-8:].upper()}", "payment_id": payment["id"], "transaction_id": payment.get("transaction_id"), "amount": payment.get("amount"), "payment_method": payment.get("payment_method"), "paid_at": payment.get("paid_at"), "invoice_number": invoice.get("invoice_number") if invoice else None, "status": payment.get("status")}
    
    def list_payment_methods(self, customer_id: str) -> List[Dict]:
        return self._saved_methods.get(customer_id, [])
    
    def add_payment_method(self, customer_id: str, method_type: str, details: Dict) -> Dict:
        method = {"id": f"pm_{uuid4().hex[:12]}", "type": method_type, "last_four": details.get("last_four", "****"), "brand": details.get("brand"), "expiry": details.get("expiry"), "is_default": len(self._saved_methods.get(customer_id, [])) == 0, "created_at": datetime.utcnow().isoformat()}
        if customer_id not in self._saved_methods:
            self._saved_methods[customer_id] = []
        self._saved_methods[customer_id].append(method)
        return method
    
    def remove_payment_method(self, customer_id: str, method_id: str):
        methods = self._saved_methods.get(customer_id, [])
        self._saved_methods[customer_id] = [m for m in methods if m["id"] != method_id]
    
    def get_auto_pay(self, customer_id: str) -> Optional[Dict]:
        return self._auto_pay.get(customer_id)
    
    def setup_auto_pay(self, customer_id: str, payment_method_id: str, enabled: bool = True) -> Dict:
        self._auto_pay[customer_id] = {"enabled": enabled, "payment_method_id": payment_method_id, "created_at": datetime.utcnow().isoformat()}
        return self._auto_pay[customer_id]
    
    def disable_auto_pay(self, customer_id: str):
        if customer_id in self._auto_pay:
            self._auto_pay[customer_id]["enabled"] = False
    
    def get_statement(self, customer_id: str, start_date: str, end_date: str) -> Dict:
        invoices = [i for i in db.invoices.find_all() if i.get("client_id") == customer_id and start_date <= i.get("created_at", "")[:10] <= end_date]
        payments = [p for p in db.payments.find_all() if p.get("client_id") == customer_id and start_date <= p.get("created_at", "")[:10] <= end_date]
        total_invoiced = sum(i.get("total", 0) for i in invoices)
        total_paid = sum(p.get("amount", 0) for p in payments if p.get("status") == "completed")
        return {"period": {"start": start_date, "end": end_date}, "summary": {"total_invoiced": total_invoiced, "total_paid": total_paid, "balance": total_invoiced - total_paid}, "invoices": [self._invoice_to_dict(i) for i in invoices], "payments": [self._payment_to_dict(p) for p in payments]}
    
    def _invoice_to_dict(self, invoice: Dict, include_items: bool = False) -> Dict:
        result = {"id": invoice["id"], "invoice_number": invoice.get("invoice_number", invoice["id"][:8]), "status": invoice.get("status"), "total": invoice.get("total", 0), "amount_paid": invoice.get("amount_paid", 0), "amount_due": invoice.get("total", 0) - invoice.get("amount_paid", 0), "issue_date": invoice.get("created_at"), "due_date": invoice.get("due_date"), "paid_at": invoice.get("paid_at"), "is_overdue": invoice.get("status") == "overdue"}
        if include_items:
            result["items"] = invoice.get("items", [])
        return result
    
    def _payment_to_dict(self, payment: Dict) -> Dict:
        return {"id": payment["id"], "invoice_id": payment.get("invoice_id"), "amount": payment.get("amount", 0), "payment_method": payment.get("payment_method"), "status": payment.get("status"), "transaction_id": payment.get("transaction_id"), "paid_at": payment.get("paid_at"), "created_at": payment.get("created_at")}


portal_payment_service = PortalPaymentService()
```

---

## Task 16: Payment Portal API Routes

**File: `backend/app/routes/portal_v2/payments.py`**

```python
"""
Portal v2 Payment Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.portal.payment_service import portal_payment_service
from app.utils.auth import get_current_user

router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("/invoices")
async def list_invoices(status: Optional[str] = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), current_user: dict = Depends(get_portal_user)):
    return portal_payment_service.get_invoices(current_user.get("customer_id"), status, page, page_size)


@router.get("/invoices/stats")
async def get_stats(current_user: dict = Depends(get_portal_user)):
    return portal_payment_service.get_invoice_stats(current_user.get("customer_id"))


@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, current_user: dict = Depends(get_portal_user)):
    invoice = portal_payment_service.get_invoice(invoice_id, current_user.get("customer_id"))
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


class PayInvoiceRequest(BaseModel):
    payment_method: str
    amount: Optional[float] = None


@router.post("/invoices/{invoice_id}/pay")
async def pay_invoice(invoice_id: str, data: PayInvoiceRequest, current_user: dict = Depends(get_portal_user)):
    try:
        return portal_payment_service.initiate_payment(invoice_id, current_user.get("customer_id"), data.payment_method, data.amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def get_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), current_user: dict = Depends(get_portal_user)):
    return portal_payment_service.get_payment_history(current_user.get("customer_id"), page, page_size)


@router.get("/receipts/{payment_id}")
async def get_receipt(payment_id: str, current_user: dict = Depends(get_portal_user)):
    receipt = portal_payment_service.get_payment_receipt(payment_id, current_user.get("customer_id"))
    if not receipt:
        raise HTTPException(status_code=404, detail="Payment not found")
    return receipt


@router.get("/methods")
async def list_methods(current_user: dict = Depends(get_portal_user)):
    return portal_payment_service.list_payment_methods(current_user.get("customer_id"))


class AddMethodRequest(BaseModel):
    method_type: str
    last_four: str
    brand: Optional[str] = None
    expiry: Optional[str] = None


@router.post("/methods")
async def add_method(data: AddMethodRequest, current_user: dict = Depends(get_portal_user)):
    return portal_payment_service.add_payment_method(current_user.get("customer_id"), data.method_type, data.dict())


@router.delete("/methods/{method_id}")
async def remove_method(method_id: str, current_user: dict = Depends(get_portal_user)):
    portal_payment_service.remove_payment_method(current_user.get("customer_id"), method_id)
    return {"success": True}


@router.get("/auto-pay")
async def get_auto_pay(current_user: dict = Depends(get_portal_user)):
    return portal_payment_service.get_auto_pay(current_user.get("customer_id"))


class AutoPayRequest(BaseModel):
    payment_method_id: str
    enabled: bool = True


@router.post("/auto-pay")
async def setup_auto_pay(data: AutoPayRequest, current_user: dict = Depends(get_portal_user)):
    return portal_payment_service.setup_auto_pay(current_user.get("customer_id"), data.payment_method_id, data.enabled)


@router.delete("/auto-pay")
async def disable_auto_pay(current_user: dict = Depends(get_portal_user)):
    portal_payment_service.disable_auto_pay(current_user.get("customer_id"))
    return {"success": True}


@router.get("/statements")
async def get_statement(start_date: str, end_date: str, current_user: dict = Depends(get_portal_user)):
    return portal_payment_service.get_statement(current_user.get("customer_id"), start_date, end_date)
```

---

## Task 17: Knowledge Base UI

**File: `frontend/src/features/portal/pages/KnowledgeBase.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { Search, Book, ChevronRight, ThumbsUp, ThumbsDown, Eye, Rocket, CreditCard, User, Folder, Tool } from 'lucide-react';
import { portalAPI } from '../../../services/api';
import ReactMarkdown from 'react-markdown';

const categoryIcons = { 'getting-started': Rocket, 'billing': CreditCard, 'account': User, 'projects': Folder, 'troubleshooting': Tool };

export default function KnowledgeBase() {
  const [categories, setCategories] = useState([]);
  const [articles, setArticles] = useState([]);
  const [popularArticles, setPopularArticles] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => { loadData(); }, [selectedCategory]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [catRes, artRes, popRes] = await Promise.all([portalAPI.getKBCategories(), portalAPI.getKBArticles({ category: selectedCategory }), portalAPI.getPopularArticles()]);
      setCategories(catRes.data || []);
      setArticles(artRes.data.items || []);
      setPopularArticles(popRes.data || []);
    } catch (error) { console.error('Failed:', error); }
    finally { setIsLoading(false); }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) { setSearchResults(null); return; }
    try {
      const res = await portalAPI.searchKBArticles(searchQuery);
      setSearchResults(res.data || []);
    } catch (error) { console.error('Search failed:', error); }
  };

  const loadArticle = async (slug) => {
    try {
      const res = await portalAPI.getKBArticle(slug);
      setSelectedArticle(res.data);
    } catch (error) { console.error('Failed:', error); }
  };

  const handleVote = async (articleId, helpful) => {
    try {
      await portalAPI.voteKBArticle(articleId, helpful);
      if (selectedArticle?.id === articleId) {
        setSelectedArticle({ ...selectedArticle, helpful_yes: selectedArticle.helpful_yes + (helpful ? 1 : 0), helpful_no: selectedArticle.helpful_no + (helpful ? 0 : 1) });
      }
    } catch (error) { console.error('Vote failed:', error); }
  };

  if (selectedArticle) {
    return (
      <div className="kb-article">
        <button onClick={() => setSelectedArticle(null)}>← Back</button>
        <article className="article-content">
          <span className="category-badge">{selectedArticle.category_name}</span>
          <h1>{selectedArticle.title}</h1>
          <div className="meta"><Eye className="w-4 h-4" /> {selectedArticle.view_count} views</div>
          <div className="content"><ReactMarkdown>{selectedArticle.content}</ReactMarkdown></div>
          <div className="helpful">
            <span>Was this helpful?</span>
            <button onClick={() => handleVote(selectedArticle.id, true)}><ThumbsUp className="w-4 h-4" /> Yes ({selectedArticle.helpful_yes})</button>
            <button onClick={() => handleVote(selectedArticle.id, false)}><ThumbsDown className="w-4 h-4" /> No ({selectedArticle.helpful_no})</button>
          </div>
        </article>
      </div>
    );
  }

  return (
    <div className="knowledge-base">
      <div className="kb-header">
        <h1>Knowledge Base</h1>
        <p>Find answers to common questions</p>
        <div className="search-box">
          <Search className="w-5 h-5" />
          <input type="text" placeholder="Search..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSearch()} />
          <button onClick={handleSearch}>Search</button>
        </div>
      </div>

      {searchResults ? (
        <div className="search-results">
          <div className="results-header"><h2>Results</h2><button onClick={() => { setSearchResults(null); setSearchQuery(''); }}>Clear</button></div>
          {searchResults.length > 0 ? searchResults.map((article) => (
            <button key={article.id} className="article-card" onClick={() => loadArticle(article.slug)}>
              <h3>{article.title}</h3><p>{article.excerpt}</p>
            </button>
          )) : <p>No articles found</p>}
        </div>
      ) : (
        <>
          <div className="categories-grid">
            {categories.map((cat) => {
              const Icon = categoryIcons[cat.slug] || Book;
              return (
                <button key={cat.id} className={`category-card ${selectedCategory === cat.slug ? 'active' : ''}`} onClick={() => setSelectedCategory(selectedCategory === cat.slug ? '' : cat.slug)}>
                  <Icon className="w-8 h-8" /><h3>{cat.name}</h3><p>{cat.description}</p><span>{cat.article_count} articles</span>
                </button>
              );
            })}
          </div>
          <div className="content-grid">
            <div className="articles-section">
              <h2>{selectedCategory ? categories.find(c => c.slug === selectedCategory)?.name : 'All Articles'}</h2>
              <div className="article-list">
                {articles.map((article) => (
                  <button key={article.id} className="article-card" onClick={() => loadArticle(article.slug)}>
                    <h3>{article.title}</h3><p>{article.excerpt}</p>
                    <div className="meta"><span>{article.category_name}</span><span><Eye className="w-3 h-3" /> {article.view_count}</span></div>
                  </button>
                ))}
              </div>
            </div>
            <aside className="popular-section">
              <h3>Popular Articles</h3>
              {popularArticles.map((article) => (
                <button key={article.id} className="popular-item" onClick={() => loadArticle(article.slug)}>
                  <span>{article.title}</span><ChevronRight className="w-4 h-4" />
                </button>
              ))}
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
```

---

## Task 18: Payments Page

**File: `frontend/src/features/portal/pages/Payments.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { CreditCard, Download, Clock, CheckCircle, AlertCircle, FileText, DollarSign } from 'lucide-react';
import { portalAPI } from '../../../services/api';

export default function Payments() {
  const [invoices, setInvoices] = useState([]);
  const [stats, setStats] = useState(null);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('invoices');
  const [statusFilter, setStatusFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [isPaying, setIsPaying] = useState(false);

  useEffect(() => { loadData(); }, [statusFilter]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [invRes, statsRes, histRes] = await Promise.all([portalAPI.getInvoices({ status: statusFilter }), portalAPI.getInvoiceStats(), portalAPI.getPaymentHistory()]);
      setInvoices(invRes.data.items || []);
      setStats(statsRes.data);
      setPaymentHistory(histRes.data.items || []);
    } catch (error) { console.error('Failed:', error); }
    finally { setIsLoading(false); }
  };

  const handlePayInvoice = async (invoiceId) => {
    try {
      setIsPaying(true);
      await portalAPI.payInvoice(invoiceId, { payment_method: 'card' });
      alert('Payment successful!');
      setSelectedInvoice(null);
      loadData();
    } catch (error) { alert('Payment failed'); }
    finally { setIsPaying(false); }
  };

  const getStatusBadge = (status) => {
    const styles = { paid: { bg: 'bg-green-100', text: 'text-green-700', icon: CheckCircle }, pending: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: Clock }, overdue: { bg: 'bg-red-100', text: 'text-red-700', icon: AlertCircle } };
    const style = styles[status] || styles.pending;
    const Icon = style.icon;
    return <span className={`status-badge ${style.bg} ${style.text}`}><Icon className="w-3 h-3" />{status}</span>;
  };

  return (
    <div className="payments-page">
      <div className="page-header"><h1>Payments</h1><p>Manage your invoices and payments</p></div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card"><DollarSign className="w-8 h-8 text-blue-500" /><div><span className="stat-value">${stats.total_pending?.toLocaleString()}</span><span className="stat-label">Pending ({stats.pending_count})</span></div></div>
          <div className="stat-card"><AlertCircle className="w-8 h-8 text-red-500" /><div><span className="stat-value">${stats.total_overdue?.toLocaleString()}</span><span className="stat-label">Overdue</span></div></div>
          <div className="stat-card"><CheckCircle className="w-8 h-8 text-green-500" /><div><span className="stat-value">${stats.total_paid?.toLocaleString()}</span><span className="stat-label">Paid</span></div></div>
        </div>
      )}

      <div className="tabs">
        <button className={activeTab === 'invoices' ? 'active' : ''} onClick={() => setActiveTab('invoices')}><FileText className="w-4 h-4" /> Invoices</button>
        <button className={activeTab === 'history' ? 'active' : ''} onClick={() => setActiveTab('history')}><CreditCard className="w-4 h-4" /> History</button>
      </div>

      {activeTab === 'invoices' && (
        <div className="invoices-section">
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All</option><option value="unpaid">Unpaid</option><option value="paid">Paid</option><option value="overdue">Overdue</option>
          </select>
          <div className="invoice-list">
            {invoices.map((inv) => (
              <div key={inv.id} className="invoice-card">
                <div className="invoice-info"><span className="invoice-number">#{inv.invoice_number}</span>{getStatusBadge(inv.status)}</div>
                <div className="invoice-dates"><span>Due: {new Date(inv.due_date).toLocaleDateString()}</span></div>
                <div className="invoice-amount"><span className="amount">${inv.total?.toLocaleString()}</span></div>
                <div className="invoice-actions">
                  <button onClick={() => setSelectedInvoice(inv)}>View</button>
                  {inv.status !== 'paid' && <button className="pay-btn" onClick={() => handlePayInvoice(inv.id)}>Pay Now</button>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'history' && (
        <div className="history-section">
          {paymentHistory.map((payment) => (
            <div key={payment.id} className="payment-card">
              <CreditCard className="w-5 h-5" />
              <div className="payment-info"><span className="payment-amount">${payment.amount?.toLocaleString()}</span><span className="payment-date">{new Date(payment.paid_at || payment.created_at).toLocaleDateString()}</span></div>
              <span className={`payment-status ${payment.status}`}>{payment.status}</span>
              <button><Download className="w-4 h-4" /> Receipt</button>
            </div>
          ))}
        </div>
      )}

      {selectedInvoice && (
        <div className="modal-overlay" onClick={() => setSelectedInvoice(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Invoice #{selectedInvoice.invoice_number}</h2>
            <div className="detail-row"><span>Total</span><span>${selectedInvoice.total?.toLocaleString()}</span></div>
            <div className="detail-row"><span>Amount Due</span><span>${selectedInvoice.amount_due?.toLocaleString()}</span></div>
            <div className="modal-actions">
              <button><Download className="w-4 h-4" /> Download PDF</button>
              {selectedInvoice.status !== 'paid' && <button className="pay-btn" onClick={() => handlePayInvoice(selectedInvoice.id)} disabled={isPaying}>{isPaying ? 'Processing...' : `Pay $${selectedInvoice.amount_due?.toLocaleString()}`}</button>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Summary: Part 3 Complete

### Files Created:

| File | Purpose | Lines |
|------|---------|-------|
| `knowledge_service.py` | KB service | ~180 |
| `knowledge.py` | KB API routes | ~60 |
| `payment_service.py` | Payment service | ~150 |
| `payments.py` | Payment API routes | ~100 |
| `KnowledgeBase.jsx` | KB UI | ~120 |
| `Payments.jsx` | Payments UI | ~100 |
| **Total** | | **~710** |

### Features:

| Feature | Status |
|---------|--------|
| KB categories | ✅ |
| KB articles | ✅ |
| Article search | ✅ |
| Popular articles | ✅ |
| Helpful voting | ✅ |
| Invoice list | ✅ |
| Invoice detail | ✅ |
| Pay invoice | ✅ |
| Payment history | ✅ |
| Saved methods | ✅ |
| Auto-pay | ✅ |

### Next: Part 4 - Projects, Quotes & Messages
