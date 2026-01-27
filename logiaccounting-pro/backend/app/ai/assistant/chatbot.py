"""
AI Assistant Chatbot
Conversational AI for business queries
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
import logging

from app.ai.client import ai_client
from app.ai.config import get_model_config
from app.ai.assistant.prompts import SYSTEM_PROMPT, get_context_prompt

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Optional[Dict] = None
    suggested_actions: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "suggested_actions": self.suggested_actions,
        }


@dataclass
class Conversation:
    """Chat conversation."""
    id: str = field(default_factory=lambda: f"conv_{uuid4().hex[:12]}")
    customer_id: str = ""
    messages: List[Message] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def add_message(self, role: str, content: str, **kwargs) -> Message:
        """Add a message to the conversation."""
        msg = Message(role=role, content=content, **kwargs)
        self.messages.append(msg)
        self.updated_at = datetime.utcnow()
        return msg

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "messages": [m.to_dict() for m in self.messages],
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class AssistantResponse:
    """Response from AI assistant."""
    response: str
    conversation_id: str
    data: Optional[Dict] = None
    suggested_actions: List[Dict] = field(default_factory=list)
    tokens_used: int = 0

    def to_dict(self) -> Dict:
        return {
            "response": self.response,
            "conversation_id": self.conversation_id,
            "data": self.data,
            "suggested_actions": self.suggested_actions,
            "tokens_used": self.tokens_used,
        }


class AIAssistant:
    """AI assistant for business queries."""

    def __init__(self):
        self._conversations: Dict[str, Conversation] = {}
        self.model_config = get_model_config("balanced")

    def get_or_create_conversation(
        self,
        customer_id: str,
        conversation_id: str = None,
    ) -> Conversation:
        """Get existing or create new conversation."""
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]

        # Create new conversation
        conv = Conversation(customer_id=customer_id)
        self._conversations[conv.id] = conv
        return conv

    async def chat(
        self,
        customer_id: str,
        message: str,
        conversation_id: str = None,
        context: Dict = None,
    ) -> AssistantResponse:
        """Process a chat message."""
        logger.info(f"Processing chat for customer {customer_id}")

        # Get conversation
        conv = self.get_or_create_conversation(customer_id, conversation_id)

        # Update context
        if context:
            conv.context.update(context)

        # Add user message
        conv.add_message("user", message)

        try:
            # Build messages for AI
            ai_messages = self._build_ai_messages(conv)

            # Get system prompt with context
            system = SYSTEM_PROMPT + "\n\n" + get_context_prompt(conv.context)

            # Call AI
            response_text = await ai_client.chat(
                messages=ai_messages,
                system=system,
                model_config=self.model_config,
            )

            # Parse response for data and actions
            data, actions = self._parse_response(response_text)

            # Add assistant message
            conv.add_message(
                "assistant",
                response_text,
                data=data,
                suggested_actions=actions,
            )

            return AssistantResponse(
                response=response_text,
                conversation_id=conv.id,
                data=data,
                suggested_actions=actions,
            )

        except Exception as e:
            logger.error(f"Chat failed: {e}")
            error_msg = "I apologize, but I encountered an error processing your request. Please try again."
            conv.add_message("assistant", error_msg)
            return AssistantResponse(
                response=error_msg,
                conversation_id=conv.id,
            )

    def _build_ai_messages(self, conv: Conversation) -> List[Dict]:
        """Build messages list for AI API."""
        messages = []

        # Include recent messages (last 10)
        recent = conv.messages[-10:]
        for msg in recent:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        return messages

    def _parse_response(self, response: str) -> tuple:
        """Parse response for data and suggested actions."""
        # For now, simple extraction
        data = None
        actions = []

        # Check for common action triggers
        response_lower = response.lower()

        if "invoice" in response_lower:
            actions.append({"action": "view_invoices", "label": "View Invoices"})
        if "cash flow" in response_lower or "cashflow" in response_lower:
            actions.append({"action": "view_cashflow", "label": "View Cash Flow"})
        if "expense" in response_lower:
            actions.append({"action": "view_expenses", "label": "View Expenses"})
        if "customer" in response_lower:
            actions.append({"action": "view_customers", "label": "View Customers"})
        if "report" in response_lower:
            actions.append({"action": "view_reports", "label": "View Reports"})

        return data, actions[:3]  # Limit to 3 actions

    def get_conversation(self, customer_id: str, conversation_id: str) -> Optional[Conversation]:
        """Get a specific conversation."""
        conv = self._conversations.get(conversation_id)
        if conv and conv.customer_id == customer_id:
            return conv
        return None

    def get_conversations(self, customer_id: str, limit: int = 10) -> List[Conversation]:
        """Get recent conversations for customer."""
        convs = [c for c in self._conversations.values() if c.customer_id == customer_id]
        convs.sort(key=lambda c: c.updated_at, reverse=True)
        return convs[:limit]

    def delete_conversation(self, customer_id: str, conversation_id: str) -> bool:
        """Delete a conversation."""
        conv = self._conversations.get(conversation_id)
        if conv and conv.customer_id == customer_id:
            del self._conversations[conversation_id]
            return True
        return False


# Global assistant instance
ai_assistant = AIAssistant()
