/**
 * Reports API Service
 */

import api from '../api';

export const reportsAPI = {
  // CRUD Operations
  list: (params) => api.get('/api/v1/reports', { params }),
  get: (id) => api.get(`/api/v1/reports/${id}`),
  create: (data) => api.post('/api/v1/reports', data),
  update: (id, data) => api.put(`/api/v1/reports/${id}`, data),
  delete: (id) => api.delete(`/api/v1/reports/${id}`),

  // Execution
  execute: (id, parameters) => api.post(`/api/v1/reports/${id}/execute`, { parameters }),

  // Export
  export: (id, format, parameters) => api.get(`/api/v1/reports/${id}/export/${format}`, {
    params: parameters,
    responseType: 'blob',
  }),

  // Sharing
  share: (id, userIds) => api.post(`/api/v1/reports/${id}/share`, { user_ids: userIds }),
  publish: (id) => api.post(`/api/v1/reports/${id}/publish`),

  // Favorites
  toggleFavorite: (id) => api.post(`/api/v1/reports/${id}/favorite`),
  getFavorites: () => api.get('/api/v1/reports/favorites'),
  getRecent: () => api.get('/api/v1/reports/recent'),

  // Categories
  getCategories: () => api.get('/api/v1/reports/categories'),
  createCategory: (data) => api.post('/api/v1/reports/categories', data),

  // Templates
  getTemplates: () => api.get('/api/v1/reports/templates'),
  createFromTemplate: (templateId) => api.post(`/api/v1/reports/templates/${templateId}/create`),

  // Scheduling
  getSchedules: (reportId) => api.get(`/api/v1/reports/${reportId}/schedules`),
  createSchedule: (reportId, data) => api.post(`/api/v1/reports/${reportId}/schedules`, data),
  updateSchedule: (reportId, scheduleId, data) =>
    api.put(`/api/v1/reports/${reportId}/schedules/${scheduleId}`, data),
  deleteSchedule: (reportId, scheduleId) =>
    api.delete(`/api/v1/reports/${reportId}/schedules/${scheduleId}`),
};

export default reportsAPI;
