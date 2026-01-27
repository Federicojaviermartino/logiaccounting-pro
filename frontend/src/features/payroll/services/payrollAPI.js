import api from '../../../services/api';

const BASE_URL = '/payroll';

export const payrollAPI = {
  // Employees
  getEmployees: (params = {}) => api.get(`${BASE_URL}/employees`, { params }),
  getEmployee: (id) => api.get(`${BASE_URL}/employees/${id}`),
  createEmployee: (data) => api.post(`${BASE_URL}/employees`, data),
  updateEmployee: (id, data) => api.put(`${BASE_URL}/employees/${id}`, data),
  updateTaxInfo: (id, data) => api.put(`${BASE_URL}/employees/${id}/tax-info`, data),
  terminateEmployee: (id, data) => api.post(`${BASE_URL}/employees/${id}/terminate`, data),

  // Contracts
  getContracts: (employeeId) => api.get(`${BASE_URL}/employees/${employeeId}/contracts`),
  createContract: (employeeId, data) => api.post(`${BASE_URL}/employees/${employeeId}/contracts`, data),
  updateContract: (contractId, data) => api.put(`${BASE_URL}/employees/contracts/${contractId}`, data),

  // Pay Periods
  getPayPeriods: (params = {}) => api.get(`${BASE_URL}/payroll/periods`, { params }),
  createPayPeriod: (data) => api.post(`${BASE_URL}/payroll/periods`, data),

  // Payroll Runs
  getPayrollRuns: (params = {}) => api.get(`${BASE_URL}/payroll/runs`, { params }),
  getPayrollRun: (id) => api.get(`${BASE_URL}/payroll/runs/${id}`),
  createPayrollRun: (data) => api.post(`${BASE_URL}/payroll/runs`, data),
  calculatePayroll: (runId) => api.post(`${BASE_URL}/payroll/runs/${runId}/calculate`),
  approvePayroll: (runId) => api.post(`${BASE_URL}/payroll/runs/${runId}/approve`),
  processPayments: (runId) => api.post(`${BASE_URL}/payroll/runs/${runId}/process`),

  // Deductions
  getDeductionTypes: (params = {}) => api.get(`${BASE_URL}/deductions/types`, { params }),
  createDeductionType: (data) => api.post(`${BASE_URL}/deductions/types`, data),
  getEmployeeDeductions: (employeeId) => api.get(`${BASE_URL}/deductions/employee/${employeeId}`),
  assignDeduction: (employeeId, data) => api.post(`${BASE_URL}/deductions/employee/${employeeId}`, data),

  // Benefits
  getBenefitTypes: (params = {}) => api.get(`${BASE_URL}/deductions/benefits/types`, { params }),
  createBenefitType: (data) => api.post(`${BASE_URL}/deductions/benefits/types`, data),

  // Time Off
  getTimeOffRequests: (params = {}) => api.get(`${BASE_URL}/time-off/requests`, { params }),
  createTimeOffRequest: (employeeId, data) => api.post(`${BASE_URL}/time-off/requests`, { employee_id: employeeId, ...data }),
  reviewTimeOffRequest: (requestId, data) => api.post(`${BASE_URL}/time-off/requests/${requestId}/review`, data),
  cancelTimeOffRequest: (requestId) => api.post(`${BASE_URL}/time-off/requests/${requestId}/cancel`),
  getTimeOffBalances: (employeeId, year = null) => api.get(`${BASE_URL}/time-off/balances/${employeeId}`, { params: { year } }),
};

export default payrollAPI;
