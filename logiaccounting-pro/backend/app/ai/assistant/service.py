"""
AI Assistant Service
High-level service for AI assistant features
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.utils.datetime_utils import utc_now
from app.ai.base import AIResult
from app.ai.assistant.chatbot import AIAssistant, ai_assistant, AssistantResponse
from app.ai.assistant.prompts import get_suggestions

logger = logging.getLogger(__name__)


class AssistantService:
    """Service layer for AI assistant."""

    def __init__(self, assistant: AIAssistant = None):
        self.assistant = assistant or ai_assistant

    async def chat(
        self,
        customer_id: str,
        message: str,
        conversation_id: str = None,
        context: Dict = None,
    ) -> AIResult:
        """Process a chat message."""
        logger.info(f"Chat request from customer {customer_id}")

        if not message or not message.strip():
            return AIResult.fail("Message cannot be empty")

        try:
            response = await self.assistant.chat(
                customer_id=customer_id,
                message=message,
                conversation_id=conversation_id,
                context=context or {},
            )

            return AIResult.ok(response.to_dict())

        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return AIResult.fail(str(e))

    async def get_quick_insights(self, customer_id: str) -> AIResult:
        """Get quick AI-generated insights."""
        logger.info(f"Getting quick insights for customer {customer_id}")

        try:
            # Generate quick insights prompt
            prompt = """Based on typical business patterns, provide 3-4 quick insights a business owner would find valuable today. Include:
1. A cash flow observation
2. An accounts receivable insight
3. An expense trend
4. A recommended action

Keep each insight to 1-2 sentences."""

            response = await self.assistant.chat(
                customer_id=customer_id,
                message=prompt,
                context={"type": "quick_insights"},
            )

            return AIResult.ok({
                "insights": response.response,
                "generated_at": utc_now().isoformat(),
            })

        except Exception as e:
            logger.error(f"Quick insights failed: {e}")
            return AIResult.fail(str(e))

    async def analyze_entity(
        self,
        customer_id: str,
        entity_type: str,
        entity_id: str,
        analysis_type: str = "general",
    ) -> AIResult:
        """Analyze a specific entity."""
        logger.info(f"Analyzing {entity_type} {entity_id} for customer {customer_id}")

        try:
            prompt = f"""Analyze this {entity_type} (ID: {entity_id}).
Analysis type: {analysis_type}

Provide:
1. Key metrics and observations
2. Comparison to benchmarks if applicable
3. Potential issues or opportunities
4. Recommended actions"""

            response = await self.assistant.chat(
                customer_id=customer_id,
                message=prompt,
                context={
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "analysis_type": analysis_type,
                },
            )

            return AIResult.ok({
                "analysis": response.response,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "suggested_actions": response.suggested_actions,
            })

        except Exception as e:
            logger.error(f"Entity analysis failed: {e}")
            return AIResult.fail(str(e))

    def get_conversations(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations."""
        conversations = self.assistant.get_conversations(customer_id, limit)
        return [conv.to_dict() for conv in conversations]

    def get_conversation(self, customer_id: str, conversation_id: str) -> Optional[Dict]:
        """Get a specific conversation."""
        conv = self.assistant.get_conversation(customer_id, conversation_id)
        return conv.to_dict() if conv else None

    def delete_conversation(self, customer_id: str, conversation_id: str) -> bool:
        """Delete a conversation."""
        return self.assistant.delete_conversation(customer_id, conversation_id)

    async def get_suggestions(self, customer_id: str, query_prefix: str = "") -> List[str]:
        """Get query suggestions."""
        return get_suggestions(query_prefix)


# Global service instance
assistant_service = AssistantService()
