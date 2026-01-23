/**
 * Invoices Service - API calls for invoice management
 */

import { apiClient } from './client';

export interface Invoice {
  id: string;
  invoiceNumber: string;
  customerId: string;
  customerName: string;
  status: 'draft' | 'pending' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  issueDate: string;
  dueDate: string;
  subtotal: number;
  tax: number;
  total: number;
  currency: string;
  items: InvoiceItem[];
  notes?: string;
  paymentTerms?: string;
  createdAt: string;
  updatedAt: string;
}

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  taxRate: number;
  total: number;
}

export interface InvoiceFilters {
  status?: string;
  customerId?: string;
  startDate?: string;
  endDate?: string;
  search?: string;
  page?: number;
  limit?: number;
}

export interface InvoiceStats {
  totalRevenue: number;
  pendingAmount: number;
  overdueAmount: number;
  invoiceCount: number;
  paidCount: number;
  pendingCount: number;
  overdueCount: number;
}

export interface CreateInvoiceData {
  customerId: string;
  issueDate: string;
  dueDate: string;
  items: Omit<InvoiceItem, 'id'>[];
  notes?: string;
  paymentTerms?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export const invoicesService = {
  async getAll(filters?: InvoiceFilters): Promise<PaginatedResponse<Invoice>> {
    const response = await apiClient.get<PaginatedResponse<Invoice>>('/invoices', {
      params: filters,
    });
    return response.data;
  },

  async getById(id: string): Promise<Invoice> {
    const response = await apiClient.get<Invoice>(`/invoices/${id}`);
    return response.data;
  },

  async create(data: CreateInvoiceData): Promise<Invoice> {
    const response = await apiClient.post<Invoice>('/invoices', data);
    return response.data;
  },

  async update(id: string, data: Partial<CreateInvoiceData>): Promise<Invoice> {
    const response = await apiClient.patch<Invoice>(`/invoices/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/invoices/${id}`);
  },

  async getStats(): Promise<InvoiceStats> {
    const response = await apiClient.get<InvoiceStats>('/invoices/stats');
    return response.data;
  },

  async markAsPaid(id: string, paymentDate?: string): Promise<Invoice> {
    const response = await apiClient.post<Invoice>(`/invoices/${id}/mark-paid`, {
      paymentDate: paymentDate || new Date().toISOString(),
    });
    return response.data;
  },

  async sendEmail(id: string, email?: string): Promise<{ message: string }> {
    const response = await apiClient.post(`/invoices/${id}/send`, { email });
    return response.data;
  },

  async downloadPdf(id: string): Promise<Blob> {
    const response = await apiClient.get(`/invoices/${id}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },

  async duplicate(id: string): Promise<Invoice> {
    const response = await apiClient.post<Invoice>(`/invoices/${id}/duplicate`);
    return response.data;
  },

  async getOverdue(): Promise<Invoice[]> {
    const response = await apiClient.get<Invoice[]>('/invoices/overdue');
    return response.data;
  },

  async getRecent(limit: number = 10): Promise<Invoice[]> {
    const response = await apiClient.get<Invoice[]>('/invoices/recent', {
      params: { limit },
    });
    return response.data;
  },
};
