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
