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
                  {syncing[`${store.id}-products`] ? '...' : '📦'} Products
                </button>
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => handleSync(store.id, 'inventory')}
                  disabled={syncing[`${store.id}-inventory`]}
                >
                  {syncing[`${store.id}-inventory`] ? '...' : '📊'} Inventory
                </button>
                <button
                  className="btn btn-sm btn-outline"
                  onClick={() => handleSync(store.id, 'orders')}
                  disabled={syncing[`${store.id}-orders`]}
                >
                  {syncing[`${store.id}-orders`] ? '...' : '🛍️'} Orders
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
                x
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
