"""
Profitability Assistant Routes
Natural Language Processing chatbot for financial queries
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from app.utils.auth import get_current_user
from app.models.store import db
from app.services.profitability_assistant import create_profitability_assistant, ANTHROPIC_AVAILABLE
from app.services.ai_assistant import ai_assistant

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # "user" or "assistant"
    content: str


class QueryRequest(BaseModel):
    """Request for natural language query"""
    query: str
    conversation_history: Optional[List[ChatMessage]] = None


class QueryResponse(BaseModel):
    """Response from assistant"""
    answer: str
    data: Optional[dict] = None
    suggestions: Optional[List[str]] = None
    query_type: str = "general"
    confidence: float = 1.0


@router.post("/query", response_model=QueryResponse)
async def query_assistant(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ask a natural language question about projects and profitability

    Example queries:
    - "What projects are over budget?"
    - "Show me the most profitable projects"
    - "Which suppliers have the highest expenses?"
    - "What's our monthly revenue trend?"
    - "Which projects are at risk?"
    - "Compare expenses by category"
    - "What payments are due this week?"
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )

    try:
        assistant = create_profitability_assistant(db)

        # Provide user context for role-based filtering
        user_context = {
            "user_id": current_user["id"],
            "role": current_user["role"],
            "company": current_user.get("company_name")
        }

        result = assistant.query(request.query, user_context)

        return QueryResponse(
            answer=result.answer,
            data=result.data,
            suggestions=result.suggestions,
            query_type=result.query_type,
            confidence=result.confidence
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )


@router.get("/suggestions")
async def get_query_suggestions(
    context: Optional[str] = Query(None, description="Context for suggestions (e.g., 'projects', 'expenses')"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get suggested queries based on context

    Returns a list of example queries the user can ask.
    """
    assistant = create_profitability_assistant(db)

    # Context-specific suggestions
    suggestions_map = {
        "projects": [
            "What projects are over budget?",
            "Show me the most profitable projects",
            "Which projects are at risk?",
            "Compare project profitability",
            "What's the budget utilization for active projects?"
        ],
        "expenses": [
            "Show expenses by category",
            "Which suppliers have the highest expenses?",
            "What are the largest expenses this month?",
            "Compare monthly expense trends",
            "Find unusual expense patterns"
        ],
        "revenue": [
            "What's our monthly revenue trend?",
            "Show income by project",
            "What's our profit margin?",
            "Compare revenue by client",
            "Which projects generate the most income?"
        ],
        "payments": [
            "What payments are due this week?",
            "Show overdue payments",
            "What's the total pending payable?",
            "List upcoming receivables",
            "Payment schedule for next 30 days"
        ],
        "inventory": [
            "Show low stock materials",
            "What items need reordering?",
            "Inventory value by category",
            "Most used materials",
            "Stock movement trends"
        ]
    }

    if context and context.lower() in suggestions_map:
        suggestions = suggestions_map[context.lower()]
    else:
        # Mix of all categories
        suggestions = assistant.EXAMPLE_QUERIES

    return {"suggestions": suggestions, "context": context}


@router.get("/quick-insights")
async def get_quick_insights(
    current_user: dict = Depends(get_current_user)
):
    """
    Get quick financial insights without a specific query

    Returns key metrics and alerts automatically.
    """
    assistant = create_profitability_assistant(db)

    insights = []

    # Check for over-budget projects
    result = assistant._query_over_budget_projects()
    if result.data and result.data.get("over_budget_projects"):
        count = len(result.data["over_budget_projects"])
        insights.append({
            "type": "warning",
            "category": "projects",
            "title": "Over Budget Projects",
            "message": f"{count} project(s) are over budget",
            "action": "Review budget allocation"
        })

    # Check for at-risk projects
    result = assistant._query_at_risk_projects()
    if result.data and result.data.get("at_risk_projects"):
        count = len(result.data["at_risk_projects"])
        insights.append({
            "type": "alert",
            "category": "projects",
            "title": "Projects at Risk",
            "message": f"{count} project(s) need attention",
            "action": "Review project status"
        })

    # Check for upcoming payments
    result = assistant._query_upcoming_payments()
    if result.data and result.data.get("upcoming_payments"):
        payments = result.data["upcoming_payments"]
        overdue = [p for p in payments if p.get("status") == "overdue"]
        if overdue:
            total = sum(p.get("amount", 0) for p in overdue)
            insights.append({
                "type": "critical",
                "category": "payments",
                "title": "Overdue Payments",
                "message": f"{len(overdue)} payment(s) overdue totaling ${total:,.2f}",
                "action": "Process payments immediately"
            })
        elif payments:
            total = sum(p.get("amount", 0) for p in payments)
            insights.append({
                "type": "info",
                "category": "payments",
                "title": "Upcoming Payments",
                "message": f"{len(payments)} payment(s) due this week totaling ${total:,.2f}",
                "action": "Schedule payments"
            })

    # Check for low stock
    result = assistant._query_low_stock()
    if result.data and result.data.get("low_stock_items"):
        count = len(result.data["low_stock_items"])
        insights.append({
            "type": "warning",
            "category": "inventory",
            "title": "Low Stock Alert",
            "message": f"{count} item(s) below minimum stock level",
            "action": "Create purchase orders"
        })

    # Get overall summary
    summary = assistant._get_data_summary()

    return {
        "insights": insights,
        "summary": {
            "total_income": summary["totals"]["income"],
            "total_expenses": summary["totals"]["expenses"],
            "net_profit": summary["totals"]["net_profit"],
            "profit_margin": summary["totals"]["profit_margin"],
            "active_projects": len([p for p in summary["projects"] if p["status"] == "active"]),
            "pending_payable": summary["payments"]["pending_payable"],
            "pending_receivable": summary["payments"]["pending_receivable"]
        }
    }


@router.get("/status")
async def get_assistant_status():
    """
    Check assistant status and capabilities
    """
    return {
        "nlp_enabled": ANTHROPIC_AVAILABLE,
        "nlp_provider": "Claude API" if ANTHROPIC_AVAILABLE else "Keyword matching (fallback)",
        "capabilities": [
            "Project profitability analysis",
            "Budget tracking and alerts",
            "Expense categorization",
            "Revenue trend analysis",
            "Payment scheduling",
            "Inventory monitoring",
            "Risk assessment",
            "Natural language queries" if ANTHROPIC_AVAILABLE else "Keyword-based queries"
        ],
        "example_queries": [
            "What projects are over budget?",
            "Show me the most profitable projects",
            "Which suppliers have the highest expenses?",
            "What's our monthly revenue trend?"
        ]
    }


class ChatRequest(BaseModel):
    message: str
    language: str = "en"


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send a message to the AI assistant"""
    return ai_assistant.process_query(
        user_id=current_user["id"],
        message=request.message,
        language=request.language
    )


@router.get("/history")
async def get_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation history"""
    return {"messages": ai_assistant.get_conversation_history(current_user["id"], limit)}


@router.delete("/history")
async def clear_history(current_user: dict = Depends(get_current_user)):
    """Clear conversation history"""
    ai_assistant.clear_conversation(current_user["id"])
    return {"message": "Conversation cleared"}
