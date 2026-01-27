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
