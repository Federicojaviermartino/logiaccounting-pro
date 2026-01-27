/**
 * Audit & Compliance API Service
 * Phase 15 - Enterprise Audit Trail, Compliance & Regulatory Framework
 */

import api from './api';

// ==================== Audit Logs ====================

export const auditLogsAPI = {
  // List audit logs with filters
  getLogs: (params) => api.get('/api/v1/audit/logs', { params }),

  // Get single log entry
  getLog: (logId) => api.get(`/api/v1/audit/logs/${logId}`),

  // Get entity audit trail
  getEntityTrail: (entityType, entityId, limit = 100) =>
    api.get(`/api/v1/audit/logs/entity/${entityType}/${entityId}`, { params: { limit } }),

  // Get user activity
  getUserTrail: (userId, days = 30, limit = 200) =>
    api.get(`/api/v1/audit/logs/user/${userId}`, { params: { days, limit } }),

  // Get event types
  getEventTypes: (category) =>
    api.get('/api/v1/audit/event-types', { params: { category } }),

  // Get statistics
  getStatistics: (days = 30) =>
    api.get('/api/v1/audit/statistics', { params: { days } }),

  // Export logs
  exportLogs: (format, filters) =>
    api.post('/api/v1/audit/export', { format, filters }, {
      responseType: format !== 'json' ? 'blob' : 'json'
    }),
};

// ==================== Change History ====================

export const changeHistoryAPI = {
  // Get entity change history
  getHistory: (entityType, entityId, limit = 50) =>
    api.get(`/api/v1/audit/changes/${entityType}/${entityId}`, { params: { limit } }),

  // Get version diff
  getDiff: (entityType, entityId, v1, v2) =>
    api.get(`/api/v1/audit/changes/${entityType}/${entityId}/diff`, { params: { v1, v2 } }),

  // Get specific version
  getVersion: (entityType, entityId, version) =>
    api.get(`/api/v1/audit/changes/${entityType}/${entityId}/version/${version}`),
};

// ==================== Integrity ====================

export const integrityAPI = {
  // Get integrity status
  getStatus: () => api.get('/api/v1/audit/integrity/status'),

  // Verify chain integrity
  verify: (startSequence, endSequence) =>
    api.post('/api/v1/audit/integrity/verify', {
      start_sequence: startSequence,
      end_sequence: endSequence
    }),
};

// ==================== Alerts ====================

export const alertsAPI = {
  // List alerts
  getAlerts: (params) => api.get('/api/v1/audit/alerts', { params }),

  // Get single alert
  getAlert: (alertId) => api.get(`/api/v1/audit/alerts/${alertId}`),

  // Acknowledge alert
  acknowledge: (alertId) => api.put(`/api/v1/audit/alerts/${alertId}/acknowledge`),

  // Resolve alert
  resolve: (alertId, notes) =>
    api.put(`/api/v1/audit/alerts/${alertId}/resolve`, { notes }),

  // Dismiss alert
  dismiss: (alertId, notes) =>
    api.put(`/api/v1/audit/alerts/${alertId}/dismiss`, { notes }),
};

// ==================== Alert Rules ====================

export const alertRulesAPI = {
  // List rules
  getRules: (isActive) =>
    api.get('/api/v1/audit/alert-rules', { params: { is_active: isActive } }),

  // Create rule
  createRule: (data) => api.post('/api/v1/audit/alert-rules', data),

  // Update rule
  updateRule: (ruleId, data) => api.put(`/api/v1/audit/alert-rules/${ruleId}`, data),

  // Delete rule
  deleteRule: (ruleId) => api.delete(`/api/v1/audit/alert-rules/${ruleId}`),
};

// ==================== Retention Policies ====================

export const retentionAPI = {
  // List policies
  getPolicies: () => api.get('/api/v1/audit/retention-policies'),

  // Create policy
  createPolicy: (data) => api.post('/api/v1/audit/retention-policies', data),

  // Update policy
  updatePolicy: (policyId, data) =>
    api.put(`/api/v1/audit/retention-policies/${policyId}`, data),

  // Delete policy
  deletePolicy: (policyId) => api.delete(`/api/v1/audit/retention-policies/${policyId}`),
};

// ==================== Reports ====================

export const auditReportsAPI = {
  // List available reports
  getReportTypes: () => api.get('/api/v1/audit/reports'),

  // Generate report
  generateReport: (reportType, parameters, format = 'json') =>
    api.post('/api/v1/audit/reports/generate',
      { report_type: reportType, parameters, format },
      { responseType: format !== 'json' ? 'blob' : 'json' }
    ),
};

// ==================== Compliance ====================

export const complianceAPI = {
  // List frameworks
  getFrameworks: () => api.get('/api/v1/compliance/frameworks'),

  // Get framework status
  getFrameworkStatus: (frameworkId) =>
    api.get(`/api/v1/compliance/frameworks/${frameworkId}`),

  // Run compliance check
  runCheck: (frameworkId) =>
    api.post(`/api/v1/compliance/frameworks/${frameworkId}/run`),

  // Get dashboard
  getDashboard: () => api.get('/api/v1/compliance/dashboard'),

  // Get summary
  getSummary: () => api.get('/api/v1/compliance/dashboard/summary'),

  // Get control details
  getControl: (frameworkId, controlId) =>
    api.get(`/api/v1/compliance/controls/${frameworkId}/${controlId}`),

  // Get compliance history
  getHistory: (frameworkId, limit = 50) =>
    api.get('/api/v1/compliance/history', { params: { framework_id: frameworkId, limit } }),

  // Get violations
  getViolations: (params) => api.get('/api/v1/compliance/violations', { params }),

  // Generate compliance report
  generateReport: (frameworkId, format = 'json', includeEvidence = true) =>
    api.get(`/api/v1/compliance/reports/${frameworkId}`, {
      params: { format, include_evidence: includeEvidence },
      responseType: format !== 'json' ? 'blob' : 'json'
    }),

  // Get settings
  getSettings: () => api.get('/api/v1/compliance/settings'),

  // Update settings
  updateSettings: (settings) => api.put('/api/v1/compliance/settings', settings),
};

// ==================== SOX Specific ====================

export const soxAPI = {
  getControls: () => api.get('/api/v1/compliance/sox/controls'),
};

// ==================== GDPR Specific ====================

export const gdprAPI = {
  getControls: () => api.get('/api/v1/compliance/gdpr/controls'),
  getDataSubjectRequests: (params) =>
    api.get('/api/v1/compliance/gdpr/data-subjects', { params }),
  completeRequest: (requestId, notes) =>
    api.post(`/api/v1/compliance/gdpr/data-subjects/${requestId}/complete`, { notes }),
};

// ==================== SOC 2 Specific ====================

export const soc2API = {
  getControls: () => api.get('/api/v1/compliance/soc2/controls'),
};

// Combined export
const auditApi = {
  logs: auditLogsAPI,
  changes: changeHistoryAPI,
  integrity: integrityAPI,
  alerts: alertsAPI,
  alertRules: alertRulesAPI,
  retention: retentionAPI,
  reports: auditReportsAPI,
  compliance: complianceAPI,
  sox: soxAPI,
  gdpr: gdprAPI,
  soc2: soc2API,
};

export default auditApi;
