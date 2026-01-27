/**
 * Workflow API Service
 * API calls for workflow management
 */

import api from '../../../services/api';

export const workflowAPI = {
  /**
   * List workflows
   */
  async listWorkflows({ status, limit = 50, offset = 0 } = {}) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit);
    params.append('offset', offset);

    const response = await api.get(`/workflows?${params}`);
    return response.data;
  },

  /**
   * Get single workflow
   */
  async getWorkflow(id) {
    const response = await api.get(`/workflows/${id}`);
    return response.data;
  },

  /**
   * Create workflow
   */
  async createWorkflow(data) {
    const response = await api.post('/workflows', data);
    return response.data;
  },

  /**
   * Update workflow
   */
  async updateWorkflow(id, data) {
    const response = await api.put(`/workflows/${id}`, data);
    return response.data;
  },

  /**
   * Delete workflow
   */
  async deleteWorkflow(id) {
    const response = await api.delete(`/workflows/${id}`);
    return response.data;
  },

  /**
   * Duplicate workflow
   */
  async duplicateWorkflow(id) {
    const response = await api.post(`/workflows/${id}/duplicate`);
    return response.data;
  },

  /**
   * Activate workflow
   */
  async activateWorkflow(id) {
    const response = await api.post(`/workflows/${id}/activate`);
    return response.data;
  },

  /**
   * Deactivate workflow
   */
  async deactivateWorkflow(id) {
    const response = await api.post(`/workflows/${id}/deactivate`);
    return response.data;
  },

  /**
   * Execute workflow manually
   */
  async executeWorkflow(id, inputData = {}) {
    const response = await api.post(`/workflows/${id}/execute`, {
      input_data: inputData,
    });
    return response.data;
  },

  /**
   * Get execution history
   */
  async getExecutions(workflowId, limit = 20) {
    const response = await api.get(`/workflows/${workflowId}/executions?limit=${limit}`);
    return response.data;
  },

  /**
   * Get single execution
   */
  async getExecution(workflowId, executionId) {
    const response = await api.get(`/workflows/${workflowId}/executions/${executionId}`);
    return response.data;
  },

  /**
   * Get workflow stats
   */
  async getWorkflowStats(id) {
    const response = await api.get(`/workflows/${id}/stats`);
    return response.data;
  },

  /**
   * Get customer stats
   */
  async getStats() {
    const response = await api.get('/workflows/stats');
    return response.data;
  },

  /**
   * Get templates
   */
  async getTemplates(category) {
    const params = category ? `?category=${category}` : '';
    const response = await api.get(`/workflows/templates${params}`);
    return response.data;
  },

  /**
   * Create from template
   */
  async createFromTemplate(templateId, overrides = {}) {
    const response = await api.post('/workflows/from-template', {
      template_id: templateId,
      ...overrides,
    });
    return response.data;
  },

  /**
   * Get available triggers
   */
  async getTriggers() {
    const response = await api.get('/workflows/metadata/triggers');
    return response.data;
  },

  /**
   * Get available actions
   */
  async getActions() {
    const response = await api.get('/workflows/metadata/actions');
    return response.data;
  },

  /**
   * Get condition metadata
   */
  async getConditions() {
    const response = await api.get('/workflows/metadata/conditions');
    return response.data;
  },

  /**
   * Get available variables
   */
  async getVariables() {
    const response = await api.get('/workflows/metadata/variables');
    return response.data;
  },

  /**
   * Validate cron expression
   */
  async validateCron(cron) {
    const response = await api.post('/workflows/metadata/cron/validate', { cron });
    return response.data;
  },

  /**
   * Preview cron schedule
   */
  async previewCron(cron, count = 10) {
    const response = await api.post('/workflows/metadata/cron/preview', { cron, count });
    return response.data;
  },
};

export default workflowAPI;
