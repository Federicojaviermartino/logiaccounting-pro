/**
 * Audit Trail API Service
 */
import api from '../../../services/api';

const auditAPI = {
  // Audit Logs
  getLogs: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page);
    if (params.pageSize) queryParams.append('page_size', params.pageSize);
    if (params.startDate) queryParams.append('start_date', params.startDate);
    if (params.endDate) queryParams.append('end_date', params.endDate);
    if (params.userId) queryParams.append('user_id', params.userId);
    if (params.action) queryParams.append('action', params.action);
    if (params.severity) queryParams.append('severity', params.severity);
    if (params.resourceType) queryParams.append('resource_type', params.resourceType);
    if (params.search) queryParams.append('search', params.search);
    return api.get(`/audit/logs?${queryParams}`);
  },

  getLogById: (logId) => api.get(`/audit/logs/${logId}`),

  getEntityHistory: (resourceType, resourceId) => 
    api.get(`/audit/entity/${resourceType}/${resourceId}/history`),

  getUserActivity: (userId, days = 30) => 
    api.get(`/audit/user/${userId}/activity?days=${days}`),

  getSummary: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.startDate) queryParams.append('start_date', params.startDate);
    if (params.endDate) queryParams.append('end_date', params.endDate);
    return api.get(`/audit/summary?${queryParams}`);
  },

  getActions: () => api.get('/audit/actions'),
  getResourceTypes: () => api.get('/audit/resource-types'),

  // Compliance
  getDashboard: () => api.get('/compliance/dashboard'),

  getRetentionPolicies: () => api.get('/compliance/retention-policies'),
  createRetentionPolicy: (data) => api.post('/compliance/retention-policies', data),

  getRules: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.standard) queryParams.append('standard', params.standard);
    if (params.category) queryParams.append('category', params.category);
    return api.get(`/compliance/rules?${queryParams}`);
  },
  createRule: (data) => api.post('/compliance/rules', data),

  getViolations: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page);
    if (params.status) queryParams.append('status', params.status);
    if (params.severity) queryParams.append('severity', params.severity);
    return api.get(`/compliance/violations?${queryParams}`);
  },
  resolveViolation: (violationId, data) => 
    api.put(`/compliance/violations/${violationId}/resolve`, data),

  getAccessLogs: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page);
    if (params.containsPii) queryParams.append('contains_pii', params.containsPii);
    return api.get(`/compliance/access-logs?${queryParams}`);
  },

  getAccessReport: (startDate, endDate) => {
    const queryParams = new URLSearchParams();
    if (startDate) queryParams.append('start_date', startDate);
    if (endDate) queryParams.append('end_date', endDate);
    return api.get(`/compliance/access-report?${queryParams}`);
  },

  getStandards: () => api.get('/compliance/standards')
};

export default auditAPI;
