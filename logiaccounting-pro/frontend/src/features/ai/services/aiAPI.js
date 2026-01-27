/**
 * AI API Service
 * API calls for AI/ML features
 */

import api from '../../../services/api';

export const aiAPI = {
  // ==================== Cash Flow ====================

  async trainCashFlowModel(data) {
    const response = await api.post('/ai/cashflow/train', data);
    return response.data;
  },

  async getCashFlowForecast(params) {
    const response = await api.post('/ai/cashflow/forecast', params);
    return response.data;
  },

  async getCashFlowStatus() {
    const response = await api.get('/ai/cashflow/status');
    return response.data;
  },

  // ==================== OCR ====================

  async processDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/ai/ocr/process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async batchProcessDocuments(files) {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    const response = await api.post('/ai/ocr/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async getProcessedDocuments(limit = 50) {
    const response = await api.get(`/ai/ocr/documents?limit=${limit}`);
    return response.data;
  },

  async getDocument(documentId) {
    const response = await api.get(`/ai/ocr/documents/${documentId}`);
    return response.data;
  },

  async updateDocument(documentId, updates) {
    const response = await api.put(`/ai/ocr/documents/${documentId}`, updates);
    return response.data;
  },

  async approveDocument(documentId) {
    const response = await api.post(`/ai/ocr/documents/${documentId}/approve`);
    return response.data;
  },

  // ==================== Assistant ====================

  async chatWithAssistant(params) {
    const response = await api.post('/ai/assistant/chat', params);
    return response.data;
  },

  async getQuickInsights() {
    const response = await api.get('/ai/assistant/insights');
    return response.data;
  },

  async analyzeEntity(params) {
    const response = await api.post('/ai/assistant/analyze', params);
    return response.data;
  },

  async getConversations(limit = 10) {
    const response = await api.get(`/ai/assistant/conversations?limit=${limit}`);
    return response.data;
  },

  async getConversation(conversationId) {
    const response = await api.get(`/ai/assistant/conversations/${conversationId}`);
    return response.data;
  },

  async deleteConversation(conversationId) {
    const response = await api.delete(`/ai/assistant/conversations/${conversationId}`);
    return response.data;
  },

  async getAssistantSuggestions(query) {
    const response = await api.get(`/ai/assistant/suggestions?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  // ==================== Anomaly Detection ====================

  async trainAnomalyModels(data) {
    const response = await api.post('/ai/anomaly/train', data);
    return response.data;
  },

  async analyzeTransaction(transaction) {
    const response = await api.post('/ai/anomaly/analyze', { transaction });
    return response.data;
  },

  async batchAnalyzeTransactions(transactions) {
    const response = await api.post('/ai/anomaly/batch-analyze', transactions);
    return response.data;
  },

  async getAnomalyAlerts(params = {}) {
    const queryParams = new URLSearchParams();
    if (params.status) queryParams.append('status', params.status);
    if (params.severity) queryParams.append('severity', params.severity);
    if (params.limit) queryParams.append('limit', params.limit);

    const response = await api.get(`/ai/anomaly/alerts?${queryParams}`);
    return response.data;
  },

  async getAnomalySummary() {
    const response = await api.get('/ai/anomaly/alerts/summary');
    return response.data;
  },

  async acknowledgeAlert(alertId) {
    const response = await api.post(`/ai/anomaly/alerts/${alertId}/acknowledge`);
    return response.data;
  },

  async resolveAlert(alertId, params = {}) {
    const response = await api.post(`/ai/anomaly/alerts/${alertId}/resolve`, params);
    return response.data;
  },

  async dismissAlert(alertId, params = {}) {
    const response = await api.post(`/ai/anomaly/alerts/${alertId}/dismiss`, params);
    return response.data;
  },
};

export default aiAPI;
