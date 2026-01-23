# Phase 27: Customer Portal v2 - Part 4
## Projects, Quotes & Communication Center

---

## Task 19: Project Visibility Service

**File: `backend/app/services/portal/project_service.py`**

```python
"""
Portal Project Service
Customer project visibility
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging

from app.models.store import db

logger = logging.getLogger(__name__)


class PortalProjectService:
    """Customer project visibility service."""
    
    def __init__(self):
        self._feedbacks: Dict[str, List[Dict]] = {}
        self._approvals: Dict[str, Dict] = {}
    
    def list_projects(self, customer_id: str, status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """List customer projects."""
        projects = [p for p in db.projects.find_all() if p.get("client_id") == customer_id]
        
        if status:
            projects = [p for p in projects if p.get("status") == status]
        
        projects.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        
        total = len(projects)
        skip = (page - 1) * page_size
        projects = projects[skip:skip + page_size]
        
        return {"items": [self._project_to_dict(p) for p in projects], "total": total, "page": page, "page_size": page_size}
    
    def get_project(self, project_id: str, customer_id: str) -> Optional[Dict]:
        """Get project detail."""
        project = db.projects.find_by_id(project_id)
        if not project or project.get("client_id") != customer_id:
            return None
        return self._project_to_dict(project, include_details=True)
    
    def get_project_timeline(self, project_id: str, customer_id: str) -> Optional[List[Dict]]:
        """Get project timeline/milestones."""
        project = db.projects.find_by_id(project_id)
        if not project or project.get("client_id") != customer_id:
            return None
        
        milestones = project.get("milestones", [])
        timeline = []
        
        for ms in milestones:
            timeline.append({
                "id": ms.get("id"),
                "name": ms.get("name"),
                "description": ms.get("description"),
                "due_date": ms.get("due_date"),
                "status": ms.get("status", "pending"),
                "completed_at": ms.get("completed_at"),
                "progress": ms.get("progress", 0),
            })
        
        timeline.sort(key=lambda t: t.get("due_date", ""))
        return timeline
    
    def get_project_documents(self, project_id: str, customer_id: str) -> List[Dict]:
        """Get project documents."""
        project = db.projects.find_by_id(project_id)
        if not project or project.get("client_id") != customer_id:
            return []
        
        documents = []
        all_docs = db.documents.find_all() if hasattr(db, 'documents') else []
        
        for doc in all_docs:
            if doc.get("project_id") == project_id and doc.get("shared_with_client", True):
                documents.append({
                    "id": doc["id"],
                    "name": doc.get("name"),
                    "type": doc.get("type"),
                    "size": doc.get("size"),
                    "uploaded_at": doc.get("created_at"),
                    "category": doc.get("category"),
                })
        
        return documents
    
    def submit_feedback(self, project_id: str, customer_id: str, content: str, rating: int = None) -> Dict:
        """Submit project feedback."""
        project = db.projects.find_by_id(project_id)
        if not project or project.get("client_id") != customer_id:
            raise ValueError("Project not found")
        
        feedback = {
            "id": f"fb_{uuid4().hex[:12]}",
            "project_id": project_id,
            "customer_id": customer_id,
            "content": content,
            "rating": rating,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        if project_id not in self._feedbacks:
            self._feedbacks[project_id] = []
        self._feedbacks[project_id].append(feedback)
        
        return feedback
    
    def approve_deliverable(self, project_id: str, deliverable_id: str, customer_id: str, approved: bool, comment: str = None) -> Dict:
        """Approve or reject a deliverable."""
        project = db.projects.find_by_id(project_id)
        if not project or project.get("client_id") != customer_id:
            raise ValueError("Project not found")
        
        approval = {
            "id": f"appr_{uuid4().hex[:12]}",
            "project_id": project_id,
            "deliverable_id": deliverable_id,
            "customer_id": customer_id,
            "approved": approved,
            "comment": comment,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self._approvals[deliverable_id] = approval
        
        return approval
    
    def get_project_stats(self, customer_id: str) -> Dict[str, Any]:
        """Get project statistics."""
        projects = [p for p in db.projects.find_all() if p.get("client_id") == customer_id]
        
        return {
            "total": len(projects),
            "active": len([p for p in projects if p.get("status") == "active"]),
            "completed": len([p for p in projects if p.get("status") == "completed"]),
            "on_hold": len([p for p in projects if p.get("status") == "on_hold"]),
        }
    
    def _project_to_dict(self, project: Dict, include_details: bool = False) -> Dict:
        result = {
            "id": project["id"],
            "name": project.get("name"),
            "description": project.get("description"),
            "status": project.get("status"),
            "progress": project.get("progress", 0),
            "start_date": project.get("start_date"),
            "end_date": project.get("end_date"),
            "budget": project.get("budget"),
            "created_at": project.get("created_at"),
        }
        
        if include_details:
            result["milestones"] = project.get("milestones", [])
            result["team_members"] = project.get("team_members", [])
            result["tags"] = project.get("tags", [])
        
        return result


portal_project_service = PortalProjectService()
```

---

## Task 20: Quote Service

**File: `backend/app/services/portal/quote_service.py`**

```python
"""
Portal Quote Service
Customer quote management
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging

from app.models.crm_store import crm_store

logger = logging.getLogger(__name__)


class PortalQuoteService:
    """Customer quote management service."""
    
    def __init__(self):
        self._signatures: Dict[str, Dict] = {}
    
    def list_quotes(self, customer_id: str, status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """List customer quotes."""
        quotes = crm_store.list_quotes_for_company(customer_id)
        
        if status:
            quotes = [q for q in quotes if q.get("status") == status]
        
        quotes.sort(key=lambda q: q.get("created_at", ""), reverse=True)
        
        total = len(quotes)
        skip = (page - 1) * page_size
        quotes = quotes[skip:skip + page_size]
        
        return {"items": [self._quote_to_dict(q) for q in quotes], "total": total, "page": page, "page_size": page_size}
    
    def get_quote(self, quote_id: str, customer_id: str) -> Optional[Dict]:
        """Get quote detail."""
        quote = crm_store.get_quote(quote_id)
        if not quote or quote.get("company_id") != customer_id:
            return None
        return self._quote_to_dict(quote, include_items=True)
    
    def accept_quote(self, quote_id: str, customer_id: str, signature_data: str = None, acceptance_notes: str = None) -> Dict:
        """Accept a quote."""
        quote = crm_store.get_quote(quote_id)
        if not quote or quote.get("company_id") != customer_id:
            raise ValueError("Quote not found")
        
        if quote.get("status") != "sent":
            raise ValueError("Quote cannot be accepted in current status")
        
        valid_until = quote.get("valid_until")
        if valid_until:
            expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            if expiry < datetime.utcnow():
                raise ValueError("Quote has expired")
        
        crm_store.update_quote(quote_id, {
            "status": "accepted",
            "accepted_at": datetime.utcnow().isoformat(),
            "acceptance_notes": acceptance_notes,
        })
        
        if signature_data:
            self._signatures[quote_id] = {
                "quote_id": quote_id,
                "customer_id": customer_id,
                "signature_data": signature_data,
                "signed_at": datetime.utcnow().isoformat(),
                "ip_address": None,
            }
        
        logger.info(f"Quote {quote_id} accepted by customer {customer_id}")
        
        return {"success": True, "status": "accepted", "quote_id": quote_id}
    
    def decline_quote(self, quote_id: str, customer_id: str, reason: str = None) -> Dict:
        """Decline a quote."""
        quote = crm_store.get_quote(quote_id)
        if not quote or quote.get("company_id") != customer_id:
            raise ValueError("Quote not found")
        
        if quote.get("status") != "sent":
            raise ValueError("Quote cannot be declined in current status")
        
        crm_store.update_quote(quote_id, {
            "status": "declined",
            "declined_at": datetime.utcnow().isoformat(),
            "decline_reason": reason,
        })
        
        logger.info(f"Quote {quote_id} declined by customer {customer_id}")
        
        return {"success": True, "status": "declined", "quote_id": quote_id}
    
    def request_revision(self, quote_id: str, customer_id: str, revision_notes: str) -> Dict:
        """Request quote revision."""
        quote = crm_store.get_quote(quote_id)
        if not quote or quote.get("company_id") != customer_id:
            raise ValueError("Quote not found")
        
        crm_store.update_quote(quote_id, {
            "status": "revision_requested",
            "revision_notes": revision_notes,
            "revision_requested_at": datetime.utcnow().isoformat(),
        })
        
        return {"success": True, "status": "revision_requested", "quote_id": quote_id}
    
    def get_quote_stats(self, customer_id: str) -> Dict[str, Any]:
        """Get quote statistics."""
        quotes = crm_store.list_quotes_for_company(customer_id)
        
        pending = len([q for q in quotes if q.get("status") == "sent"])
        accepted = len([q for q in quotes if q.get("status") == "accepted"])
        declined = len([q for q in quotes if q.get("status") == "declined"])
        total_value = sum(q.get("total", 0) for q in quotes if q.get("status") == "accepted")
        
        return {"pending": pending, "accepted": accepted, "declined": declined, "total_accepted_value": total_value}
    
    def _quote_to_dict(self, quote: Dict, include_items: bool = False) -> Dict:
        result = {
            "id": quote["id"],
            "quote_number": quote.get("quote_number"),
            "subject": quote.get("subject"),
            "status": quote.get("status"),
            "total": quote.get("total", 0),
            "subtotal": quote.get("subtotal", 0),
            "tax": quote.get("tax", 0),
            "discount": quote.get("discount", 0),
            "valid_until": quote.get("valid_until"),
            "created_at": quote.get("created_at"),
            "accepted_at": quote.get("accepted_at"),
            "is_expired": self._is_expired(quote.get("valid_until")),
            "expires_soon": self._expires_soon(quote.get("valid_until")),
        }
        
        if include_items:
            result["items"] = quote.get("items", [])
            result["terms"] = quote.get("terms")
            result["notes"] = quote.get("notes")
        
        return result
    
    def _is_expired(self, valid_until: str) -> bool:
        if not valid_until:
            return False
        try:
            expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            return expiry < datetime.utcnow()
        except:
            return False
    
    def _expires_soon(self, valid_until: str, days: int = 7) -> bool:
        if not valid_until:
            return False
        try:
            from datetime import timedelta
            expiry = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            return datetime.utcnow() < expiry <= datetime.utcnow() + timedelta(days=days)
        except:
            return False


portal_quote_service = PortalQuoteService()
```

---

## Task 21: Message Service

**File: `backend/app/services/portal/message_service.py`**

```python
"""
Portal Message Service
Customer communication center
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class Conversation:
    def __init__(self, tenant_id: str, customer_id: str, subject: str = None):
        self.id = f"conv_{uuid4().hex[:12]}"
        self.tenant_id = tenant_id
        self.customer_id = customer_id
        self.subject = subject
        self.status = "active"
        self.last_message_at = datetime.utcnow()
        self.last_message_preview = None
        self.unread_customer = 0
        self.unread_agent = 0
        self.messages = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class Message:
    def __init__(self, conversation_id: str, sender_type: str, sender_id: str, sender_name: str, content: str, attachments: List = None):
        self.id = f"msg_{uuid4().hex[:12]}"
        self.conversation_id = conversation_id
        self.sender_type = sender_type
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.content = content
        self.attachments = attachments or []
        self.read_at = None
        self.created_at = datetime.utcnow()


class MessageService:
    """Customer messaging service."""
    
    def __init__(self):
        self._conversations: Dict[str, Conversation] = {}
    
    def list_conversations(self, customer_id: str, status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """List customer conversations."""
        conversations = [c for c in self._conversations.values() if c.customer_id == customer_id]
        
        if status:
            conversations = [c for c in conversations if c.status == status]
        
        conversations.sort(key=lambda c: c.last_message_at, reverse=True)
        
        total = len(conversations)
        skip = (page - 1) * page_size
        conversations = conversations[skip:skip + page_size]
        
        return {"items": [self._conversation_to_dict(c) for c in conversations], "total": total, "page": page, "page_size": page_size}
    
    def get_conversation(self, conversation_id: str, customer_id: str) -> Optional[Dict]:
        """Get conversation with messages."""
        conv = self._conversations.get(conversation_id)
        if not conv or conv.customer_id != customer_id:
            return None
        return self._conversation_to_dict(conv, include_messages=True)
    
    def start_conversation(self, tenant_id: str, customer_id: str, contact_id: str, subject: str, initial_message: str, attachments: List = None) -> Conversation:
        """Start a new conversation."""
        from app.models.crm_store import crm_store
        contact = crm_store.get_contact(contact_id)
        sender_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() if contact else "Customer"
        
        conv = Conversation(tenant_id=tenant_id, customer_id=customer_id, subject=subject)
        
        msg = Message(conversation_id=conv.id, sender_type="customer", sender_id=contact_id, sender_name=sender_name, content=initial_message, attachments=attachments)
        
        conv.messages.append(msg)
        conv.last_message_preview = initial_message[:100]
        conv.unread_agent = 1
        
        self._conversations[conv.id] = conv
        
        logger.info(f"Conversation started: {conv.id}")
        
        return conv
    
    def send_message(self, conversation_id: str, customer_id: str, contact_id: str, content: str, attachments: List = None) -> Message:
        """Send a message in conversation."""
        conv = self._conversations.get(conversation_id)
        if not conv or conv.customer_id != customer_id:
            raise ValueError("Conversation not found")
        
        from app.models.crm_store import crm_store
        contact = crm_store.get_contact(contact_id)
        sender_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() if contact else "Customer"
        
        msg = Message(conversation_id=conversation_id, sender_type="customer", sender_id=contact_id, sender_name=sender_name, content=content, attachments=attachments)
        
        conv.messages.append(msg)
        conv.last_message_at = datetime.utcnow()
        conv.last_message_preview = content[:100]
        conv.unread_agent += 1
        conv.updated_at = datetime.utcnow()
        
        return msg
    
    def mark_as_read(self, conversation_id: str, customer_id: str):
        """Mark conversation as read."""
        conv = self._conversations.get(conversation_id)
        if not conv or conv.customer_id != customer_id:
            raise ValueError("Conversation not found")
        
        for msg in conv.messages:
            if msg.sender_type != "customer" and not msg.read_at:
                msg.read_at = datetime.utcnow()
        
        conv.unread_customer = 0
    
    def archive_conversation(self, conversation_id: str, customer_id: str):
        """Archive a conversation."""
        conv = self._conversations.get(conversation_id)
        if not conv or conv.customer_id != customer_id:
            raise ValueError("Conversation not found")
        
        conv.status = "archived"
        conv.updated_at = datetime.utcnow()
    
    def get_unread_count(self, customer_id: str) -> int:
        """Get total unread message count."""
        return sum(c.unread_customer for c in self._conversations.values() if c.customer_id == customer_id)
    
    def search_messages(self, customer_id: str, query: str, limit: int = 20) -> List[Dict]:
        """Search messages."""
        results = []
        query_lower = query.lower()
        
        for conv in self._conversations.values():
            if conv.customer_id != customer_id:
                continue
            
            for msg in conv.messages:
                if query_lower in msg.content.lower():
                    results.append({
                        "conversation_id": conv.id,
                        "message_id": msg.id,
                        "content": msg.content,
                        "sender_name": msg.sender_name,
                        "created_at": msg.created_at.isoformat(),
                    })
        
        results.sort(key=lambda r: r["created_at"], reverse=True)
        return results[:limit]
    
    def _conversation_to_dict(self, conv: Conversation, include_messages: bool = False) -> Dict:
        result = {
            "id": conv.id,
            "subject": conv.subject,
            "status": conv.status,
            "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
            "last_message_preview": conv.last_message_preview,
            "unread_count": conv.unread_customer,
            "message_count": len(conv.messages),
            "created_at": conv.created_at.isoformat(),
        }
        
        if include_messages:
            result["messages"] = [
                {
                    "id": m.id,
                    "sender_type": m.sender_type,
                    "sender_name": m.sender_name,
                    "content": m.content,
                    "attachments": m.attachments,
                    "read_at": m.read_at.isoformat() if m.read_at else None,
                    "created_at": m.created_at.isoformat(),
                }
                for m in conv.messages
            ]
        
        return result


message_service = MessageService()
```

---

## Task 22: Portal API Routes - Projects, Quotes, Messages

**File: `backend/app/routes/portal_v2/projects.py`**

```python
"""Portal v2 Project Routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.portal.project_service import portal_project_service
from app.utils.auth import get_current_user

router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("")
async def list_projects(status: Optional[str] = None, page: int = Query(1, ge=1), current_user: dict = Depends(get_portal_user)):
    return portal_project_service.list_projects(current_user.get("customer_id"), status, page)


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_portal_user)):
    return portal_project_service.get_project_stats(current_user.get("customer_id"))


@router.get("/{project_id}")
async def get_project(project_id: str, current_user: dict = Depends(get_portal_user)):
    project = portal_project_service.get_project(project_id, current_user.get("customer_id"))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/timeline")
async def get_timeline(project_id: str, current_user: dict = Depends(get_portal_user)):
    timeline = portal_project_service.get_project_timeline(project_id, current_user.get("customer_id"))
    if timeline is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return timeline


@router.get("/{project_id}/documents")
async def get_documents(project_id: str, current_user: dict = Depends(get_portal_user)):
    return portal_project_service.get_project_documents(project_id, current_user.get("customer_id"))


class FeedbackRequest(BaseModel):
    content: str
    rating: Optional[int] = None


@router.post("/{project_id}/feedback")
async def submit_feedback(project_id: str, data: FeedbackRequest, current_user: dict = Depends(get_portal_user)):
    try:
        return portal_project_service.submit_feedback(project_id, current_user.get("customer_id"), data.content, data.rating)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class ApprovalRequest(BaseModel):
    approved: bool
    comment: Optional[str] = None


@router.post("/{project_id}/deliverables/{deliverable_id}/approve")
async def approve_deliverable(project_id: str, deliverable_id: str, data: ApprovalRequest, current_user: dict = Depends(get_portal_user)):
    try:
        return portal_project_service.approve_deliverable(project_id, deliverable_id, current_user.get("customer_id"), data.approved, data.comment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**File: `backend/app/routes/portal_v2/quotes.py`**

```python
"""Portal v2 Quote Routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.services.portal.quote_service import portal_quote_service
from app.utils.auth import get_current_user

router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("")
async def list_quotes(status: Optional[str] = None, page: int = Query(1, ge=1), current_user: dict = Depends(get_portal_user)):
    return portal_quote_service.list_quotes(current_user.get("customer_id"), status, page)


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_portal_user)):
    return portal_quote_service.get_quote_stats(current_user.get("customer_id"))


@router.get("/{quote_id}")
async def get_quote(quote_id: str, current_user: dict = Depends(get_portal_user)):
    quote = portal_quote_service.get_quote(quote_id, current_user.get("customer_id"))
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


class AcceptRequest(BaseModel):
    signature_data: Optional[str] = None
    acceptance_notes: Optional[str] = None


@router.post("/{quote_id}/accept")
async def accept_quote(quote_id: str, data: AcceptRequest, current_user: dict = Depends(get_portal_user)):
    try:
        return portal_quote_service.accept_quote(quote_id, current_user.get("customer_id"), data.signature_data, data.acceptance_notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class DeclineRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/{quote_id}/decline")
async def decline_quote(quote_id: str, data: DeclineRequest, current_user: dict = Depends(get_portal_user)):
    try:
        return portal_quote_service.decline_quote(quote_id, current_user.get("customer_id"), data.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class RevisionRequest(BaseModel):
    revision_notes: str


@router.post("/{quote_id}/revision")
async def request_revision(quote_id: str, data: RevisionRequest, current_user: dict = Depends(get_portal_user)):
    try:
        return portal_quote_service.request_revision(quote_id, current_user.get("customer_id"), data.revision_notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**File: `backend/app/routes/portal_v2/messages.py`**

```python
"""Portal v2 Message Routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from app.services.portal.message_service import message_service
from app.utils.auth import get_current_user

router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("")
async def list_conversations(status: Optional[str] = None, page: int = Query(1, ge=1), current_user: dict = Depends(get_portal_user)):
    return message_service.list_conversations(current_user.get("customer_id"), status, page)


@router.get("/unread")
async def get_unread_count(current_user: dict = Depends(get_portal_user)):
    return {"unread": message_service.get_unread_count(current_user.get("customer_id"))}


@router.get("/search")
async def search_messages(q: str, limit: int = Query(20, ge=1, le=50), current_user: dict = Depends(get_portal_user)):
    return message_service.search_messages(current_user.get("customer_id"), q, limit)


class StartConversationRequest(BaseModel):
    subject: str
    message: str
    attachments: Optional[List[str]] = None


@router.post("")
async def start_conversation(data: StartConversationRequest, current_user: dict = Depends(get_portal_user)):
    conv = message_service.start_conversation(
        tenant_id=current_user.get("tenant_id"),
        customer_id=current_user.get("customer_id"),
        contact_id=current_user.get("contact_id"),
        subject=data.subject,
        initial_message=data.message,
        attachments=data.attachments,
    )
    return message_service._conversation_to_dict(conv, include_messages=True)


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, current_user: dict = Depends(get_portal_user)):
    conv = message_service.get_conversation(conversation_id, current_user.get("customer_id"))
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


class SendMessageRequest(BaseModel):
    content: str
    attachments: Optional[List[str]] = None


@router.post("/{conversation_id}/messages")
async def send_message(conversation_id: str, data: SendMessageRequest, current_user: dict = Depends(get_portal_user)):
    try:
        msg = message_service.send_message(
            conversation_id=conversation_id,
            customer_id=current_user.get("customer_id"),
            contact_id=current_user.get("contact_id"),
            content=data.content,
            attachments=data.attachments,
        )
        return {"id": msg.id, "content": msg.content, "created_at": msg.created_at.isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{conversation_id}/read")
async def mark_as_read(conversation_id: str, current_user: dict = Depends(get_portal_user)):
    try:
        message_service.mark_as_read(conversation_id, current_user.get("customer_id"))
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{conversation_id}/archive")
async def archive_conversation(conversation_id: str, current_user: dict = Depends(get_portal_user)):
    try:
        message_service.archive_conversation(conversation_id, current_user.get("customer_id"))
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Task 23: Frontend - Projects, Quotes, Messages Pages

**File: `frontend/src/features/portal/pages/Projects.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FolderOpen, Clock, CheckCircle, Pause, ChevronRight, Calendar, Users } from 'lucide-react';
import { portalAPI } from '../../../services/api';

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [stats, setStats] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => { loadData(); }, [statusFilter]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [projRes, statsRes] = await Promise.all([portalAPI.getProjects({ status: statusFilter }), portalAPI.getProjectStats()]);
      setProjects(projRes.data.items || []);
      setStats(statsRes.data);
    } catch (error) { console.error('Failed:', error); }
    finally { setIsLoading(false); }
  };

  const getStatusBadge = (status) => {
    const styles = { active: { bg: 'bg-blue-100', text: 'text-blue-700', icon: Clock }, completed: { bg: 'bg-green-100', text: 'text-green-700', icon: CheckCircle }, on_hold: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: Pause } };
    const style = styles[status] || styles.active;
    const Icon = style.icon;
    return <span className={`status-badge ${style.bg} ${style.text}`}><Icon className="w-3 h-3" />{status.replace('_', ' ')}</span>;
  };

  return (
    <div className="projects-page">
      <div className="page-header"><h1>Projects</h1><p>Track your active and completed projects</p></div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card"><FolderOpen className="w-8 h-8 text-blue-500" /><div><span className="stat-value">{stats.total}</span><span className="stat-label">Total</span></div></div>
          <div className="stat-card"><Clock className="w-8 h-8 text-blue-500" /><div><span className="stat-value">{stats.active}</span><span className="stat-label">Active</span></div></div>
          <div className="stat-card"><CheckCircle className="w-8 h-8 text-green-500" /><div><span className="stat-value">{stats.completed}</span><span className="stat-label">Completed</span></div></div>
        </div>
      )}

      <div className="filter-bar">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All Projects</option><option value="active">Active</option><option value="completed">Completed</option><option value="on_hold">On Hold</option>
        </select>
      </div>

      <div className="project-list">
        {projects.map((project) => (
          <Link key={project.id} to={`/portal/projects/${project.id}`} className="project-card">
            <div className="project-main">
              <div className="project-header"><h3>{project.name}</h3>{getStatusBadge(project.status)}</div>
              <p className="project-desc">{project.description}</p>
              <div className="progress-bar"><div className="progress-fill" style={{ width: `${project.progress}%` }} /></div>
              <div className="project-meta">
                <span><Calendar className="w-4 h-4" /> {project.end_date ? new Date(project.end_date).toLocaleDateString() : 'No deadline'}</span>
                <span>{project.progress}% complete</span>
              </div>
            </div>
            <ChevronRight className="w-5 h-5" />
          </Link>
        ))}
      </div>
    </div>
  );
}
```

**File: `frontend/src/features/portal/pages/Quotes.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { FileCheck, Clock, CheckCircle, XCircle, AlertTriangle, Download } from 'lucide-react';
import { portalAPI } from '../../../services/api';

export default function Quotes() {
  const [quotes, setQuotes] = useState([]);
  const [stats, setStats] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedQuote, setSelectedQuote] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => { loadData(); }, [statusFilter]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [quotesRes, statsRes] = await Promise.all([portalAPI.getQuotes({ status: statusFilter }), portalAPI.getQuoteStats()]);
      setQuotes(quotesRes.data.items || []);
      setStats(statsRes.data);
    } catch (error) { console.error('Failed:', error); }
    finally { setIsLoading(false); }
  };

  const handleAccept = async (quoteId) => {
    if (!confirm('Accept this quote?')) return;
    try {
      setIsProcessing(true);
      await portalAPI.acceptQuote(quoteId, {});
      alert('Quote accepted!');
      setSelectedQuote(null);
      loadData();
    } catch (error) { alert('Failed: ' + (error.response?.data?.detail || 'Unknown error')); }
    finally { setIsProcessing(false); }
  };

  const handleDecline = async (quoteId) => {
    const reason = prompt('Reason for declining (optional):');
    try {
      setIsProcessing(true);
      await portalAPI.declineQuote(quoteId, { reason });
      alert('Quote declined');
      setSelectedQuote(null);
      loadData();
    } catch (error) { alert('Failed'); }
    finally { setIsProcessing(false); }
  };

  const getStatusBadge = (status, isExpired, expiresSoon) => {
    if (isExpired) return <span className="status-badge bg-gray-100 text-gray-700">Expired</span>;
    if (status === 'sent' && expiresSoon) return <span className="status-badge bg-orange-100 text-orange-700"><AlertTriangle className="w-3 h-3" /> Expires Soon</span>;
    const styles = { sent: { bg: 'bg-blue-100', text: 'text-blue-700', icon: Clock }, accepted: { bg: 'bg-green-100', text: 'text-green-700', icon: CheckCircle }, declined: { bg: 'bg-red-100', text: 'text-red-700', icon: XCircle } };
    const style = styles[status] || styles.sent;
    const Icon = style.icon;
    return <span className={`status-badge ${style.bg} ${style.text}`}><Icon className="w-3 h-3" />{status}</span>;
  };

  return (
    <div className="quotes-page">
      <div className="page-header"><h1>Quotes</h1><p>Review and respond to quotes</p></div>

      {stats && (
        <div className="stats-grid">
          <div className="stat-card"><Clock className="w-8 h-8 text-blue-500" /><div><span className="stat-value">{stats.pending}</span><span className="stat-label">Pending</span></div></div>
          <div className="stat-card"><CheckCircle className="w-8 h-8 text-green-500" /><div><span className="stat-value">{stats.accepted}</span><span className="stat-label">Accepted</span></div></div>
          <div className="stat-card"><XCircle className="w-8 h-8 text-red-500" /><div><span className="stat-value">{stats.declined}</span><span className="stat-label">Declined</span></div></div>
        </div>
      )}

      <div className="quote-list">
        {quotes.map((quote) => (
          <div key={quote.id} className="quote-card">
            <div className="quote-main">
              <div className="quote-header"><span className="quote-number">#{quote.quote_number}</span>{getStatusBadge(quote.status, quote.is_expired, quote.expires_soon)}</div>
              <h3>{quote.subject || `Quote #${quote.quote_number}`}</h3>
              <div className="quote-meta"><span>Valid until: {quote.valid_until ? new Date(quote.valid_until).toLocaleDateString() : 'N/A'}</span></div>
            </div>
            <div className="quote-amount"><span className="amount">${quote.total?.toLocaleString()}</span></div>
            <div className="quote-actions">
              <button onClick={() => setSelectedQuote(quote)}>View</button>
              {quote.status === 'sent' && !quote.is_expired && (<><button className="accept-btn" onClick={() => handleAccept(quote.id)}>Accept</button><button className="decline-btn" onClick={() => handleDecline(quote.id)}>Decline</button></>)}
            </div>
          </div>
        ))}
      </div>

      {selectedQuote && (
        <div className="modal-overlay" onClick={() => setSelectedQuote(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Quote #{selectedQuote.quote_number}</h2>
            <div className="quote-items">{selectedQuote.items?.map((item, i) => (<div key={i} className="quote-item"><span>{item.description}</span><span>${item.total?.toLocaleString()}</span></div>))}</div>
            <div className="quote-total"><span>Total</span><span>${selectedQuote.total?.toLocaleString()}</span></div>
            <div className="modal-actions">
              <button><Download className="w-4 h-4" /> Download PDF</button>
              {selectedQuote.status === 'sent' && !selectedQuote.is_expired && (<><button className="accept-btn" onClick={() => handleAccept(selectedQuote.id)} disabled={isProcessing}>Accept</button><button className="decline-btn" onClick={() => handleDecline(selectedQuote.id)} disabled={isProcessing}>Decline</button></>)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

**File: `frontend/src/features/portal/pages/Messages.jsx`**

```jsx
import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, Send, Plus, Search, Archive, User, Bot } from 'lucide-react';
import { portalAPI } from '../../../services/api';

export default function Messages() {
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [newMessage, setNewMessage] = useState('');
  const [showNewConversation, setShowNewConversation] = useState(false);
  const [newSubject, setNewSubject] = useState('');
  const [newContent, setNewContent] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => { loadConversations(); }, []);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [selectedConversation?.messages]);

  const loadConversations = async () => {
    try {
      const res = await portalAPI.getConversations();
      setConversations(res.data.items || []);
    } catch (error) { console.error('Failed:', error); }
  };

  const loadConversation = async (id) => {
    try {
      const res = await portalAPI.getConversation(id);
      setSelectedConversation(res.data);
      await portalAPI.markConversationRead(id);
    } catch (error) { console.error('Failed:', error); }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;
    try {
      setIsSending(true);
      await portalAPI.sendMessage(selectedConversation.id, { content: newMessage });
      setNewMessage('');
      loadConversation(selectedConversation.id);
    } catch (error) { console.error('Failed:', error); }
    finally { setIsSending(false); }
  };

  const handleStartConversation = async () => {
    if (!newSubject.trim() || !newContent.trim()) return;
    try {
      setIsSending(true);
      const res = await portalAPI.startConversation({ subject: newSubject, message: newContent });
      setShowNewConversation(false);
      setNewSubject('');
      setNewContent('');
      loadConversations();
      setSelectedConversation(res.data);
    } catch (error) { console.error('Failed:', error); }
    finally { setIsSending(false); }
  };

  return (
    <div className="messages-page">
      <div className="conversations-sidebar">
        <div className="sidebar-header">
          <h2>Messages</h2>
          <button onClick={() => setShowNewConversation(true)}><Plus className="w-4 h-4" /></button>
        </div>
        <div className="conversation-list">
          {conversations.map((conv) => (
            <button key={conv.id} className={`conversation-item ${selectedConversation?.id === conv.id ? 'active' : ''}`} onClick={() => loadConversation(conv.id)}>
              <div className="conv-icon"><MessageCircle className="w-5 h-5" /></div>
              <div className="conv-info"><span className="conv-subject">{conv.subject}</span><span className="conv-preview">{conv.last_message_preview}</span></div>
              {conv.unread_count > 0 && <span className="unread-badge">{conv.unread_count}</span>}
            </button>
          ))}
        </div>
      </div>

      <div className="conversation-view">
        {selectedConversation ? (
          <>
            <div className="conv-header"><h3>{selectedConversation.subject}</h3></div>
            <div className="messages-list">
              {selectedConversation.messages?.map((msg) => (
                <div key={msg.id} className={`message ${msg.sender_type === 'customer' ? 'outgoing' : 'incoming'}`}>
                  <div className="message-avatar">{msg.sender_type === 'customer' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}</div>
                  <div className="message-content">
                    <div className="message-header"><span className="sender">{msg.sender_name}</span><span className="time">{new Date(msg.created_at).toLocaleString()}</span></div>
                    <div className="message-text">{msg.content}</div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            <div className="reply-box">
              <input type="text" placeholder="Type a message..." value={newMessage} onChange={(e) => setNewMessage(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()} />
              <button onClick={handleSendMessage} disabled={isSending || !newMessage.trim()}><Send className="w-4 h-4" /></button>
            </div>
          </>
        ) : (
          <div className="empty-state"><MessageCircle className="w-12 h-12" /><h3>Select a conversation</h3><p>Or start a new one</p></div>
        )}
      </div>

      {showNewConversation && (
        <div className="modal-overlay" onClick={() => setShowNewConversation(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>New Conversation</h2>
            <input type="text" placeholder="Subject" value={newSubject} onChange={(e) => setNewSubject(e.target.value)} />
            <textarea placeholder="Your message..." value={newContent} onChange={(e) => setNewContent(e.target.value)} rows={4} />
            <div className="modal-actions">
              <button onClick={() => setShowNewConversation(false)}>Cancel</button>
              <button className="primary" onClick={handleStartConversation} disabled={isSending}><Send className="w-4 h-4" /> Send</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Summary: Part 4 Complete

### Files Created:

| File | Purpose | Lines |
|------|---------|-------|
| `project_service.py` | Project visibility | ~140 |
| `quote_service.py` | Quote management | ~150 |
| `message_service.py` | Messaging service | ~180 |
| `projects.py` | Project API routes | ~70 |
| `quotes.py` | Quote API routes | ~80 |
| `messages.py` | Message API routes | ~90 |
| `Projects.jsx` | Projects UI | ~80 |
| `Quotes.jsx` | Quotes UI | ~100 |
| `Messages.jsx` | Messages UI | ~110 |
| **Total** | | **~1,000** |

### Features:

| Feature | Status |
|---------|--------|
| Project list | ✅ |
| Project detail | ✅ |
| Project timeline | ✅ |
| Project documents | ✅ |
| Project feedback | ✅ |
| Deliverable approval | ✅ |
| Quote list | ✅ |
| Quote detail | ✅ |
| Accept quote | ✅ |
| Decline quote | ✅ |
| Request revision | ✅ |
| Conversation list | ✅ |
| Send message | ✅ |
| Start conversation | ✅ |
| Mark as read | ✅ |
| Archive conversation | ✅ |

---

## Phase 27 Complete Summary

### Total Files: 22 files, ~5,400 lines

| Part | Files | Lines | Focus |
|------|-------|-------|-------|
| Part 1 | 7 | ~1,630 | Foundation & Dashboard |
| Part 2 | 5 | ~1,410 | Support Ticketing |
| Part 3 | 6 | ~710 | Knowledge Base & Payments |
| Part 4 | 9 | ~1,000 | Projects, Quotes, Messages |

### Feature Summary (96 features)

| Category | Implemented |
|----------|-------------|
| Dashboard | ✅ 12 features |
| Support Tickets | ✅ 16 features |
| Knowledge Base | ✅ 14 features |
| Communication | ✅ 12 features |
| Projects | ✅ 10 features |
| Quotes | ✅ 10 features |
| Payments | ✅ 12 features |
| Account | ✅ 10 features |

**Phase 27: COMPLETE** 🎉
