import { useState, useEffect } from 'react';
import { activityAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import toast from '../utils/toast';

export default function ActivityLog() {
  const { user } = useAuth();
  const [activities, setActivities] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [options, setOptions] = useState({ actions: [], entities: [] });
  const [filters, setFilters] = useState({
    action: '',
    entity_type: '',
    date_from: '',
    date_to: ''
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
    total: 0,
    hasMore: false
  });

  useEffect(() => {
    loadOptions();
    loadStats();
  }, []);

  useEffect(() => {
    loadActivities();
  }, [filters, pagination.offset]);

  const loadOptions = async () => {
    try {
      const res = await activityAPI.getAvailableActions();
      setOptions(res.data);
    } catch (error) {
      console.error('Failed to load options:', error);
    }
  };

  const loadStats = async () => {
    try {
      const res = await activityAPI.getStats(30);
      setStats(res.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadActivities = async () => {
    setLoading(true);
    try {
      const params = {
        ...filters,
        limit: pagination.limit,
        offset: pagination.offset
      };
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (!params[key]) delete params[key];
      });

      const res = await activityAPI.getActivities(params);
      setActivities(res.data.activities);
      setPagination(prev => ({
        ...prev,
        total: res.data.total,
        hasMore: res.data.has_more
      }));
    } catch (error) {
      console.error('Failed to load activities:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, offset: 0 }));
  };

  const handleExport = async () => {
    try {
      const res = await activityAPI.exportCSV(filters);
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `activity_log_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Export failed');
    }
  };

  const getActionBadgeColor = (action) => {
    const colors = {
      LOGIN: 'primary',
      LOGOUT: 'gray',
      CREATE: 'success',
      UPDATE: 'warning',
      DELETE: 'danger',
      EXPORT: 'primary',
      IMPORT: 'primary',
      STATUS_CHANGE: 'warning'
    };
    return colors[action] || 'gray';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <>
      {/* Stats Overview */}
      {stats && (
        <div className="stats-grid mb-6">
          <div className="stat-card">
            <span className="stat-icon">📊</span>
            <div className="stat-content">
              <div className="stat-label">Total (30 days)</div>
              <div className="stat-value">{stats.total_activities}</div>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">📈</span>
            <div className="stat-content">
              <div className="stat-label">Daily Average</div>
              <div className="stat-value">{stats.daily_average}</div>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">✏️</span>
            <div className="stat-content">
              <div className="stat-label">Updates</div>
              <div className="stat-value">{stats.by_action?.UPDATE || 0}</div>
            </div>
          </div>
          <div className="stat-card">
            <span className="stat-icon">🔐</span>
            <div className="stat-content">
              <div className="stat-label">Logins</div>
              <div className="stat-value">{stats.by_action?.LOGIN || 0}</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="section mb-6">
        <div className="toolbar">
          <div className="flex gap-3 flex-wrap">
            <select
              className="form-select"
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
            >
              <option value="">All Actions</option>
              {options.actions.map(a => (
                <option key={a.code} value={a.code}>{a.label}</option>
              ))}
            </select>

            <select
              className="form-select"
              value={filters.entity_type}
              onChange={(e) => handleFilterChange('entity_type', e.target.value)}
            >
              <option value="">All Entities</option>
              {options.entities.map(e => (
                <option key={e.code} value={e.code}>{e.label}</option>
              ))}
            </select>

            <input
              type="date"
              className="form-input"
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
              placeholder="From date"
            />

            <input
              type="date"
              className="form-input"
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
              placeholder="To date"
            />
          </div>

          <button className="btn btn-secondary" onClick={handleExport}>
            Export CSV
          </button>
        </div>
      </div>

      {/* Activity Table */}
      <div className="section">
        <h3 className="section-title">Activity Log</h3>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : activities.length === 0 ? (
          <div className="text-center text-muted">No activities found</div>
        ) : (
          <>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Entity</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {activities.map(activity => (
                    <tr key={activity.id}>
                      <td className="text-muted" style={{ whiteSpace: 'nowrap' }}>
                        {formatDate(activity.timestamp)}
                      </td>
                      <td>
                        <div>{activity.user_email}</div>
                        <div className="text-muted text-sm">{activity.user_role}</div>
                      </td>
                      <td>
                        <span className={`badge badge-${getActionBadgeColor(activity.action)}`}>
                          {activity.action}
                        </span>
                      </td>
                      <td>
                        <div>{activity.entity_type}</div>
                        {activity.entity_name && (
                          <div className="text-muted text-sm">{activity.entity_name}</div>
                        )}
                      </td>
                      <td className="text-muted text-sm">
                        {Object.keys(activity.details).length > 0 ? (
                          <code>{JSON.stringify(activity.details)}</code>
                        ) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-4">
              <div className="text-muted">
                Showing {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total}
              </div>
              <div className="flex gap-2">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setPagination(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
                  disabled={pagination.offset === 0}
                >
                  Previous
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
                  disabled={!pagination.hasMore}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}
