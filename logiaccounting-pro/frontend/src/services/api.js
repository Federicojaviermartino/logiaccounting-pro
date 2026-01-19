import axios from 'axios';

const api = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  login: (data) => api.post('/api/v1/auth/login', data),
  logout: () => api.post('/api/v1/auth/logout'),
  getMe: () => api.get('/api/v1/auth/me'),
  register: (data) => api.post('/api/v1/auth/register', data),
  updateProfile: (data) => api.put('/api/v1/auth/profile', data),
  changePassword: (data) => api.put('/api/v1/auth/password', data),
  getUsers: () => api.get('/api/v1/auth/users'),
  updateUserStatus: (id, status) => api.put(`/api/v1/auth/users/${id}/status`, { status })
};

// Inventory API
export const inventoryAPI = {
  getMaterials: (params) => api.get('/api/v1/inventory/materials', { params }),
  getMaterial: (id) => api.get(`/api/v1/inventory/materials/${id}`),
  createMaterial: (data) => api.post('/api/v1/inventory/materials', data),
  updateMaterial: (id, data) => api.put(`/api/v1/inventory/materials/${id}`, data),
  deleteMaterial: (id) => api.delete(`/api/v1/inventory/materials/${id}`),
  getCategories: (type) => api.get('/api/v1/inventory/categories', { params: { type } }),
  getLocations: () => api.get('/api/v1/inventory/locations')
};

// Projects API
export const projectsAPI = {
  getProjects: (params) => api.get('/api/v1/projects', { params }),
  getProject: (id) => api.get(`/api/v1/projects/${id}`),
  createProject: (data) => api.post('/api/v1/projects', data),
  updateProject: (id, data) => api.put(`/api/v1/projects/${id}`, data),
  deleteProject: (id) => api.delete(`/api/v1/projects/${id}`)
};

// Movements API
export const movementsAPI = {
  getMovements: (params) => api.get('/api/v1/movements', { params }),
  createMovement: (data) => api.post('/api/v1/movements', data),
  deleteMovement: (id) => api.delete(`/api/v1/movements/${id}`)
};

// Transactions API
export const transactionsAPI = {
  getTransactions: (params) => api.get('/api/v1/transactions', { params }),
  getTransaction: (id) => api.get(`/api/v1/transactions/${id}`),
  createTransaction: (data) => api.post('/api/v1/transactions', data),
  updateTransaction: (id, data) => api.put(`/api/v1/transactions/${id}`, data),
  deleteTransaction: (id) => api.delete(`/api/v1/transactions/${id}`)
};

// Payments API
export const paymentsAPI = {
  getPayments: (params) => api.get('/api/v1/payments', { params }),
  getPendingPayments: () => api.get('/api/v1/payments/pending'),
  createPayment: (data) => api.post('/api/v1/payments', data),
  updatePayment: (id, data) => api.put(`/api/v1/payments/${id}`, data),
  markAsPaid: (id, paidDate) => api.put(`/api/v1/payments/${id}/pay`, { paid_date: paidDate }),
  deletePayment: (id) => api.delete(`/api/v1/payments/${id}`)
};

// Notifications API
export const notificationsAPI = {
  getNotifications: (params) => api.get('/api/v1/notifications', { params }),
  getUnreadCount: () => api.get('/api/v1/notifications/count'),
  markAsRead: (id) => api.put(`/api/v1/notifications/${id}/read`),
  markAllAsRead: () => api.put('/api/v1/notifications/read-all')
};

// Reports API
export const reportsAPI = {
  getDashboard: () => api.get('/api/v1/reports/dashboard'),
  getCashFlow: (months) => api.get('/api/v1/reports/cash-flow', { params: { months } }),
  getExpensesByCategory: () => api.get('/api/v1/reports/expenses-by-category'),
  getProjectProfitability: () => api.get('/api/v1/reports/project-profitability'),
  getInventorySummary: () => api.get('/api/v1/reports/inventory-summary'),
  getPaymentSummary: () => api.get('/api/v1/reports/payment-summary')
};

// ============================================
// AI-POWERED FEATURES API
// ============================================

// OCR API - Smart Invoice Processing
export const ocrAPI = {
  processInvoice: (file, autoCreate = false) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v1/ocr/extract-and-create?auto_create=${autoCreate}&create_payment=false`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  extractOnly: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/v1/ocr/extract', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  createFromExtracted: (data) => api.post('/api/v1/ocr/create-from-extracted', data),
  getCategorySuggestions: (vendorName) =>
    api.get('/api/v1/ocr/categories/suggestions', { params: { vendor_name: vendorName } }),
  getStatus: () => api.get('/api/v1/ocr/status')
};

// Cash Flow Predictor API
export const cashflowAPI = {
  predict: (days = 90, includePending = true) =>
    api.get('/api/v1/cashflow/predict', {
      params: { days, include_pending: includePending }
    }),
  getSummary: () => api.get('/api/v1/cashflow/predict/summary'),
  getDailyPredictions: (days = 30, offset = 0) =>
    api.get('/api/v1/cashflow/predict/daily', { params: { days, offset } }),
  getInsights: () => api.get('/api/v1/cashflow/insights'),
  getRiskAssessment: () => api.get('/api/v1/cashflow/risk-assessment'),
  getStatus: () => api.get('/api/v1/cashflow/status')
};

// Anomaly Detection API
export const anomalyAPI = {
  runScan: () => api.get('/api/v1/anomaly/scan'),
  getSummary: () => api.get('/api/v1/anomaly/summary'),
  getByType: (type) => api.get(`/api/v1/anomaly/by-type/${type}`),
  getBySeverity: (severity) => api.get(`/api/v1/anomaly/by-severity/${severity}`),
  checkTransaction: (data) => api.post('/api/v1/anomaly/check-transaction', data),
  checkDuplicates: (invoiceNumber) =>
    api.get('/api/v1/anomaly/duplicates', { params: { invoice_number: invoiceNumber } }),
  analyzeVendor: (vendorId) => api.get(`/api/v1/anomaly/vendor/${vendorId}/analysis`),
  getStatus: () => api.get('/api/v1/anomaly/status')
};

// Payment Scheduler API
export const schedulerAPI = {
  optimize: (availableCash, strategy = 'balanced') =>
    api.get('/api/v1/scheduler/optimize', {
      params: { available_cash: availableCash, strategy }
    }),
  getSummary: () => api.get('/api/v1/scheduler/summary'),
  getDailySchedule: (days = 30) =>
    api.get('/api/v1/scheduler/daily', { params: { days } }),
  getPaymentInsights: (paymentId) => api.get(`/api/v1/scheduler/payment/${paymentId}/insights`),
  getUrgentPayments: () => api.get('/api/v1/scheduler/urgent'),
  getDiscountOpportunities: () => api.get('/api/v1/scheduler/discounts'),
  simulate: (data) => api.post('/api/v1/scheduler/simulate', data),
  getStatus: () => api.get('/api/v1/scheduler/status')
};

// Profitability Assistant API
export const assistantAPI = {
  query: (userQuery, conversationHistory = null) =>
    api.post('/api/v1/assistant/query', {
      query: userQuery,
      conversation_history: conversationHistory
    }),
  getSuggestions: (context = null) =>
    api.get('/api/v1/assistant/suggestions', { params: { context } }),
  getQuickInsights: () => api.get('/api/v1/assistant/quick-insights'),
  getStatus: () => api.get('/api/v1/assistant/status')
};

// Settings API
export const settingsAPI = {
  getUserPreferences: () => api.get('/api/v1/settings/user'),
  updateUserPreferences: (prefs) => api.put('/api/v1/settings/user', prefs),
  getSystemSettings: () => api.get('/api/v1/settings/system'),
  updateSystemSettings: (settings) => api.put('/api/v1/settings/system', settings),
  getAvailableOptions: () => api.get('/api/v1/settings/available-options')
};

// Activity Log API
export const activityAPI = {
  getActivities: (params) => api.get('/api/v1/activity', { params }),
  getStats: (days = 30) => api.get('/api/v1/activity/stats', { params: { days } }),
  getAvailableActions: () => api.get('/api/v1/activity/actions'),
  exportCSV: (params) => api.get('/api/v1/activity/export', { params, responseType: 'blob' })
};

// Bulk Operations API
export const bulkAPI = {
  getTemplate: (entity) => api.get(`/api/v1/bulk/template/${entity}`, { responseType: 'blob' }),
  importData: (entity, file, skipErrors = false) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v1/bulk/import/${entity}?skip_errors=${skipErrors}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  exportData: (entity, ids = null, format = 'csv') =>
    api.post(`/api/v1/bulk/export/${entity}?format=${format}`, ids, { responseType: 'blob' }),
  bulkDelete: (entity, ids) => api.post(`/api/v1/bulk/delete/${entity}`, { ids }),
  bulkUpdate: (entity, ids, updates) => api.post(`/api/v1/bulk/update/${entity}`, { ids, updates })
};

// Email Notifications API
export const emailAPI = {
  sendNotification: (data) => api.post('/api/v1/email/send', data),
  sendPaymentReminder: (paymentId) => api.post(`/api/v1/email/payment-reminder/${paymentId}`),
  sendLowStockAlert: (materialId) => api.post(`/api/v1/email/low-stock-alert/${materialId}`),
  getTemplates: () => api.get('/api/v1/email/templates'),
  getHistory: (params) => api.get('/api/v1/email/history', { params }),
  getStatus: () => api.get('/api/v1/email/status')
};

// Two-Factor Auth API
export const twoFactorAPI = {
  getStatus: () => api.get('/api/v1/2fa/status'),
  setup: () => api.post('/api/v1/2fa/setup'),
  verifySetup: (code) => api.post('/api/v1/2fa/verify-setup', { code }),
  disable: (code) => api.post('/api/v1/2fa/disable', { code }),
  verifyLogin: (email, code) => api.post('/api/v1/auth/verify-2fa', null, {
    params: { email, code }
  })
};

// Report Builder API
export const reportBuilderAPI = {
  getColumns: (type) => api.get(`/api/v1/report-builder/columns/${type}`),
  preview: (config, limit = 20) => api.post('/api/v1/report-builder/preview', config, {
    params: { limit }
  }),
  generate: (config, format = 'json') => api.post('/api/v1/report-builder/generate', config, {
    params: { format },
    responseType: format === 'csv' ? 'blob' : 'json'
  }),
  getTemplates: () => api.get('/api/v1/report-builder/templates'),
  saveTemplate: (template) => api.post('/api/v1/report-builder/templates', template),
  deleteTemplate: (id) => api.delete(`/api/v1/report-builder/templates/${id}`)
};

// Backup API
export const backupAPI = {
  create: (data) => api.post('/api/v1/backup/create', data),
  list: () => api.get('/api/v1/backup/list'),
  download: (id) => api.get(`/api/v1/backup/download/${id}`, { responseType: 'blob' }),
  delete: (id) => api.delete(`/api/v1/backup/${id}`),
  restore: (data) => api.post('/api/v1/backup/restore', data),
  restoreFromFile: (file, mode = 'merge') => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v1/backup/restore/upload?mode=${mode}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  }
};

// Webhook API
export const webhookAPI = {
  getEvents: () => api.get('/api/v1/webhooks/events'),
  list: () => api.get('/api/v1/webhooks'),
  create: (data) => api.post('/api/v1/webhooks', data),
  get: (id) => api.get(`/api/v1/webhooks/${id}`),
  update: (id, data) => api.put(`/api/v1/webhooks/${id}`, data),
  delete: (id) => api.delete(`/api/v1/webhooks/${id}`),
  test: (id) => api.post(`/api/v1/webhooks/${id}/test`),
  getLogs: (id, limit = 50) => api.get(`/api/v1/webhooks/${id}/logs`, { params: { limit } }),
  getAllLogs: (params) => api.get('/api/v1/webhooks/logs/all', { params })
};

// ============================================
// PHASE 5 - ENTERPRISE FEATURES API
// ============================================

// AI Chat Assistant API
export const chatAssistantAPI = {
  chat: (message, language = 'en') => api.post('/api/v1/assistant/chat', { message, language }),
  getHistory: (limit = 20) => api.get('/api/v1/assistant/history', { params: { limit } }),
  clearHistory: () => api.delete('/api/v1/assistant/history')
};

// Approvals API
export const approvalsAPI = {
  getPending: () => api.get('/api/v1/approvals/pending'),
  getMyRequests: () => api.get('/api/v1/approvals/my-requests'),
  get: (id) => api.get(`/api/v1/approvals/${id}`),
  approve: (id, comments = '') => api.post(`/api/v1/approvals/${id}/approve`, { comments }),
  reject: (id, comments) => api.post(`/api/v1/approvals/${id}/reject`, { comments }),
  getRules: () => api.get('/api/v1/approvals/rules'),
  createRule: (data) => api.post('/api/v1/approvals/rules', data),
  updateRule: (id, data) => api.put(`/api/v1/approvals/rules/${id}`, data),
  deleteRule: (id) => api.delete(`/api/v1/approvals/rules/${id}`)
};

// Recurring Transactions API
export const recurringAPI = {
  getAll: () => api.get('/api/v1/recurring'),
  get: (id) => api.get(`/api/v1/recurring/${id}`),
  create: (data) => api.post('/api/v1/recurring', data),
  update: (id, data) => api.put(`/api/v1/recurring/${id}`, data),
  delete: (id) => api.delete(`/api/v1/recurring/${id}`),
  pause: (id) => api.post(`/api/v1/recurring/${id}/pause`),
  resume: (id) => api.post(`/api/v1/recurring/${id}/resume`),
  preview: (id, count = 5) => api.get(`/api/v1/recurring/${id}/preview`, { params: { count } }),
  generateNow: (id) => api.post(`/api/v1/recurring/${id}/generate`)
};

// Budgets API
export const budgetsAPI = {
  getAll: () => api.get('/api/v1/budgets'),
  get: (id) => api.get(`/api/v1/budgets/${id}`),
  create: (data) => api.post('/api/v1/budgets', data),
  update: (id, data) => api.put(`/api/v1/budgets/${id}`, data),
  delete: (id) => api.delete(`/api/v1/budgets/${id}`),
  getSpending: (id) => api.get(`/api/v1/budgets/${id}/spending`),
  getVariance: () => api.get('/api/v1/budgets/variance/report')
};

// Documents API
export const documentsAPI = {
  upload: (entityType, entityId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v1/documents/upload/${entityType}/${entityId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  getByEntity: (entityType, entityId) => api.get(`/api/v1/documents/${entityType}/${entityId}`),
  download: (id) => api.get(`/api/v1/documents/download/${id}`, { responseType: 'blob' }),
  delete: (id) => api.delete(`/api/v1/documents/${id}`),
  search: (query) => api.get('/api/v1/documents/search', { params: { query } })
};

// API Keys API
export const apiKeysAPI = {
  list: () => api.get('/api/v1/api-keys'),
  get: (id) => api.get(`/api/v1/api-keys/${id}`),
  create: (data) => api.post('/api/v1/api-keys', data),
  getPermissions: () => api.get('/api/v1/api-keys/permissions'),
  updatePermissions: (id, permissions) => api.put(`/api/v1/api-keys/${id}/permissions`, { permissions }),
  revoke: (id) => api.post(`/api/v1/api-keys/${id}/revoke`),
  delete: (id) => api.delete(`/api/v1/api-keys/${id}`)
};

// ============================================
// PHASE 6 - ULTIMATE ENTERPRISE FEATURES API
// ============================================

// Dashboard Builder API
export const dashboardAPI = {
  list: () => api.get('/api/v1/dashboards'),
  get: (id) => api.get(`/api/v1/dashboards/${id}`),
  create: (data) => api.post('/api/v1/dashboards', data),
  update: (id, data) => api.put(`/api/v1/dashboards/${id}`, data),
  delete: (id) => api.delete(`/api/v1/dashboards/${id}`),
  setDefault: (id) => api.post(`/api/v1/dashboards/${id}/default`),
  duplicate: (id) => api.post(`/api/v1/dashboards/${id}/duplicate`),
  share: (id, data) => api.post(`/api/v1/dashboards/${id}/share`, data),
  getShared: () => api.get('/api/v1/dashboards/shared'),
  getTemplates: () => api.get('/api/v1/dashboards/templates'),
  createFromTemplate: (templateId) => api.post(`/api/v1/dashboards/templates/${templateId}/create`),
  getWidgetData: (widgetType, config) => api.post('/api/v1/dashboards/widget-data', { widget_type: widgetType, config })
};

// Bank Reconciliation API
export const reconciliationAPI = {
  getSessions: () => api.get('/api/v1/reconciliation/sessions'),
  getSession: (id) => api.get(`/api/v1/reconciliation/sessions/${id}`),
  createSession: (data) => api.post('/api/v1/reconciliation/sessions', data),
  importStatement: (sessionId, file, bankFormat = 'generic') => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/api/v1/reconciliation/sessions/${sessionId}/import?bank_format=${bankFormat}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  autoMatch: (sessionId) => api.post(`/api/v1/reconciliation/sessions/${sessionId}/auto-match`),
  manualMatch: (sessionId, data) => api.post(`/api/v1/reconciliation/sessions/${sessionId}/manual-match`, data),
  unmatch: (sessionId, matchId) => api.post(`/api/v1/reconciliation/sessions/${sessionId}/unmatch/${matchId}`),
  completeSession: (sessionId) => api.post(`/api/v1/reconciliation/sessions/${sessionId}/complete`),
  getUnmatched: (sessionId) => api.get(`/api/v1/reconciliation/sessions/${sessionId}/unmatched`),
  getSuggestions: (sessionId, statementId) => api.get(`/api/v1/reconciliation/sessions/${sessionId}/suggestions/${statementId}`)
};

// Scheduled Reports API
export const scheduledReportsAPI = {
  list: () => api.get('/api/v1/scheduled-reports'),
  get: (id) => api.get(`/api/v1/scheduled-reports/${id}`),
  create: (data) => api.post('/api/v1/scheduled-reports', data),
  update: (id, data) => api.put(`/api/v1/scheduled-reports/${id}`, data),
  delete: (id) => api.delete(`/api/v1/scheduled-reports/${id}`),
  pause: (id) => api.post(`/api/v1/scheduled-reports/${id}/pause`),
  resume: (id) => api.post(`/api/v1/scheduled-reports/${id}/resume`),
  runNow: (id) => api.post(`/api/v1/scheduled-reports/${id}/run`),
  getHistory: (id, limit = 10) => api.get(`/api/v1/scheduled-reports/${id}/history`, { params: { limit } }),
  downloadReport: (id, executionId) => api.get(`/api/v1/scheduled-reports/${id}/download/${executionId}`, { responseType: 'blob' })
};

// Currency API
export const currencyAPI = {
  list: () => api.get('/api/v1/currencies'),
  get: (code) => api.get(`/api/v1/currencies/${code}`),
  create: (data) => api.post('/api/v1/currencies', data),
  update: (code, data) => api.put(`/api/v1/currencies/${code}`, data),
  delete: (code) => api.delete(`/api/v1/currencies/${code}`),
  setBase: (code) => api.post(`/api/v1/currencies/${code}/set-base`),
  updateRate: (code, rate) => api.put(`/api/v1/currencies/${code}/rate`, { rate }),
  convert: (amount, from, to) => api.get('/api/v1/currencies/convert', { params: { amount, from_currency: from, to_currency: to } }),
  fetchRates: () => api.post('/api/v1/currencies/fetch-rates'),
  getHistoricalRates: (code, days = 30) => api.get(`/api/v1/currencies/${code}/history`, { params: { days } })
};

// Client Portal API
export const clientPortalAPI = {
  getDashboard: () => api.get('/api/v1/portal/client/dashboard'),
  getProjects: () => api.get('/api/v1/portal/client/projects'),
  getProject: (id) => api.get(`/api/v1/portal/client/projects/${id}`),
  getPayments: () => api.get('/api/v1/portal/client/payments'),
  getInvoices: () => api.get('/api/v1/portal/client/invoices'),
  getInvoice: (id) => api.get(`/api/v1/portal/client/invoices/${id}`),
  downloadInvoice: (id) => api.get(`/api/v1/portal/client/invoices/${id}/download`, { responseType: 'blob' })
};

// Supplier Portal API
export const supplierPortalAPI = {
  getDashboard: () => api.get('/api/v1/portal/supplier/dashboard'),
  getOrders: () => api.get('/api/v1/portal/supplier/orders'),
  getOrder: (id) => api.get(`/api/v1/portal/supplier/orders/${id}`),
  updateOrderStatus: (id, status) => api.put(`/api/v1/portal/supplier/orders/${id}/status`, { status }),
  getPayments: () => api.get('/api/v1/portal/supplier/payments'),
  getCatalog: () => api.get('/api/v1/portal/supplier/catalog'),
  updateCatalogItem: (id, data) => api.put(`/api/v1/portal/supplier/catalog/${id}`, data)
};

// ============================================
// PHASE 7 - ADVANCED ANALYTICS & INTEGRATIONS API
// ============================================

// Audit Trail API
export const auditAPI = {
  getActions: () => api.get('/api/v1/audit/actions'),
  getEntities: () => api.get('/api/v1/audit/entities'),
  search: (params) => api.get('/api/v1/audit', { params }),
  getStatistics: (days = 30) => api.get('/api/v1/audit/statistics', { params: { days } }),
  getAnomalies: () => api.get('/api/v1/audit/anomalies'),
  getEntityHistory: (entityType, entityId) => api.get(`/api/v1/audit/entity/${entityType}/${entityId}`),
  getUserActivity: (userId, days = 30) => api.get(`/api/v1/audit/user/${userId}`, { params: { days } }),
  export: (format, dateFrom, dateTo) => api.get('/api/v1/audit/export', { params: { format, date_from: dateFrom, date_to: dateTo } }),
  get: (logId) => api.get(`/api/v1/audit/${logId}`)
};

// Data Import API
export const importAPI = {
  getEntities: () => api.get('/api/v1/import/entities'),
  getEntityConfig: (entity) => api.get(`/api/v1/import/entities/${entity}/config`),
  parse: (content, delimiter = ',') => api.post('/api/v1/import/parse', { content, delimiter }),
  suggestMapping: (entity, headers) => api.post('/api/v1/import/suggest-mapping', headers, { params: { entity } }),
  create: (data) => api.post('/api/v1/import', data),
  list: (limit = 20) => api.get('/api/v1/import', { params: { limit } }),
  get: (importId) => api.get(`/api/v1/import/${importId}`),
  execute: (importId) => api.post(`/api/v1/import/${importId}/execute`),
  rollback: (importId) => api.post(`/api/v1/import/${importId}/rollback`)
};

// Comments API
export const commentsAPI = {
  getReactions: () => api.get('/api/v1/comments/reactions'),
  create: (data) => api.post('/api/v1/comments', data),
  getEntityComments: (entityType, entityId) => api.get(`/api/v1/comments/entity/${entityType}/${entityId}`),
  getMentions: () => api.get('/api/v1/comments/mentions'),
  get: (commentId) => api.get(`/api/v1/comments/${commentId}`),
  update: (commentId, content) => api.put(`/api/v1/comments/${commentId}`, { content }),
  delete: (commentId) => api.delete(`/api/v1/comments/${commentId}`),
  addReaction: (commentId, reaction) => api.post(`/api/v1/comments/${commentId}/reactions`, { reaction }),
  removeReaction: (commentId, reaction) => api.delete(`/api/v1/comments/${commentId}/reactions/${reaction}`)
};

// Tasks API
export const tasksAPI = {
  getStatuses: () => api.get('/api/v1/tasks/statuses'),
  getPriorities: () => api.get('/api/v1/tasks/priorities'),
  getMy: (status) => api.get('/api/v1/tasks/my', { params: status ? { status } : {} }),
  getOverdue: () => api.get('/api/v1/tasks/overdue'),
  create: (data) => api.post('/api/v1/tasks', data),
  getEntityTasks: (entityType, entityId) => api.get(`/api/v1/tasks/entity/${entityType}/${entityId}`),
  getActivityFeed: (entityType, entityId, limit = 20) => api.get(`/api/v1/tasks/activity/${entityType}/${entityId}`, { params: { limit } }),
  get: (taskId) => api.get(`/api/v1/tasks/${taskId}`),
  update: (taskId, data) => api.put(`/api/v1/tasks/${taskId}`, data),
  delete: (taskId) => api.delete(`/api/v1/tasks/${taskId}`)
};

// Tax Management API
export const taxAPI = {
  getTypes: () => api.get('/api/v1/taxes/types'),
  list: (activeOnly = true, taxType) => api.get('/api/v1/taxes', { params: { active_only: activeOnly, tax_type: taxType } }),
  create: (data) => api.post('/api/v1/taxes', data),
  getDefault: (taxType = 'vat') => api.get('/api/v1/taxes/default', { params: { tax_type: taxType } }),
  calculate: (data) => api.post('/api/v1/taxes/calculate', data),
  getReport: (periodStart, periodEnd) => api.get('/api/v1/taxes/report', { params: { period_start: periodStart, period_end: periodEnd } }),
  get: (taxId) => api.get(`/api/v1/taxes/${taxId}`),
  update: (taxId, data) => api.put(`/api/v1/taxes/${taxId}`, data),
  delete: (taxId) => api.delete(`/api/v1/taxes/${taxId}`)
};

// Custom Fields API
export const customFieldsAPI = {
  getTypes: () => api.get('/api/v1/custom-fields/types'),
  getEntities: () => api.get('/api/v1/custom-fields/entities'),
  getEntityFields: (entity, activeOnly = true) => api.get(`/api/v1/custom-fields/entity/${entity}`, { params: { active_only: activeOnly } }),
  create: (data) => api.post('/api/v1/custom-fields', data),
  get: (fieldId) => api.get(`/api/v1/custom-fields/${fieldId}`),
  update: (fieldId, data) => api.put(`/api/v1/custom-fields/${fieldId}`, data),
  delete: (fieldId) => api.delete(`/api/v1/custom-fields/${fieldId}`),
  getValues: (entity, entityId) => api.get(`/api/v1/custom-fields/values/${entity}/${entityId}`),
  setValue: (entity, entityId, fieldId, value) => api.put(`/api/v1/custom-fields/values/${entity}/${entityId}/${fieldId}`, { value }),
  setBulkValues: (entity, entityId, values) => api.put(`/api/v1/custom-fields/values/${entity}/${entityId}`, { values })
};

// Calendar API
export const calendarAPI = {
  getTypes: () => api.get('/api/v1/calendar/types'),
  getEvents: (start, end, type) => api.get('/api/v1/calendar', { params: { start, end, type } }),
  getUpcoming: (days = 7) => api.get('/api/v1/calendar/upcoming', { params: { days } }),
  generate: () => api.post('/api/v1/calendar/generate'),
  create: (data) => api.post('/api/v1/calendar', data),
  get: (eventId) => api.get(`/api/v1/calendar/${eventId}`),
  update: (eventId, data) => api.put(`/api/v1/calendar/${eventId}`, data),
  delete: (eventId) => api.delete(`/api/v1/calendar/${eventId}`)
};

// Export api instance
export { api };
