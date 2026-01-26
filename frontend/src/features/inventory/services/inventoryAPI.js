import api from '@/services/api';

const BASE = '/inventory';

export const inventoryAPI = {
  // Products
  getProducts: (params) => api.get(`${BASE}/products`, { params }).then(r => r.data),
  getProduct: (id) => api.get(`${BASE}/products/${id}`).then(r => r.data),
  createProduct: (data) => api.post(`${BASE}/products`, data).then(r => r.data),
  updateProduct: (id, data) => api.put(`${BASE}/products/${id}`, data).then(r => r.data),
  deactivateProduct: (id) => api.delete(`${BASE}/products/${id}`).then(r => r.data),
  getProductStock: (id) => api.get(`${BASE}/products/${id}/stock`).then(r => r.data),

  // Categories
  getCategories: () => api.get(`${BASE}/categories`).then(r => r.data),
  createCategory: (data) => api.post(`${BASE}/categories`, data).then(r => r.data),

  // UOMs
  getUOMs: () => api.get(`${BASE}/uom`).then(r => r.data),

  // Warehouses
  getWarehouses: () => api.get(`${BASE}/warehouses`).then(r => r.data),
  getWarehouse: (id, includeLocations = false) =>
    api.get(`${BASE}/warehouses/${id}`, { params: { include_locations: includeLocations } }).then(r => r.data),
  createWarehouse: (data) => api.post(`${BASE}/warehouses`, data).then(r => r.data),
  getLocations: (warehouseId, params) =>
    api.get(`${BASE}/warehouses/${warehouseId}/locations`, { params }).then(r => r.data),
  createLocation: (warehouseId, data) =>
    api.post(`${BASE}/warehouses/${warehouseId}/locations`, data).then(r => r.data),
  bulkCreateLocations: (warehouseId, data) =>
    api.post(`${BASE}/warehouses/${warehouseId}/locations/bulk`, data).then(r => r.data),
  getZones: (warehouseId) => api.get(`${BASE}/warehouses/${warehouseId}/zones`).then(r => r.data),

  // Stock
  getStockLevels: (params) => api.get(`${BASE}/stock`, { params }).then(r => r.data),
  getLowStock: (warehouseId) => api.get(`${BASE}/stock/low`, { params: { warehouse_id: warehouseId } }).then(r => r.data),
  getValuationReport: (params) => api.get(`${BASE}/stock/valuation`, { params }).then(r => r.data),

  // Movements
  getMovements: (params) => api.get(`${BASE}/movements`, { params }).then(r => r.data),
  createReceipt: (data) => api.post(`${BASE}/movements/receipt`, data).then(r => r.data),
  createIssue: (data) => api.post(`${BASE}/movements/issue`, data).then(r => r.data),
  createTransfer: (data) => api.post(`${BASE}/movements/transfer`, data).then(r => r.data),
  createAdjustment: (data) => api.post(`${BASE}/movements/adjustment`, data).then(r => r.data),
  confirmMovement: (id) => api.post(`${BASE}/movements/${id}/confirm`).then(r => r.data),
  cancelMovement: (id, reason) => api.post(`${BASE}/movements/${id}/cancel`, null, { params: { reason } }).then(r => r.data),

  // Counts
  getCounts: (params) => api.get(`${BASE}/counts`, { params }).then(r => r.data),
  createCount: (data) => api.post(`${BASE}/counts`, data).then(r => r.data),
  startCount: (id) => api.post(`${BASE}/counts/${id}/start`).then(r => r.data),
  recordCount: (lineId, data) => api.post(`${BASE}/counts/lines/${lineId}/record`, data).then(r => r.data),
  completeCount: (id) => api.post(`${BASE}/counts/${id}/complete`).then(r => r.data),
  approveCount: (id) => api.post(`${BASE}/counts/${id}/approve`).then(r => r.data),

  // Reorder
  getReorderRules: () => api.get(`${BASE}/reorder/rules`).then(r => r.data),
  createReorderRule: (data) => api.post(`${BASE}/reorder/rules`, data).then(r => r.data),
  checkReorderPoints: (createReqs = false) =>
    api.post(`${BASE}/reorder/check`, null, { params: { create_requisitions: createReqs } }).then(r => r.data),
  getRequisitions: (params) => api.get(`${BASE}/requisitions`, { params }).then(r => r.data),
  approveRequisition: (id) => api.post(`${BASE}/requisitions/${id}/approve`).then(r => r.data),
};

export default inventoryAPI;
