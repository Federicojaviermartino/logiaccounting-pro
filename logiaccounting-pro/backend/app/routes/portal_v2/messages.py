"""
Portal v2 Message Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from app.services.portal.message_service import message_service
from app.utils.auth import get_current_user

router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("")
async def list_conversations(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    current_user: dict = Depends(get_portal_user)
):
    """List customer conversations."""
    return message_service.list_conversations(current_user.get("customer_id"), status, page)


@router.get("/unread")
async def get_unread_count(current_user: dict = Depends(get_portal_user)):
    """Get unread message count."""
    return {"unread": message_service.get_unread_count(current_user.get("customer_id"))}


@router.get("/search")
async def search_messages(
    q: str,
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_portal_user)
):
    """Search messages."""
    return message_service.search_messages(current_user.get("customer_id"), q, limit)


class StartConversationRequest(BaseModel):
    subject: str
    message: str
    attachments: Optional[List[str]] = None


@router.post("")
async def start_conversation(
    data: StartConversationRequest,
    current_user: dict = Depends(get_portal_user)
):
    """Start a new conversation."""
    conv = message_service.start_conversation(
        tenant_id=current_user.get("tenant_id"),
        customer_id=current_user.get("customer_id"),
        contact_id=current_user.get("contact_id"),
        subject=data.subject,
        initial_message=data.message,
        attachments=data.attachments,
    )
    return message_service._conversation_to_dict(conv, include_messages=True)


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_portal_user)
):
    """Get conversation with messages."""
    conv = message_service.get_conversation(conversation_id, current_user.get("customer_id"))
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


class SendMessageRequest(BaseModel):
    content: str
    attachments: Optional[List[str]] = None


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    data: SendMessageRequest,
    current_user: dict = Depends(get_portal_user)
):
    """Send a message in conversation."""
    try:
        msg = message_service.send_message(
            conversation_id=conversation_id,
            customer_id=current_user.get("customer_id"),
            contact_id=current_user.get("contact_id"),
            content=data.content,
            attachments=data.attachments,
        )
        return {"id": msg.id, "content": msg.content, "created_at": msg.created_at.isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{conversation_id}/read")
async def mark_as_read(
    conversation_id: str,
    current_user: dict = Depends(get_portal_user)
):
    """Mark conversation as read."""
    try:
        message_service.mark_as_read(conversation_id, current_user.get("customer_id"))
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_portal_user)
):
    """Archive a conversation."""
    try:
        message_service.archive_conversation(conversation_id, current_user.get("customer_id"))
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
