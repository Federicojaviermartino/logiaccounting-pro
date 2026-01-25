"""
AI Assistant Prompts
System prompts and templates for the AI assistant
"""

from typing import Dict, Any, Optional


SYSTEM_PROMPT = """You are an intelligent business assistant for LogiAccounting Pro, an accounting and financial management platform. You help users understand their financial data, answer questions about their business, and provide actionable insights.

## Your Capabilities:
1. **Financial Analysis**: Analyze cash flow, expenses, revenue, and profitability
2. **Invoice Management**: Help with invoice queries, overdue payments, and customer billing
3. **Expense Tracking**: Categorize expenses, identify trends, and find savings opportunities
4. **Business Insights**: Provide data-driven recommendations to improve business performance
5. **Report Interpretation**: Explain financial reports and metrics in simple terms

## Guidelines:
- Be concise and professional, but friendly
- When discussing numbers, format them properly (e.g., $1,234.56)
- If you don't have specific data, explain what information would be needed
- Suggest relevant actions the user can take
- For complex analyses, break down the explanation into clear steps
- If asked about something outside your scope, politely explain your limitations

## Response Format:
- Use clear paragraphs for explanations
- Use bullet points for lists of items or recommendations
- Include specific numbers and percentages when relevant
- End with a suggested next action when appropriate"""


def get_context_prompt(context: Dict) -> str:
    """Generate context-aware prompt addition."""
    parts = []

    if context.get("current_page"):
        parts.append(f"The user is currently viewing the {context['current_page']} page.")

    if context.get("selected_entity"):
        entity = context["selected_entity"]
        parts.append(f"The user has selected {entity.get('type', 'item')}: {entity.get('name', entity.get('id', 'unknown'))}")

    if context.get("date_range"):
        dr = context["date_range"]
        parts.append(f"Current date range filter: {dr.get('start')} to {dr.get('end')}")

    if context.get("quick_stats"):
        stats = context["quick_stats"]
        parts.append("Quick stats available:")
        for key, value in stats.items():
            parts.append(f"  - {key}: {value}")

    if not parts:
        return ""

    return "## Current Context:\n" + "\n".join(parts)


# Query templates for common questions
QUERY_TEMPLATES = {
    "cash_position": """Analyze the current cash position:
- Current balance: {current_balance}
- Pending receivables: {pending_receivables}
- Pending payables: {pending_payables}
- Net position: {net_position}

Provide a brief assessment and any concerns.""",

    "customer_analysis": """Analyze customer {customer_name}:
- Total revenue: {total_revenue}
- Outstanding balance: {outstanding}
- Average payment days: {avg_payment_days}
- Last transaction: {last_transaction}

Assess the customer relationship and any recommended actions.""",

    "expense_summary": """Summarize expenses for the period:
{expense_breakdown}

Total: {total_expenses}

Identify the largest categories and any unusual spending patterns.""",

    "invoice_aging": """Analyze invoice aging:
- Current (0-30 days): {current}
- 31-60 days: {days_31_60}
- 61-90 days: {days_61_90}
- Over 90 days: {over_90}

Total outstanding: {total_outstanding}

Recommend collection priorities.""",

    "profitability": """Analyze profitability:
- Revenue: {revenue}
- Cost of Goods Sold: {cogs}
- Gross Profit: {gross_profit}
- Operating Expenses: {operating_expenses}
- Net Profit: {net_profit}
- Profit Margin: {profit_margin}%

Provide insights on profitability trends and improvement opportunities.""",
}


def get_query_template(template_name: str, **kwargs) -> str:
    """Get a filled query template."""
    template = QUERY_TEMPLATES.get(template_name, "")
    if template and kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
    return template


# Suggested questions for users
SUGGESTED_QUESTIONS = [
    "What's my current cash position?",
    "Which invoices are overdue?",
    "What are my largest expense categories this month?",
    "How is my revenue trending compared to last month?",
    "Which customers have the highest outstanding balances?",
    "What's my projected cash flow for the next 30 days?",
    "Are there any unusual transactions I should review?",
    "How can I improve my profit margins?",
]


def get_suggestions(query_prefix: str = "") -> list:
    """Get suggested questions, optionally filtered."""
    if not query_prefix:
        return SUGGESTED_QUESTIONS[:5]

    prefix_lower = query_prefix.lower()
    filtered = [q for q in SUGGESTED_QUESTIONS if prefix_lower in q.lower()]
    return filtered[:5] if filtered else SUGGESTED_QUESTIONS[:5]
