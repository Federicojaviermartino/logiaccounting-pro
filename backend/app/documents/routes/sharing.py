"""Document sharing API routes."""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.documents.services.sharing_service import SharingService
from app.documents.services.document_service import DocumentService
from app.documents.schemas.sharing import (
    ShareCreate, ShareResponse,
    ShareLinkCreate, ShareLinkResponse,
    AccessLogResponse
)

router = APIRouter(prefix="/documents", tags=["Document Sharing"])


@router.post("/{document_id}/share", response_model=ShareResponse)
async def share_document(
    document_id: UUID,
    data: ShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Share document with user or email."""
    doc_service = DocumentService(db)
    document = await doc_service.get_document_by_id(
        current_user.customer_id, document_id
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    service = SharingService(db)
    share = await service.share_document(
        document_id=document_id,
        user_id=current_user.id,
        data=data
    )
    return ShareResponse.model_validate(share)


@router.get("/{document_id}/shares", response_model=List[ShareResponse])
async def get_document_shares(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all shares for a document."""
    service = SharingService(db)
    shares = await service.get_document_shares(document_id)
    return [ShareResponse.model_validate(s) for s in shares]


@router.delete("/shares/{share_id}")
async def revoke_share(
    share_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke a document share."""
    service = SharingService(db)
    success = await service.revoke_share(share_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Share not found")
    
    return {"message": "Share revoked"}


@router.post("/{document_id}/share-link", response_model=ShareLinkResponse)
async def create_share_link(
    document_id: UUID,
    data: ShareLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a public share link."""
    doc_service = DocumentService(db)
    document = await doc_service.get_document_by_id(
        current_user.customer_id, document_id
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    service = SharingService(db)
    share_link = await service.create_share_link(
        document_id=document_id,
        user_id=current_user.id,
        data=data
    )
    
    response = ShareLinkResponse.model_validate(share_link)
    response.link = service.get_share_link_url(share_link.token)
    
    return response


@router.get("/{document_id}/share-links", response_model=List[ShareLinkResponse])
async def get_share_links(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all share links for a document."""
    service = SharingService(db)
    links = await service.get_document_share_links(document_id)
    
    responses = []
    for link in links:
        response = ShareLinkResponse.model_validate(link)
        response.link = service.get_share_link_url(link.token)
        responses.append(response)
    
    return responses


@router.delete("/share-links/{link_id}")
async def revoke_share_link(
    link_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke a share link."""
    service = SharingService(db)
    success = await service.revoke_share_link(link_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Share link not found")
    
    return {"message": "Share link revoked"}


@router.get("/{document_id}/access-logs", response_model=dict)
async def get_access_logs(
    document_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get access logs for a document."""
    service = SharingService(db)
    logs, total = await service.get_access_logs(
        document_id=document_id,
        page=page,
        page_size=page_size
    )
    
    return {
        "items": [AccessLogResponse.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ==========================================
# PUBLIC SHARED ACCESS
# ==========================================

public_router = APIRouter(prefix="/shared", tags=["Public Sharing"])


@public_router.get("/{token}")
async def access_shared_document(
    token: str,
    password: Optional[str] = Query(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Access a shared document via link."""
    service = SharingService(db)
    
    valid, share_link, message = await service.validate_share_link(token, password)
    
    if not valid:
        if message == "Password required":
            return {"requires_password": True, "message": message}
        raise HTTPException(status_code=403, detail=message)
    
    await service.record_link_access(share_link)
    
    doc_service = DocumentService(db)
    document = await doc_service.get_document_by_id(
        share_link.document_id.customer_id if hasattr(share_link.document_id, 'customer_id') else None,
        share_link.document_id
    )
    
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    
    await service.log_access(
        document_id=share_link.document_id,
        access_type="view",
        share_link_id=share_link.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {
        "document": {
            "id": str(share_link.document_id),
            "title": document.title if document else "Unknown",
            "file_name": document.file_name if document else "Unknown",
            "file_size": document.file_size if document else 0,
            "mime_type": document.mime_type if document else "application/octet-stream"
        },
        "permission": share_link.permission.value,
        "can_download": share_link.permission.value in ["download", "edit", "full"]
    }


@public_router.get("/{token}/download")
async def download_shared_document(
    token: str,
    password: Optional[str] = Query(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Download a shared document."""
    service = SharingService(db)
    
    valid, share_link, message = await service.validate_share_link(token, password)
    
    if not valid:
        raise HTTPException(status_code=403, detail=message)
    
    if share_link.permission.value not in ["download", "edit", "full"]:
        raise HTTPException(status_code=403, detail="Download not allowed")
    
    doc_service = DocumentService(db)
    
    from sqlalchemy import select
    from app.documents.models.document import Document
    document = db.execute(
        select(Document).where(Document.id == share_link.document_id)
    ).scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = f"{doc_service.UPLOAD_DIR}/{document.file_path}"
    
    ip_address = request.client.host if request else None
    user_agent = request.headers.get("user-agent") if request else None
    
    await service.log_access(
        document_id=share_link.document_id,
        access_type="download",
        share_link_id=share_link.id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    from fastapi.responses import FileResponse
    return FileResponse(
        file_path,
        filename=document.file_name,
        media_type=document.mime_type
    )
