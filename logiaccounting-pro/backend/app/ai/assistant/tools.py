"""
AI Assistant Tools
Function calling tools for the AI assistant
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class AssistantTool:
    """Definition of a tool the assistant can use."""
    name: str
    description: str
    parameters: Dict
    handler: Callable
    requires_confirmation: bool = False

    def to_dict(self) -> Dict:
        """Convert to API-compatible format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": [k for k, v in self.parameters.items() if v.get("required", False)],
            },
        }


class AssistantToolRegistry:
    """Registry for assistant tools."""

    def __init__(self):
        self._tools: Dict[str, AssistantTool] = {}
        self._register_default_tools()

    def register(self, tool: AssistantTool):
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[AssistantTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict]:
        """List all tools in API format."""
        return [tool.to_dict() for tool in self._tools.values()]

    async def execute(self, name: str, params: Dict) -> Dict:
        """Execute a tool."""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}

        try:
            result = await tool.handler(**params)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"success": False, "error": str(e)}

    def _register_default_tools(self):
        """Register default tools."""
        # Get invoice summary tool
        self.register(AssistantTool(
            name="get_invoice_summary",
            description="Get a summary of invoices for a date range",
            parameters={
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
                "status": {
                    "type": "string",
                    "enum": ["all", "paid", "unpaid", "overdue"],
                    "description": "Filter by invoice status",
                },
            },
            handler=self._get_invoice_summary,
        ))

        # Get expense breakdown tool
        self.register(AssistantTool(
            name="get_expense_breakdown",
            description="Get expense breakdown by category",
            parameters={
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format",
                },
            },
            handler=self._get_expense_breakdown,
        ))

        # Get cash flow summary tool
        self.register(AssistantTool(
            name="get_cash_flow_summary",
            description="Get cash flow summary",
            parameters={
                "period": {
                    "type": "string",
                    "enum": ["week", "month", "quarter", "year"],
                    "description": "Period for the summary",
                },
            },
            handler=self._get_cash_flow_summary,
        ))

        # Get customer info tool
        self.register(AssistantTool(
            name="get_customer_info",
            description="Get information about a specific customer",
            parameters={
                "customer_id": {
                    "type": "string",
                    "description": "Customer ID",
                    "required": True,
                },
            },
            handler=self._get_customer_info,
        ))

        # Get overdue invoices tool
        self.register(AssistantTool(
            name="get_overdue_invoices",
            description="Get list of overdue invoices",
            parameters={
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of invoices to return",
                    "default": 10,
                },
            },
            handler=self._get_overdue_invoices,
        ))

    # Tool handlers (placeholder implementations)
    async def _get_invoice_summary(
        self,
        start_date: str = None,
        end_date: str = None,
        status: str = "all",
    ) -> Dict:
        """Get invoice summary."""
        # Placeholder - would integrate with actual data layer
        return {
            "total_invoices": 42,
            "total_amount": 125000.00,
            "paid_amount": 95000.00,
            "pending_amount": 30000.00,
            "overdue_count": 5,
            "overdue_amount": 8500.00,
        }

    async def _get_expense_breakdown(
        self,
        start_date: str = None,
        end_date: str = None,
    ) -> Dict:
        """Get expense breakdown."""
        return {
            "total": 45000.00,
            "by_category": {
                "software": 12000.00,
                "office_supplies": 3500.00,
                "professional_services": 15000.00,
                "utilities": 2500.00,
                "travel": 8000.00,
                "other": 4000.00,
            },
        }

    async def _get_cash_flow_summary(self, period: str = "month") -> Dict:
        """Get cash flow summary."""
        return {
            "starting_balance": 50000.00,
            "ending_balance": 62000.00,
            "total_inflows": 85000.00,
            "total_outflows": 73000.00,
            "net_change": 12000.00,
            "trend": "positive",
        }

    async def _get_customer_info(self, customer_id: str) -> Dict:
        """Get customer information."""
        return {
            "id": customer_id,
            "name": "Sample Customer",
            "total_revenue": 45000.00,
            "outstanding_balance": 5000.00,
            "avg_payment_days": 28,
            "status": "active",
        }

    async def _get_overdue_invoices(self, limit: int = 10) -> Dict:
        """Get overdue invoices."""
        return {
            "count": 5,
            "total_amount": 8500.00,
            "invoices": [
                {"invoice_number": "INV-001", "customer": "Customer A", "amount": 2500.00, "days_overdue": 15},
                {"invoice_number": "INV-002", "customer": "Customer B", "amount": 3000.00, "days_overdue": 8},
            ],
        }


# Global registry instance
tool_registry = AssistantToolRegistry()
