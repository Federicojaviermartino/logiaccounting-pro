"""Document management API routes."""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.documents.services.document_service import DocumentService
from app.documents.schemas.document import (
    DocumentUpload, DocumentUpdate, DocumentResponse, DocumentDetail,
    DocumentFilter, DocumentVersionResponse,
    CategoryCreate, CategoryResponse
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    document_type: str = Form(...),
    category_id: Optional[UUID] = Form(None),
    folder_id: Optional[UUID] = Form(None),
    tags: Optional[str] = Form(None),  # comma-separated
    is_confidential: bool = Form(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a new document."""
    service = DocumentService(db)
    
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    data = DocumentUpload(
        title=title,
        description=description,
        document_type=document_type,
        category_id=category_id,
        folder_id=folder_id,
        tags=tag_list,
        is_confidential=is_confidential
    )
    
    try:
        document = await service.upload_document(
            customer_id=current_user.customer_id,
            user_id=current_user.id,
            file=file.file,
            file_name=file.filename,
            file_size=file.size,
            mime_type=file.content_type,
            data=data
        )
        return DocumentResponse.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=dict)
async def get_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    category_id: Optional[UUID] = None,
    folder_id: Optional[UUID] = None,
    created_by: Optional[UUID] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    is_confidential: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get documents with filtering and pagination."""
    service = DocumentService(db)
    
    filters = DocumentFilter(
        search=search,
        document_type=document_type,
        status=status,
        category_id=category_id,
        folder_id=folder_id,
        created_by=created_by,
        is_confidential=is_confidential
    )
    
    documents, total = await service.get_documents(
        customer_id=current_user.customer_id,
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    return {
        "items": [DocumentResponse.model_validate(d) for d in documents],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document details."""
    service = DocumentService(db)
    document = await service.get_document_by_id(
        customer_id=current_user.customer_id,
        document_id=document_id
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    versions = await service.get_document_versions(
        current_user.customer_id, document_id
    )
    
    response = DocumentDetail.model_validate(document)
    response.version_count = len(versions) + 1
    
    return response


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update document metadata."""
    service = DocumentService(db)
    document = await service.update_document(
        customer_id=current_user.customer_id,
        document_id=document_id,
        user_id=current_user.id,
        data=data
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    permanent: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete document."""
    service = DocumentService(db)
    success = await service.delete_document(
        customer_id=current_user.customer_id,
        document_id=document_id,
        user_id=current_user.id,
        permanent=permanent
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download document file."""
    service = DocumentService(db)
    
    document = await service.get_document_by_id(
        customer_id=current_user.customer_id,
        document_id=document_id
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = await service.get_file_path(
        current_user.customer_id, document_id
    )
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        filename=document.file_name,
        media_type=document.mime_type
    )


@router.post("/{document_id}/versions", response_model=DocumentResponse)
async def upload_new_version(
    document_id: UUID,
    file: UploadFile = File(...),
    change_summary: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a new version of a document."""
    service = DocumentService(db)
    
    try:
        document = await service.upload_new_version(
            customer_id=current_user.customer_id,
            document_id=document_id,
            user_id=current_user.id,
            file=file.file,
            file_name=file.filename,
            file_size=file.size,
            mime_type=file.content_type,
            change_summary=change_summary
        )
        return DocumentResponse.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
async def get_document_versions(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document version history."""
    service = DocumentService(db)
    versions = await service.get_document_versions(
        customer_id=current_user.customer_id,
        document_id=document_id
    )
    return [DocumentVersionResponse.model_validate(v) for v in versions]


# ==========================================
# CATEGORIES
# ==========================================

@router.get("/categories/list", response_model=List[CategoryResponse])
async def get_categories(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document categories."""
    service = DocumentService(db)
    categories = await service.get_categories(
        customer_id=current_user.customer_id,
        include_inactive=include_inactive
    )
    return [CategoryResponse.model_validate(c) for c in categories]


@router.post("/categories", response_model=CategoryResponse)
async def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create document category."""
    service = DocumentService(db)
    category = await service.create_category(
        customer_id=current_user.customer_id,
        data=data
    )
    return CategoryResponse.model_validate(category)


# ==========================================
# DOCUMENT TYPES
# ==========================================

@router.get("/types/list", response_model=List[dict])
async def get_document_types():
    """Get available document types."""
    from app.documents.models.document import DocumentType
    return [{"code": t.value, "name": t.name.replace("_", " ").title()} for t in DocumentType]
