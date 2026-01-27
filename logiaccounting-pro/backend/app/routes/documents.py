"""
Document Management routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.document_service import document_service
from app.utils.auth import get_current_user
import io

router = APIRouter()


class UploadDocumentRequest(BaseModel):
    filename: str
    content: str
    mime_type: str
    entity_type: str
    entity_id: str
    category: str = "other"
    description: str = ""


class UpdateDocumentRequest(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None


@router.get("/categories")
async def get_categories():
    """Get document categories"""
    return {"categories": document_service.CATEGORIES}


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """Get storage statistics"""
    return document_service.get_storage_stats()


@router.post("")
async def upload_document(
    request: UploadDocumentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Upload a document"""
    result = document_service.upload_document(
        filename=request.filename,
        content_base64=request.content,
        mime_type=request.mime_type,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        category=request.category,
        description=request.description,
        uploaded_by=current_user["id"]
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("")
async def list_documents(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List documents"""
    return {"documents": document_service.list_documents(entity_type, entity_id, category)}


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_documents(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all documents for an entity"""
    return {"documents": document_service.get_entity_documents(entity_type, entity_id)}


@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get document metadata"""
    doc = document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download document content"""
    doc = document_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    content = document_service.get_document_content(doc_id)

    return StreamingResponse(
        io.BytesIO(content),
        media_type=doc["mime_type"],
        headers={"Content-Disposition": f'attachment; filename="{doc["filename"]}"'}
    )


@router.put("/{doc_id}")
async def update_document(
    doc_id: str,
    request: UpdateDocumentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update document metadata"""
    doc = document_service.update_document(
        doc_id,
        category=request.category,
        description=request.description
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return doc


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a document"""
    if document_service.delete_document(doc_id):
        return {"message": "Document deleted"}
    raise HTTPException(status_code=404, detail="Document not found")
