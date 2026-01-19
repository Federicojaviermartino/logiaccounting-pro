import { useState, useEffect } from 'react';
import { auditAPI } from '../services/api';

export default function AuditTrail() {
  const [logs, setLogs] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionTypes, setActionTypes] = useState([]);
  const [entityTypes, setEntityTypes] = useState([]);

  const [filters, setFilters] = useState({
    action: '',
    entity_type: '',
    user_email: '',
    date_from: '',
    date_to: ''
  });

  const [pagination, setPagination] = useState({ limit: 50, offset: 0, total: 0 });
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    loadLogs();
  }, [filters, pagination.offset]);

  const loadInitialData = async () => {
    try {
      const [actionsRes, entitiesRes, statsRes, anomaliesRes] = await Promise.all([
        auditAPI.getActions(),
        auditAPI.getEntities(),
        auditAPI.getStatistics(),
        auditAPI.getAnomalies()
      ]);
      setActionTypes(actionsRes.data.actions);
      setEntityTypes(entitiesRes.data.entities);
      setStatistics(statsRes.data);
      setAnomalies(anomaliesRes.data.anomalies);
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  const loadLogs = async () => {
    setLoading(true);
    try {
      const params = {
        ...filters,
        limit: pagination.limit,
        offset: pagination.offset
      };
      // Remove empty filters
      Object.keys(params).forEach(k => !params[k] && delete params[k]);

      const res = await auditAPI.search(params);
      setLogs(res.data.logs);
      setPagination(p => ({ ...p, total: res.data.total }));
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const res = await auditAPI.export(format, filters.date_from, filters.date_to);
      const blob = new Blob([res.data.content || JSON.stringify(res.data.data, null, 2)], {
        type: format === 'csv' ? 'text/csv' : 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_logs.${format}`;
      a.click();
    } catch (err) {
      alert('Export failed');
    }
  };

  const getActionBadge = (action) => {
    const colors = {
      CREATE: 'badge-success',
      UPDATE: 'badge-info',
      DELETE: 'badge-danger',
      LOGIN: 'badge-primary',
      LOGOUT: 'badge-gray',
      LOGIN_FAILED: 'badge-danger',
      EXPORT: 'badge-warning'
    };
    return <span className={`badge ${colors[action] || 'badge-gray'}`}>{action}</span>;
  };

  const getSeverityBadge = (severity) => {
    const colors = { high: 'badge-danger', medium: 'badge-warning', low: 'badge-info' };
    return <span className={`badge ${colors[severity]}`}>{severity}</span>;
  };

  return (
    <>
      <div className="info-banner mb-6">
        Immutable audit trail for compliance and security monitoring.
      </div>

      {/* Anomalies Alert */}
      {anomalies.length > 0 && (
        <div className="alert alert-danger mb-6">
          <strong>Security Anomalies Detected ({anomalies.length})</strong>
          <div className="mt-2">
            {anomalies.slice(0, 3).map((a, i) => (
              <div key={i} className="text-sm">
                {getSeverityBadge(a.severity)} {a.description}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statistics */}
      {statistics && (
        <div className="stats-grid mb-6">
          <div className="stat-card">
            <div className="stat-icon">#{statistics.total_logs}</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.total_logs}</div>
              <div className="stat-label">Total Logs (30d)</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">!</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.failed_logins}</div>
              <div className="stat-label">Failed Logins</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">@</div>
            <div className="stat-content">
              <div className="stat-value">{Object.keys(statistics.by_user || {}).length}</div>
              <div className="stat-label">Active Users</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="section mb-4">
        <div className="flex flex-wrap gap-4">
          <select
            className="form-select"
            value={filters.action}
            onChange={(e) => setFilters({ ...filters, action: e.target.value })}
          >
            <option value="">All Actions</option>
            {actionTypes.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
          <select
            className="form-select"
            value={filters.entity_type}
            onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}
          >
            <option value="">All Entities</option>
            {entityTypes.map(e => <option key={e} value={e}>{e}</option>)}
          </select>
          <input
            type="text"
            className="form-input"
            placeholder="User email..."
            value={filters.user_email}
            onChange={(e) => setFilters({ ...filters, user_email: e.target.value })}
          />
          <input
            type="date"
            className="form-input"
            value={filters.date_from}
            onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
          />
          <input
            type="date"
            className="form-input"
            value={filters.date_to}
            onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
          />
          <button className="btn btn-secondary" onClick={() => handleExport('csv')}>
            Export CSV
          </button>
          <button className="btn btn-secondary" onClick={() => handleExport('json')}>
            Export JSON
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="section">
        {loading ? (
          <div className="text-center p-8">Loading...</div>
        ) : (
          <>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Action</th>
                    <th>Entity</th>
                    <th>User</th>
                    <th>IP</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map(log => (
                    <tr key={log.id} onClick={() => setSelectedLog(log)} style={{ cursor: 'pointer' }}>
                      <td><code>{new Date(log.timestamp).toLocaleString()}</code></td>
                      <td>{getActionBadge(log.action)}</td>
                      <td>{log.entity_type}/{log.entity_id || '-'}</td>
                      <td>{log.user_email || 'system'}</td>
                      <td><code>{log.ip_address || '-'}</code></td>
                      <td>
                        {log.changes && Object.keys(log.changes).length > 0 && (
                          <span className="badge badge-info">{Object.keys(log.changes).length} changes</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex justify-between items-center mt-4">
              <span className="text-muted">
                Showing {pagination.offset + 1}-{Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total}
              </span>
              <div className="flex gap-2">
                <button
                  className="btn btn-sm btn-secondary"
                  disabled={pagination.offset === 0}
                  onClick={() => setPagination(p => ({ ...p, offset: Math.max(0, p.offset - p.limit) }))}
                >
                  Previous
                </button>
                <button
                  className="btn btn-sm btn-secondary"
                  disabled={pagination.offset + pagination.limit >= pagination.total}
                  onClick={() => setPagination(p => ({ ...p, offset: p.offset + p.limit }))}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="modal-overlay" onClick={() => setSelectedLog(null)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Log Details</h3>
              <button className="modal-close" onClick={() => setSelectedLog(null)}>x</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div><strong>ID:</strong> <code>{selectedLog.id}</code></div>
                <div><strong>Hash:</strong> <code>{selectedLog.hash}</code></div>
                <div><strong>Action:</strong> {getActionBadge(selectedLog.action)}</div>
                <div><strong>Timestamp:</strong> {new Date(selectedLog.timestamp).toLocaleString()}</div>
                <div><strong>Entity:</strong> {selectedLog.entity_type}</div>
                <div><strong>Entity ID:</strong> {selectedLog.entity_id || '-'}</div>
                <div><strong>User:</strong> {selectedLog.user_email || 'system'}</div>
                <div><strong>Role:</strong> {selectedLog.user_role || '-'}</div>
                <div><strong>IP:</strong> <code>{selectedLog.ip_address || '-'}</code></div>
                <div><strong>Session:</strong> <code>{selectedLog.session_id || '-'}</code></div>
              </div>
              {selectedLog.changes && Object.keys(selectedLog.changes).length > 0 && (
                <div className="mt-4">
                  <strong>Changes:</strong>
                  <div className="changes-list mt-2">
                    {Object.entries(selectedLog.changes).map(([field, change]) => (
                      <div key={field} className="change-item">
                        <span className="change-field">{field}</span>
                        <span className="change-before">{JSON.stringify(change.before)}</span>
                        <span className="change-arrow">-&gt;</span>
                        <span className="change-after">{JSON.stringify(change.after)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {selectedLog.user_agent && (
                <div className="mt-4">
                  <strong>User Agent:</strong>
                  <div className="text-sm text-muted">{selectedLog.user_agent}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
