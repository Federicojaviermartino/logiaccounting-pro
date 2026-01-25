"""
AI Assistant Module
Conversational AI for business insights
"""

from app.ai.assistant.chatbot import AIAssistant, Message, Conversation, AssistantResponse
from app.ai.assistant.prompts import SYSTEM_PROMPT, get_context_prompt
from app.ai.assistant.tools import AssistantTool, AssistantToolRegistry, tool_registry
from app.ai.assistant.service import assistant_service, AssistantService


__all__ = [
    'AIAssistant',
    'Message',
    'Conversation',
    'AssistantResponse',
    'SYSTEM_PROMPT',
    'get_context_prompt',
    'AssistantTool',
    'AssistantToolRegistry',
    'tool_registry',
    'assistant_service',
    'AssistantService',
]
