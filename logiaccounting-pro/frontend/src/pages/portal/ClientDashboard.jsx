import { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Link } from 'react-router-dom';

export default function ClientDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await api.get('/api/v1/portal/client/dashboard');
      setData(res.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;

  const { stats, recent_projects, pending_payments } = data || {};

  return (
    <>
      <div className="portal-welcome mb-6">
        <h2>Welcome to Your Portal</h2>
        <p>View your projects, invoices, and payments.</p>
      </div>

      {/* Stats */}
      <div className="stats-grid mb-6">
        <div className="stat-card">
          <div className="stat-icon">P</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.total_projects || 0}</div>
            <div className="stat-label">Total Projects</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">A</div>
          <div className="stat-content">
            <div className="stat-value">{stats?.active_projects || 0}</div>
            <div className="stat-label">Active Projects</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">$</div>
          <div className="stat-content">
            <div className="stat-value">${stats?.total_paid?.toLocaleString() || 0}</div>
            <div className="stat-label">Total Paid</div>
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
        {/* Recent Projects */}
        <div className="section">
          <h3 className="section-title">Recent Projects</h3>
          {recent_projects?.length === 0 ? (
            <div className="text-muted">No projects yet</div>
          ) : (
            <div className="portal-list">
              {recent_projects?.map(project => (
                <Link key={project.id} to={`/portal/projects/${project.id}`} className="portal-item">
                  <div className="portal-item-name">{project.name}</div>
                  <span className={`badge badge-${project.status === 'active' ? 'success' : 'gray'}`}>
                    {project.status}
                  </span>
                </Link>
              ))}
            </div>
          )}
          <Link to="/portal/projects" className="btn btn-secondary btn-sm mt-4">View All</Link>
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
          <Link to="/portal/payments" className="btn btn-secondary btn-sm mt-4">View All</Link>
        </div>
      </div>
    </>
  );
}
