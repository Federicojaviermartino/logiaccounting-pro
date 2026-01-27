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
};

export default budgetingAPI;
