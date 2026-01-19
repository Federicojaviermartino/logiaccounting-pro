/**
 * Transactions API Service
 */

import apiClient from './client';

export interface Transaction {
  id: string;
  type: 'income' | 'expense';
  category: string;
  amount: number;
  taxAmount: number;
  date: string;
  description: string;
  vendorName?: string;
  invoiceNumber?: string;
  invoiceUrl?: string;
  projectId?: string;
}

export interface TransactionFilters {
  type?: 'income' | 'expense';
  startDate?: string;
  endDate?: string;
  category?: string;
  projectId?: string;
}

export const transactionsApi = {
  getTransactions: (filters?: TransactionFilters) =>
    apiClient.get<Transaction[]>('/transactions', { params: filters }),

  getTransaction: (id: string) =>
    apiClient.get<Transaction>(`/transactions/${id}`),

  createTransaction: (data: Omit<Transaction, 'id'>) =>
    apiClient.post<Transaction>('/transactions', data),

  updateTransaction: (id: string, data: Partial<Transaction>) =>
    apiClient.put<Transaction>(`/transactions/${id}`, data),

  deleteTransaction: (id: string) => apiClient.delete(`/transactions/${id}`),

  // Upload receipt
  uploadReceipt: (transactionId: string, file: FormData) =>
    apiClient.post(`/transactions/${transactionId}/receipt`, file, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // OCR receipt
  processReceipt: (imageData: FormData) =>
    apiClient.post<Partial<Transaction>>('/transactions/ocr', imageData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Summary
  getSummary: (startDate: string, endDate: string) =>
    apiClient.get<{
      totalIncome: number;
      totalExpenses: number;
      netProfit: number;
      byCategory: { category: string; amount: number }[];
    }>('/transactions/summary', { params: { startDate, endDate } }),
};

export default transactionsApi;
