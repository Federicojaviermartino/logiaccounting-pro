/**
 * Documents API Service - Phase 13
 * Client for document management endpoints
 */

import api from './api';

export const documentsApi = {
  /**
   * Upload a document
   * @param {File} file - File to upload
   * @param {Object} options - Upload options
   * @returns {Promise<Object>} Upload result
   */
  async upload(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);

    if (options.name) {
      formData.append('name', options.name);
    }
    if (options.documentType) {
      formData.append('document_type', options.documentType);
    }
    if (options.categoryId) {
      formData.append('category_id', options.categoryId);
    }
    if (options.description) {
      formData.append('description', options.description);
    }
    if (options.tags?.length) {
      formData.append('tags', options.tags.join(','));
    }
    if (options.relatedEntityType) {
      formData.append('related_entity_type', options.relatedEntityType);
    }
    if (options.relatedEntityId) {
      formData.append('related_entity_id', options.relatedEntityId);
    }

    const response = await api.post('/documents-v2/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const progress = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        options.onProgress?.(progress);
      },
    });

    return response.data;
  },

  /**
   * Upload new version
   * @param {string} documentId - Document ID
   * @param {File} file - File to upload
   * @param {string} changeNotes - Change notes
   * @returns {Promise<Object>} Upload result
   */
  async uploadVersion(documentId, file, changeNotes) {
    const formData = new FormData();
    formData.append('file', file);
    if (changeNotes) {
      formData.append('change_notes', changeNotes);
    }

    const response = await api.post(`/documents-v2/${documentId}/version`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  /**
   * List documents
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Documents list with pagination
   */
  async list(params = {}) {
    const response = await api.get('/documents-v2', { params });
    return response.data;
  },

  /**
   * Get document by ID
   * @param {string} documentId - Document ID
   * @returns {Promise<Object>} Document details
   */
  async get(documentId) {
    const response = await api.get(`/documents-v2/${documentId}`);
    return response.data.document;
  },

  /**
   * Update document metadata
   * @param {string} documentId - Document ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>} Updated document
   */
  async update(documentId, data) {
    const response = await api.put(`/documents-v2/${documentId}`, data);
    return response.data.document;
  },

  /**
   * Delete document
   * @param {string} documentId - Document ID
   * @param {boolean} permanent - Permanent deletion
   * @returns {Promise<void>}
   */
  async delete(documentId, permanent = false) {
    await api.delete(`/documents-v2/${documentId}`, {
      params: { permanent },
    });
  },

  /**
   * Restore deleted document
   * @param {string} documentId - Document ID
   * @returns {Promise<Object>} Restored document
   */
  async restore(documentId) {
    const response = await api.post(`/documents-v2/${documentId}/restore`);
    return response.data.document;
  },

  /**
   * Get download URL
   * @param {string} documentId - Document ID
   * @param {number} version - Version number (optional)
   * @returns {Promise<string>} Download URL
   */
  async getDownloadUrl(documentId, version = null) {
    const params = version ? { version } : {};
    const response = await api.get(`/documents-v2/${documentId}/download-url`, { params });
    return response.data.download_url;
  },

  /**
   * Get document versions
   * @param {string} documentId - Document ID
   * @returns {Promise<Object[]>} Version list
   */
  async getVersions(documentId) {
    const response = await api.get(`/documents-v2/${documentId}/versions`);
    return response.data.versions;
  },

  /**
   * Search documents
   * @param {Object} params - Search parameters
   * @returns {Promise<Object>} Search results
   */
  async search(params) {
    const response = await api.get('/documents-v2/search', { params });
    return response.data.data;
  },

  /**
   * Get search suggestions
   * @param {string} query - Search prefix
   * @returns {Promise<string[]>} Suggestions
   */
  async suggest(query) {
    const response = await api.get('/documents-v2/search/suggest', {
      params: { q: query },
    });
    return response.data.suggestions;
  },

  /**
   * Create share link
   * @param {string} documentId - Document ID
   * @param {Object} options - Share options
   * @returns {Promise<Object>} Share details
   */
  async createShareLink(documentId, options = {}) {
    const response = await api.post(`/documents-v2/${documentId}/share`, options);
    return response.data.share;
  },

  /**
   * Share with user
   * @param {string} documentId - Document ID
   * @param {Object} data - Share data
   * @returns {Promise<Object>} Share details
   */
  async shareWithUser(documentId, data) {
    const response = await api.post(`/documents-v2/${documentId}/share/user`, data);
    return response.data.share;
  },

  /**
   * Get shares
   * @param {string} documentId - Document ID
   * @returns {Promise<Object[]>} Shares list
   */
  async getShares(documentId) {
    const response = await api.get(`/documents-v2/${documentId}/shares`);
    return response.data.shares;
  },

  /**
   * Revoke share
   * @param {string} documentId - Document ID
   * @param {string} shareId - Share ID
   * @returns {Promise<void>}
   */
  async revokeShare(documentId, shareId) {
    await api.delete(`/documents-v2/${documentId}/shares/${shareId}`);
  },

  /**
   * Get comments
   * @param {string} documentId - Document ID
   * @returns {Promise<Object[]>} Comments list
   */
  async getComments(documentId) {
    const response = await api.get(`/documents-v2/${documentId}/comments`);
    return response.data.comments;
  },

  /**
   * Add comment
   * @param {string} documentId - Document ID
   * @param {Object} data - Comment data
   * @returns {Promise<Object>} Created comment
   */
  async addComment(documentId, data) {
    const response = await api.post(`/documents-v2/${documentId}/comments`, data);
    return response.data.comment;
  },

  /**
   * Resolve comment
   * @param {string} documentId - Document ID
   * @param {string} commentId - Comment ID
   * @returns {Promise<Object>} Resolved comment
   */
  async resolveComment(documentId, commentId) {
    const response = await api.post(`/documents-v2/${documentId}/comments/${commentId}/resolve`);
    return response.data.comment;
  },

  /**
   * Get activity log
   * @param {string} documentId - Document ID
   * @returns {Promise<Object[]>} Activity log
   */
  async getActivity(documentId) {
    const response = await api.get(`/documents-v2/${documentId}/activity`);
    return response.data.activity;
  },

  /**
   * Run OCR
   * @param {string} documentId - Document ID
   * @returns {Promise<Object>} OCR result
   */
  async runOcr(documentId) {
    const response = await api.post(`/documents-v2/${documentId}/ocr`);
    return response.data;
  },

  /**
   * Extract data with AI
   * @param {string} documentId - Document ID
   * @param {string} documentType - Document type hint
   * @returns {Promise<Object>} Extraction result
   */
  async extractData(documentId, documentType = null) {
    const response = await api.post(`/documents-v2/${documentId}/extract`, null, {
      params: documentType ? { document_type: documentType } : {},
    });
    return response.data;
  },

  /**
   * Classify document
   * @param {string} documentId - Document ID
   * @returns {Promise<Object>} Classification result
   */
  async classifyDocument(documentId) {
    const response = await api.post(`/documents-v2/${documentId}/classify`);
    return response.data;
  },

  /**
   * Get categories
   * @returns {Promise<Object[]>} Categories list
   */
  async getCategories() {
    const response = await api.get('/documents-v2/categories');
    return response.data.categories;
  },

  /**
   * Get category tree
   * @returns {Promise<Object[]>} Category tree
   */
  async getCategoryTree() {
    const response = await api.get('/documents-v2/categories/tree');
    return response.data.tree;
  },

  /**
   * Create category
   * @param {Object} data - Category data
   * @returns {Promise<Object>} Created category
   */
  async createCategory(data) {
    const response = await api.post('/documents-v2/categories', data);
    return response.data.category;
  },

  /**
   * Get tags
   * @returns {Promise<Object[]>} Tags list
   */
  async getTags() {
    const response = await api.get('/documents-v2/tags');
    return response.data.tags;
  },

  /**
   * Create tag
   * @param {Object} data - Tag data
   * @returns {Promise<Object>} Created tag
   */
  async createTag(data) {
    const response = await api.post('/documents-v2/tags', data);
    return response.data.tag;
  },

  /**
   * Get storage stats
   * @returns {Promise<Object>} Storage statistics
   */
  async getStats() {
    const response = await api.get('/documents-v2/stats');
    return response.data;
  },
};

// Signatures API
export const signaturesApi = {
  /**
   * Create signature request
   * @param {Object} data - Request data
   * @returns {Promise<Object>} Signature request
   */
  async createRequest(data) {
    const response = await api.post('/signatures/requests', data);
    return response.data.request;
  },

  /**
   * Send signature request
   * @param {string} requestId - Request ID
   * @returns {Promise<Object>} Send result
   */
  async sendRequest(requestId) {
    const response = await api.post(`/signatures/requests/${requestId}/send`);
    return response.data;
  },

  /**
   * List signature requests
   * @param {Object} params - Query params
   * @returns {Promise<Object>} Requests list
   */
  async listRequests(params = {}) {
    const response = await api.get('/signatures/requests', { params });
    return response.data;
  },

  /**
   * Get signature request
   * @param {string} requestId - Request ID
   * @returns {Promise<Object>} Request details
   */
  async getRequest(requestId) {
    const response = await api.get(`/signatures/requests/${requestId}`);
    return response.data.request;
  },

  /**
   * Cancel signature request
   * @param {string} requestId - Request ID
   * @returns {Promise<Object>} Cancel result
   */
  async cancelRequest(requestId) {
    const response = await api.post(`/signatures/requests/${requestId}/cancel`);
    return response.data;
  },

  /**
   * Verify signatures
   * @param {string} requestId - Request ID
   * @returns {Promise<Object>} Verification result
   */
  async verifySignatures(requestId) {
    const response = await api.get(`/signatures/requests/${requestId}/verify`);
    return response.data;
  },

  /**
   * Get signing document (public)
   * @param {string} accessToken - Access token
   * @returns {Promise<Object>} Signing info
   */
  async getSigningDocument(accessToken) {
    const response = await api.get(`/signatures/sign/${accessToken}`);
    return response.data;
  },

  /**
   * Sign document (public)
   * @param {string} accessToken - Access token
   * @param {string} signatureData - Base64 signature
   * @returns {Promise<Object>} Sign result
   */
  async signDocument(accessToken, signatureData) {
    const response = await api.post(`/signatures/sign/${accessToken}`, {
      signature_data: signatureData,
    });
    return response.data;
  },

  /**
   * Decline signature (public)
   * @param {string} accessToken - Access token
   * @param {string} reason - Decline reason
   * @returns {Promise<Object>} Decline result
   */
  async declineSignature(accessToken, reason = null) {
    const response = await api.post(`/signatures/sign/${accessToken}/decline`, {
      reason,
    });
    return response.data;
  },
};

export default documentsApi;
