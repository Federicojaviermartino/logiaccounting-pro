import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Link } from 'react-router-dom';

export default function SupplierDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await api.get('/api/v1/portal/supplier/dashboard');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;

  const { stats, recent_orders, pending_payments } = data || {};

  return (
    <>
      <div className="portal-welcome mb-6">
        <h2>Supplier Portal</h2>
        <p>View your orders, payments, and manage your catalog.</p>
      </div>

      {/* Stats */}
      <div className="stats-grid mb-6">
        <div className="stat-card">
          <div className="stat-icon">O</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.total_orders || 0}</div>
            <div className="stat-label">Total Orders</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">$</div>
          <div className="stat-content">
            <div className="stat-value">${stats?.total_revenue?.toLocaleString() || 0}</div>
            <div className="stat-label">Total Revenue</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">+</div>
          <div className="stat-content">
            <div className="stat-value">${stats?.total_paid?.toLocaleString() || 0}</div>
            <div className="stat-label">Paid</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">...</div>
          <div className="stat-content">
            <div className="stat-value">${stats?.total_pending?.toLocaleString() || 0}</div>
            <div className="stat-label">Pending</div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Recent Orders */}
        <div className="section">
          <h3 className="section-title">Recent Orders</h3>
          {recent_orders?.length === 0 ? (
            <div className="text-muted">No orders yet</div>
          ) : (
            <div className="portal-list">
              {recent_orders?.slice(0, 5).map(order => (
                <div key={order.id} className="portal-item">
                  <div>
                    <div className="portal-item-name">{order.description}</div>
                    <div className="text-muted text-sm">{order.date}</div>
                  </div>
                  <strong>${order.amount?.toLocaleString()}</strong>
                </div>
              ))}
            </div>
          )}
          <Link to="/portal/supplier/orders" className="btn btn-secondary btn-sm mt-4">View All</Link>
        </div>

        {/* Pending Payments */}
        <div className="section">
          <h3 className="section-title">Pending Payments</h3>
          {pending_payments?.length === 0 ? (
            <div className="text-muted">No pending payments</div>
          ) : (
            <div className="portal-list">
              {pending_payments?.map(payment => (
                <div key={payment.id} className="portal-item">
                  <div>
                    <div className="portal-item-name">${payment.amount?.toLocaleString()}</div>
                    <div className="text-muted text-sm">Due: {payment.due_date}</div>
                  </div>
                  <span className="badge badge-warning">Pending</span>
                </div>
              ))}
            </div>
          )}
          <Link to="/portal/supplier/payments" className="btn btn-secondary btn-sm mt-4">View All</Link>
        </div>
      </div>
    </>
  );
}
