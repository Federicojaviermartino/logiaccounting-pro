"""
AI Conversation Models
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import uuid


# In-memory storage
conversations_db: Dict[str, 'AIConversation'] = {}
messages_db: Dict[str, 'AIMessage'] = {}


@dataclass
class AIConversation:
    """AI assistant conversation"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ''
    user_id: str = ''
    title: Optional[str] = None
    is_active: bool = True
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def save(self):
        conversations_db[self.id] = self

    @classmethod
    def get_by_id(cls, conversation_id: str, tenant_id: str) -> Optional['AIConversation']:
        """Get conversation by ID"""
        conv = conversations_db.get(conversation_id)
        if conv and conv.tenant_id == tenant_id:
            return conv
        return None

    @classmethod
    def get_by_user(
        cls,
        tenant_id: str,
        user_id: str,
        limit: int = 20
    ) -> List['AIConversation']:
        """Get conversations for user"""
        convs = [
            c for c in conversations_db.values()
            if c.tenant_id == tenant_id and c.user_id == user_id and c.is_active
        ]
        convs.sort(key=lambda x: x.updated_at, reverse=True)
        return convs[:limit]

    def get_messages(self, limit: int = 100) -> List['AIMessage']:
        """Get messages for this conversation"""
        msgs = [m for m in messages_db.values() if m.conversation_id == self.id]
        msgs.sort(key=lambda x: x.created_at)
        return msgs[:limit]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'is_active': self.is_active,
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class AIMessage:
    """AI assistant message"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = ''
    role: str = ''
    content: str = ''
    tool_calls: Optional[Dict] = None
    tool_results: Optional[Dict] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def save(self):
        messages_db[self.id] = self

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'tool_calls': self.tool_calls,
            'tool_results': self.tool_results,
            'feedback': self.feedback,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
