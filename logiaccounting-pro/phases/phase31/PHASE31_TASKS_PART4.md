# Phase 31: AI/ML Features - Part 4: AI Assistant / Chatbot

## Overview
This part covers the intelligent AI assistant that helps users analyze data, answer questions, and provide insights through natural language conversation.

---

## File 1: AI Chatbot
**Path:** `backend/app/ai/assistant/chatbot.py`

```python
"""
AI Assistant Chatbot
Conversational AI for business insights
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from uuid import uuid4
import json
import logging

from app.ai.base import BaseAssistant
from app.ai.client import ai_client, AIProvider
from app.ai.config import get_model_config
from app.ai.assistant.prompts import SYSTEM_PROMPT, get_context_prompt
from app.ai.assistant.tools import AssistantToolRegistry, tool_registry

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Chat message."""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    def to_api_format(self) -> Dict:
        """Convert to API message format."""
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass
class Conversation:
    """Chat conversation."""
    id: str
    customer_id: str
    messages: List[Message] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "messages": [m.to_dict() for m in self.messages],
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": len(self.messages),
        }
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add message to conversation."""
        self.messages.append(Message(
            role=role,
            content=content,
            metadata=metadata or {},
        ))
        self.updated_at = datetime.utcnow()
    
    def get_messages_for_api(self, max_messages: int = 20) -> List[Dict]:
        """Get messages in API format."""
        recent = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        return [m.to_api_format() for m in recent]


@dataclass
class AssistantResponse:
    """Response from the AI assistant."""
    response: str
    data: Optional[Dict] = None
    suggested_actions: List[Dict] = field(default_factory=list)
    sources: List[Dict] = field(default_factory=list)
    conversation_id: str = ""
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "response": self.response,
            "data": self.data,
            "suggested_actions": self.suggested_actions,
            "sources": self.sources,
            "conversation_id": self.conversation_id,
            "processing_time_ms": self.processing_time_ms,
        }


class AIAssistant(BaseAssistant):
    """Intelligent business assistant."""
    
    MAX_TOOL_ITERATIONS = 5
    
    def __init__(self, customer_id: str):
        super().__init__(
            name="LogiAccounting Assistant",
            system_prompt=SYSTEM_PROMPT,
        )
        self.customer_id = customer_id
        self._conversations: Dict[str, Conversation] = {}
        self._model_config = get_model_config("balanced")
    
    async def process_message(
        self,
        message: str,
        conversation_id: str = None,
        context: Dict = None,
    ) -> AssistantResponse:
        """Process user message and generate response."""
        import time
        start_time = time.time()
        
        # Get or create conversation
        conversation = self._get_or_create_conversation(conversation_id, context)
        
        # Add user message
        conversation.add_message("user", message)
        
        try:
            # Build system prompt with context
            system = self._build_system_prompt(conversation.context)
            
            # Get conversation messages
            messages = conversation.get_messages_for_api()
            
            # Get available tools
            tools = tool_registry.get_tools_for_context(conversation.context)
            
            # Process with tools if available
            if tools:
                result = await self._process_with_tools(messages, system, tools)
            else:
                result = await self._process_simple(messages, system)
            
            # Add assistant response
            conversation.add_message("assistant", result["response"])
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return AssistantResponse(
                response=result["response"],
                data=result.get("data"),
                suggested_actions=result.get("suggested_actions", []),
                sources=result.get("sources", []),
                conversation_id=conversation.id,
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            logger.error(f"Assistant error: {e}")
            
            error_response = "I apologize, but I encountered an error processing your request. Please try again or rephrase your question."
            conversation.add_message("assistant", error_response)
            
            return AssistantResponse(
                response=error_response,
                conversation_id=conversation.id,
            )
    
    async def process_with_tools(
        self,
        message: str,
        tools: List[Dict],
        context: Dict = None,
    ) -> Dict:
        """Process message with specific tools."""
        conversation = self._get_or_create_conversation(None, context)
        conversation.add_message("user", message)
        
        system = self._build_system_prompt(context or {})
        messages = conversation.get_messages_for_api()
        
        result = await self._process_with_tools(messages, system, tools)
        conversation.add_message("assistant", result["response"])
        
        return result
    
    async def _process_simple(self, messages: List[Dict], system: str) -> Dict:
        """Process without tools."""
        response = await ai_client.chat(
            messages=messages,
            system=system,
            model_config=self._model_config,
        )
        
        return {
            "response": response,
            "data": None,
            "suggested_actions": [],
        }
    
    async def _process_with_tools(self, messages: List[Dict], system: str, tools: List[Dict]) -> Dict:
        """Process with tool use."""
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic()
        collected_data = {}
        sources = []
        
        current_messages = messages.copy()
        
        for iteration in range(self.MAX_TOOL_ITERATIONS):
            # Call with tools
            response = await client.messages.create(
                model=self._model_config.model_name,
                max_tokens=self._model_config.max_tokens,
                system=system,
                messages=current_messages,
                tools=tools,
            )
            
            # Check for tool use
            tool_uses = [block for block in response.content if block.type == "tool_use"]
            
            if not tool_uses:
                # No more tool calls, extract text response
                text_blocks = [block for block in response.content if block.type == "text"]
                final_response = text_blocks[0].text if text_blocks else ""
                
                return {
                    "response": final_response,
                    "data": collected_data if collected_data else None,
                    "suggested_actions": self._extract_suggested_actions(final_response),
                    "sources": sources,
                }
            
            # Execute tools
            tool_results = []
            for tool_use in tool_uses:
                tool_name = tool_use.name
                tool_input = tool_use.input
                
                # Execute tool
                result = await tool_registry.execute_tool(
                    tool_name,
                    tool_input,
                    self.customer_id,
                )
                
                # Collect data from tools
                if result.get("data"):
                    collected_data[tool_name] = result["data"]
                
                if result.get("source"):
                    sources.append(result["source"])
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result),
                })
            
            # Add assistant message and tool results
            current_messages.append({
                "role": "assistant",
                "content": response.content,
            })
            current_messages.append({
                "role": "user",
                "content": tool_results,
            })
        
        # Max iterations reached
        return {
            "response": "I've gathered the information but reached my processing limit. Here's what I found:",
            "data": collected_data,
            "suggested_actions": [],
            "sources": sources,
        }
    
    def _get_or_create_conversation(self, conversation_id: str = None, context: Dict = None) -> Conversation:
        """Get existing or create new conversation."""
        if conversation_id and conversation_id in self._conversations:
            conversation = self._conversations[conversation_id]
            if context:
                conversation.context.update(context)
            return conversation
        
        # Create new conversation
        new_id = conversation_id or f"conv_{uuid4().hex[:12]}"
        conversation = Conversation(
            id=new_id,
            customer_id=self.customer_id,
            context=context or {},
        )
        self._conversations[new_id] = conversation
        return conversation
    
    def _build_system_prompt(self, context: Dict) -> str:
        """Build system prompt with context."""
        base = self.system_prompt
        
        # Add context-specific instructions
        context_prompt = get_context_prompt(context)
        if context_prompt:
            base += f"\n\n{context_prompt}"
        
        # Add current date/time
        base += f"\n\nCurrent date and time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        
        return base
    
    def _extract_suggested_actions(self, response: str) -> List[Dict]:
        """Extract suggested actions from response."""
        actions = []
        
        # Simple extraction based on keywords
        action_patterns = [
            ("view_invoice", ["view invoice", "see invoice", "check invoice"]),
            ("view_project", ["view project", "project details", "check project"]),
            ("view_customer", ["view customer", "customer details"]),
            ("create_invoice", ["create invoice", "new invoice"]),
            ("export_report", ["export", "download report"]),
        ]
        
        response_lower = response.lower()
        for action, keywords in action_patterns:
            if any(kw in response_lower for kw in keywords):
                actions.append({"action": action})
        
        return actions[:3]  # Limit to 3 suggestions
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        return self._conversations.get(conversation_id)
    
    def clear_conversation(self, conversation_id: str):
        """Clear conversation history."""
        if conversation_id in self._conversations:
            self._conversations[conversation_id].messages = []
    
    def delete_conversation(self, conversation_id: str):
        """Delete conversation."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
```

---

## File 2: Prompts
**Path:** `backend/app/ai/assistant/prompts.py`

```python
"""
AI Assistant Prompts
System prompts and templates for the assistant
"""

from typing import Dict, Optional


SYSTEM_PROMPT = """You are an intelligent business assistant for LogiAccounting Pro, a comprehensive logistics and accounting platform. Your role is to help users understand their business data, answer questions, and provide actionable insights.

## Your Capabilities

1. **Data Analysis**: Analyze invoices, payments, projects, customers, and financial data
2. **Insights**: Provide meaningful business insights and trends
3. **Recommendations**: Suggest actions to improve business performance
4. **Comparisons**: Compare performance across time periods, projects, or customers
5. **Forecasting**: Explain cash flow predictions and trends
6. **Explanations**: Clarify financial concepts and platform features

## Response Guidelines

- Be concise and direct in your responses
- Use bullet points for lists and comparisons
- Include specific numbers and percentages when available
- Always base insights on actual data, not assumptions
- If you don't have enough data, say so clearly
- Suggest relevant actions the user can take
- Use professional but friendly language

## Data Access

You have access to tools that can query:
- Invoices and payments
- Customers and vendors
- Projects and their profitability
- Financial summaries and reports
- Cash flow forecasts
- Tickets and support requests

## Important Notes

- Never make up data or statistics
- Always clarify if information might be outdated
- Respect data privacy - don't expose sensitive details unnecessarily
- If a question is unclear, ask for clarification
- For complex analysis, break down your reasoning

## Example Interactions

User: "How profitable is Project Alpha?"
Good: "Project Alpha has a profit margin of 42% with total revenue of $107,000 and costs of $62,000. This is above your average project margin of 35%."

User: "Why are my receivables high?"
Good: "Your accounts receivable is $45,000, which is 15% higher than last month. The main contributors are:
- Invoice #1234 ($15,000) - 45 days overdue
- Invoice #1235 ($12,000) - 30 days overdue
I recommend sending reminder emails to these customers."
"""


CONTEXT_PROMPTS = {
    "dashboard": """
The user is viewing the main dashboard. They likely want quick summaries and key metrics.
Focus on providing concise, high-level insights.
""",
    
    "invoices": """
The user is in the invoices section. They may want to know about:
- Invoice statuses and aging
- Payment collection
- Revenue trends
- Specific invoice details
""",
    
    "projects": """
The user is in the projects section. They may want to know about:
- Project profitability
- Budget vs actual
- Timeline and milestones
- Resource allocation
""",
    
    "customers": """
The user is in the customers section. They may want to know about:
- Customer lifetime value
- Payment patterns
- Account health
- Communication history
""",
    
    "reports": """
The user is in the reports section. They may want to:
- Understand report data
- Compare periods
- Export data
- Get insights from reports
""",
    
    "cashflow": """
The user is viewing cash flow forecasts. They may want to:
- Understand predictions
- Know about potential issues
- See what factors affect cash flow
- Get recommendations for improvement
""",
}


def get_context_prompt(context: Dict) -> Optional[str]:
    """Get context-specific prompt additions."""
    if not context:
        return None
    
    current_page = context.get("current_page", "").lower()
    
    if current_page in CONTEXT_PROMPTS:
        return CONTEXT_PROMPTS[current_page]
    
    # Build dynamic context
    parts = []
    
    if context.get("selected_customer"):
        parts.append(f"The user is viewing customer: {context['selected_customer']}")
    
    if context.get("selected_project"):
        parts.append(f"The user is viewing project: {context['selected_project']}")
    
    if context.get("date_range"):
        parts.append(f"Date range selected: {context['date_range']}")
    
    return "\n".join(parts) if parts else None


QUERY_TEMPLATES = {
    "profitability": """
Analyze the profitability of {entity_type} "{entity_name}":
1. Total revenue and costs
2. Profit margin percentage
3. Comparison to average
4. Key contributing factors
5. Recommendations for improvement
""",
    
    "trend_analysis": """
Analyze the trend for {metric} over {period}:
1. Overall direction (increasing/decreasing/stable)
2. Rate of change
3. Key inflection points
4. Contributing factors
5. Forecast if continuing
""",
    
    "comparison": """
Compare {entity_type_a} "{entity_a}" with {entity_type_b} "{entity_b}":
1. Key metrics side by side
2. Relative performance
3. Strengths and weaknesses
4. Recommendations
""",
    
    "risk_assessment": """
Assess risks for {entity_type} "{entity_name}":
1. Identified risk factors
2. Severity levels
3. Potential impact
4. Mitigation recommendations
""",
}


def get_query_template(template_name: str, **kwargs) -> Optional[str]:
    """Get and fill a query template."""
    template = QUERY_TEMPLATES.get(template_name)
    if template:
        return template.format(**kwargs)
    return None


RESPONSE_TEMPLATES = {
    "no_data": """
I don't have enough data to answer that question accurately. 
{reason}
Would you like me to help with something else?
""",
    
    "clarification_needed": """
I want to make sure I understand your question correctly. 
Could you clarify:
{questions}
""",
    
    "error": """
I apologize, but I encountered an issue while processing your request.
{error_type}
Please try again or rephrase your question.
""",
}


def get_response_template(template_name: str, **kwargs) -> str:
    """Get and fill a response template."""
    template = RESPONSE_TEMPLATES.get(template_name, "")
    return template.format(**kwargs)
```

---

## File 3: Assistant Tools
**Path:** `backend/app/ai/assistant/tools.py`

```python
"""
AI Assistant Tools
Function calling tools for the assistant
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class AssistantTool:
    """Definition of an assistant tool."""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict,
        handler: Callable,
        contexts: List[str] = None,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.contexts = contexts or ["all"]
    
    def to_dict(self) -> Dict:
        """Convert to API tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters.get("properties", {}),
                "required": self.parameters.get("required", []),
            },
        }
    
    async def execute(self, input_data: Dict, customer_id: str) -> Dict:
        """Execute the tool."""
        try:
            return await self.handler(input_data, customer_id)
        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {e}")
            return {"error": str(e)}


class AssistantToolRegistry:
    """Registry of available assistant tools."""
    
    def __init__(self):
        self._tools: Dict[str, AssistantTool] = {}
        self._register_default_tools()
    
    def register(self, tool: AssistantTool):
        """Register a tool."""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[AssistantTool]:
        """Get tool by name."""
        return self._tools.get(name)
    
    def get_tools_for_context(self, context: Dict) -> List[Dict]:
        """Get tools available for current context."""
        current_page = context.get("current_page", "").lower()
        
        tools = []
        for tool in self._tools.values():
            if "all" in tool.contexts or current_page in tool.contexts:
                tools.append(tool.to_dict())
        
        return tools
    
    async def execute_tool(self, name: str, input_data: Dict, customer_id: str) -> Dict:
        """Execute a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        
        return await tool.execute(input_data, customer_id)
    
    def _register_default_tools(self):
        """Register default tools."""
        
        # Query invoices
        self.register(AssistantTool(
            name="query_invoices",
            description="Query invoices with filters. Use this to get invoice data, totals, aging, etc.",
            parameters={
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["all", "draft", "pending", "paid", "overdue", "cancelled"],
                        "description": "Filter by status",
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Filter by customer ID",
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return",
                        "default": 10,
                    },
                },
                "required": [],
            },
            handler=self._query_invoices,
            contexts=["all", "invoices", "dashboard"],
        ))
        
        # Query projects
        self.register(AssistantTool(
            name="query_projects",
            description="Query projects with profitability data. Use this to analyze project performance.",
            parameters={
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["all", "active", "completed", "on_hold", "cancelled"],
                        "description": "Filter by status",
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Filter by customer ID",
                    },
                    "include_financials": {
                        "type": "boolean",
                        "description": "Include financial details",
                        "default": True,
                    },
                },
                "required": [],
            },
            handler=self._query_projects,
            contexts=["all", "projects", "dashboard"],
        ))
        
        # Get customer details
        self.register(AssistantTool(
            name="get_customer_details",
            description="Get detailed information about a specific customer including their invoices, payments, and projects.",
            parameters={
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID to look up",
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name to search for",
                    },
                },
                "required": [],
            },
            handler=self._get_customer_details,
            contexts=["all", "customers"],
        ))
        
        # Financial summary
        self.register(AssistantTool(
            name="get_financial_summary",
            description="Get financial summary including revenue, expenses, profit, and key metrics for a time period.",
            parameters={
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "this_week", "this_month", "this_quarter", "this_year", "last_month", "last_quarter", "last_year"],
                        "description": "Time period for summary",
                    },
                    "compare_to_previous": {
                        "type": "boolean",
                        "description": "Include comparison to previous period",
                        "default": True,
                    },
                },
                "required": ["period"],
            },
            handler=self._get_financial_summary,
            contexts=["all", "dashboard", "reports"],
        ))
        
        # Cash flow forecast
        self.register(AssistantTool(
            name="get_cashflow_forecast",
            description="Get cash flow forecast and predictions. Use this to understand future cash position.",
            parameters={
                "properties": {
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days to forecast",
                        "default": 30,
                    },
                    "include_alerts": {
                        "type": "boolean",
                        "description": "Include cash flow alerts",
                        "default": True,
                    },
                },
                "required": [],
            },
            handler=self._get_cashflow_forecast,
            contexts=["all", "cashflow", "dashboard"],
        ))
        
        # Aging report
        self.register(AssistantTool(
            name="get_aging_report",
            description="Get accounts receivable aging report showing overdue invoices.",
            parameters={
                "properties": {
                    "buckets": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Age buckets in days",
                        "default": [0, 30, 60, 90],
                    },
                },
                "required": [],
            },
            handler=self._get_aging_report,
            contexts=["all", "invoices", "reports"],
        ))
    
    # ==================== Tool Handlers ====================
    
    async def _query_invoices(self, params: Dict, customer_id: str) -> Dict:
        """Query invoices."""
        # In production: query actual database
        # Demo data
        return {
            "data": {
                "invoices": [
                    {"id": "inv_001", "number": "INV-2024-001", "customer": "Acme Corp", "amount": 5000, "status": "paid"},
                    {"id": "inv_002", "number": "INV-2024-002", "customer": "Tech Inc", "amount": 7500, "status": "pending"},
                    {"id": "inv_003", "number": "INV-2024-003", "customer": "Global Ltd", "amount": 3200, "status": "overdue"},
                ],
                "summary": {
                    "total_count": 3,
                    "total_amount": 15700,
                    "paid_amount": 5000,
                    "pending_amount": 10700,
                },
            },
            "source": {"type": "invoices", "query": params},
        }
    
    async def _query_projects(self, params: Dict, customer_id: str) -> Dict:
        """Query projects."""
        return {
            "data": {
                "projects": [
                    {
                        "id": "proj_001",
                        "name": "Project Alpha",
                        "customer": "Acme Corp",
                        "status": "active",
                        "revenue": 107000,
                        "costs": 62000,
                        "profit": 45000,
                        "margin": 0.42,
                    },
                    {
                        "id": "proj_002",
                        "name": "Project Beta",
                        "customer": "Tech Inc",
                        "status": "active",
                        "revenue": 85000,
                        "costs": 53000,
                        "profit": 32000,
                        "margin": 0.38,
                    },
                ],
                "summary": {
                    "total_projects": 2,
                    "total_revenue": 192000,
                    "total_profit": 77000,
                    "average_margin": 0.40,
                },
            },
        }
    
    async def _get_customer_details(self, params: Dict, customer_id: str) -> Dict:
        """Get customer details."""
        return {
            "data": {
                "customer": {
                    "id": "cust_001",
                    "name": params.get("customer_name", "Acme Corp"),
                    "email": "contact@acme.com",
                    "total_revenue": 125000,
                    "outstanding_balance": 15000,
                    "invoice_count": 12,
                    "payment_terms": "Net 30",
                    "average_payment_days": 28,
                },
            },
        }
    
    async def _get_financial_summary(self, params: Dict, customer_id: str) -> Dict:
        """Get financial summary."""
        return {
            "data": {
                "period": params.get("period", "this_month"),
                "revenue": 85000,
                "expenses": 52000,
                "profit": 33000,
                "profit_margin": 0.39,
                "invoices_sent": 15,
                "payments_received": 12,
                "comparison": {
                    "revenue_change": 0.12,
                    "profit_change": 0.08,
                    "direction": "up",
                },
            },
        }
    
    async def _get_cashflow_forecast(self, params: Dict, customer_id: str) -> Dict:
        """Get cash flow forecast."""
        return {
            "data": {
                "current_balance": 45000,
                "forecast_30_days": 52000,
                "lowest_point": {
                    "date": "2024-01-22",
                    "balance": 28000,
                },
                "alerts": [
                    {
                        "type": "low_balance",
                        "date": "2024-01-22",
                        "message": "Cash may drop below $30,000",
                    },
                ],
                "trend": "increasing",
            },
        }
    
    async def _get_aging_report(self, params: Dict, customer_id: str) -> Dict:
        """Get aging report."""
        return {
            "data": {
                "total_receivables": 45000,
                "aging": {
                    "current": 15000,
                    "1_30_days": 12000,
                    "31_60_days": 8000,
                    "61_90_days": 5000,
                    "over_90_days": 5000,
                },
                "top_overdue": [
                    {"customer": "Global Ltd", "amount": 5000, "days_overdue": 45},
                    {"customer": "StartupXYZ", "amount": 3000, "days_overdue": 35},
                ],
            },
        }


# Global tool registry
tool_registry = AssistantToolRegistry()
```

---

## File 4: Assistant Service
**Path:** `backend/app/ai/assistant/service.py`

```python
"""
AI Assistant Service
High-level service for the AI assistant
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.ai.assistant.chatbot import AIAssistant, AssistantResponse, Conversation
from app.ai.base import AIResult

logger = logging.getLogger(__name__)


class AssistantService:
    """Service for AI assistant interactions."""
    
    def __init__(self):
        self._assistants: Dict[str, AIAssistant] = {}
    
    def get_assistant(self, customer_id: str) -> AIAssistant:
        """Get or create assistant for customer."""
        if customer_id not in self._assistants:
            self._assistants[customer_id] = AIAssistant(customer_id)
        return self._assistants[customer_id]
    
    async def chat(
        self,
        customer_id: str,
        message: str,
        conversation_id: str = None,
        context: Dict = None,
    ) -> AIResult:
        """Send message to assistant and get response."""
        try:
            assistant = self.get_assistant(customer_id)
            
            response = await assistant.process_message(
                message=message,
                conversation_id=conversation_id,
                context=context,
            )
            
            return AIResult(
                success=True,
                data=response.to_dict(),
                processing_time_ms=response.processing_time_ms,
            )
            
        except Exception as e:
            logger.error(f"Assistant chat failed: {e}")
            return AIResult(success=False, error=str(e))
    
    async def get_quick_insights(self, customer_id: str, context: Dict = None) -> AIResult:
        """Get quick insights for dashboard."""
        try:
            assistant = self.get_assistant(customer_id)
            
            # Use a system-generated query
            response = await assistant.process_message(
                message="Give me a brief summary of key business metrics and any important alerts or actions needed.",
                context=context or {"current_page": "dashboard"},
            )
            
            return AIResult(
                success=True,
                data={
                    "insights": response.response,
                    "suggested_actions": response.suggested_actions,
                },
            )
            
        except Exception as e:
            logger.error(f"Quick insights failed: {e}")
            return AIResult(success=False, error=str(e))
    
    async def analyze_entity(
        self,
        customer_id: str,
        entity_type: str,
        entity_id: str,
        analysis_type: str = "profitability",
    ) -> AIResult:
        """Analyze a specific entity."""
        try:
            assistant = self.get_assistant(customer_id)
            
            prompts = {
                "profitability": f"Analyze the profitability of {entity_type} {entity_id}. Include revenue, costs, margin, and comparison to similar {entity_type}s.",
                "trends": f"Analyze trends for {entity_type} {entity_id} over the past 6 months.",
                "risks": f"Assess risks for {entity_type} {entity_id} and provide recommendations.",
                "forecast": f"Provide a forecast for {entity_type} {entity_id} for the next 3 months.",
            }
            
            message = prompts.get(analysis_type, prompts["profitability"])
            
            response = await assistant.process_message(
                message=message,
                context={"entity_type": entity_type, "entity_id": entity_id},
            )
            
            return AIResult(
                success=True,
                data={
                    "analysis": response.response,
                    "data": response.data,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "analysis_type": analysis_type,
                },
            )
            
        except Exception as e:
            logger.error(f"Entity analysis failed: {e}")
            return AIResult(success=False, error=str(e))
    
    def get_conversation(self, customer_id: str, conversation_id: str) -> Optional[Dict]:
        """Get conversation history."""
        assistant = self._assistants.get(customer_id)
        if not assistant:
            return None
        
        conversation = assistant.get_conversation(conversation_id)
        if conversation:
            return conversation.to_dict()
        return None
    
    def get_conversations(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations for customer."""
        assistant = self._assistants.get(customer_id)
        if not assistant:
            return []
        
        conversations = list(assistant._conversations.values())
        conversations.sort(key=lambda c: c.updated_at, reverse=True)
        
        return [
            {
                "id": c.id,
                "message_count": len(c.messages),
                "last_message": c.messages[-1].content[:100] if c.messages else "",
                "updated_at": c.updated_at.isoformat(),
            }
            for c in conversations[:limit]
        ]
    
    def clear_conversation(self, customer_id: str, conversation_id: str):
        """Clear conversation history."""
        assistant = self._assistants.get(customer_id)
        if assistant:
            assistant.clear_conversation(conversation_id)
    
    def delete_conversation(self, customer_id: str, conversation_id: str):
        """Delete conversation."""
        assistant = self._assistants.get(customer_id)
        if assistant:
            assistant.delete_conversation(conversation_id)
    
    async def get_suggestions(self, customer_id: str, partial_query: str) -> List[str]:
        """Get query suggestions based on partial input."""
        # Common query templates
        suggestions = [
            "What is my current cash balance?",
            "Which invoices are overdue?",
            "How profitable is Project {}?",
            "Compare this month to last month",
            "What are my top customers by revenue?",
            "Show me upcoming payments",
            "What's my accounts receivable aging?",
            "Which projects are at risk?",
        ]
        
        if not partial_query:
            return suggestions[:5]
        
        # Filter by partial match
        query_lower = partial_query.lower()
        matching = [s for s in suggestions if query_lower in s.lower()]
        
        return matching[:5]


# Global service instance
assistant_service = AssistantService()
```

---

## File 5: Assistant Module Init
**Path:** `backend/app/ai/assistant/__init__.py`

```python
"""
AI Assistant Module
Conversational AI for business insights
"""

from app.ai.assistant.chatbot import (
    AIAssistant,
    Message,
    Conversation,
    AssistantResponse,
)
from app.ai.assistant.prompts import (
    SYSTEM_PROMPT,
    get_context_prompt,
    get_query_template,
    get_response_template,
)
from app.ai.assistant.tools import (
    AssistantTool,
    AssistantToolRegistry,
    tool_registry,
)
from app.ai.assistant.service import AssistantService, assistant_service


__all__ = [
    'AIAssistant',
    'Message',
    'Conversation',
    'AssistantResponse',
    'SYSTEM_PROMPT',
    'get_context_prompt',
    'get_query_template',
    'get_response_template',
    'AssistantTool',
    'AssistantToolRegistry',
    'tool_registry',
    'AssistantService',
    'assistant_service',
]
```

---

## Summary Part 4

| File | Description | Lines |
|------|-------------|-------|
| `assistant/chatbot.py` | AI chatbot with tool use | ~380 |
| `assistant/prompts.py` | System prompts & templates | ~220 |
| `assistant/tools.py` | Function calling tools | ~350 |
| `assistant/service.py` | Assistant service layer | ~200 |
| `assistant/__init__.py` | Module initialization | ~35 |
| **Total** | | **~1,185 lines** |
