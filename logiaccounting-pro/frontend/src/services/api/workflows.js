/**
 * Workflow API Service
 */

import axios from 'axios';

const API_BASE = '/api/v1/workflows';

export const workflowAPI = {
  // Workflows
  listWorkflows: (params = {}) => axios.get(`${API_BASE}`, { params }),
  getWorkflow: (id) => axios.get(`${API_BASE}/${id}`),
  createWorkflow: (data) => axios.post(`${API_BASE}`, data),
  updateWorkflow: (id, data) => axios.put(`${API_BASE}/${id}`, data),
  deleteWorkflow: (id) => axios.delete(`${API_BASE}/${id}`),
  activateWorkflow: (id) => axios.post(`${API_BASE}/${id}/activate`),
  deactivateWorkflow: (id) => axios.post(`${API_BASE}/${id}/deactivate`),
  triggerWorkflow: (id, data = {}) => axios.post(`${API_BASE}/${id}/trigger`, data),

  // Executions
  listExecutions: (params = {}) => axios.get(`${API_BASE}/executions`, { params }),
  getActiveExecutions: (params = {}) => axios.get(`${API_BASE}/executions/active`, { params }),
  getExecution: (id) => axios.get(`${API_BASE}/executions/${id}`),
  getExecutionTimeline: (id) => axios.get(`${API_BASE}/executions/${id}/timeline`),
  cancelExecution: (id) => axios.post(`${API_BASE}/executions/${id}/cancel`),
  retryExecution: (id) => axios.post(`${API_BASE}/executions/${id}/retry`),
  getDashboardStats: (params = {}) => axios.get(`${API_BASE}/executions/dashboard`, { params }),
  getWorkflowStats: (id, params = {}) => axios.get(`${API_BASE}/executions/workflows/${id}/stats`, { params }),

  // Versions
  listVersions: (id, params = {}) => axios.get(`${API_BASE}/${id}/versions`, { params }),
  getVersion: (id, version) => axios.get(`${API_BASE}/${id}/versions/${version}`),
  createVersion: (id, data = {}) => axios.post(`${API_BASE}/${id}/versions`, data),
  rollbackVersion: (id, version) => axios.post(`${API_BASE}/${id}/versions/${version}/rollback`),
  compareVersions: (id, params) => axios.get(`${API_BASE}/${id}/versions/compare`, { params }),

  // Dead Letter Queue
  listDeadLetter: (params = {}) => axios.get(`${API_BASE}/dead-letter`, { params }),
  getDeadLetterStats: (params = {}) => axios.get(`${API_BASE}/dead-letter/stats`, { params }),
  getDeadLetterEntry: (id) => axios.get(`${API_BASE}/dead-letter/${id}`),
  retryDeadLetter: (id) => axios.post(`${API_BASE}/dead-letter/${id}/retry`),
  resolveDeadLetter: (id, data = {}) => axios.post(`${API_BASE}/dead-letter/${id}/resolve`, data),
  ignoreDeadLetter: (id, data = {}) => axios.post(`${API_BASE}/dead-letter/${id}/ignore`, data),

  // Templates
  listTemplates: (params = {}) => axios.get(`${API_BASE}/templates`, { params }),
  getTemplateCategories: () => axios.get(`${API_BASE}/templates/categories`),
  getTemplate: (id) => axios.get(`${API_BASE}/templates/${id}`),
  previewTemplate: (id) => axios.get(`${API_BASE}/templates/${id}/preview`),
  installTemplate: (id, data = {}) => axios.post(`${API_BASE}/templates/${id}/install`, data),
  publishTemplate: (data) => axios.post(`${API_BASE}/templates/publish`, data),
  rateTemplate: (id, data) => axios.post(`${API_BASE}/templates/${id}/rate`, data),

  // AI
  getSuggestions: () => axios.get(`${API_BASE}/templates/suggestions`),
  fromDescription: (data) => axios.post(`${API_BASE}/templates/from-description`, data),
  explainWorkflow: (data) => axios.post(`${API_BASE}/templates/explain`, data),

  // CRM Workflows
  getCRMEvents: () => axios.get(`${API_BASE}/crm/events`),
  getCRMActions: () => axios.get(`${API_BASE}/crm/actions`),
  getCRMConditionTemplates: (params = {}) => axios.get(`${API_BASE}/crm/conditions/templates`, { params }),
  getCRMWorkflowTemplates: () => axios.get(`${API_BASE}/crm/templates`),
  getThresholdMetrics: () => axios.get(`${API_BASE}/thresholds/metrics`),
};
