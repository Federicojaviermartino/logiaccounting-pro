/**
 * Analytics API Service
 * Handles all analytics and ML forecasting API calls
 */

import api from './api';

const analyticsApi = {
  // ============================================
  // DASHBOARD & KPIs
  // ============================================

  /**
   * Get main analytics dashboard
   */
  getDashboard: async () => {
    const response = await api.get('/api/v1/analytics/dashboard');
    return response.data;
  },

  /**
   * Get financial health score
   */
  getHealthScore: async () => {
    const response = await api.get('/api/v1/analytics/health-score');
    return response.data;
  },

  /**
   * Get KPI trends
   * @param {string} metric - revenue, expenses, profit, margin
   * @param {number} periods - Number of periods
   */
  getKPITrends: async (metric, periods = 6) => {
    const response = await api.get(`/api/v1/analytics/kpi-trends/${metric}`, {
      params: { periods }
    });
    return response.data;
  },

  // ============================================
  // FORECASTING
  // ============================================

  /**
   * Get cash flow forecast
   * @param {number} days - Forecast period
   * @param {boolean} includePending - Include pending payments
   */
  forecastCashflow: async (days = 90, includePending = true) => {
    const response = await api.get('/api/v1/analytics/forecast/cashflow', {
      params: { days, include_pending: includePending }
    });
    return response.data;
  },

  /**
   * Get inventory demand forecast
   * @param {string} sku - Item SKU
   * @param {number} days - Forecast period
   */
  forecastInventory: async (sku, days = 90) => {
    const response = await api.get(`/api/v1/analytics/forecast/inventory/${sku}`, {
      params: { days }
    });
    return response.data;
  },

  // ============================================
  // INVENTORY ANALYTICS
  // ============================================

  /**
   * Get inventory overview
   */
  getInventoryOverview: async () => {
    const response = await api.get('/api/v1/analytics/inventory/overview');
    return response.data;
  },

  /**
   * Get demand forecast for SKU
   */
  getInventoryDemand: async (sku, days = 90) => {
    const response = await api.get(`/api/v1/analytics/inventory/demand/${sku}`, {
      params: { days }
    });
    return response.data;
  },

  /**
   * Get reorder recommendations
   */
  getReorderRecommendations: async () => {
    const response = await api.get('/api/v1/analytics/inventory/reorder');
    return response.data;
  },

  /**
   * Get ABC analysis
   */
  getABCAnalysis: async () => {
    const response = await api.get('/api/v1/analytics/inventory/abc');
    return response.data;
  },

  // ============================================
  // TREND ANALYSIS
  // ============================================

  /**
   * Get trends overview
   */
  getTrendsOverview: async () => {
    const response = await api.get('/api/v1/analytics/trends');
    return response.data;
  },

  /**
   * Get metric trend
   */
  getMetricTrend: async (metric, period = 'monthly', months = 12) => {
    const response = await api.get(`/api/v1/analytics/trends/${metric}`, {
      params: { period, months }
    });
    return response.data;
  },

  /**
   * Get year-over-year analysis
   */
  getYoYAnalysis: async () => {
    const response = await api.get('/api/v1/analytics/trends/yoy');
    return response.data;
  },

  /**
   * Get seasonality analysis
   */
  getSeasonality: async () => {
    const response = await api.get('/api/v1/analytics/trends/seasonality');
    return response.data;
  },

  // ============================================
  // SCENARIO PLANNING
  // ============================================

  /**
   * Run scenario analysis
   */
  runScenario: async (scenarioType, parameters) => {
    const response = await api.post('/api/v1/analytics/scenario', {
      scenario_type: scenarioType,
      parameters
    });
    return response.data;
  },

  /**
   * Compare multiple scenarios
   */
  compareScenarios: async (scenarios) => {
    const response = await api.post('/api/v1/analytics/scenario/compare', {
      scenarios
    });
    return response.data;
  },

  /**
   * Get best/worst/expected scenarios
   */
  getBWEScenarios: async () => {
    const response = await api.get('/api/v1/analytics/scenario/bwe');
    return response.data;
  },

  // ============================================
  // AI INSIGHTS
  // ============================================

  /**
   * Get AI-generated insights
   */
  getInsights: async () => {
    const response = await api.get('/api/v1/analytics/insights');
    return response.data;
  },

  /**
   * Get weekly summary
   */
  getWeeklySummary: async () => {
    const response = await api.get('/api/v1/analytics/insights/weekly');
    return response.data;
  },

  // ============================================
  // EXPORT
  // ============================================

  /**
   * Export analytics data
   */
  exportData: async (type = 'dashboard', format = 'json') => {
    const response = await api.get('/api/v1/analytics/export', {
      params: { export_type: type, export_format: format },
      responseType: format === 'csv' ? 'blob' : 'json'
    });
    return response.data;
  }
};

export default analyticsApi;
