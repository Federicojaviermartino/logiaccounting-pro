import api from '../../../services/api';

const BASE_URL = '/budgeting';

export const budgetingAPI = {
  // Budgets
  getBudgets: (params = {}) => api.get(`${BASE_URL}/budgets`, { params }),
  getBudget: (id, includeVersions = false) =>
    api.get(`${BASE_URL}/budgets/${id}`, { params: { include_versions: includeVersions } }),
  createBudget: (data) => api.post(`${BASE_URL}/budgets`, data),
  updateBudget: (id, data) => api.put(`${BASE_URL}/budgets/${id}`, data),
  deleteBudget: (id) => api.delete(`${BASE_URL}/budgets/${id}`),

  // Versions
  getVersions: (budgetId) => api.get(`${BASE_URL}/budgets/${budgetId}/versions`),
  createVersion: (budgetId, data) => api.post(`${BASE_URL}/budgets/${budgetId}/versions`, data),
  submitVersion: (versionId) => api.post(`${BASE_URL}/versions/${versionId}/submit`),
  approveVersion: (versionId) => api.post(`${BASE_URL}/versions/${versionId}/approve`),
  rejectVersion: (versionId, reason) =>
    api.post(`${BASE_URL}/versions/${versionId}/reject`, null, { params: { reason } }),
  activateVersion: (versionId) => api.post(`${BASE_URL}/versions/${versionId}/activate`),

  // Budget Lines
  getLines: (versionId, params = {}) =>
    api.get(`${BASE_URL}/versions/${versionId}/lines`, { params }),
  createLine: (versionId, data) => api.post(`${BASE_URL}/versions/${versionId}/lines`, data),
  updateLine: (lineId, data) => api.put(`${BASE_URL}/lines/${lineId}`, data),
  deleteLine: (lineId) => api.delete(`${BASE_URL}/lines/${lineId}`),

  // Periods
  getLinePeriods: (lineId) => api.get(`${BASE_URL}/lines/${lineId}/periods`),
  updatePeriod: (periodId, amount, notes = null) =>
    api.put(`${BASE_URL}/periods/${periodId}`, null, { params: { amount, notes } }),
  distributeLine: (lineId, method, patternId = null) =>
    api.post(`${BASE_URL}/lines/${lineId}/distribute`, null, { params: { method, pattern_id: patternId } }),

  // Variance Analysis
  getBudgetVsActual: (budgetId, periodType = 'ytd', year = null, month = null) =>
    api.get(`${BASE_URL}/variance/budgets/${budgetId}/comparison`, {
      params: { period_type: periodType, year, month }
    }),
  updateActualsFromGL: (budgetId, year, month) =>
    api.post(`${BASE_URL}/variance/budgets/${budgetId}/update-actuals`, null, {
      params: { year, month }
    }),

  // Variance Thresholds
  getThresholds: (budgetId = null) =>
    api.get(`${BASE_URL}/variance/thresholds`, { params: { budget_id: budgetId } }),
  createThreshold: (data) => api.post(`${BASE_URL}/variance/thresholds`, data),
  updateThreshold: (id, data) => api.put(`${BASE_URL}/variance/thresholds/${id}`, data),
  deleteThreshold: (id) => api.delete(`${BASE_URL}/variance/thresholds/${id}`),

  // Variance Alerts
  getAlerts: (params = {}) => api.get(`${BASE_URL}/variance/alerts`, { params }),
  getAlertSummary: (budgetId = null) =>
    api.get(`${BASE_URL}/variance/alerts/summary`, { params: { budget_id: budgetId } }),
  acknowledgeAlert: (id, notes = null) =>
    api.post(`${BASE_URL}/variance/alerts/${id}/acknowledge`, { notes }),
  resolveAlert: (id, notes) =>
    api.post(`${BASE_URL}/variance/alerts/${id}/resolve`, { resolution_notes: notes }),
  dismissAlert: (id) => api.post(`${BASE_URL}/variance/alerts/${id}/dismiss`),

  // Forecasts
  getForecasts: (params = {}) => api.get(`${BASE_URL}/forecasts`, { params }),
  getForecast: (id) => api.get(`${BASE_URL}/forecasts/${id}`),
  createForecast: (data) => api.post(`${BASE_URL}/forecasts`, data),
  updateForecast: (id, data) => api.put(`${BASE_URL}/forecasts/${id}`, data),
  deleteForecast: (id) => api.delete(`${BASE_URL}/forecasts/${id}`),
  generateForecast: (id) => api.post(`${BASE_URL}/forecasts/${id}/generate`),

  // Reports
  getBudgetSummaryReport: (budgetId, format = 'json') =>
    api.get(`${BASE_URL}/reports/budgets/${budgetId}/summary`, { params: { format } }),
  getVarianceReport: (budgetId, params = {}) =>
    api.get(`${BASE_URL}/reports/budgets/${budgetId}/variance`, { params }),
  exportBudget: (budgetId) =>
    api.get(`${BASE_URL}/reports/budgets/${budgetId}/export`, { responseType: 'blob' }),
};

export default budgetingAPI;
