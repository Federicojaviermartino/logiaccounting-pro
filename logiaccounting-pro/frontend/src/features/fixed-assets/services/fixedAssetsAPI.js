/**
 * Fixed Assets module API service.
 */
import api from '../../../services/api';

// ==================== Categories ====================

export const categoriesAPI = {
  getAll: (parentId = null, activeOnly = true) =>
    api.get('/fixed-assets/categories', { params: { parent_id: parentId, active_only: activeOnly } }),

  getTree: () => api.get('/fixed-assets/categories/tree'),

  getById: (id) => api.get(`/fixed-assets/categories/${id}`),

  create: (data) => api.post('/fixed-assets/categories', data),

  update: (id, data) => api.put(`/fixed-assets/categories/${id}`, data),

  delete: (id) => api.delete(`/fixed-assets/categories/${id}`),

  setupDefaults: () => api.post('/fixed-assets/categories/setup-defaults'),
};


// ==================== Assets ====================

export const assetsAPI = {
  getAll: (params) => api.get('/fixed-assets/assets', { params }),

  getSummary: () => api.get('/fixed-assets/assets/summary'),

  getByBarcode: (barcode) => api.get(`/fixed-assets/assets/barcode/${barcode}`),

  getById: (id, includeSchedule = false, includeMovements = false) =>
    api.get(`/fixed-assets/assets/${id}`, {
      params: { include_schedule: includeSchedule, include_movements: includeMovements }
    }),

  create: (data) => api.post('/fixed-assets/assets', data),

  update: (id, data) => api.put(`/fixed-assets/assets/${id}`, data),

  delete: (id) => api.delete(`/fixed-assets/assets/${id}`),

  activate: (id, depreciationStartDate = null) =>
    api.post(`/fixed-assets/assets/${id}/activate`, null, {
      params: { depreciation_start_date: depreciationStartDate }
    }),

  suspendDepreciation: (id, reason) =>
    api.post(`/fixed-assets/assets/${id}/suspend-depreciation`, null, { params: { reason } }),

  resumeDepreciation: (id) => api.post(`/fixed-assets/assets/${id}/resume-depreciation`),

  getSchedule: (id) => api.get(`/fixed-assets/assets/${id}/schedule`),

  regenerateSchedule: (id) => api.post(`/fixed-assets/assets/${id}/regenerate-schedule`),

  import: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/fixed-assets/assets/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  export: (format = 'xlsx', categoryId = null, status = null) =>
    api.get('/fixed-assets/assets/export', {
      params: { format, category_id: categoryId, status },
      responseType: 'blob',
    }),
};


// ==================== Depreciation ====================

export const depreciationAPI = {
  getRuns: (params) => api.get('/fixed-assets/depreciation/runs', { params }),

  getRunById: (id, includeEntries = false) =>
    api.get(`/fixed-assets/depreciation/runs/${id}`, { params: { include_entries: includeEntries } }),

  createRun: (data) => api.post('/fixed-assets/depreciation/runs', data),

  postRun: (id) => api.post(`/fixed-assets/depreciation/runs/${id}/post`),

  cancelRun: (id) => api.post(`/fixed-assets/depreciation/runs/${id}/cancel`),

  reverseRun: (id, reason) =>
    api.post(`/fixed-assets/depreciation/runs/${id}/reverse`, null, { params: { reason } }),

  getEntries: (params) => api.get('/fixed-assets/depreciation/entries', { params }),

  recordUnits: (assetId, periodYear, periodMonth, units) =>
    api.post('/fixed-assets/depreciation/record-units', {
      asset_id: assetId,
      period_year: periodYear,
      period_month: periodMonth,
      units,
    }),

  preview: (periodYear, periodMonth, categoryId = null) =>
    api.get('/fixed-assets/depreciation/preview', {
      params: { period_year: periodYear, period_month: periodMonth, category_id: categoryId }
    }),
};


// ==================== Movements ====================

export const movementsAPI = {
  getAll: (params) => api.get('/fixed-assets/movements', { params }),

  getById: (id) => api.get(`/fixed-assets/movements/${id}`),

  transfer: (data) => api.post('/fixed-assets/transfer', data),

  revalue: (data) => api.post('/fixed-assets/revalue', data),

  improve: (data) => api.post('/fixed-assets/improve', data),
};


// ==================== Disposals ====================

export const disposalsAPI = {
  getAll: (params) => api.get('/fixed-assets/disposals', { params }),

  getById: (id) => api.get(`/fixed-assets/disposals/${id}`),

  create: (data) => api.post('/fixed-assets/disposals', data),

  approve: (id) => api.post(`/fixed-assets/disposals/${id}/approve`),

  post: (id) => api.post(`/fixed-assets/disposals/${id}/post`),

  cancel: (id) => api.post(`/fixed-assets/disposals/${id}/cancel`),
};


// ==================== Reports ====================

export const reportsAPI = {
  assetRegister: (asOfDate, params = {}) =>
    api.get('/fixed-assets/reports/asset-register', { params: { as_of_date: asOfDate, ...params } }),

  depreciationSchedule: (year, params = {}) =>
    api.get('/fixed-assets/reports/depreciation-schedule', { params: { year, ...params } }),

  depreciationSummary: (startDate, endDate, groupBy = 'category') =>
    api.get('/fixed-assets/reports/depreciation-summary', {
      params: { start_date: startDate, end_date: endDate, group_by: groupBy }
    }),

  movementHistory: (startDate, endDate, params = {}) =>
    api.get('/fixed-assets/reports/movement-history', {
      params: { start_date: startDate, end_date: endDate, ...params }
    }),

  disposalReport: (startDate, endDate, params = {}) =>
    api.get('/fixed-assets/reports/disposal-report', {
      params: { start_date: startDate, end_date: endDate, ...params }
    }),

  fullyDepreciated: (asOfDate = null, categoryId = null) =>
    api.get('/fixed-assets/reports/fully-depreciated', {
      params: { as_of_date: asOfDate, category_id: categoryId }
    }),

  insuranceExpiry: (daysAhead = 30) =>
    api.get('/fixed-assets/reports/insurance-expiry', { params: { days_ahead: daysAhead } }),

  warrantyExpiry: (daysAhead = 30) =>
    api.get('/fixed-assets/reports/warranty-expiry', { params: { days_ahead: daysAhead } }),

  categorySummary: (asOfDate = null) =>
    api.get('/fixed-assets/reports/category-summary', { params: { as_of_date: asOfDate } }),
};


export default {
  categories: categoriesAPI,
  assets: assetsAPI,
  depreciation: depreciationAPI,
  movements: movementsAPI,
  disposals: disposalsAPI,
  reports: reportsAPI,
};
