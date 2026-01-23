/**
 * CRM API Service
 * Handles all CRM-related API calls
 */

import axios from 'axios';

const API_BASE = '/api/v1/crm';

// ============================================
// LEADS
// ============================================

export const leadsAPI = {
  list: (params = {}) => axios.get(`${API_BASE}/leads`, { params }),
  get: (id) => axios.get(`${API_BASE}/leads/${id}`),
  create: (data) => axios.post(`${API_BASE}/leads`, data),
  update: (id, data) => axios.put(`${API_BASE}/leads/${id}`, data),
  delete: (id) => axios.delete(`${API_BASE}/leads/${id}`),
  convert: (id, data) => axios.post(`${API_BASE}/leads/${id}/convert`, data),
  assign: (id, ownerId) => axios.post(`${API_BASE}/leads/${id}/assign`, { owner_id: ownerId }),
  changeStatus: (id, status) => axios.put(`${API_BASE}/leads/${id}/status?status=${status}`),
  bulkAssign: (leadIds, ownerId) => axios.post(`${API_BASE}/leads/bulk-assign`, { lead_ids: leadIds, owner_id: ownerId }),
  import: (leads) => axios.post(`${API_BASE}/leads/import`, { leads }),
  getSources: () => axios.get(`${API_BASE}/leads/sources`),
  getStatuses: () => axios.get(`${API_BASE}/leads/statuses`),
  getSourceStats: () => axios.get(`${API_BASE}/leads/sources/stats`),
};

// ============================================
// CONTACTS
// ============================================

export const contactsAPI = {
  list: (params = {}) => axios.get(`${API_BASE}/contacts`, { params }),
  get: (id) => axios.get(`${API_BASE}/contacts/${id}`),
  get360: (id) => axios.get(`${API_BASE}/contacts/${id}/360`),
  create: (data) => axios.post(`${API_BASE}/contacts`, data),
  update: (id, data) => axios.put(`${API_BASE}/contacts/${id}`, data),
  delete: (id) => axios.delete(`${API_BASE}/contacts/${id}`),
  search: (q, limit = 10) => axios.get(`${API_BASE}/contacts/search`, { params: { q, limit } }),
  merge: (primaryId, secondaryId) => axios.post(`${API_BASE}/contacts/merge`, { primary_id: primaryId, secondary_id: secondaryId }),
  setPreferences: (id, prefs) => axios.put(`${API_BASE}/contacts/${id}/preferences`, prefs),
  import: (contacts) => axios.post(`${API_BASE}/contacts/import`, { contacts }),
  export: (format = 'csv') => axios.get(`${API_BASE}/contacts/export`, { params: { format }, responseType: 'blob' }),
  getRoles: () => axios.get(`${API_BASE}/contacts/roles`),
};

// ============================================
// COMPANIES
// ============================================

export const companiesAPI = {
  list: (params = {}) => axios.get(`${API_BASE}/companies`, { params }),
  get: (id) => axios.get(`${API_BASE}/companies/${id}`),
  getSummary: (id) => axios.get(`${API_BASE}/companies/${id}/summary`),
  create: (data) => axios.post(`${API_BASE}/companies`, data),
  update: (id, data) => axios.put(`${API_BASE}/companies/${id}`, data),
  delete: (id) => axios.delete(`${API_BASE}/companies/${id}`),
  setParent: (id, parentId) => axios.post(`${API_BASE}/companies/${id}/parent`, { parent_id: parentId }),
  getSubsidiaries: (id) => axios.get(`${API_BASE}/companies/${id}/subsidiaries`),
  linkToClient: (id, clientId) => axios.post(`${API_BASE}/companies/${id}/link-client`, { client_id: clientId }),
  getTop: (limit = 10) => axios.get(`${API_BASE}/companies/top`, { params: { limit } }),
  getAtRisk: () => axios.get(`${API_BASE}/companies/at-risk`),
  getTypes: () => axios.get(`${API_BASE}/companies/types`),
  getIndustries: () => axios.get(`${API_BASE}/companies/industries`),
};

// ============================================
// OPPORTUNITIES
// ============================================

export const opportunitiesAPI = {
  list: (params = {}) => axios.get(`${API_BASE}/opportunities`, { params }),
  get: (id) => axios.get(`${API_BASE}/opportunities/${id}`),
  create: (data) => axios.post(`${API_BASE}/opportunities`, data),
  update: (id, data) => axios.put(`${API_BASE}/opportunities/${id}`, data),
  delete: (id) => axios.delete(`${API_BASE}/opportunities/${id}`),
  moveStage: (id, stageId) => axios.post(`${API_BASE}/opportunities/${id}/move`, { stage_id: stageId }),
  win: (id, data = {}) => axios.post(`${API_BASE}/opportunities/${id}/win`, data),
  lose: (id, data = {}) => axios.post(`${API_BASE}/opportunities/${id}/lose`, data),
  reopen: (id) => axios.post(`${API_BASE}/opportunities/${id}/reopen`),
  getBoard: (pipelineId = null) => axios.get(`${API_BASE}/opportunities/board`, { params: { pipeline_id: pipelineId } }),
  getForecast: (params = {}) => axios.get(`${API_BASE}/opportunities/forecast`, { params }),
  getWinLoss: (days = 90) => axios.get(`${API_BASE}/opportunities/win-loss`, { params: { days } }),
};

// ============================================
// PIPELINES
// ============================================

export const pipelinesAPI = {
  list: () => axios.get(`${API_BASE}/opportunities/pipelines`),
  get: (id) => axios.get(`${API_BASE}/opportunities/pipelines/${id}`),
  create: (data) => axios.post(`${API_BASE}/opportunities/pipelines`, data),
  delete: (id) => axios.delete(`${API_BASE}/opportunities/pipelines/${id}`),
  getStats: (id) => axios.get(`${API_BASE}/opportunities/pipelines/${id}/stats`),
  addStage: (id, data) => axios.post(`${API_BASE}/opportunities/pipelines/${id}/stages`, data),
  updateStage: (pipelineId, stageId, data) => axios.put(`${API_BASE}/opportunities/pipelines/${pipelineId}/stages/${stageId}`, data),
  deleteStage: (pipelineId, stageId, moveToStageId = null) => axios.delete(`${API_BASE}/opportunities/pipelines/${pipelineId}/stages/${stageId}`, { params: { move_to_stage_id: moveToStageId } }),
  reorderStages: (pipelineId, stageIds) => axios.post(`${API_BASE}/opportunities/pipelines/${pipelineId}/stages/reorder`, { stage_ids: stageIds }),
};

// ============================================
// ACTIVITIES
// ============================================

export const activitiesAPI = {
  list: (params = {}) => axios.get(`${API_BASE}/activities`, { params }),
  get: (id) => axios.get(`${API_BASE}/activities/${id}`),
  create: (data) => axios.post(`${API_BASE}/activities`, data),
  update: (id, data) => axios.put(`${API_BASE}/activities/${id}`, data),
  delete: (id) => axios.delete(`${API_BASE}/activities/${id}`),
  complete: (id, data = {}) => axios.post(`${API_BASE}/activities/${id}/complete`, data),
  cancel: (id, reason = null) => axios.post(`${API_BASE}/activities/${id}/cancel`, null, { params: { reason } }),
  reschedule: (id, newDate) => axios.post(`${API_BASE}/activities/${id}/reschedule`, null, { params: { new_date: newDate } }),
  logCall: (data) => axios.post(`${API_BASE}/activities/log-call`, data),
  logEmail: (data) => axios.post(`${API_BASE}/activities/log-email`, data),
  scheduleMeeting: (data) => axios.post(`${API_BASE}/activities/schedule-meeting`, data),
  createTask: (data) => axios.post(`${API_BASE}/activities/create-task`, data),
  getUpcoming: (days = 7) => axios.get(`${API_BASE}/activities/upcoming`, { params: { days } }),
  getOverdue: () => axios.get(`${API_BASE}/activities/overdue`),
  getStats: (days = 30) => axios.get(`${API_BASE}/activities/stats`, { params: { days } }),
  getTypes: () => axios.get(`${API_BASE}/activities/types`),
  getCallOutcomes: () => axios.get(`${API_BASE}/activities/call-outcomes`),
};

// ============================================
// EMAIL TEMPLATES
// ============================================

export const templatesAPI = {
  list: (params = {}) => axios.get(`${API_BASE}/activities/templates`, { params }),
  get: (id) => axios.get(`${API_BASE}/activities/templates/${id}`),
  create: (data) => axios.post(`${API_BASE}/activities/templates`, data),
  render: (templateId, context) => axios.post(`${API_BASE}/activities/templates/render`, { template_id: templateId, context }),
  getMergeFields: () => axios.get(`${API_BASE}/activities/templates/merge-fields`),
};

// ============================================
// QUOTES
// ============================================

export const quotesAPI = {
  list: (params = {}) => axios.get(`${API_BASE}/quotes`, { params }),
  get: (id) => axios.get(`${API_BASE}/quotes/${id}`),
  create: (data) => axios.post(`${API_BASE}/quotes`, data),
  update: (id, data) => axios.put(`${API_BASE}/quotes/${id}`, data),
  delete: (id) => axios.delete(`${API_BASE}/quotes/${id}`),
  duplicate: (id) => axios.post(`${API_BASE}/quotes/${id}/duplicate`),
  addItem: (id, data) => axios.post(`${API_BASE}/quotes/${id}/items`, data),
  updateItem: (quoteId, itemId, data) => axios.put(`${API_BASE}/quotes/${quoteId}/items/${itemId}`, data),
  removeItem: (quoteId, itemId) => axios.delete(`${API_BASE}/quotes/${quoteId}/items/${itemId}`),
  submit: (id) => axios.post(`${API_BASE}/quotes/${id}/submit`),
  approve: (id) => axios.post(`${API_BASE}/quotes/${id}/approve`),
  reject: (id, reason = null) => axios.post(`${API_BASE}/quotes/${id}/reject`, { reason }),
  send: (id, email = null) => axios.post(`${API_BASE}/quotes/${id}/send`, { email }),
  accept: (id, signature = null) => axios.post(`${API_BASE}/quotes/${id}/accept`, { signature }),
  decline: (id, reason = null) => axios.post(`${API_BASE}/quotes/${id}/decline`, { reason }),
  convertToInvoice: (id) => axios.post(`${API_BASE}/quotes/${id}/convert`),
  getStatuses: () => axios.get(`${API_BASE}/quotes/statuses`),
  getPublic: (id) => axios.get(`${API_BASE}/quotes/public/${id}`),
};

// ============================================
// COMBINED API OBJECT
// ============================================

export const crmAPI = {
  leads: leadsAPI,
  contacts: contactsAPI,
  companies: companiesAPI,
  opportunities: opportunitiesAPI,
  pipelines: pipelinesAPI,
  activities: activitiesAPI,
  templates: templatesAPI,
  quotes: quotesAPI,

  // Convenience methods
  getPipelineStats: (pipelineId) => pipelinesAPI.getStats(pipelineId),
  getForecast: (params) => opportunitiesAPI.getForecast(params),
  getWinLossAnalysis: (days) => opportunitiesAPI.getWinLoss(days),
  getActivityStats: (days) => activitiesAPI.getStats(days),
  getTopAccounts: (limit) => companiesAPI.getTop(limit),
  getUpcomingActivities: (days) => activitiesAPI.getUpcoming(days),
  getOverdueTasks: () => activitiesAPI.getOverdue(),
  convertLead: (id, data) => leadsAPI.convert(id, data),
};

export default crmAPI;
