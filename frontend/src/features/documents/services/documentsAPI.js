/**
 * Documents API Service
 */
import api from '../../../services/api';

const documentsAPI = {
  // Documents
  upload: (formData) => api.post('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),

  getDocuments: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page);
    if (params.pageSize) queryParams.append('page_size', params.pageSize);
    if (params.search) queryParams.append('search', params.search);
    if (params.documentType) queryParams.append('document_type', params.documentType);
    if (params.status) queryParams.append('status', params.status);
    if (params.categoryId) queryParams.append('category_id', params.categoryId);
    if (params.folderId) queryParams.append('folder_id', params.folderId);
    return api.get(`/documents?${queryParams}`);
  },

  getDocument: (id) => api.get(`/documents/${id}`),
  updateDocument: (id, data) => api.put(`/documents/${id}`, data),
  deleteDocument: (id, permanent = false) => 
    api.delete(`/documents/${id}?permanent=${permanent}`),
  downloadDocument: (id) => api.get(`/documents/${id}/download`, { responseType: 'blob' }),

  uploadNewVersion: (id, formData) => api.post(`/documents/${id}/versions`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getVersions: (id) => api.get(`/documents/${id}/versions`),

  getCategories: () => api.get('/documents/categories/list'),
  createCategory: (data) => api.post('/documents/categories', data),

  getDocumentTypes: () => api.get('/documents/types/list'),

  // Folders
  createFolder: (data) => api.post('/folders', data),
  getFolders: (parentId = null) => {
    const params = parentId ? `?parent_id=${parentId}` : '';
    return api.get(`/folders${params}`);
  },
  getFolderTree: () => api.get('/folders/tree'),
  getFolder: (id) => api.get(`/folders/${id}`),
  getFolderContents: (id, page = 1) => api.get(`/folders/${id}/contents?page=${page}`),
  updateFolder: (id, data) => api.put(`/folders/${id}`, data),
  deleteFolder: (id, recursive = false) => 
    api.delete(`/folders/${id}?recursive=${recursive}`),
  moveFolder: (id, newParentId) => 
    api.post(`/folders/${id}/move?new_parent_id=${newParentId || ''}`),
  addDocumentToFolder: (folderId, documentId) => 
    api.post(`/folders/${folderId}/documents/${documentId}`),
  removeDocumentFromFolder: (folderId, documentId) => 
    api.delete(`/folders/${folderId}/documents/${documentId}`),

  // Sharing
  shareDocument: (documentId, data) => api.post(`/documents/${documentId}/share`, data),
  getShares: (documentId) => api.get(`/documents/${documentId}/shares`),
  revokeShare: (shareId) => api.delete(`/documents/shares/${shareId}`),
  createShareLink: (documentId, data) => api.post(`/documents/${documentId}/share-link`, data),
  getShareLinks: (documentId) => api.get(`/documents/${documentId}/share-links`),
  revokeShareLink: (linkId) => api.delete(`/documents/share-links/${linkId}`),
  getAccessLogs: (documentId) => api.get(`/documents/${documentId}/access-logs`)
};

export default documentsAPI;
