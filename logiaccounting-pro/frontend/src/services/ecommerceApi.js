/**
 * E-commerce API Service
 */

const API_BASE = '/api/v1/ecommerce';

// Platforms
export const getPlatforms = async () => {
  const response = await fetch(`${API_BASE}/platforms`);
  return response.json();
};

// Stores
export const getStores = async () => {
  const response = await fetch(`${API_BASE}/stores`);
  return response.json();
};

export const getStore = async (storeId) => {
  const response = await fetch(`${API_BASE}/stores/${storeId}`);
  return response.json();
};

export const connectStore = async (storeData) => {
  const response = await fetch(`${API_BASE}/stores`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(storeData)
  });
  return response.json();
};

export const updateStore = async (storeId, storeData) => {
  const response = await fetch(`${API_BASE}/stores/${storeId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(storeData)
  });
  return response.json();
};

export const disconnectStore = async (storeId) => {
  const response = await fetch(`${API_BASE}/stores/${storeId}`, {
    method: 'DELETE'
  });
  return response.json();
};

export const testConnection = async (storeId) => {
  const response = await fetch(`${API_BASE}/stores/${storeId}/test`, {
    method: 'POST'
  });
  return response.json();
};

// Products
export const getStoreProducts = async (storeId, limit = 50, page = 1) => {
  const response = await fetch(
    `${API_BASE}/stores/${storeId}/products?limit=${limit}&page=${page}`
  );
  return response.json();
};

// Inventory
export const getStoreInventory = async (storeId) => {
  const response = await fetch(`${API_BASE}/stores/${storeId}/inventory`);
  return response.json();
};

// Orders
export const getStoreOrders = async (storeId, status = null, limit = 50) => {
  let url = `${API_BASE}/stores/${storeId}/orders?limit=${limit}`;
  if (status) url += `&status=${status}`;
  const response = await fetch(url);
  return response.json();
};

// Sync
export const syncProducts = async (storeId, options = {}) => {
  const response = await fetch(`${API_BASE}/sync/products`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ store_id: storeId, options })
  });
  return response.json();
};

export const syncInventory = async (storeId) => {
  const response = await fetch(`${API_BASE}/sync/inventory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ store_id: storeId })
  });
  return response.json();
};

export const importOrders = async (storeId) => {
  const response = await fetch(`${API_BASE}/sync/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ store_id: storeId })
  });
  return response.json();
};

export const getProductMappings = async (storeId = null) => {
  let url = `${API_BASE}/sync/products/mappings`;
  if (storeId) url += `?store_id=${storeId}`;
  const response = await fetch(url);
  return response.json();
};

export const getLowStockAlerts = async (storeId = null) => {
  let url = `${API_BASE}/sync/inventory/alerts`;
  if (storeId) url += `?store_id=${storeId}`;
  const response = await fetch(url);
  return response.json();
};

export const getImportedOrders = async (storeId = null, limit = 50) => {
  let url = `${API_BASE}/sync/orders?limit=${limit}`;
  if (storeId) url += `&store_id=${storeId}`;
  const response = await fetch(url);
  return response.json();
};

// Analytics
export const getDashboardSummary = async () => {
  const response = await fetch(`${API_BASE}/analytics/summary`);
  return response.json();
};

export const getRevenueByStore = async () => {
  const response = await fetch(`${API_BASE}/analytics/revenue`);
  return response.json();
};

export const getTopProducts = async (limit = 10) => {
  const response = await fetch(`${API_BASE}/analytics/top-products?limit=${limit}`);
  return response.json();
};

export const getSyncStatus = async () => {
  const response = await fetch(`${API_BASE}/analytics/sync-status`);
  return response.json();
};
