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
