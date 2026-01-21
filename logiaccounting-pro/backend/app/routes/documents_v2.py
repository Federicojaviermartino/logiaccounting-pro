"""
Document Management Routes - Phase 13
Enhanced document management API with full-featured operations
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from io import BytesIO
import logging

from app.utils.auth import get_current_user
from app.services.document_management_service import document_management_service
from app.services.document_ocr_service import document_ocr_service
from app.services.ai_extraction_service import ai_extraction_service
from app.services.document_search_service import document_search_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class DocumentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None


class CreateShareRequest(BaseModel):
    permission: str = "view"
    expires_days: Optional[int] = None
    can_download: bool = True


class ShareWithUserRequest(BaseModel):
    user_id: str
    permission: str = "view"
    can_download: bool = True
    can_share: bool = False


class CommentRequest(BaseModel):
    content: str
    parent_id: Optional[str] = None
    page_number: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None


class CreateCategoryRequest(BaseModel):
    name: str
    parent_id: Optional[str] = None
    icon: str = "folder"
    color: str = "#6B7280"


class CreateTagRequest(BaseModel):
    name: str
    color: str = "#6B7280"


# Upload Endpoints
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    document_type: str = Form("other"),
    category_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    related_entity_type: Optional[str] = Form(None),
    related_entity_id: Optional[str] = Form(None),
    extract_text: bool = Form(True),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a document

    Supports multipart/form-data upload with optional OCR processing
    """
    org_id = current_user.get("organization_id", "default")

    tag_list = tags.split(",") if tags else None

    result = document_management_service.upload_document(
        file_data=file.file,
        filename=file.filename,
        organization_id=org_id,
        owner_id=current_user["id"],
        mime_type=file.content_type,
        document_type=document_type,
        category_id=category_id,
        name=name,
        description=description,
        tags=tag_list,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        extract_text=extract_text,
    )

    if not result.get("success"):
        if result.get("error") == "duplicate":
            raise HTTPException(
                status_code=409,
                detail={
                    "message": result["message"],
                    "existing_document_id": result.get("existing_document_id")
                }
            )
        raise HTTPException(status_code=400, detail=result.get("errors", result.get("error")))

    # Process OCR in background if enabled
    if extract_text and result.get("document"):
        doc = result["document"]
        if doc.get("mime_type", "").startswith(("image/", "application/pdf")):
            try:
                file.file.seek(0)
                content = file.file.read()
                ocr_result = document_ocr_service.extract_text(content, file.filename)

                if ocr_result.get("success"):
                    document_management_service.update_ocr_text(
                        doc["id"],
                        ocr_result.get("text", ""),
                        ocr_result.get("confidence")
                    )

                    # Index for search
                    document_search_service.index_document(doc)

            except Exception as e:
                logger.error(f"OCR processing failed: {e}")

    return {"success": True, "document": result["document"]}


@router.post("/{document_id}/version")
async def upload_new_version(
    document_id: str,
    file: UploadFile = File(...),
    change_notes: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload a new version of an existing document"""
    org_id = current_user.get("organization_id", "default")

    result = document_management_service.upload_new_version(
        document_id=document_id,
        file_data=file.file,
        filename=file.filename,
        organization_id=org_id,
        user_id=current_user["id"],
        change_notes=change_notes,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


# Document CRUD Endpoints
@router.get("")
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = None,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List documents with pagination and filters"""
    org_id = current_user.get("organization_id", "default")

    filters = {}
    if category_id:
        filters["category_id"] = category_id
    if document_type:
        filters["document_type"] = document_type
    if status:
        filters["status"] = status
    if search:
        filters["search"] = search
    if related_entity_type:
        filters["related_entity_type"] = related_entity_type
    if related_entity_id:
        filters["related_entity_id"] = related_entity_id

    result = document_management_service.list_documents(
        organization_id=org_id,
        page=page,
        per_page=per_page,
        **filters
    )

    return result


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get document details"""
    org_id = current_user.get("organization_id", "default")

    doc = document_management_service.get_document(document_id, org_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"document": doc}


@router.put("/{document_id}")
async def update_document(
    document_id: str,
    request: DocumentUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update document metadata"""
    org_id = current_user.get("organization_id", "default")

    doc = document_management_service.update_document(
        document_id=document_id,
        organization_id=org_id,
        user_id=current_user["id"],
        **request.model_dump(exclude_none=True)
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"document": doc}


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    permanent: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    """Delete a document (soft or permanent)"""
    org_id = current_user.get("organization_id", "default")

    if not document_management_service.delete_document(
        document_id=document_id,
        organization_id=org_id,
        user_id=current_user["id"],
        permanent=permanent
    ):
        raise HTTPException(status_code=404, detail="Document not found")

    document_search_service.delete_from_index(document_id)

    return {"message": "Document deleted"}


@router.post("/{document_id}/restore")
async def restore_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Restore a deleted document"""
    org_id = current_user.get("organization_id", "default")

    doc = document_management_service.restore_document(
        document_id=document_id,
        organization_id=org_id,
        user_id=current_user["id"]
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"document": doc}


# Download Endpoints
@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    version: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Download document content"""
    org_id = current_user.get("organization_id", "default")

    result = document_management_service.download_document(
        document_id=document_id,
        organization_id=org_id,
        user_id=current_user["id"],
        version=version
    )

    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    return StreamingResponse(
        BytesIO(result["content"]),
        media_type=result["mime_type"],
        headers={"Content-Disposition": f'attachment; filename="{result["filename"]}"'}
    )


@router.get("/{document_id}/download-url")
async def get_download_url(
    document_id: str,
    expires_in: int = Query(3600, ge=60, le=86400),
    version: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get presigned download URL"""
    org_id = current_user.get("organization_id", "default")

    url = document_management_service.get_download_url(
        document_id=document_id,
        organization_id=org_id,
        expires_in=expires_in,
        version=version
    )

    if not url:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"download_url": url}


# Version Endpoints
@router.get("/{document_id}/versions")
async def get_versions(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get document versions"""
    org_id = current_user.get("organization_id", "default")

    versions = document_management_service.get_versions(document_id, org_id)

    return {"versions": versions}


# Sharing Endpoints
@router.post("/{document_id}/share")
async def create_share_link(
    document_id: str,
    request: CreateShareRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a shareable link"""
    org_id = current_user.get("organization_id", "default")

    share = document_management_service.create_share_link(
        document_id=document_id,
        organization_id=org_id,
        user_id=current_user["id"],
        permission=request.permission,
        expires_days=request.expires_days,
        can_download=request.can_download
    )

    if not share:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"share": share}


@router.post("/{document_id}/share/user")
async def share_with_user(
    document_id: str,
    request: ShareWithUserRequest,
    current_user: dict = Depends(get_current_user)
):
    """Share document with another user"""
    org_id = current_user.get("organization_id", "default")

    share = document_management_service.share_with_user(
        document_id=document_id,
        organization_id=org_id,
        user_id=current_user["id"],
        share_with_user_id=request.user_id,
        permission=request.permission,
        can_download=request.can_download,
        can_share=request.can_share
    )

    if not share:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"share": share}


@router.get("/{document_id}/shares")
async def get_shares(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all shares for a document"""
    org_id = current_user.get("organization_id", "default")

    shares = document_management_service.get_shares(document_id, org_id)

    return {"shares": shares}


@router.delete("/{document_id}/shares/{share_id}")
async def revoke_share(
    document_id: str,
    share_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke a share"""
    org_id = current_user.get("organization_id", "default")

    if not document_management_service.revoke_share(
        share_id=share_id,
        document_id=document_id,
        organization_id=org_id,
        user_id=current_user["id"]
    ):
        raise HTTPException(status_code=404, detail="Share not found")

    return {"message": "Share revoked"}


# Public Share Access
@router.get("/share/{share_token}")
async def access_shared_document(share_token: str):
    """Access a document via share link (public endpoint)"""
    result = document_management_service.access_shared_document(share_token)

    if not result:
        raise HTTPException(status_code=404, detail="Share not found")

    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])

    return result


# Comment Endpoints
@router.post("/{document_id}/comments")
async def add_comment(
    document_id: str,
    request: CommentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add a comment to a document"""
    org_id = current_user.get("organization_id", "default")

    comment = document_management_service.add_comment(
        document_id=document_id,
        organization_id=org_id,
        user_id=current_user["id"],
        content=request.content,
        parent_id=request.parent_id,
        page_number=request.page_number,
        position_x=request.position_x,
        position_y=request.position_y
    )

    if not comment:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"comment": comment}


@router.get("/{document_id}/comments")
async def get_comments(
    document_id: str,
    include_resolved: bool = Query(True),
    current_user: dict = Depends(get_current_user)
):
    """Get comments for a document"""
    org_id = current_user.get("organization_id", "default")

    comments = document_management_service.get_comments(
        document_id=document_id,
        organization_id=org_id,
        include_resolved=include_resolved
    )

    return {"comments": comments}


@router.post("/{document_id}/comments/{comment_id}/resolve")
async def resolve_comment(
    document_id: str,
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Resolve a comment"""
    org_id = current_user.get("organization_id", "default")

    comment = document_management_service.resolve_comment(
        comment_id=comment_id,
        document_id=document_id,
        organization_id=org_id,
        user_id=current_user["id"]
    )

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    return {"comment": comment}


# Activity Endpoints
@router.get("/{document_id}/activity")
async def get_activity(
    document_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get activity log for a document"""
    org_id = current_user.get("organization_id", "default")

    activity = document_management_service.get_activity(
        document_id=document_id,
        organization_id=org_id,
        limit=limit
    )

    return {"activity": activity}


# OCR & Extraction Endpoints
@router.post("/{document_id}/ocr")
async def run_ocr(
    document_id: str,
    language: str = Query("eng+spa"),
    current_user: dict = Depends(get_current_user)
):
    """Run OCR on a document"""
    org_id = current_user.get("organization_id", "default")

    result = document_management_service.download_document(
        document_id=document_id,
        organization_id=org_id,
        user_id=current_user["id"]
    )

    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    ocr_result = document_ocr_service.extract_text(
        result["content"],
        result["filename"],
        language=language
    )

    if not ocr_result.get("success"):
        raise HTTPException(status_code=400, detail=ocr_result.get("error"))

    document_management_service.update_ocr_text(
        document_id,
        ocr_result.get("text", ""),
        ocr_result.get("confidence")
    )

    return ocr_result


@router.post("/{document_id}/extract")
async def extract_data(
    document_id: str,
    document_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Extract structured data from document using AI"""
    org_id = current_user.get("organization_id", "default")

    doc = document_management_service.get_document(document_id, org_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = doc.get("ocr_text", "")

    if not text:
        result = document_management_service.download_document(
            document_id=document_id,
            organization_id=org_id,
            user_id=current_user["id"]
        )

        if result:
            ocr_result = document_ocr_service.extract_text(result["content"], result["filename"])
            if ocr_result.get("success"):
                text = ocr_result.get("text", "")
                document_management_service.update_ocr_text(
                    document_id,
                    text,
                    ocr_result.get("confidence")
                )

    if not text:
        raise HTTPException(status_code=400, detail="No text available for extraction")

    extraction_result = ai_extraction_service.extract_data(
        text=text,
        document_type=document_type or doc.get("document_type")
    )

    if extraction_result.get("success"):
        document_management_service.update_extracted_data(
            document_id,
            extraction_result.get("data", {})
        )

    return extraction_result


@router.post("/{document_id}/classify")
async def classify_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Classify document type using AI"""
    org_id = current_user.get("organization_id", "default")

    doc = document_management_service.get_document(document_id, org_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    text = doc.get("ocr_text", "")

    if not text:
        raise HTTPException(status_code=400, detail="No text available for classification")

    result = ai_extraction_service.classify_document(text)

    if result.get("success") and result.get("document_type"):
        document_management_service.update_document(
            document_id=document_id,
            organization_id=org_id,
            user_id=current_user["id"],
            document_type=result["document_type"]
        )

    return result


# Category & Tag Endpoints
@router.get("/categories")
async def get_categories(current_user: dict = Depends(get_current_user)):
    """Get document categories"""
    org_id = current_user.get("organization_id", "default")
    return {"categories": document_management_service.get_categories(org_id)}


@router.get("/categories/tree")
async def get_category_tree(current_user: dict = Depends(get_current_user)):
    """Get category tree"""
    org_id = current_user.get("organization_id", "default")
    return {"tree": document_management_service.get_category_tree(org_id)}


@router.post("/categories")
async def create_category(
    request: CreateCategoryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new category"""
    org_id = current_user.get("organization_id", "default")

    category = document_management_service.create_category(
        organization_id=org_id,
        name=request.name,
        parent_id=request.parent_id,
        icon=request.icon,
        color=request.color
    )

    return {"category": category}


@router.get("/tags")
async def get_tags(current_user: dict = Depends(get_current_user)):
    """Get document tags"""
    org_id = current_user.get("organization_id", "default")
    return {"tags": document_management_service.get_tags(org_id)}


@router.post("/tags")
async def create_tag(
    request: CreateTagRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new tag"""
    org_id = current_user.get("organization_id", "default")

    tag = document_management_service.create_tag(
        organization_id=org_id,
        name=request.name,
        color=request.color
    )

    return {"tag": tag}


# Statistics
@router.get("/stats")
async def get_storage_stats(current_user: dict = Depends(get_current_user)):
    """Get storage statistics"""
    org_id = current_user.get("organization_id", "default")
    return document_management_service.get_storage_stats(org_id)


# Search Endpoints
@router.get("/search")
async def search_documents(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = None,
    document_type: Optional[str] = None,
    mime_type: Optional[str] = None,
    tags: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    owner_id: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: dict = Depends(get_current_user)
):
    """
    Search documents with full-text search and filters
    """
    org_id = current_user.get("organization_id", "default")

    filters = {}
    if category_id:
        filters["category_id"] = category_id
    if document_type:
        filters["document_type"] = document_type
    if mime_type:
        filters["mime_type"] = mime_type
    if tags:
        filters["tags"] = tags.split(",")
    if status:
        filters["status"] = status
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if owner_id:
        filters["owner_id"] = owner_id

    result = document_search_service.search(
        organization_id=org_id,
        query=q,
        filters=filters,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return {
        "success": True,
        "data": result
    }


@router.get("/search/suggest")
async def search_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=20),
    current_user: dict = Depends(get_current_user)
):
    """Get search suggestions (autocomplete)"""
    org_id = current_user.get("organization_id", "default")

    suggestions = document_search_service.suggest(
        organization_id=org_id,
        prefix=q,
        limit=limit
    )

    return {"success": True, "suggestions": suggestions}
