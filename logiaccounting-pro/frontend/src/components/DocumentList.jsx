import { useState, useEffect } from 'react';
import { documentsAPI } from '../services/api';

export default function DocumentList({ entityType, entityId, onDelete }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [previewDoc, setPreviewDoc] = useState(null);

  useEffect(() => {
    if (entityType && entityId) {
      loadDocuments();
    }
  }, [entityType, entityId]);

  const loadDocuments = async () => {
    try {
      const response = await documentsAPI.getByEntity(entityType, entityId);
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (doc) => {
    try {
      const response = await documentsAPI.download(doc.id);
      const blob = new Blob([response.data], { type: doc.mime_type });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      alert('Failed to download document');
    }
  };

  const handleDelete = async (docId) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await documentsAPI.delete(docId);
      setDocuments(documents.filter(d => d.id !== docId));
      if (onDelete) onDelete(docId);
    } catch (error) {
      alert('Failed to delete document');
    }
  };

  const getFileIcon = (mimeType) => {
    if (mimeType?.includes('pdf')) return '📄';
    if (mimeType?.includes('image')) return '🖼️';
    if (mimeType?.includes('word') || mimeType?.includes('document')) return '📝';
    if (mimeType?.includes('sheet') || mimeType?.includes('excel')) return '📊';
    return '📎';
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="text-center py-4">
        <div className="loading-spinner mx-auto"></div>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <p className="text-muted text-center py-4">No documents attached</p>
    );
  }

  return (
    <>
      <div className="document-list">
        {documents.map((doc) => (
          <div key={doc.id} className="document-item">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{getFileIcon(doc.mime_type)}</span>
              <div className="flex-1 min-w-0">
                <p className="font-bold truncate" title={doc.filename}>
                  {doc.filename}
                </p>
                <p className="text-muted text-sm">
                  {formatFileSize(doc.size_bytes)} • {new Date(doc.uploaded_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              {doc.mime_type?.includes('image') && (
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => setPreviewDoc(doc)}
                >
                  Preview
                </button>
              )}
              <button
                className="btn btn-sm btn-primary"
                onClick={() => handleDownload(doc)}
              >
                Download
              </button>
              <button
                className="btn btn-sm btn-danger"
                onClick={() => handleDelete(doc.id)}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Image Preview Modal */}
      {previewDoc && (
        <div className="modal-overlay" onClick={() => setPreviewDoc(null)}>
          <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{previewDoc.filename}</h3>
              <button className="modal-close" onClick={() => setPreviewDoc(null)}>×</button>
            </div>
            <div className="modal-body text-center">
              <img
                src={`data:${previewDoc.mime_type};base64,${previewDoc.content_preview || ''}`}
                alt={previewDoc.filename}
                className="max-w-full max-h-96 mx-auto"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.parentNode.innerHTML = '<p class="text-muted">Preview not available</p>';
                }}
              />
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setPreviewDoc(null)}>
                Close
              </button>
              <button className="btn btn-primary" onClick={() => handleDownload(previewDoc)}>
                Download
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
