/**
 * Reporting API Service
 */
import api from '../../../services/api';

const reportingAPI = {
  // ==========================================
  // FINANCIAL STATEMENTS
  // ==========================================
  
  /**
   * Get Balance Sheet
   */
  getBalanceSheet: (params) => {
    const queryParams = new URLSearchParams();
    queryParams.append('as_of_date', params.asOfDate);
    if (params.comparePriorPeriod) queryParams.append('compare_prior_period', 'true');
    if (params.departmentId) queryParams.append('department_id', params.departmentId);
    if (params.showZeroBalances) queryParams.append('show_zero_balances', 'true');
    return api.get(`/reporting/financial-statements/balance-sheet?${queryParams}`);
  },

  /**
   * Get Income Statement
   */
  getIncomeStatement: (params) => {
    const queryParams = new URLSearchParams();
    queryParams.append('start_date', params.startDate);
    queryParams.append('end_date', params.endDate);
    if (params.comparePriorPeriod) queryParams.append('compare_prior_period', 'true');
    if (params.departmentId) queryParams.append('department_id', params.departmentId);
    if (params.showZeroBalances) queryParams.append('show_zero_balances', 'true');
    return api.get(`/reporting/financial-statements/income-statement?${queryParams}`);
  },

  /**
   * Get Cash Flow Statement
   */
  getCashFlow: (params) => {
    const queryParams = new URLSearchParams();
    queryParams.append('start_date', params.startDate);
    queryParams.append('end_date', params.endDate);
    if (params.departmentId) queryParams.append('department_id', params.departmentId);
    return api.get(`/reporting/financial-statements/cash-flow?${queryParams}`);
  },

  /**
   * Get Trial Balance
   */
  getTrialBalance: (params) => {
    const queryParams = new URLSearchParams();
    queryParams.append('as_of_date', params.asOfDate);
    if (params.departmentId) queryParams.append('department_id', params.departmentId);
    if (params.showZeroBalances) queryParams.append('show_zero_balances', 'true');
    return api.get(`/reporting/financial-statements/trial-balance?${queryParams}`);
  },

  // ==========================================
  // DASHBOARD
  // ==========================================

  /**
   * Get Dashboard Summary
   */
  getDashboardSummary: (asOfDate = null) => {
    const queryParams = asOfDate ? `?as_of_date=${asOfDate}` : '';
    return api.get(`/reporting/dashboard/summary${queryParams}`);
  },

  /**
   * Get KPIs
   */
  getKPIs: (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.asOfDate) queryParams.append('as_of_date', params.asOfDate);
    if (params.category) queryParams.append('category', params.category);
    const query = queryParams.toString();
    return api.get(`/reporting/dashboard/kpis${query ? '?' + query : ''}`);
  },

  // ==========================================
  // EXPORTS
  // ==========================================

  /**
   * Export Balance Sheet to Excel
   */
  exportBalanceSheetExcel: (params) => {
    const queryParams = new URLSearchParams();
    queryParams.append('as_of_date', params.asOfDate);
    if (params.comparePriorPeriod) queryParams.append('compare_prior_period', 'true');
    return api.get(`/reporting/export/balance-sheet/excel?${queryParams}`, {
      responseType: 'blob'
    });
  },

  /**
   * Export Balance Sheet to PDF
   */
  exportBalanceSheetPDF: (params) => {
    const queryParams = new URLSearchParams();
    queryParams.append('as_of_date', params.asOfDate);
    if (params.comparePriorPeriod) queryParams.append('compare_prior_period', 'true');
    return api.get(`/reporting/export/balance-sheet/pdf?${queryParams}`, {
      responseType: 'blob'
    });
  },

  /**
   * Export Income Statement to Excel
   */
  exportIncomeStatementExcel: (params) => {
    const queryParams = new URLSearchParams();
    queryParams.append('start_date', params.startDate);
    queryParams.append('end_date', params.endDate);
    if (params.comparePriorPeriod) queryParams.append('compare_prior_period', 'true');
    return api.get(`/reporting/export/income-statement/excel?${queryParams}`, {
      responseType: 'blob'
    });
  },

  /**
   * Export Income Statement to PDF
   */
  exportIncomeStatementPDF: (params) => {
    const queryParams = new URLSearchParams();
    queryParams.append('start_date', params.startDate);
    queryParams.append('end_date', params.endDate);
    if (params.comparePriorPeriod) queryParams.append('compare_prior_period', 'true');
    return api.get(`/reporting/export/income-statement/pdf?${queryParams}`, {
      responseType: 'blob'
    });
  },

  /**
   * Export Trial Balance to Excel
   */
  exportTrialBalanceExcel: (params) => {
    const queryParams = new URLSearchParams();
    queryParams.append('as_of_date', params.asOfDate);
    if (params.showZeroBalances) queryParams.append('show_zero_balances', 'true');
    return api.get(`/reporting/export/trial-balance/excel?${queryParams}`, {
      responseType: 'blob'
    });
  },

  // ==========================================
  // UTILITY
  // ==========================================

  /**
   * Download blob as file
   */
  downloadBlob: (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
};

export default reportingAPI;
