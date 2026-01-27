"""
AI Assistant Routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from app.utils.auth import get_current_user, require_roles
from ..services.assistant import ChatAssistant

router = APIRouter()
chat_assistant = ChatAssistant()


class ChatRequest(BaseModel):
    """Chat request"""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response"""
    conversation_id: str
    message_id: str
    content: str
    tool_calls: Optional[list] = None
    tokens_used: int


class FeedbackRequest(BaseModel):
    """Feedback request"""
    feedback: str  # 'positive', 'negative', 'neutral'


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """
    Chat with the AI assistant

    The assistant can answer questions about:
    - Revenue and sales
    - Expenses and spending
    - Profitability metrics
    - Cash position
    - Accounts receivable/payable
    - Budget vs actual
    """
    try:
        tenant_id = current_user.get("tenant_id", "default")
        user_id = current_user.get("id", "unknown")

        result = await chat_assistant.chat(
            conversation_id=request.conversation_id or "",
            tenant_id=tenant_id,
            user_id=user_id,
            message=request.message,
        )

        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/conversations")
async def get_conversations(
    limit: int = 20,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get user's conversations"""
    tenant_id = current_user.get("tenant_id", "default")
    user_id = current_user.get("id", "unknown")

    conversations = await chat_assistant.get_user_conversations(
        tenant_id=tenant_id,
        user_id=user_id,
        limit=limit,
    )

    return [conv.to_dict() for conv in conversations]


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Get conversation with messages"""
    tenant_id = current_user.get("tenant_id", "default")

    conversation = await chat_assistant.get_conversation(
        conversation_id=conversation_id,
        tenant_id=tenant_id,
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = conversation.get_messages()

    return {
        **conversation.to_dict(),
        "messages": [m.to_dict() for m in messages],
    }


@router.post("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Archive a conversation"""
    tenant_id = current_user.get("tenant_id", "default")

    conversation = await chat_assistant.get_conversation(
        conversation_id=conversation_id,
        tenant_id=tenant_id,
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    conversation.is_active = False
    conversation.save()

    return {"status": "archived"}


@router.post("/messages/{message_id}/feedback")
async def provide_feedback(
    message_id: str,
    request: FeedbackRequest,
    current_user: dict = Depends(require_roles("admin", "client"))
):
    """Provide feedback on an assistant message"""
    success = await chat_assistant.provide_feedback(
        message_id=message_id,
        feedback=request.feedback,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )

    return {"status": "feedback recorded"}


@router.get("/capabilities")
async def get_capabilities():
    """Get assistant capabilities"""
    from ..services.assistant.tools import AssistantTools
    tools = AssistantTools("demo")

    return {
        "description": "AI-powered accounting assistant for business queries",
        "capabilities": [
            "Answer questions about revenue and sales",
            "Analyze expenses by category",
            "Calculate profitability metrics",
            "Report on cash position",
            "Track accounts receivable aging",
            "Monitor accounts payable",
            "Compare budget vs actual spending",
            "Search transactions",
        ],
        "available_tools": tools.get_available_tools(),
    }
