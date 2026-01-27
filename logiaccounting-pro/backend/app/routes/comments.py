"""
Comments and Collaboration routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.collaboration_service import collaboration_service
from app.utils.auth import get_current_user

router = APIRouter()


class CreateCommentRequest(BaseModel):
    entity_type: str
    entity_id: str
    content: str
    attachments: List[str] = []
    thread_id: Optional[str] = None


class UpdateCommentRequest(BaseModel):
    content: str


class ReactionRequest(BaseModel):
    reaction: str


@router.get("/reactions")
async def get_available_reactions():
    """Get available reactions"""
    return {"reactions": collaboration_service.REACTIONS}


@router.post("")
async def create_comment(
    request: CreateCommentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a comment"""
    return collaboration_service.create_comment(
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        content=request.content,
        author_id=current_user["id"],
        author_name=current_user.get("name", current_user["email"]),
        author_email=current_user["email"],
        attachments=request.attachments,
        thread_id=request.thread_id
    )


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_comments(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get comments for an entity"""
    return {"comments": collaboration_service.get_entity_comments(entity_type, entity_id)}


@router.get("/mentions")
async def get_my_mentions(current_user: dict = Depends(get_current_user)):
    """Get comments mentioning current user"""
    return {"mentions": collaboration_service.get_user_mentions(
        current_user["id"],
        current_user["email"]
    )}


@router.get("/{comment_id}")
async def get_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a comment"""
    comment = collaboration_service.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.put("/{comment_id}")
async def update_comment(
    comment_id: str,
    request: UpdateCommentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a comment"""
    comment = collaboration_service.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment["author_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Cannot edit others' comments")

    updated = collaboration_service.update_comment(comment_id, request.content)
    return updated


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a comment"""
    comment = collaboration_service.get_comment(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment["author_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Cannot delete others' comments")

    collaboration_service.delete_comment(comment_id)
    return {"message": "Comment deleted"}


@router.post("/{comment_id}/reactions")
async def add_reaction(
    comment_id: str,
    request: ReactionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add reaction to comment"""
    comment = collaboration_service.add_reaction(comment_id, request.reaction, current_user["id"])
    if not comment:
        raise HTTPException(status_code=400, detail="Invalid comment or reaction")
    return comment


@router.delete("/{comment_id}/reactions/{reaction}")
async def remove_reaction(
    comment_id: str,
    reaction: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove reaction from comment"""
    comment = collaboration_service.remove_reaction(comment_id, reaction, current_user["id"])
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment
