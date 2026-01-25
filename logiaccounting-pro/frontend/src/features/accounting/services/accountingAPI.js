import api from '@/services/api';

const BASE = '/accounting';

export const accountingAPI = {
  // Chart of Accounts
  getAccountTypes: () => api.get(`${BASE}/accounts/types`).then(r => r.data),
  getAccountTemplates: () => api.get(`${BASE}/accounts/templates`).then(r => r.data),
  importTemplate: (name) => api.post(`${BASE}/accounts/import-template`, null, { params: { template_name: name } }).then(r => r.data),
  getAccountTree: (params) => api.get(`${BASE}/accounts/tree`, { params }).then(r => r.data),
  getAccounts: (params) => api.get(`${BASE}/accounts`, { params }).then(r => r.data),
  getAccount: (id) => api.get(`${BASE}/accounts/${id}`).then(r => r.data),
  createAccount: (data) => api.post(`${BASE}/accounts`, data).then(r => r.data),
  updateAccount: (id, data) => api.put(`${BASE}/accounts/${id}`, data).then(r => r.data),
  deactivateAccount: (id) => api.delete(`${BASE}/accounts/${id}`).then(r => r.data),

  // Journal Entries
  getJournalEntries: (params) => api.get(`${BASE}/journal`, { params }).then(r => r.data),
  getJournalEntry: (id) => api.get(`${BASE}/journal/${id}`).then(r => r.data),
  createJournalEntry: (data) => api.post(`${BASE}/journal`, data).then(r => r.data),
  updateJournalEntry: (id, data) => api.put(`${BASE}/journal/${id}`, data).then(r => r.data),
  deleteJournalEntry: (id) => api.delete(`${BASE}/journal/${id}`).then(r => r.data),
  submitEntry: (id, notes) => api.post(`${BASE}/journal/${id}/submit`, { notes }).then(r => r.data),
  approveEntry: (id, data) => api.post(`${BASE}/journal/${id}/approve`, data).then(r => r.data),
  postEntry: (id) => api.post(`${BASE}/journal/${id}/post`).then(r => r.data),
  reverseEntry: (id, data) => api.post(`${BASE}/journal/${id}/reverse`, data).then(r => r.data),
  batchPostEntries: (ids) => api.post(`${BASE}/journal/batch/post`, { entry_ids: ids }).then(r => r.data),

  // Ledger & Reports
  getAccountLedger: (id, params) => api.get(`${BASE}/ledger/account/${id}`, { params }).then(r => r.data),
  getTrialBalance: (params) => api.get(`${BASE}/ledger/trial-balance`, { params }).then(r => r.data),
  getBalanceSheet: (params) => api.get(`${BASE}/ledger/statements/balance-sheet`, { params }).then(r => r.data),
  getIncomeStatement: (params) => api.get(`${BASE}/ledger/statements/income-statement`, { params }).then(r => r.data),
  getCashFlow: (params) => api.get(`${BASE}/ledger/statements/cash-flow`, { params }).then(r => r.data),

  // Fiscal Periods
  getFiscalYears: (params) => api.get(`${BASE}/fiscal-years`, { params }).then(r => r.data),
  createFiscalYear: (data) => api.post(`${BASE}/fiscal-years`, null, { params: data }).then(r => r.data),
  getCurrentPeriod: (date) => api.get(`${BASE}/fiscal-years/current-period`, { params: { as_of_date: date } }).then(r => r.data),
  closePeriod: (id, notes) => api.post(`${BASE}/periods/${id}/close`, null, { params: { notes } }).then(r => r.data),
  closeFiscalYear: (id) => api.post(`${BASE}/fiscal-years/${id}/close`).then(r => r.data),

  // Bank Reconciliation
  getBankAccounts: () => api.get(`${BASE}/bank-accounts`).then(r => r.data),
  createBankAccount: (data) => api.post(`${BASE}/bank-accounts`, null, { params: data }).then(r => r.data),
  importBankStatement: (bankId, file) => {
    const form = new FormData();
    form.append('file', file);
    return api.post(`${BASE}/bank-accounts/${bankId}/import`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(r => r.data);
  },
  startReconciliation: (data) => api.post(`${BASE}/reconciliations`, null, { params: data }).then(r => r.data),
  getReconciliation: (id) => api.get(`${BASE}/reconciliations/${id}`).then(r => r.data),
  autoMatchTransactions: (id) => api.post(`${BASE}/reconciliations/${id}/auto-match`).then(r => r.data),
  manualMatch: (reconId, transId, lineId) => api.post(`${BASE}/reconciliations/${reconId}/match`, null, { params: { transaction_id: transId, line_id: lineId } }).then(r => r.data),
  completeReconciliation: (id, notes) => api.post(`${BASE}/reconciliations/${id}/complete`, null, { params: { notes } }).then(r => r.data),
};

export default accountingAPI;
