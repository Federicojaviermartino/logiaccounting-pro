"""Folder management API routes."""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.documents.services.folder_service import FolderService
from app.documents.schemas.folder import (
    FolderCreate, FolderUpdate, FolderResponse,
    FolderTree, FolderContents
)

router = APIRouter(prefix="/folders", tags=["Folders"])


@router.post("", response_model=FolderResponse)
async def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new folder."""
    service = FolderService(db)
    folder = await service.create_folder(
        customer_id=current_user.customer_id,
        user_id=current_user.id,
        data=data
    )
    return FolderResponse.model_validate(folder)


@router.get("", response_model=List[FolderResponse])
async def get_folders(
    parent_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get folders, optionally filtered by parent."""
    service = FolderService(db)
    folders = await service.get_folders(
        customer_id=current_user.customer_id,
        parent_id=parent_id
    )
    return [FolderResponse.model_validate(f) for f in folders]


@router.get("/tree", response_model=List[FolderTree])
async def get_folder_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete folder tree structure."""
    service = FolderService(db)
    return await service.get_folder_tree(current_user.customer_id)


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get folder details."""
    service = FolderService(db)
    folder = await service.get_folder_by_id(
        customer_id=current_user.customer_id,
        folder_id=folder_id
    )
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    return FolderResponse.model_validate(folder)


@router.get("/{folder_id}/contents", response_model=FolderContents)
async def get_folder_contents(
    folder_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get folder contents including subfolders and documents."""
    service = FolderService(db)
    try:
        return await service.get_folder_contents(
            customer_id=current_user.customer_id,
            folder_id=folder_id,
            page=page,
            page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: UUID,
    data: FolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update folder."""
    service = FolderService(db)
    folder = await service.update_folder(
        customer_id=current_user.customer_id,
        folder_id=folder_id,
        data=data
    )
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found or is a system folder")
    
    return FolderResponse.model_validate(folder)


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: UUID,
    recursive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete folder."""
    service = FolderService(db)
    try:
        success = await service.delete_folder(
            customer_id=current_user.customer_id,
            folder_id=folder_id,
            recursive=recursive
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Folder not found or is a system folder")
        
        return {"message": "Folder deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{folder_id}/move")
async def move_folder(
    folder_id: UUID,
    new_parent_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Move folder to a new parent."""
    service = FolderService(db)
    try:
        folder = await service.move_folder(
            customer_id=current_user.customer_id,
            folder_id=folder_id,
            new_parent_id=new_parent_id
        )
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        return FolderResponse.model_validate(folder)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{folder_id}/documents/{document_id}")
async def add_document_to_folder(
    folder_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add document to folder."""
    service = FolderService(db)
    await service.add_document_to_folder(
        document_id=document_id,
        folder_id=folder_id,
        user_id=current_user.id
    )
    return {"message": "Document added to folder"}


@router.delete("/{folder_id}/documents/{document_id}")
async def remove_document_from_folder(
    folder_id: UUID,
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove document from folder."""
    service = FolderService(db)
    success = await service.remove_document_from_folder(
        document_id=document_id,
        folder_id=folder_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not in folder")
    
    return {"message": "Document removed from folder"}
