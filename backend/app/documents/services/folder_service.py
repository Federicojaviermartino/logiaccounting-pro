"""Folder management service."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import Session

from app.documents.models.folder import Folder, DocumentFolder
from app.documents.models.document import Document, DocumentStatus
from app.documents.schemas.folder import (
    FolderCreate, FolderUpdate, FolderResponse, FolderTree, FolderContents
)

import re

# Characters not allowed in folder names (path separators and null bytes)
_UNSAFE_FOLDER_CHARS = re.compile(r'[/\\:\x00]')


def _sanitize_folder_name(name: str) -> str:
    """Remove path separators and null bytes from folder names."""
    return _UNSAFE_FOLDER_CHARS.sub('_', name).strip()


class FolderService:
    """Service for folder management."""

    def __init__(self, db: Session):
        self.db = db

    async def create_folder(
        self,
        customer_id: UUID,
        user_id: UUID,
        data: FolderCreate
    ) -> Folder:
        """Create a new folder."""
        data.name = _sanitize_folder_name(data.name)
        path = f"/{data.name}"
        depth = 0
        
        if data.parent_id:
            parent = await self.get_folder_by_id(customer_id, data.parent_id)
            if parent:
                path = f"{parent.path}/{data.name}"
                depth = parent.depth + 1
        
        folder = Folder(
            id=uuid4(),
            customer_id=customer_id,
            name=data.name,
            description=data.description,
            parent_id=data.parent_id,
            path=path,
            depth=depth,
            color=data.color,
            icon=data.icon,
            created_by=user_id
        )
        
        self.db.add(folder)
        self.db.commit()
        self.db.refresh(folder)
        
        return folder
    
    async def update_folder(
        self,
        customer_id: UUID,
        folder_id: UUID,
        data: FolderUpdate
    ) -> Optional[Folder]:
        """Update folder."""
        folder = await self.get_folder_by_id(customer_id, folder_id)
        if not folder or folder.is_system:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        old_path = folder.path
        if 'name' in update_data and update_data['name'] != folder.name:
            if folder.parent_id:
                parent = await self.get_folder_by_id(customer_id, folder.parent_id)
                new_path = f"{parent.path}/{update_data['name']}"
            else:
                new_path = f"/{update_data['name']}"
            
            await self._update_child_paths(customer_id, old_path, new_path)
            folder.path = new_path
        
        _ALLOWED_FIELDS = frozenset({'name', 'description', 'color', 'icon', 'is_active'})
        for field, value in update_data.items():
            if field not in _ALLOWED_FIELDS:
                continue
            if field == 'name':
                folder.name = _sanitize_folder_name(value)
            else:
                setattr(folder, field, value)
        
        folder.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(folder)
        
        return folder
    
    async def delete_folder(
        self,
        customer_id: UUID,
        folder_id: UUID,
        recursive: bool = False
    ) -> bool:
        """Delete folder."""
        folder = await self.get_folder_by_id(customer_id, folder_id)
        if not folder or folder.is_system:
            return False
        
        children = await self.get_subfolders(customer_id, folder_id)
        if children and not recursive:
            raise ValueError("Folder has subfolders. Use recursive=True to delete all.")
        
        docs_in_folder = self.db.execute(
            select(func.count()).where(DocumentFolder.folder_id == folder_id)
        ).scalar()
        
        if docs_in_folder > 0 and not recursive:
            raise ValueError("Folder contains documents. Move them first or use recursive=True.")
        
        if recursive:
            for child in children:
                await self.delete_folder(customer_id, child.id, recursive=True)
            
            self.db.execute(
                DocumentFolder.__table__.delete().where(
                    DocumentFolder.folder_id == folder_id
                )
            )
        
        self.db.delete(folder)
        self.db.commit()
        
        return True
    
    async def get_folder_by_id(
        self,
        customer_id: UUID,
        folder_id: UUID
    ) -> Optional[Folder]:
        """Get folder by ID."""
        query = select(Folder).where(
            Folder.id == folder_id,
            Folder.customer_id == customer_id
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_folders(
        self,
        customer_id: UUID,
        parent_id: Optional[UUID] = None
    ) -> List[Folder]:
        """Get folders, optionally filtered by parent."""
        query = select(Folder).where(Folder.customer_id == customer_id)
        
        if parent_id is None:
            query = query.where(Folder.parent_id.is_(None))
        else:
            query = query.where(Folder.parent_id == parent_id)
        
        query = query.order_by(Folder.name)
        result = self.db.execute(query)
        return result.scalars().all()
    
    async def get_subfolders(
        self,
        customer_id: UUID,
        folder_id: UUID
    ) -> List[Folder]:
        """Get immediate subfolders."""
        query = select(Folder).where(
            Folder.customer_id == customer_id,
            Folder.parent_id == folder_id
        ).order_by(Folder.name)
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    async def get_folder_tree(
        self,
        customer_id: UUID
    ) -> List[FolderTree]:
        """Get complete folder tree structure."""
        query = select(Folder).where(
            Folder.customer_id == customer_id
        ).order_by(Folder.path)
        
        result = self.db.execute(query)
        folders = result.scalars().all()
        
        folder_map = {}
        roots = []
        
        for folder in folders:
            tree_item = FolderTree(
                id=folder.id,
                name=folder.name,
                path=folder.path,
                document_count=folder.document_count,
                children=[]
            )
            folder_map[folder.id] = tree_item
            
            if folder.parent_id is None:
                roots.append(tree_item)
            elif folder.parent_id in folder_map:
                folder_map[folder.parent_id].children.append(tree_item)
        
        return roots
    
    async def get_folder_contents(
        self,
        customer_id: UUID,
        folder_id: UUID,
        page: int = 1,
        page_size: int = 50
    ) -> FolderContents:
        """Get folder contents including subfolders and documents."""
        folder = await self.get_folder_by_id(customer_id, folder_id)
        if not folder:
            raise ValueError("Folder not found")
        
        subfolders = await self.get_subfolders(customer_id, folder_id)
        
        doc_query = select(Document).join(
            DocumentFolder, DocumentFolder.document_id == Document.id
        ).where(
            DocumentFolder.folder_id == folder_id,
            Document.status != DocumentStatus.DELETED
        ).order_by(desc(Document.created_at))
        
        doc_query = doc_query.offset((page - 1) * page_size).limit(page_size)
        documents = self.db.execute(doc_query).scalars().all()
        
        breadcrumbs = await self._get_breadcrumbs(customer_id, folder)
        
        return FolderContents(
            folder=FolderResponse.model_validate(folder),
            subfolders=[FolderResponse.model_validate(f) for f in subfolders],
            documents=[{
                "id": str(d.id),
                "title": d.title,
                "file_name": d.file_name,
                "file_size": d.file_size,
                "document_type": d.document_type.value,
                "created_at": d.created_at.isoformat()
            } for d in documents],
            breadcrumbs=breadcrumbs
        )
    
    async def move_folder(
        self,
        customer_id: UUID,
        folder_id: UUID,
        new_parent_id: Optional[UUID]
    ) -> Optional[Folder]:
        """Move folder to new parent."""
        folder = await self.get_folder_by_id(customer_id, folder_id)
        if not folder or folder.is_system:
            return None
        
        if new_parent_id:
            new_parent = await self.get_folder_by_id(customer_id, new_parent_id)
            if not new_parent:
                raise ValueError("Target folder not found")
            
            if new_parent.path.startswith(folder.path):
                raise ValueError("Cannot move folder into its own subfolder")
            
            new_path = f"{new_parent.path}/{folder.name}"
            new_depth = new_parent.depth + 1
        else:
            new_path = f"/{folder.name}"
            new_depth = 0
        
        old_path = folder.path
        await self._update_child_paths(customer_id, old_path, new_path)
        
        folder.parent_id = new_parent_id
        folder.path = new_path
        folder.depth = new_depth
        folder.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(folder)
        
        return folder
    
    async def add_document_to_folder(
        self,
        document_id: UUID,
        folder_id: UUID,
        user_id: UUID
    ) -> DocumentFolder:
        """Add document to folder."""
        existing = self.db.execute(
            select(DocumentFolder).where(
                DocumentFolder.document_id == document_id,
                DocumentFolder.folder_id == folder_id
            )
        ).scalar_one_or_none()
        
        if existing:
            return existing
        
        doc_folder = DocumentFolder(
            id=uuid4(),
            document_id=document_id,
            folder_id=folder_id,
            added_by=user_id
        )
        
        self.db.add(doc_folder)
        
        folder = self.db.execute(
            select(Folder).where(Folder.id == folder_id)
        ).scalar_one_or_none()
        if folder:
            folder.document_count += 1
        
        self.db.commit()
        self.db.refresh(doc_folder)
        
        return doc_folder
    
    async def remove_document_from_folder(
        self,
        document_id: UUID,
        folder_id: UUID
    ) -> bool:
        """Remove document from folder."""
        doc_folder = self.db.execute(
            select(DocumentFolder).where(
                DocumentFolder.document_id == document_id,
                DocumentFolder.folder_id == folder_id
            )
        ).scalar_one_or_none()
        
        if not doc_folder:
            return False
        
        self.db.delete(doc_folder)
        
        folder = self.db.execute(
            select(Folder).where(Folder.id == folder_id)
        ).scalar_one_or_none()
        if folder and folder.document_count > 0:
            folder.document_count -= 1
        
        self.db.commit()
        return True
    
    async def _update_child_paths(
        self,
        customer_id: UUID,
        old_path: str,
        new_path: str
    ):
        """Update paths of all child folders."""
        children = self.db.execute(
            select(Folder).where(
                Folder.customer_id == customer_id,
                Folder.path.like(f"{old_path}/%")
            )
        ).scalars().all()
        
        for child in children:
            child.path = child.path.replace(old_path, new_path, 1)
    
    async def _get_breadcrumbs(
        self,
        customer_id: UUID,
        folder: Folder
    ) -> List[dict]:
        """Get breadcrumb trail for folder."""
        breadcrumbs = []
        current = folder
        
        while current:
            breadcrumbs.insert(0, {
                "id": str(current.id),
                "name": current.name,
                "path": current.path
            })
            
            if current.parent_id:
                current = await self.get_folder_by_id(customer_id, current.parent_id)
            else:
                break
        
        return breadcrumbs
