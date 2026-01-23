"""
Portal v2 Knowledge Base Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.services.portal.knowledge_service import knowledge_service
from app.utils.auth import get_current_user

router = APIRouter()


def get_portal_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "portal_customer":
        raise HTTPException(status_code=403, detail="Portal access required")
    return current_user


@router.get("/categories")
async def list_categories(current_user: dict = Depends(get_portal_user)):
    """List KB categories."""
    return knowledge_service.list_categories()


@router.get("/articles")
async def list_articles(
    category: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    current_user: dict = Depends(get_portal_user)
):
    """List KB articles."""
    category_id = None
    if category:
        cat = knowledge_service.get_category_by_slug(category)
        if cat:
            category_id = cat["id"]
    return knowledge_service.list_articles(category_id=category_id, search=search, page=page)


@router.get("/articles/popular")
async def get_popular(
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_portal_user)
):
    """Get popular articles."""
    return knowledge_service.get_popular_articles(limit)


@router.get("/articles/recent")
async def get_recent(
    limit: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_portal_user)
):
    """Get recently viewed articles."""
    return knowledge_service.get_recent_articles(current_user.get("customer_id"), limit)


@router.get("/search")
async def search(
    q: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_portal_user)
):
    """Search articles."""
    return knowledge_service.search_articles(query=q, limit=limit)


@router.get("/faq")
async def get_faq(
    limit: int = Query(10, ge=1, le=30),
    current_user: dict = Depends(get_portal_user)
):
    """Get FAQ articles."""
    return knowledge_service.get_faq(limit)


@router.get("/articles/{slug}")
async def get_article(slug: str, current_user: dict = Depends(get_portal_user)):
    """Get article by slug."""
    article = knowledge_service.get_article_by_slug(slug, current_user.get("customer_id"))
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/articles/{article_id}/helpful")
async def vote_helpful(
    article_id: str,
    helpful: bool = True,
    current_user: dict = Depends(get_portal_user)
):
    """Vote article as helpful or not."""
    try:
        return knowledge_service.vote_helpful(article_id, helpful, current_user.get("customer_id"))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
