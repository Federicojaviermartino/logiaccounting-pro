# LogiAccounting Pro - Phase 5 Tasks (Part 3/3)

## DOCUMENT MANAGEMENT + API KEYS + SCHEDULED REPORTS + DASHBOARD BUILDER

---

## TASK 7: DOCUMENT MANAGEMENT 📎

### 7.1 Create Document Service

**File:** `backend/app/services/document_service.py`

```python
"""
Document Management Service
Handle file attachments for entities
"""

import base64
import hashlib
from datetime import datetime
from typing import Dict, List, Optional


class DocumentService:
    """Manages document attachments"""
    
    _instance = None
    _documents: Dict[str, dict] = {}
    _counter = 0
    
    ALLOWED_TYPES = {
        "application/pdf": "pdf",
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx"
    }
    
    CATEGORIES = ["invoice", "receipt", "contract", "quote", "report", "other"]
    
    MAX_SIZE_MB = 10
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._documents = {}
            cls._counter = 0
        return cls._instance
    
    def upload_document(
        self,
        filename: str,
        content_base64: str,
        mime_type: str,
        entity_type: str,
        entity_id: str,
        category: str = "other",
        description: str = "",
        uploaded_by: str = None
    ) -> dict:
        """Upload and store a document"""
        # Validate mime type
        if mime_type not in self.ALLOWED_TYPES:
            return {"error": f"File type not allowed: {mime_type}"}
        
        # Decode and check size
        try:
            content = base64.b64decode(content_base64)
            size_bytes = len(content)
            
            if size_bytes > self.MAX_SIZE_MB * 1024 * 1024:
                return {"error": f"File too large. Max size: {self.MAX_SIZE_MB}MB"}
            
        except Exception as e:
            return {"error": f"Invalid file content: {str(e)}"}
        
        self._counter += 1
        doc_id = f"DOC-{self._counter:06d}"
        
        # Generate hash for deduplication
        content_hash = hashlib.sha256(content).hexdigest()[:16]
        
        document = {
            "id": doc_id,
            "filename": filename,
            "mime_type": mime_type,
            "extension": self.ALLOWED_TYPES[mime_type],
            "size_bytes": size_bytes,
            "content_hash": content_hash,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "category": category,
            "description": description,
            "content": content_base64,  # Store base64 for simplicity
            "uploaded_by": uploaded_by,
            "uploaded_at": datetime.utcnow().isoformat(),
            "version": 1
        }
        
        self._documents[doc_id] = document
        
        # Return without content
        return {k: v for k, v in document.items() if k != "content"}
    
    def get_document(self, doc_id: str, include_content: bool = False) -> Optional[dict]:
        """Get a document by ID"""
        doc = self._documents.get(doc_id)
        if not doc:
            return None
        
        if include_content:
            return doc
        
        return {k: v for k, v in doc.items() if k != "content"}
    
    def get_document_content(self, doc_id: str) -> Optional[bytes]:
        """Get document content as bytes"""
        doc = self._documents.get(doc_id)
        if not doc:
            return None
        
        return base64.b64decode(doc["content"])
    
    def list_documents(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[dict]:
        """List documents with optional filters"""
        docs = list(self._documents.values())
        
        if entity_type:
            docs = [d for d in docs if d["entity_type"] == entity_type]
        
        if entity_id:
            docs = [d for d in docs if d["entity_id"] == entity_id]
        
        if category:
            docs = [d for d in docs if d["category"] == category]
        
        # Return without content
        return [
            {k: v for k, v in d.items() if k != "content"}
            for d in sorted(docs, key=lambda x: x["uploaded_at"], reverse=True)
        ]
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False
    
    def update_document(
        self,
        doc_id: str,
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[dict]:
        """Update document metadata"""
        if doc_id not in self._documents:
            return None
        
        doc = self._documents[doc_id]
        
        if category:
            doc["category"] = category
        if description is not None:
            doc["description"] = description
        
        return {k: v for k, v in doc.items() if k != "content"}
    
    def get_entity_documents(self, entity_type: str, entity_id: str) -> List[dict]:
        """Get all documents for a specific entity"""
        return self.list_documents(entity_type=entity_type, entity_id=entity_id)
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics"""
        total_size = sum(d["size_bytes"] for d in self._documents.values())
        by_category = {}
        by_type = {}
        
        for doc in self._documents.values():
            cat = doc["category"]
            by_category[cat] = by_category.get(cat, 0) + 1
            
            ext = doc["extension"]
            by_type[ext] = by_type.get(ext, 0) + 1
        
        return {
            "total_documents": len(self._documents),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_category": by_category,
            "by_type": by_type
        }


document_service = DocumentService()
```

### 7.2 Create Document Routes

**File:** `backend/app/routes/documents.py`

```python
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
    content: str  # base64
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


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_documents(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all documents for an entity"""
    return {"documents": document_service.get_entity_documents(entity_type, entity_id)}
```

### 7.3 Add Document API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Documents API
export const documentsAPI = {
  getCategories: () => api.get('/api/v1/documents/categories'),
  getStats: () => api.get('/api/v1/documents/stats'),
  upload: (data) => api.post('/api/v1/documents', data),
  list: (params) => api.get('/api/v1/documents', { params }),
  get: (id) => api.get(`/api/v1/documents/${id}`),
  download: (id) => api.get(`/api/v1/documents/${id}/download`, { responseType: 'blob' }),
  update: (id, data) => api.put(`/api/v1/documents/${id}`, data),
  delete: (id) => api.delete(`/api/v1/documents/${id}`),
  getEntityDocuments: (entityType, entityId) => api.get(`/api/v1/documents/entity/${entityType}/${entityId}`)
};
```

### 7.4 Create Document Uploader Component

**File:** `frontend/src/components/DocumentUploader.jsx`

```jsx
import { useState, useRef } from 'react';
import { documentsAPI } from '../services/api';

const CATEGORIES = ['invoice', 'receipt', 'contract', 'quote', 'report', 'other'];

export default function DocumentUploader({ entityType, entityId, onUpload }) {
  const [uploading, setUploading] = useState(false);
  const [category, setCategory] = useState('other');
  const [description, setDescription] = useState('');
  const fileInputRef = useRef(null);

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    
    try {
      // Convert to base64
      const reader = new FileReader();
      reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        
        const res = await documentsAPI.upload({
          filename: file.name,
          content: base64,
          mime_type: file.type,
          entity_type: entityType,
          entity_id: entityId,
          category,
          description
        });
        
        setDescription('');
        fileInputRef.current.value = '';
        onUpload?.(res.data);
      };
      reader.readAsDataURL(file);
    } catch (err) {
      alert(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="document-uploader">
      <div className="upload-controls">
        <select
          className="form-select"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          style={{ width: '150px' }}
        >
          {CATEGORIES.map(c => (
            <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
          ))}
        </select>
        <input
          type="text"
          className="form-input"
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          style={{ flex: 1 }}
        />
      </div>
      
      <div 
        className="upload-dropzone"
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".pdf,.png,.jpg,.jpeg,.webp,.docx,.xlsx"
          style={{ display: 'none' }}
        />
        {uploading ? (
          <p>Uploading...</p>
        ) : (
          <>
            <div className="upload-icon">📎</div>
            <p>Click or drag files here</p>
            <span className="text-muted text-sm">PDF, Images, DOCX, XLSX (max 10MB)</span>
          </>
        )}
      </div>
    </div>
  );
}
```

### 7.5 Create Document List Component

**File:** `frontend/src/components/DocumentList.jsx`

```jsx
import { useState, useEffect } from 'react';
import { documentsAPI } from '../services/api';

export default function DocumentList({ entityType, entityId, onDelete }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDocuments();
  }, [entityType, entityId]);

  const loadDocuments = async () => {
    try {
      const res = await documentsAPI.getEntityDocuments(entityType, entityId);
      setDocuments(res.data.documents);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (doc) => {
    try {
      const res = await documentsAPI.download(doc.id);
      const blob = new Blob([res.data], { type: doc.mime_type });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.filename;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Download failed');
    }
  };

  const handleDelete = async (doc) => {
    if (!confirm('Delete this document?')) return;
    try {
      await documentsAPI.delete(doc.id);
      loadDocuments();
      onDelete?.(doc);
    } catch (err) {
      alert('Delete failed');
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getIcon = (ext) => {
    const icons = {
      pdf: '📄',
      png: '🖼️',
      jpg: '🖼️',
      jpeg: '🖼️',
      webp: '🖼️',
      docx: '📝',
      xlsx: '📊'
    };
    return icons[ext] || '📎';
  };

  if (loading) return <div className="text-muted">Loading documents...</div>;
  if (documents.length === 0) return <div className="text-muted">No documents attached</div>;

  return (
    <div className="document-list">
      {documents.map(doc => (
        <div key={doc.id} className="document-item">
          <div className="document-icon">{getIcon(doc.extension)}</div>
          <div className="document-info">
            <div className="document-name">{doc.filename}</div>
            <div className="document-meta">
              <span className="badge badge-sm">{doc.category}</span>
              <span>{formatSize(doc.size_bytes)}</span>
              <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
            </div>
          </div>
          <div className="document-actions">
            <button className="btn btn-sm btn-secondary" onClick={() => handleDownload(doc)}>📥</button>
            <button className="btn btn-sm btn-danger" onClick={() => handleDelete(doc)}>🗑️</button>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### 7.6 Add Document Styles

**Add to:** `frontend/src/index.css`

```css
/* Documents */
.document-uploader {
  margin-bottom: 16px;
}

.upload-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.upload-dropzone {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-dropzone:hover {
  border-color: var(--primary);
  background: rgba(102, 126, 234, 0.05);
}

.upload-icon {
  font-size: 2.5rem;
  margin-bottom: 8px;
}

.document-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.document-icon {
  font-size: 1.5rem;
}

.document-info {
  flex: 1;
}

.document-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.document-meta {
  display: flex;
  gap: 12px;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.document-actions {
  display: flex;
  gap: 4px;
}

.badge-sm {
  font-size: 0.7rem;
  padding: 2px 6px;
}
```

---

## TASK 8: API KEYS MANAGEMENT 🔑

### 8.1 Create API Key Service

**File:** `backend/app/services/api_key_service.py`

```python
"""
API Key Management Service
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class APIKeyService:
    """Manages API keys for external integrations"""
    
    _instance = None
    _keys: Dict[str, dict] = {}
    _counter = 0
    
    PERMISSIONS = {
        "materials": ["read", "write"],
        "transactions": ["read", "write"],
        "payments": ["read", "write"],
        "projects": ["read", "write"],
        "reports": ["read"]
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._keys = {}
            cls._counter = 0
        return cls._instance
    
    def generate_key(
        self,
        name: str,
        permissions: Dict[str, List[str]],
        expires_days: Optional[int] = 365,
        created_by: str = None
    ) -> dict:
        """Generate a new API key"""
        self._counter += 1
        key_id = f"KEY-{self._counter:04d}"
        
        # Generate actual key
        raw_key = f"lap_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = (datetime.utcnow() + timedelta(days=expires_days)).isoformat()
        
        key_data = {
            "id": key_id,
            "name": name,
            "key_hash": key_hash,
            "key_prefix": raw_key[:12],
            "permissions": permissions,
            "expires_at": expires_at,
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None,
            "usage_count": 0,
            "active": True
        }
        
        self._keys[key_id] = key_data
        
        # Return with actual key (only time it's visible)
        return {
            **{k: v for k, v in key_data.items() if k != "key_hash"},
            "key": raw_key
        }
    
    def validate_key(self, raw_key: str) -> Optional[dict]:
        """Validate an API key and return its data"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        for key_data in self._keys.values():
            if key_data["key_hash"] == key_hash:
                # Check if active
                if not key_data["active"]:
                    return None
                
                # Check expiration
                if key_data["expires_at"]:
                    if datetime.fromisoformat(key_data["expires_at"]) < datetime.utcnow():
                        return None
                
                # Update usage
                key_data["last_used"] = datetime.utcnow().isoformat()
                key_data["usage_count"] += 1
                
                return key_data
        
        return None
    
    def check_permission(self, key_data: dict, entity: str, action: str) -> bool:
        """Check if key has permission for action"""
        permissions = key_data.get("permissions", {})
        entity_perms = permissions.get(entity, [])
        return action in entity_perms
    
    def list_keys(self, user_id: Optional[str] = None) -> List[dict]:
        """List all API keys"""
        keys = list(self._keys.values())
        
        if user_id:
            keys = [k for k in keys if k["created_by"] == user_id]
        
        # Don't include hash
        return [
            {k: v for k, v in key.items() if k != "key_hash"}
            for key in sorted(keys, key=lambda x: x["created_at"], reverse=True)
        ]
    
    def get_key(self, key_id: str) -> Optional[dict]:
        """Get API key by ID"""
        key = self._keys.get(key_id)
        if key:
            return {k: v for k, v in key.items() if k != "key_hash"}
        return None
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        if key_id in self._keys:
            self._keys[key_id]["active"] = False
            return True
        return False
    
    def delete_key(self, key_id: str) -> bool:
        """Delete an API key"""
        if key_id in self._keys:
            del self._keys[key_id]
            return True
        return False
    
    def update_permissions(self, key_id: str, permissions: Dict[str, List[str]]) -> Optional[dict]:
        """Update key permissions"""
        if key_id not in self._keys:
            return None
        
        self._keys[key_id]["permissions"] = permissions
        return self.get_key(key_id)


api_key_service = APIKeyService()
```

### 8.2 Create API Key Routes

**File:** `backend/app/routes/api_keys.py`

```python
"""
API Key Management routes
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.api_key_service import api_key_service
from app.utils.auth import require_roles

router = APIRouter()


class CreateKeyRequest(BaseModel):
    name: str
    permissions: Dict[str, List[str]]
    expires_days: Optional[int] = 365


class UpdatePermissionsRequest(BaseModel):
    permissions: Dict[str, List[str]]


@router.get("/permissions")
async def get_available_permissions(current_user: dict = Depends(require_roles("admin"))):
    """Get available permissions"""
    return {"permissions": api_key_service.PERMISSIONS}


@router.get("")
async def list_keys(current_user: dict = Depends(require_roles("admin"))):
    """List all API keys"""
    return {"keys": api_key_service.list_keys()}


@router.post("")
async def create_key(
    request: CreateKeyRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Create a new API key"""
    return api_key_service.generate_key(
        name=request.name,
        permissions=request.permissions,
        expires_days=request.expires_days,
        created_by=current_user["id"]
    )


@router.get("/{key_id}")
async def get_key(
    key_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Get API key details"""
    key = api_key_service.get_key(key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return key


@router.put("/{key_id}/permissions")
async def update_permissions(
    key_id: str,
    request: UpdatePermissionsRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update key permissions"""
    key = api_key_service.update_permissions(key_id, request.permissions)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    return key


@router.post("/{key_id}/revoke")
async def revoke_key(
    key_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Revoke an API key"""
    if api_key_service.revoke_key(key_id):
        return {"message": "Key revoked"}
    raise HTTPException(status_code=404, detail="Key not found")


@router.delete("/{key_id}")
async def delete_key(
    key_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Delete an API key"""
    if api_key_service.delete_key(key_id):
        return {"message": "Key deleted"}
    raise HTTPException(status_code=404, detail="Key not found")
```

### 8.3 Create API Keys Page

**File:** `frontend/src/pages/APIKeys.jsx`

```jsx
import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function APIKeys() {
  const [keys, setKeys] = useState([]);
  const [permissions, setPermissions] = useState({});
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [newKey, setNewKey] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    expires_days: 365,
    permissions: {}
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [keysRes, permsRes] = await Promise.all([
        api.get('/api/v1/api-keys'),
        api.get('/api/v1/api-keys/permissions')
      ]);
      setKeys(keysRes.data.keys);
      setPermissions(permsRes.data.permissions);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      const res = await api.post('/api/v1/api-keys', formData);
      setNewKey(res.data);
      setShowForm(false);
      loadData();
    } catch (err) {
      alert('Failed to create key');
    }
  };

  const handleRevoke = async (key) => {
    if (!confirm('Revoke this API key?')) return;
    try {
      await api.post(`/api/v1/api-keys/${key.id}/revoke`);
      loadData();
    } catch (err) {
      alert('Failed to revoke');
    }
  };

  const handleDelete = async (key) => {
    if (!confirm('Delete this API key permanently?')) return;
    try {
      await api.delete(`/api/v1/api-keys/${key.id}`);
      loadData();
    } catch (err) {
      alert('Failed to delete');
    }
  };

  const togglePermission = (entity, action) => {
    const current = formData.permissions[entity] || [];
    const newPerms = current.includes(action)
      ? current.filter(a => a !== action)
      : [...current, action];
    
    setFormData({
      ...formData,
      permissions: {
        ...formData.permissions,
        [entity]: newPerms
      }
    });
  };

  return (
    <>
      <div className="info-banner mb-6">
        🔑 Manage API keys for external integrations. Keys are only shown once upon creation.
      </div>

      {/* New Key Display */}
      {newKey && (
        <div className="section mb-6 new-key-alert">
          <h4>🎉 New API Key Created</h4>
          <p className="text-warning mb-2">Copy this key now. It won't be shown again!</p>
          <div className="key-display">
            <code>{newKey.key}</code>
            <button 
              className="btn btn-sm btn-secondary"
              onClick={() => {
                navigator.clipboard.writeText(newKey.key);
                alert('Copied!');
              }}
            >
              📋 Copy
            </button>
          </div>
          <button className="btn btn-secondary mt-4" onClick={() => setNewKey(null)}>
            Done
          </button>
        </div>
      )}

      <div className="section">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title" style={{ margin: 0 }}>API Keys</h3>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            ➕ Generate Key
          </button>
        </div>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : keys.length === 0 ? (
          <div className="text-center text-muted">No API keys created</div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Key Prefix</th>
                  <th>Status</th>
                  <th>Usage</th>
                  <th>Expires</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {keys.map(key => (
                  <tr key={key.id}>
                    <td><strong>{key.name}</strong></td>
                    <td><code>{key.key_prefix}...</code></td>
                    <td>
                      <span className={`badge ${key.active ? 'badge-success' : 'badge-danger'}`}>
                        {key.active ? 'Active' : 'Revoked'}
                      </span>
                    </td>
                    <td>{key.usage_count} calls</td>
                    <td>{key.expires_at ? new Date(key.expires_at).toLocaleDateString() : 'Never'}</td>
                    <td>
                      <div className="flex gap-2">
                        {key.active && (
                          <button className="btn btn-sm btn-warning" onClick={() => handleRevoke(key)}>
                            Revoke
                          </button>
                        )}
                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(key)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Generate API Key</h3>
              <button className="modal-close" onClick={() => setShowForm(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Key Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Integration - Shopify"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Expires In (days)</label>
                <select
                  className="form-select"
                  value={formData.expires_days}
                  onChange={(e) => setFormData({ ...formData, expires_days: parseInt(e.target.value) || null })}
                >
                  <option value="30">30 days</option>
                  <option value="90">90 days</option>
                  <option value="365">1 year</option>
                  <option value="">Never</option>
                </select>
              </div>
              
              <div className="form-group">
                <label className="form-label">Permissions</label>
                <div className="permissions-grid">
                  {Object.entries(permissions).map(([entity, actions]) => (
                    <div key={entity} className="permission-entity">
                      <strong>{entity}</strong>
                      <div className="permission-actions">
                        {actions.map(action => (
                          <label key={action} className="checkbox-label">
                            <input
                              type="checkbox"
                              checked={formData.permissions[entity]?.includes(action)}
                              onChange={() => togglePermission(entity, action)}
                            />
                            <span>{action}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button 
                className="btn btn-primary" 
                onClick={handleCreate}
                disabled={!formData.name}
              >
                Generate Key
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

### 8.4 Add API Key Styles

**Add to:** `frontend/src/index.css`

```css
/* API Keys */
.new-key-alert {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(102, 126, 234, 0.1));
  border: 1px solid #10b981;
}

.key-display {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  margin-top: 12px;
}

.key-display code {
  flex: 1;
  font-family: monospace;
  font-size: 0.9rem;
  word-break: break-all;
}

.permissions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.permission-entity {
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.permission-entity strong {
  display: block;
  margin-bottom: 8px;
  text-transform: capitalize;
}

.permission-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
```

---

## TASK 9: REGISTER ALL ROUTES

### 9.1 Update Backend main.py

```python
from app.routes import documents, api_keys

app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["API Keys"])
```

### 9.2 Update Frontend App.jsx

```jsx
const APIKeys = lazy(() => import('./pages/APIKeys'));

// Add route:
<Route path="/api-keys" element={
  <PrivateRoute roles={['admin']}>
    <Layout><APIKeys /></Layout>
  </PrivateRoute>
} />
```

### 9.3 Update Layout Navigation

Add to Tools section:
```javascript
{ path: '/api-keys', icon: '🔑', label: 'API Keys', roles: ['admin'] },
```

---

## PHASE 5 FINAL CHECKLIST

### AI Assistant
- [ ] NLP service with intent detection
- [ ] Multi-language support (EN/ES)
- [ ] Time period extraction
- [ ] Query sales, expenses, payments
- [ ] Query inventory, projects, clients
- [ ] Floating chat widget
- [ ] Conversation history
- [ ] Suggestions system

### Approval Workflows
- [ ] Configurable rules by amount
- [ ] Multi-level approvals
- [ ] Approve/Reject with comments
- [ ] Approval history
- [ ] Frontend page

### Recurring Transactions
- [ ] Multiple frequencies
- [ ] Next occurrence calculation
- [ ] Auto-generate or notify
- [ ] Preview occurrences
- [ ] Pause/Resume

### Budget Management
- [ ] Create budgets by category/project
- [ ] Auto-calculate spending
- [ ] Alert thresholds
- [ ] Variance analysis
- [ ] Summary dashboard

### Document Management
- [ ] File upload (PDF, images, docs)
- [ ] Entity attachments
- [ ] Categories
- [ ] Download/delete

### API Keys
- [ ] Generate secure keys
- [ ] Granular permissions
- [ ] Expiration dates
- [ ] Usage tracking
- [ ] Revoke/delete

---

## DEPLOYMENT

```bash
# Backend dependencies
cd backend
pip install python-dateutil

# Frontend build
cd frontend
npm run build

# Commit and push
git add .
git commit -m "feat: Phase 5 Complete - AI Assistant, Approvals, Recurring, Budgets, Docs, API Keys"
git push origin main
```

---

## NEW FILES SUMMARY - PHASE 5

### Backend (12 files)
```
services/
├── ai_assistant.py
├── approval_service.py
├── recurring_service.py
├── budget_service.py
├── document_service.py
└── api_key_service.py

routes/
├── assistant.py
├── approvals.py
├── recurring.py
├── budgets.py
├── documents.py
└── api_keys.py
```

### Frontend (10+ files)
```
pages/
├── Approvals.jsx
├── RecurringItems.jsx
├── Budgets.jsx
├── APIKeys.jsx

components/
├── AIAssistant.jsx
├── DocumentUploader.jsx
├── DocumentList.jsx
```

---

🎉 **LogiAccounting Pro Phase 5 Complete!**

La plataforma ahora incluye:
- 🤖 AI Chat Assistant con NLP
- ✅ Approval Workflows multi-nivel
- 🔄 Recurring Transactions automation
- 💰 Budget Management & Variance
- 📎 Document Management
- 🔑 API Keys para integraciones

**Total Features: 50+**
**Lines of Code: ~25,000+**
