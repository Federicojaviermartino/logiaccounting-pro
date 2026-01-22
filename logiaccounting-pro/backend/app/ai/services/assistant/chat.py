"""
Chat Assistant
AI-powered business assistant for accounting queries
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from ...config import get_ai_config, ModelTier
from ...models.conversation import AIConversation, AIMessage
from ..llm_client import get_llm_client
from .tools import AssistantTools

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are an AI-powered accounting and business assistant for LogiAccounting Pro.
Your role is to help users understand their financial data, provide insights, and answer business questions.

You have access to the following tools to query business data:
{tools}

When answering questions:
1. Use the appropriate tool to fetch relevant data
2. Analyze the data and provide clear, actionable insights
3. Be specific with numbers and percentages
4. Suggest actions when appropriate
5. If you're unsure about something, say so

Guidelines:
- Always be professional and helpful
- Present financial data clearly with proper formatting
- Round currency amounts to 2 decimal places
- Include context and comparisons when relevant
- Never make up data - only use information from the tools

If the user asks about something outside your capabilities, politely explain what you can help with."""


class ChatAssistant:
    """AI chat assistant for business queries"""

    def __init__(self):
        self.config = get_ai_config()
        self.llm = get_llm_client()

    async def create_conversation(
        self,
        tenant_id: str,
        user_id: str,
        title: Optional[str] = None,
    ) -> AIConversation:
        """Create a new conversation"""
        conversation = AIConversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title or 'New Conversation',
        )
        conversation.save()
        return conversation

    async def get_conversation(
        self,
        conversation_id: str,
        tenant_id: str,
    ) -> Optional[AIConversation]:
        """Get conversation by ID"""
        return AIConversation.get_by_id(conversation_id, tenant_id)

    async def get_user_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 20,
    ) -> List[AIConversation]:
        """Get user's conversations"""
        return AIConversation.get_by_user(tenant_id, user_id, limit)

    async def chat(
        self,
        conversation_id: str,
        tenant_id: str,
        user_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate response

        Args:
            conversation_id: Conversation ID
            tenant_id: Tenant ID
            user_id: User ID
            message: User's message

        Returns:
            Response with assistant message
        """
        # Get or create conversation
        conversation = await self.get_conversation(conversation_id, tenant_id)
        if not conversation:
            conversation = await self.create_conversation(tenant_id, user_id)

        # Save user message
        user_msg = AIMessage(
            conversation_id=conversation.id,
            role='user',
            content=message,
        )
        user_msg.save()

        # Get conversation history
        messages = conversation.get_messages(limit=20)
        history = [
            {'role': msg.role, 'content': msg.content}
            for msg in messages
        ]

        # Initialize tools
        tools = AssistantTools(tenant_id)

        # Build system prompt with tools
        tools_description = json.dumps(tools.get_available_tools(), indent=2)
        system_prompt = SYSTEM_PROMPT.format(tools=tools_description)

        # Determine if we need to use tools
        tool_calls = await self._determine_tools(message, tools)

        # Execute tools and gather data
        tool_results = {}
        if tool_calls:
            for tool_call in tool_calls:
                try:
                    result = await self._execute_tool(tools, tool_call)
                    tool_results[tool_call['name']] = result
                except Exception as e:
                    logger.warning(f"Tool execution failed: {e}")
                    tool_results[tool_call['name']] = {'error': str(e)}

        # Build context with tool results
        if tool_results:
            context = f"\n\nData from business tools:\n{json.dumps(tool_results, indent=2)}"
            enhanced_message = f"{message}\n{context}"
        else:
            enhanced_message = message

        # Add enhanced message to history
        history[-1] = {'role': 'user', 'content': enhanced_message}

        # Generate response
        response = await self.llm.chat(
            messages=history,
            system_prompt=system_prompt,
            tier=ModelTier.BALANCED,
            tenant_id=tenant_id,
            feature='assistant_chat',
        )

        # Save assistant message
        assistant_msg = AIMessage(
            conversation_id=conversation.id,
            role='assistant',
            content=response.content,
            tool_calls=tool_calls if tool_calls else None,
            tool_results=tool_results if tool_results else None,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )
        assistant_msg.save()

        # Update conversation
        conversation.total_input_tokens += response.input_tokens
        conversation.total_output_tokens += response.output_tokens
        conversation.updated_at = datetime.utcnow()

        # Auto-generate title from first message
        if not conversation.title or conversation.title == 'New Conversation':
            conversation.title = await self._generate_title(message)

        conversation.save()

        return {
            'conversation_id': conversation.id,
            'message_id': assistant_msg.id,
            'content': response.content,
            'tool_calls': tool_calls,
            'tokens_used': response.input_tokens + response.output_tokens,
        }

    async def _determine_tools(
        self,
        message: str,
        tools: AssistantTools,
    ) -> List[Dict[str, Any]]:
        """Determine which tools to use based on message"""
        message_lower = message.lower()

        tool_calls = []

        # Revenue related
        if any(kw in message_lower for kw in ['revenue', 'sales', 'income', 'earnings']):
            tool_calls.append({'name': 'get_revenue_summary', 'params': {'period': 'month'}})

        # Expense related
        if any(kw in message_lower for kw in ['expense', 'spending', 'cost', 'costs']):
            tool_calls.append({'name': 'get_expense_summary', 'params': {'period': 'month'}})

        # Profitability
        if any(kw in message_lower for kw in ['profit', 'margin', 'profitability']):
            tool_calls.append({'name': 'get_profitability_metrics', 'params': {'period': 'month'}})

        # Cash
        if any(kw in message_lower for kw in ['cash', 'balance', 'bank', 'liquidity']):
            tool_calls.append({'name': 'get_cash_position', 'params': {}})

        # AR
        if any(kw in message_lower for kw in ['receivable', 'owed', 'outstanding invoices', 'ar']):
            tool_calls.append({'name': 'get_accounts_receivable', 'params': {'aging': True}})

        # AP
        if any(kw in message_lower for kw in ['payable', 'bills', 'ap', 'vendors']):
            tool_calls.append({'name': 'get_accounts_payable', 'params': {}})

        # Budget
        if any(kw in message_lower for kw in ['budget', 'variance', 'actual vs']):
            tool_calls.append({'name': 'get_budget_vs_actual', 'params': {'period': 'month'}})

        # General financial overview
        if any(kw in message_lower for kw in ['overview', 'summary', 'how are we doing', 'financial health']):
            tool_calls = [
                {'name': 'get_profitability_metrics', 'params': {'period': 'month'}},
                {'name': 'get_cash_position', 'params': {}},
                {'name': 'get_accounts_receivable', 'params': {'aging': True}},
            ]

        return tool_calls

    async def _execute_tool(
        self,
        tools: AssistantTools,
        tool_call: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a tool call"""
        name = tool_call['name']
        params = tool_call.get('params', {})

        method = getattr(tools, name, None)
        if not method:
            raise ValueError(f"Unknown tool: {name}")

        return await method(**params)

    async def _generate_title(self, first_message: str) -> str:
        """Generate conversation title from first message"""
        # Simple title generation - first 50 chars
        title = first_message[:50]
        if len(first_message) > 50:
            title += '...'
        return title

    async def provide_feedback(
        self,
        message_id: str,
        feedback: str,
    ) -> bool:
        """Record feedback for a message"""
        # Find message in storage
        from ...models.conversation import messages_db
        msg = messages_db.get(message_id)
        if msg:
            msg.feedback = feedback
            return True
        return False
