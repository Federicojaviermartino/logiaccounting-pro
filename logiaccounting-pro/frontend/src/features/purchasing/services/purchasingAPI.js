import api from '@/services/api';

const BASE = '/purchasing';

export const purchasingAPI = {
  // Suppliers
  getSuppliers: (params) => api.get(`${BASE}/suppliers`, { params }).then(r => r.data),
  getSuppliersSummary: () => api.get(`${BASE}/suppliers/summary`).then(r => r.data),
  getSupplier: (id) => api.get(`${BASE}/suppliers/${id}`).then(r => r.data),
  createSupplier: (data) => api.post(`${BASE}/suppliers`, data).then(r => r.data),
  updateSupplier: (id, data) => api.put(`${BASE}/suppliers/${id}`, data).then(r => r.data),
  approveSupplier: (id, approve = true) => api.post(`${BASE}/suppliers/${id}/approve`, null, { params: { approve } }).then(r => r.data),

  // Supplier Contacts
  addContact: (supplierId, data) => api.post(`${BASE}/suppliers/${supplierId}/contacts`, data).then(r => r.data),
  updateContact: (contactId, data) => api.put(`${BASE}/suppliers/contacts/${contactId}`, data).then(r => r.data),
  deleteContact: (contactId) => api.delete(`${BASE}/suppliers/contacts/${contactId}`).then(r => r.data),

  // Supplier Prices
  getSupplierPrices: (supplierId) => api.get(`${BASE}/suppliers/${supplierId}/prices`).then(r => r.data),
  addPrice: (supplierId, data) => api.post(`${BASE}/suppliers/${supplierId}/prices`, data).then(r => r.data),
  getProductSuppliers: (productId, quantity = 1) =>
    api.get(`${BASE}/suppliers/products/${productId}/suppliers`, { params: { quantity } }).then(r => r.data),

  // Purchase Orders
  getOrders: (params) => api.get(`${BASE}/purchase-orders`, { params }).then(r => r.data),
  getDashboard: () => api.get(`${BASE}/purchase-orders/dashboard`).then(r => r.data),
  getOrder: (id) => api.get(`${BASE}/purchase-orders/${id}`).then(r => r.data),
  createOrder: (data) => api.post(`${BASE}/purchase-orders`, data).then(r => r.data),
  updateOrder: (id, data) => api.put(`${BASE}/purchase-orders/${id}`, data).then(r => r.data),
  addOrderLine: (orderId, data) => api.post(`${BASE}/purchase-orders/${orderId}/lines`, data).then(r => r.data),
  updateOrderLine: (lineId, data) => api.put(`${BASE}/purchase-orders/lines/${lineId}`, data).then(r => r.data),
  deleteOrderLine: (lineId) => api.delete(`${BASE}/purchase-orders/lines/${lineId}`).then(r => r.data),
  submitOrder: (id) => api.post(`${BASE}/purchase-orders/${id}/submit`).then(r => r.data),
  approveOrder: (id, action, comments) => api.post(`${BASE}/purchase-orders/${id}/approve`, { action, comments }).then(r => r.data),
  sendOrder: (id) => api.post(`${BASE}/purchase-orders/${id}/send`).then(r => r.data),
  cancelOrder: (id, reason) => api.post(`${BASE}/purchase-orders/${id}/cancel`, { reason }).then(r => r.data),

  // Goods Receipts
  getReceipts: (params) => api.get(`${BASE}/goods-receipts`, { params }).then(r => r.data),
  getReceipt: (id) => api.get(`${BASE}/goods-receipts/${id}`).then(r => r.data),
  createReceiptFromPO: (data) => api.post(`${BASE}/goods-receipts/from-po`, data).then(r => r.data),
  createDirectReceipt: (data) => api.post(`${BASE}/goods-receipts/direct`, data).then(r => r.data),
  updateReceiptLine: (lineId, data) => api.put(`${BASE}/goods-receipts/lines/${lineId}`, data).then(r => r.data),
  postReceipt: (id) => api.post(`${BASE}/goods-receipts/${id}/post`).then(r => r.data),
  cancelReceipt: (id, reason) => api.post(`${BASE}/goods-receipts/${id}/cancel`, null, { params: { reason } }).then(r => r.data),

  // Supplier Invoices
  getInvoices: (params) => api.get(`${BASE}/supplier-invoices`, { params }).then(r => r.data),
  getAgingReport: () => api.get(`${BASE}/supplier-invoices/aging`).then(r => r.data),
  getInvoice: (id) => api.get(`${BASE}/supplier-invoices/${id}`).then(r => r.data),
  createInvoice: (data) => api.post(`${BASE}/supplier-invoices`, data).then(r => r.data),
  createInvoiceFromReceipt: (data) => api.post(`${BASE}/supplier-invoices/from-receipt`, data).then(r => r.data),
  performMatching: (id) => api.post(`${BASE}/supplier-invoices/${id}/match`).then(r => r.data),
  approveInvoice: (id) => api.post(`${BASE}/supplier-invoices/${id}/approve`).then(r => r.data),
  postInvoice: (id) => api.post(`${BASE}/supplier-invoices/${id}/post`).then(r => r.data),
  recordPayment: (id, data) => api.post(`${BASE}/supplier-invoices/${id}/payment`, data).then(r => r.data),
};

export default purchasingAPI;
