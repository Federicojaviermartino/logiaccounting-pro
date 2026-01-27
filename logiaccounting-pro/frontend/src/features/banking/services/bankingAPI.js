/**
 * Banking API Service
 * API calls for banking and cash management
 */

import axios from 'axios';

const API_BASE = '/api/v1/banking';

// Bank Accounts
export const bankAccountsAPI = {
  list: (params = {}) => axios.get(`${API_BASE}/accounts`, { params }),
  getSummary: (currency = null) => axios.get(`${API_BASE}/accounts/summary`, { params: { currency } }),
  getCashPosition: (baseCurrency = 'USD') => axios.get(`${API_BASE}/accounts/cash-position`, { params: { base_currency: baseCurrency } }),
  create: (data) => axios.post(`${API_BASE}/accounts`, data),
  get: (id) => axios.get(`${API_BASE}/accounts/${id}`),
  update: (id, data) => axios.put(`${API_BASE}/accounts/${id}`, data),
  setPrimary: (id) => axios.post(`${API_BASE}/accounts/${id}/set-primary`),
  deactivate: (id) => axios.post(`${API_BASE}/accounts/${id}/deactivate`),
  getBalanceHistory: (id, startDate, endDate) => axios.get(`${API_BASE}/accounts/${id}/balances`, { params: { start_date: startDate, end_date: endDate } }),
};

// Bank Transactions
export const transactionsAPI = {
  list: (params = {}) => axios.get(`${API_BASE}/transactions`, { params }),
  create: (data) => axios.post(`${API_BASE}/transactions`, data),
  get: (id) => axios.get(`${API_BASE}/transactions/${id}`),
  update: (id, data) => axios.put(`${API_BASE}/transactions/${id}`, data),
  getUnmatched: (accountId = null, daysBack = 30) => axios.get(`${API_BASE}/transactions/unmatched`, { params: { account_id: accountId, days_back: daysBack } }),
  match: (id, matchType, matchId) => axios.post(`${API_BASE}/transactions/${id}/match`, { transaction_id: id, match_type: matchType, match_id: matchId }),
  unmatch: (id) => axios.post(`${API_BASE}/transactions/${id}/unmatch`),
  categorize: (transactionIds, category) => axios.post(`${API_BASE}/transactions/categorize`, { transaction_ids: transactionIds, category }),
  importStatement: (accountId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return axios.post(`${API_BASE}/transactions/import/${accountId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};

// Bank Reconciliation
export const reconciliationAPI = {
  list: (params = {}) => axios.get(`${API_BASE}/reconciliation`, { params }),
  create: (data) => axios.post(`${API_BASE}/reconciliation`, data),
  get: (id) => axios.get(`${API_BASE}/reconciliation/${id}`),
  addLine: (reconciliationId, data) => axios.post(`${API_BASE}/reconciliation/${reconciliationId}/lines`, data),
  removeLine: (reconciliationId, lineId) => axios.delete(`${API_BASE}/reconciliation/${reconciliationId}/lines/${lineId}`),
  autoMatch: (reconciliationId, applyRules = true, matchThreshold = 0.8) => axios.post(`${API_BASE}/reconciliation/${reconciliationId}/auto-match`, null, { params: { apply_rules: applyRules, match_threshold: matchThreshold } }),
  complete: (reconciliationId) => axios.post(`${API_BASE}/reconciliation/${reconciliationId}/complete`),
};

// Payment Processing
export const paymentsAPI = {
  listBatches: (params = {}) => axios.get(`${API_BASE}/payments/batches`, { params }),
  createBatch: (data) => axios.post(`${API_BASE}/payments/batches`, data),
  getBatch: (id) => axios.get(`${API_BASE}/payments/batches/${id}`),
  updateBatch: (id, data) => axios.put(`${API_BASE}/payments/batches/${id}`, data),
  addInstruction: (batchId, data) => axios.post(`${API_BASE}/payments/batches/${batchId}/instructions`, data),
  removeInstruction: (batchId, instructionId) => axios.delete(`${API_BASE}/payments/batches/${batchId}/instructions/${instructionId}`),
  submitForApproval: (batchId) => axios.post(`${API_BASE}/payments/batches/${batchId}/submit`),
  approveBatch: (batchId, approved, notes = null) => axios.post(`${API_BASE}/payments/batches/${batchId}/approve`, { approved, notes }),
  processBatch: (batchId) => axios.post(`${API_BASE}/payments/batches/${batchId}/process`),
  generateFile: (batchId, fileFormat = 'nacha') => axios.post(`${API_BASE}/payments/batches/${batchId}/generate-file`, null, { params: { file_format: fileFormat } }),
  markSent: (batchId) => axios.post(`${API_BASE}/payments/batches/${batchId}/mark-sent`),
  completeBatch: (batchId) => axios.post(`${API_BASE}/payments/batches/${batchId}/complete`),
  cancelBatch: (batchId) => axios.post(`${API_BASE}/payments/batches/${batchId}/cancel`),
};

// Cash Flow Forecasting
export const cashflowAPI = {
  getSummary: () => axios.get(`${API_BASE}/cashflow/summary`),
  listForecasts: (params = {}) => axios.get(`${API_BASE}/cashflow/forecasts`, { params }),
  createForecast: (data) => axios.post(`${API_BASE}/cashflow/forecasts`, data),
  getForecast: (id) => axios.get(`${API_BASE}/cashflow/forecasts/${id}`),
  generateForecast: (id) => axios.post(`${API_BASE}/cashflow/forecasts/${id}/generate`),
  listPlannedTransactions: (params = {}) => axios.get(`${API_BASE}/cashflow/planned-transactions`, { params }),
  createPlannedTransaction: (data) => axios.post(`${API_BASE}/cashflow/planned-transactions`, data),
  updatePlannedTransaction: (id, data) => axios.put(`${API_BASE}/cashflow/planned-transactions/${id}`, data),
  createPositionSnapshot: () => axios.post(`${API_BASE}/cashflow/positions/snapshot`),
};

export default {
  accounts: bankAccountsAPI,
  transactions: transactionsAPI,
  reconciliation: reconciliationAPI,
  payments: paymentsAPI,
  cashflow: cashflowAPI,
};
