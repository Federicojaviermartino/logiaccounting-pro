# LogiAccounting Pro - Phase 9 Tasks Part 3

## FRONTEND COMPONENTS (EU/US Market)

---

## TASK 12: API SERVICE

### 12.1 Create E-commerce API Service

**File:** `frontend/src/services/ecommerceApi.js`

```javascript
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
```

---

## TASK 13: STORE MANAGEMENT PAGE

### 13.1 Create E-commerce Stores Page

**File:** `frontend/src/pages/EcommerceStores.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  getStores,
  getPlatforms,
  connectStore,
  disconnectStore,
  testConnection,
  syncProducts,
  syncInventory,
  importOrders
} from '../services/ecommerceApi';

const EcommerceStores = () => {
  const { t } = useTranslation();
  const [stores, setStores] = useState([]);
  const [platforms, setPlatforms] = useState({});
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [syncing, setSyncing] = useState({});
  const [newStore, setNewStore] = useState({
    platform: 'shopify',
    name: '',
    credentials: {}
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [storesData, platformsData] = await Promise.all([
        getStores(),
        getPlatforms()
      ]);
      setStores(storesData);
      setPlatforms(platformsData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const store = await connectStore(newStore);
      setStores([...stores, store]);
      setShowModal(false);
      setNewStore({ platform: 'shopify', name: '', credentials: {} });
    } catch (error) {
      console.error('Error connecting store:', error);
    }
  };

  const handleDisconnect = async (storeId) => {
    if (!confirm('Are you sure you want to disconnect this store?')) return;
    
    try {
      await disconnectStore(storeId);
      setStores(stores.filter(s => s.id !== storeId));
    } catch (error) {
      console.error('Error disconnecting store:', error);
    }
  };

  const handleTestConnection = async (storeId) => {
    try {
      const result = await testConnection(storeId);
      alert(result.success ? 'Connection successful!' : 'Connection failed');
    } catch (error) {
      alert('Connection test failed');
    }
  };

  const handleSync = async (storeId, syncType) => {
    setSyncing({ ...syncing, [`${storeId}-${syncType}`]: true });
    
    try {
      if (syncType === 'products') {
        await syncProducts(storeId);
      } else if (syncType === 'inventory') {
        await syncInventory(storeId);
      } else if (syncType === 'orders') {
        await importOrders(storeId);
      }
      loadData();
    } catch (error) {
      console.error(`Error syncing ${syncType}:`, error);
    } finally {
      setSyncing({ ...syncing, [`${storeId}-${syncType}`]: false });
    }
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      shopify: '🟢',
      woocommerce: '🔵',
      amazon: '🟠'
    };
    return icons[platform] || '🏪';
  };

  const getStatusBadge = (status) => {
    const badges = {
      connected: 'badge-success',
      pending: 'badge-warning',
      error: 'badge-danger',
      disabled: 'badge-secondary'
    };
    return badges[status] || 'badge-secondary';
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading stores...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">E-commerce Stores</h1>
          <p className="page-subtitle">
            Connect and manage your online stores
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowModal(true)}
        >
          <span className="btn-icon">+</span>
          Connect Store
        </button>
      </div>

      {/* Store Cards */}
      <div className="stores-grid">
        {stores.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🛒</div>
            <h3>No stores connected</h3>
            <p>Connect your first e-commerce store to start syncing</p>
            <button
              className="btn btn-primary"
              onClick={() => setShowModal(true)}
            >
              Connect Store
            </button>
          </div>
        ) : (
          stores.map(store => (
            <div key={store.id} className="store-card">
              <div className="store-header">
                <div className="store-platform">
                  <span className="platform-icon">
                    {getPlatformIcon(store.platform)}
                  </span>
                  <div>
                    <h3 className="store-name">{store.name}</h3>
                    <span className="platform-name">
                      {platforms[store.platform]?.name || store.platform}
                    </span>
                  </div>
                </div>
                <span className={`badge ${getStatusBadge(store.status)}`}>
                  {store.status}
                </span>
              </div>

              <div className="store-stats">
                <div className="stat">
                  <span className="stat-value">
                    {store.stats?.total_products || 0}
                  </span>
                  <span className="stat-label">Products</span>
                </div>
                <div className="stat">
                  <span className="stat-value">
                    {store.stats?.synced_products || 0}
                  </span>
                  <span className="stat-label">Synced</span>
                </div>
                <div className="stat">
                  <span className="stat-value">
                    {store.stats?.imported_orders || 0}
                  </span>
                  <span className="stat-label">Orders</span>
                </div>
              </div>

              <div className="store-sync-info">
                <div className="sync-item">
                  <span className="sync-label">Last Product Sync:</span>
                  <span className="sync-value">
                    {store.last_sync?.products
                      ? new Date(store.last_sync.products).toLocaleString()
                      : 'Never'}
                  </span>
                </div>
                <div className="sync-item">
                  <span className="sync-label">Last Order Sync:</span>
                  <span className="sync-value">
                    {store.last_sync?.orders
                      ? new Date(store.last_sync.orders).toLocaleString()
                      : 'Never'}
                  </span>
                </div>
              </div>

              <div className="store-actions">
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => handleSync(store.id, 'products')}
                  disabled={syncing[`${store.id}-products`]}
                >
                  {syncing[`${store.id}-products`] ? '⏳' : '📦'} Products
                </button>
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => handleSync(store.id, 'inventory')}
                  disabled={syncing[`${store.id}-inventory`]}
                >
                  {syncing[`${store.id}-inventory`] ? '⏳' : '📊'} Inventory
                </button>
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => handleSync(store.id, 'orders')}
                  disabled={syncing[`${store.id}-orders`]}
                >
                  {syncing[`${store.id}-orders`] ? '⏳' : '🛍️'} Orders
                </button>
              </div>

              <div className="store-footer">
                <button
                  className="btn btn-sm btn-ghost"
                  onClick={() => handleTestConnection(store.id)}
                >
                  Test Connection
                </button>
                <button
                  className="btn btn-sm btn-ghost text-danger"
                  onClick={() => handleDisconnect(store.id)}
                >
                  Disconnect
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Connect Store Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Connect E-commerce Store</h2>
              <button
                className="modal-close"
                onClick={() => setShowModal(false)}
              >
                ×
              </button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Platform</label>
                <select
                  className="form-select"
                  value={newStore.platform}
                  onChange={(e) => setNewStore({
                    ...newStore,
                    platform: e.target.value,
                    credentials: {}
                  })}
                >
                  <option value="shopify">🟢 Shopify</option>
                  <option value="woocommerce">🔵 WooCommerce</option>
                  <option value="amazon">🟠 Amazon Seller Central</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Store Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={newStore.name}
                  onChange={(e) => setNewStore({ ...newStore, name: e.target.value })}
                  placeholder="My Store"
                />
              </div>

              {/* Platform-specific credentials */}
              {newStore.platform === 'shopify' ? (
                <>
                  <div className="form-group">
                    <label className="form-label">Shop Domain</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newStore.credentials.shop_domain || ''}
                      onChange={(e) => setNewStore({
                        ...newStore,
                        credentials: {
                          ...newStore.credentials,
                          shop_domain: e.target.value
                        }
                      })}
                      placeholder="mystore.myshopify.com"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Access Token</label>
                    <input
                      type="password"
                      className="form-input"
                      value={newStore.credentials.access_token || ''}
                      onChange={(e) => setNewStore({
                        ...newStore,
                        credentials: {
                          ...newStore.credentials,
                          access_token: e.target.value
                        }
                      })}
                      placeholder="shpat_..."
                    />
                  </div>
                </>
              ) : newStore.platform === 'amazon' ? (
                <>
                  <div className="form-group">
                    <label className="form-label">Marketplace</label>
                    <select
                      className="form-select"
                      value={newStore.credentials.marketplace || 'US'}
                      onChange={(e) => setNewStore({
                        ...newStore,
                        credentials: {
                          ...newStore.credentials,
                          marketplace: e.target.value
                        }
                      })}
                    >
                      <option value="US">🇺🇸 Amazon.com (US)</option>
                      <option value="UK">🇬🇧 Amazon.co.uk (UK)</option>
                      <option value="DE">🇩🇪 Amazon.de (Germany)</option>
                      <option value="FR">🇫🇷 Amazon.fr (France)</option>
                      <option value="IT">🇮🇹 Amazon.it (Italy)</option>
                      <option value="ES">🇪🇸 Amazon.es (Spain)</option>
                      <option value="NL">🇳🇱 Amazon.nl (Netherlands)</option>
                      <option value="CA">🇨🇦 Amazon.ca (Canada)</option>
                      <option value="AU">🇦🇺 Amazon.com.au (Australia)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Seller ID</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newStore.credentials.seller_id || ''}
                      onChange={(e) => setNewStore({
                        ...newStore,
                        credentials: {
                          ...newStore.credentials,
                          seller_id: e.target.value
                        }
                      })}
                      placeholder="A1234567890XYZ"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Refresh Token</label>
                    <input
                      type="password"
                      className="form-input"
                      value={newStore.credentials.refresh_token || ''}
                      onChange={(e) => setNewStore({
                        ...newStore,
                        credentials: {
                          ...newStore.credentials,
                          refresh_token: e.target.value
                        }
                      })}
                      placeholder="Atzr|..."
                    />
                  </div>
                </>
              ) : (
                <>
                  <div className="form-group">
                    <label className="form-label">Store URL</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newStore.credentials.store_url || ''}
                      onChange={(e) => setNewStore({
                        ...newStore,
                        credentials: {
                          ...newStore.credentials,
                          store_url: e.target.value
                        }
                      })}
                      placeholder="https://mystore.com"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Consumer Key</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newStore.credentials.consumer_key || ''}
                      onChange={(e) => setNewStore({
                        ...newStore,
                        credentials: {
                          ...newStore.credentials,
                          consumer_key: e.target.value
                        }
                      })}
                      placeholder="ck_..."
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Consumer Secret</label>
                    <input
                      type="password"
                      className="form-input"
                      value={newStore.credentials.consumer_secret || ''}
                      onChange={(e) => setNewStore({
                        ...newStore,
                        credentials: {
                          ...newStore.credentials,
                          consumer_secret: e.target.value
                        }
                      })}
                      placeholder="cs_..."
                    />
                  </div>
                </>
              )}
            </div>

            <div className="modal-footer">
              <button
                className="btn btn-ghost"
                onClick={() => setShowModal(false)}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleConnect}
                disabled={!newStore.name}
              >
                Connect Store
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EcommerceStores;
```

---

## TASK 14: E-COMMERCE DASHBOARD

### 14.1 Create Dashboard Page

**File:** `frontend/src/pages/EcommerceDashboard.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import {
  getDashboardSummary,
  getRevenueByStore,
  getTopProducts,
  getSyncStatus,
  getLowStockAlerts
} from '../services/ecommerceApi';

ChartJS.register(ArcElement, Tooltip, Legend);

const EcommerceDashboard = () => {
  const { t } = useTranslation();
  const [summary, setSummary] = useState(null);
  const [revenueData, setRevenueData] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [syncStatus, setSyncStatus] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryData, revenue, products, status, alertsData] = await Promise.all([
        getDashboardSummary(),
        getRevenueByStore(),
        getTopProducts(5),
        getSyncStatus(),
        getLowStockAlerts()
      ]);
      
      setSummary(summaryData);
      setRevenueData(revenue);
      setTopProducts(products);
      setSyncStatus(status);
      setAlerts(alertsData.alerts || []);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const getRevenueChartData = () => {
    const colors = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6'];
    
    return {
      labels: revenueData.map(r => r.store_name),
      datasets: [{
        data: revenueData.map(r => r.revenue),
        backgroundColor: colors.slice(0, revenueData.length),
        borderWidth: 0
      }]
    };
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      shopify: '🟢',
      woocommerce: '🔵',
      amazon: '🟠'
    };
    return icons[platform] || '🏪';
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">E-commerce Dashboard</h1>
          <p className="page-subtitle">
            Overview of all your sales channels
          </p>
        </div>
        <button className="btn btn-outline" onClick={loadData}>
          🔄 Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">🏪</div>
          <div className="stat-content">
            <span className="stat-value">{summary?.stores?.total || 0}</span>
            <span className="stat-label">Connected Stores</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📦</div>
          <div className="stat-content">
            <span className="stat-value">{summary?.products?.total || 0}</span>
            <span className="stat-label">Total Products</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🛍️</div>
          <div className="stat-content">
            <span className="stat-value">{summary?.orders?.total || 0}</span>
            <span className="stat-label">Imported Orders</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <span className="stat-value">
              {formatCurrency(summary?.revenue?.total || 0)}
            </span>
            <span className="stat-label">Total Revenue</span>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="dashboard-row">
        {/* Revenue by Store */}
        <div className="dashboard-card">
          <h3 className="card-title">Revenue by Store</h3>
          {revenueData.length > 0 ? (
            <div className="chart-container" style={{ height: '250px' }}>
              <Doughnut
                data={getRevenueChartData()}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom'
                    }
                  }
                }}
              />
            </div>
          ) : (
            <div className="empty-state-small">
              <p>No revenue data available</p>
            </div>
          )}
        </div>

        {/* Top Products */}
        <div className="dashboard-card">
          <h3 className="card-title">Top Selling Products</h3>
          {topProducts.length > 0 ? (
            <div className="top-products-list">
              {topProducts.map((product, index) => (
                <div key={product.sku} className="top-product-item">
                  <span className="product-rank">#{index + 1}</span>
                  <div className="product-info">
                    <span className="product-name">{product.name}</span>
                    <span className="product-sku">{product.sku}</span>
                  </div>
                  <div className="product-stats">
                    <span className="product-revenue">
                      {formatCurrency(product.revenue)}
                    </span>
                    <span className="product-quantity">
                      {product.quantity} sold
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state-small">
              <p>No sales data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Sync Status & Alerts Row */}
      <div className="dashboard-row">
        {/* Sync Status */}
        <div className="dashboard-card">
          <h3 className="card-title">Sync Status</h3>
          <div className="sync-status-list">
            {syncStatus.map(store => (
              <div key={store.store_id} className="sync-status-item">
                <div className="store-info">
                  <span className="platform-icon">
                    {getPlatformIcon(store.platform)}
                  </span>
                  <span className="store-name">{store.store_name}</span>
                </div>
                <div className="sync-times">
                  <div className="sync-time">
                    <span className="sync-label">Products:</span>
                    <span className="sync-value">
                      {store.last_product_sync
                        ? new Date(store.last_product_sync).toLocaleString()
                        : 'Never'}
                    </span>
                  </div>
                  <div className="sync-time">
                    <span className="sync-label">Orders:</span>
                    <span className="sync-value">
                      {store.last_order_sync
                        ? new Date(store.last_order_sync).toLocaleString()
                        : 'Never'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Low Stock Alerts */}
        <div className="dashboard-card">
          <h3 className="card-title">
            Low Stock Alerts
            {alerts.length > 0 && (
              <span className="badge badge-danger ml-2">{alerts.length}</span>
            )}
          </h3>
          {alerts.length > 0 ? (
            <div className="alerts-list">
              {alerts.slice(0, 5).map(alert => (
                <div
                  key={alert.id}
                  className={`alert-item ${alert.severity === 'critical' ? 'critical' : 'warning'}`}
                >
                  <div className="alert-icon">
                    {alert.severity === 'critical' ? '❌' : '⚠️'}
                  </div>
                  <div className="alert-content">
                    <span className="alert-sku">{alert.sku}</span>
                    <span className="alert-stock">
                      Stock: {alert.current_stock} (threshold: {alert.threshold})
                    </span>
                  </div>
                  <span className="alert-platform">
                    {getPlatformIcon(alert.platform)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state-small success">
              <span className="success-icon">✅</span>
              <p>All stock levels are healthy</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EcommerceDashboard;
```

---

## TASK 15: IMPORTED ORDERS PAGE

### 15.1 Create Imported Orders Page

**File:** `frontend/src/pages/ImportedOrders.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getImportedOrders, getStores } from '../services/ecommerceApi';

const ImportedOrders = () => {
  const { t } = useTranslation();
  const [orders, setOrders] = useState([]);
  const [stores, setStores] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedStore, setSelectedStore] = useState('');
  const [page, setPage] = useState(1);
  const limit = 20;

  useEffect(() => {
    loadData();
  }, [selectedStore]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ordersData, storesData] = await Promise.all([
        getImportedOrders(selectedStore || null, 100),
        getStores()
      ]);
      
      setOrders(ordersData.orders || []);
      setStats(ordersData.stats || {});
      setStores(storesData);
    } catch (error) {
      console.error('Error loading orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const getPlatformIcon = (platform) => {
    const icons = {
      shopify: '🟢',
      woocommerce: '🔵',
      amazon: '🟠'
    };
    return icons[platform] || '🏪';
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'badge-warning',
      processing: 'badge-info',
      completed: 'badge-success',
      cancelled: 'badge-danger',
      refunded: 'badge-secondary'
    };
    return badges[status] || 'badge-secondary';
  };

  const paginatedOrders = orders.slice((page - 1) * limit, page * limit);
  const totalPages = Math.ceil(orders.length / limit);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading orders...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Imported Orders</h1>
          <p className="page-subtitle">
            Orders imported from your e-commerce stores
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <div className="stat-box">
          <span className="stat-value">{stats.total_orders || 0}</span>
          <span className="stat-label">Total Orders</span>
        </div>
        <div className="stat-box">
          <span className="stat-value">
            {formatCurrency(stats.total_revenue || 0)}
          </span>
          <span className="stat-label">Total Revenue</span>
        </div>
        <div className="stat-box">
          <span className="stat-value">{stats.by_status?.completed || 0}</span>
          <span className="stat-label">Completed</span>
        </div>
        <div className="stat-box">
          <span className="stat-value">{stats.by_status?.pending || 0}</span>
          <span className="stat-label">Pending</span>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <div className="filter-group">
          <label>Store:</label>
          <select
            className="form-select"
            value={selectedStore}
            onChange={(e) => setSelectedStore(e.target.value)}
          >
            <option value="">All Stores</option>
            {stores.map(store => (
              <option key={store.id} value={store.id}>
                {getPlatformIcon(store.platform)} {store.name}
              </option>
            ))}
          </select>
        </div>
        <button className="btn btn-outline" onClick={loadData}>
          🔄 Refresh
        </button>
      </div>

      {/* Orders Table */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>Order #</th>
              <th>Platform</th>
              <th>Customer</th>
              <th>Items</th>
              <th>Total</th>
              <th>Status</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {paginatedOrders.length === 0 ? (
              <tr>
                <td colSpan="7" className="empty-cell">
                  No orders found
                </td>
              </tr>
            ) : (
              paginatedOrders.map(order => (
                <tr key={order.id}>
                  <td>
                    <span className="order-number">
                      {order.source_order_number || order.id}
                    </span>
                  </td>
                  <td>
                    <span className="platform-badge">
                      {getPlatformIcon(order.source)} {order.source}
                    </span>
                  </td>
                  <td>
                    <div className="customer-info">
                      <span className="customer-name">{order.client_name}</span>
                      <span className="customer-email">{order.client_email}</span>
                    </div>
                  </td>
                  <td>
                    {order.items?.length || 0} item(s)
                  </td>
                  <td>
                    <span className="order-total">
                      {formatCurrency(order.total, order.currency)}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${getStatusBadge(order.status)}`}>
                      {order.status}
                    </span>
                  </td>
                  <td>
                    {new Date(order.date).toLocaleDateString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="btn btn-sm"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </button>
          <span className="page-info">
            Page {page} of {totalPages}
          </span>
          <button
            className="btn btn-sm"
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default ImportedOrders;
```

---

## TASK 16: STYLES

### 16.1 Add E-commerce Styles

**File:** `frontend/src/styles/ecommerce.css`

```css
/* E-commerce Stores Page */
.stores-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.store-card {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 1.5rem;
  transition: box-shadow 0.2s;
}

.store-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.store-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.store-platform {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.platform-icon {
  font-size: 2rem;
}

.store-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.platform-name {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.store-stats {
  display: flex;
  gap: 1.5rem;
  padding: 1rem 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

.store-stats .stat {
  display: flex;
  flex-direction: column;
}

.store-stats .stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary-color);
}

.store-stats .stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
}

.store-sync-info {
  padding: 1rem 0;
  font-size: 0.85rem;
}

.sync-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.sync-label {
  color: var(--text-muted);
}

.sync-value {
  font-weight: 500;
}

.store-actions {
  display: flex;
  gap: 0.5rem;
  padding: 1rem 0;
  flex-wrap: wrap;
}

.store-footer {
  display: flex;
  justify-content: space-between;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

/* Dashboard */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-content .stat-value {
  font-size: 1.75rem;
  font-weight: 700;
}

.stat-content .stat-label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.dashboard-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

@media (max-width: 1024px) {
  .dashboard-row {
    grid-template-columns: 1fr;
  }
}

.dashboard-card {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 1.5rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.chart-container {
  position: relative;
}

/* Top Products */
.top-products-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.top-product-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.product-rank {
  font-weight: 700;
  color: var(--primary-color);
  width: 30px;
}

.product-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.product-name {
  font-weight: 500;
}

.product-sku {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.product-stats {
  text-align: right;
}

.product-revenue {
  display: block;
  font-weight: 600;
}

.product-quantity {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Sync Status */
.sync-status-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sync-status-item {
  padding: 0.75rem;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.sync-status-item .store-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.sync-times {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
}

.sync-time {
  display: flex;
  justify-content: space-between;
}

/* Alerts */
.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 8px;
}

.alert-item.warning {
  background: rgba(245, 158, 11, 0.1);
  border-left: 3px solid #F59E0B;
}

.alert-item.critical {
  background: rgba(239, 68, 68, 0.1);
  border-left: 3px solid #EF4444;
}

.alert-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.alert-sku {
  font-weight: 500;
}

.alert-stock {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Orders Table */
.stats-row {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.stat-box {
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  padding: 1rem 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-box .stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary-color);
}

.stat-box .stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.filters-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding: 1rem;
  background: var(--card-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group label {
  font-weight: 500;
}

.platform-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  text-transform: capitalize;
}

.customer-info {
  display: flex;
  flex-direction: column;
}

.customer-name {
  font-weight: 500;
}

.customer-email {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.order-total {
  font-weight: 600;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.page-info {
  font-size: 0.9rem;
  color: var(--text-muted);
}

/* Empty States */
.empty-state {
  text-align: center;
  padding: 3rem;
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px dashed var(--border-color);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin-bottom: 0.5rem;
}

.empty-state p {
  color: var(--text-muted);
  margin-bottom: 1.5rem;
}

.empty-state-small {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
}

.empty-state-small.success {
  color: var(--success-color);
}

.success-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--card-bg);
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-muted);
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
}

/* Utility */
.ml-2 {
  margin-left: 0.5rem;
}

.text-danger {
  color: var(--danger-color) !important;
}
```

---

## TASK 17: NAVIGATION UPDATE

### 17.1 Add E-commerce Routes

**File:** `frontend/src/App.jsx` (add routes)

```jsx
// Add imports
import EcommerceStores from './pages/EcommerceStores';
import EcommerceDashboard from './pages/EcommerceDashboard';
import ImportedOrders from './pages/ImportedOrders';

// Add routes inside <Routes>
<Route path="/ecommerce" element={<EcommerceDashboard />} />
<Route path="/ecommerce/stores" element={<EcommerceStores />} />
<Route path="/ecommerce/orders" element={<ImportedOrders />} />
```

### 17.2 Add Navigation Items

**File:** `frontend/src/components/Sidebar.jsx` (add menu items)

```jsx
// Add to navigation items array
{
  title: 'E-commerce',
  icon: '🛒',
  path: '/ecommerce',
  children: [
    { title: 'Dashboard', path: '/ecommerce', icon: '📊' },
    { title: 'Stores', path: '/ecommerce/stores', icon: '🏪' },
    { title: 'Imported Orders', path: '/ecommerce/orders', icon: '🛍️' }
  ]
}
```

---

## PHASE 9 COMPLETION CHECKLIST

### Backend Services ✅
- [x] Base adapter class
- [x] Connection service
- [x] Shopify adapter
- [x] WooCommerce adapter
- [x] Amazon Seller adapter
- [x] Product sync service
- [x] Inventory sync service
- [x] Order import service
- [x] Analytics service
- [x] Webhook handlers

### Backend Routes ✅
- [x] Store management routes
- [x] Sync routes
- [x] Webhook routes
- [x] Analytics routes

### Frontend Pages ✅
- [x] Store management page (Shopify, WooCommerce, Amazon)
- [x] E-commerce dashboard
- [x] Imported orders page
- [x] E-commerce styles

### EU/US Compliance ✅
- [x] Multi-marketplace support (US, UK, DE, FR, IT, ES, NL, CA, AU)
- [x] Multi-currency support (USD, EUR, GBP, CAD, AUD)
- [x] Platform-specific configurations

### Integration ✅
- [x] API service
- [x] Route configuration
- [x] Navigation updates

---

## 🎉 PHASE 9 COMPLETE!

### New Files Created: ~35
### New API Endpoints: ~30
### Estimated Implementation Time: 42-52 hours

### Key Features Delivered (EU/US Focus)
1. ✅ Shopify Integration (Global)
2. ✅ WooCommerce Integration (Global)
3. ✅ Amazon Seller Central (US/EU)
4. ✅ Product Sync (bidirectional)
5. ✅ Inventory Sync (with alerts)
6. ✅ Order Import
7. ✅ E-commerce Webhooks
8. ✅ Multi-Store Management
9. ✅ E-commerce Dashboard
10. ✅ Multi-Currency Support

---

## TOTAL PROJECT SUMMARY (Phases 1-9)

| Phase | Features | Status |
|-------|----------|--------|
| Phase 1 | MVP + 5 AI | ✅ |
| Phase 2 | Testing + Exports | ✅ |
| Phase 3 | i18n + PWA + Dark Mode | ✅ |
| Phase 4 | 2FA + Enterprise | ✅ |
| Phase 5 | AI Assistant + Automation | ✅ |
| Phase 6 | Dashboards + Portals | ✅ |
| Phase 7 | Audit + Compliance | ✅ |
| Phase 8 | Payment Gateway | ✅ |
| Phase 9 | E-commerce Sync (EU/US) | ✅ |

### Total Features: 120+
### Total Estimated Code: ~70,000+ lines
### Equivalent Solo Dev Time: 20-24 months

### EU/US Market Support
```
┌─────────────────────────────────────────────────────────────┐
│  🇺🇸 United States     │  🇬🇧 United Kingdom   │  🇩🇪 Germany    │
│  🇫🇷 France            │  🇮🇹 Italy            │  🇪🇸 Spain       │
│  🇳🇱 Netherlands       │  🇨🇦 Canada           │  🇦🇺 Australia   │
├─────────────────────────────────────────────────────────────┤
│  💳 Stripe, PayPal     │  🛒 Shopify, WooComm  │  📦 Amazon     │
│  💶 Multi-Currency     │  📋 VAT Ready         │  🔒 GDPR Ready │
└─────────────────────────────────────────────────────────────┘
```

---

## Next Phases (From README)

| Phase | Focus |
|-------|-------|
| Phase 10 | ML-powered Cash Flow Forecasting |
| Phase 11 | Mobile Apps (React Native) |
| Phase 12 | Enterprise SSO (SAML/OIDC) |

---

*Phase 9 Complete - LogiAccounting Pro*
*E-commerce Sync (Shopify/WooCommerce/Amazon) - EU/US Market*
