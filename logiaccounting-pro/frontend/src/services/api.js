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
