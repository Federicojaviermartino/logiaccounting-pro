/**
 * Payments API Service
 */

import apiClient from './client';

export interface Payment {
  id: string;
  type: 'receivable' | 'payable';
  amount: number;
  dueDate: string;
  paidDate?: string;
  status: 'pending' | 'paid' | 'overdue' | 'cancelled';
  description: string;
  clientId?: string;
  clientName?: string;
  vendorId?: string;
  vendorName?: string;
}

export interface PaymentFilters {
  type?: 'receivable' | 'payable';
  status?: Payment['status'];
  startDate?: string;
  endDate?: string;
}

export const paymentsApi = {
  getPayments: (filters?: PaymentFilters) =>
    apiClient.get<Payment[]>('/payments', { params: filters }),

  getPayment: (id: string) =>
    apiClient.get<Payment>(`/payments/${id}`),

  createPayment: (data: Omit<Payment, 'id' | 'status'>) =>
    apiClient.post<Payment>('/payments', data),

  updatePayment: (id: string, data: Partial<Payment>) =>
    apiClient.put<Payment>(`/payments/${id}`, data),

  deletePayment: (id: string) => apiClient.delete(`/payments/${id}`),

  recordPayment: (id: string, paidDate: string) =>
    apiClient.post<Payment>(`/payments/${id}/record`, { paidDate }),

  cancelPayment: (id: string, reason?: string) =>
    apiClient.post<Payment>(`/payments/${id}/cancel`, { reason }),

  // Summary
  getSummary: () =>
    apiClient.get<{
      totalReceivable: number;
      totalPayable: number;
      overdueReceivable: number;
      overduePayable: number;
      upcomingPayments: Payment[];
    }>('/payments/summary'),

  // Reminders
  getOverdue: () =>
    apiClient.get<Payment[]>('/payments/overdue'),

  getUpcoming: (days: number = 7) =>
    apiClient.get<Payment[]>('/payments/upcoming', { params: { days } }),
};

export default paymentsApi;
