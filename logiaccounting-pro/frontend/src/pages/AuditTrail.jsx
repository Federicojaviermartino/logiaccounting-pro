/**
 * Audit Trail Page - Phase 15
 * Enterprise Audit Trail with comprehensive logging and integrity verification
 */

import { useState, useEffect } from 'react';
import { auditLogsAPI, integrityAPI, changeHistoryAPI, auditReportsAPI } from '../services/auditApi';

export default function AuditTrail() {
  const [logs, setLogs] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [integrityStatus, setIntegrityStatus] = useState(null);
  const [eventTypes, setEventTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);

  const [filters, setFilters] = useState({
    event_type: '',
    event_category: '',
    severity: '',
    entity_type: '',
    user_id: '',
    compliance_tag: '',
    from_date: '',
    to_date: ''
  });

  const [pagination, setPagination] = useState({ limit: 50, offset: 0, total: 0 });
  const [selectedLog, setSelectedLog] = useState(null);
  const [changeHistory, setChangeHistory] = useState(null);
  const [activeTab, setActiveTab] = useState('logs'); // logs, integrity, reports

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (activeTab === 'logs') {
      loadLogs();
    }
  }, [filters, pagination.offset, activeTab]);

  const loadInitialData = async () => {
    try {
      const [statsRes, integrityRes, eventTypesRes] = await Promise.all([
        auditLogsAPI.getStatistics(30),
        integrityAPI.getStatus(),
        auditLogsAPI.getEventTypes()
      ]);
      setStatistics(statsRes.data.statistics);
      setIntegrityStatus(integrityRes.data.status);
      setEventTypes(eventTypesRes.data.event_types || []);
    } catch (err) {
      console.error('Failed to load initial data:', err);
    }
  };

  const loadLogs = async () => {
    setLoading(true);
    try {
      const params = { ...filters, limit: pagination.limit, offset: pagination.offset };
      Object.keys(params).forEach(k => !params[k] && delete params[k]);

      const res = await auditLogsAPI.getLogs(params);
      setLogs(res.data.logs || []);
      setPagination(p => ({ ...p, total: res.data.pagination?.total || 0 }));
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const verifyIntegrity = async () => {
    setVerifying(true);
    try {
      const res = await integrityAPI.verify();
      alert(res.data.is_valid
        ? 'Integrity verification passed! All logs are intact.'
        : `Integrity issues found: ${res.data.issues_count} problems detected.`
      );
      // Refresh integrity status
      const statusRes = await integrityAPI.getStatus();
      setIntegrityStatus(statusRes.data.status);
    } catch (err) {
      alert('Verification failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setVerifying(false);
    }
  };

  const loadChangeHistory = async (entityType, entityId) => {
    try {
      const res = await changeHistoryAPI.getHistory(entityType, entityId);
      setChangeHistory({
        entityType,
        entityId,
        versions: res.data.versions || []
      });
    } catch (err) {
      console.error('Failed to load change history:', err);
    }
  };

  const handleExport = async (format) => {
    try {
      const res = await auditLogsAPI.exportLogs(format, filters);
      if (format === 'json') {
        const blob = new Blob([JSON.stringify(res.data.data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `audit_logs.json`);
      } else {
        downloadBlob(res.data, `audit_logs.${format}`);
      }
    } catch (err) {
      alert('Export failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const generateReport = async (reportType, format = 'json') => {
    try {
      const res = await auditReportsAPI.generateReport(reportType, {
        start_date: filters.from_date || undefined,
        end_date: filters.to_date || undefined
      }, format);

      if (format === 'json') {
        console.log('Report:', res.data.report);
        alert('Report generated! Check console for details.');
      } else {
        downloadBlob(res.data, `${reportType}.${format}`);
      }
    } catch (err) {
      alert('Report generation failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const downloadBlob = (blob, filename) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getSeverityBadge = (severity) => {
    const colors = {
      debug: 'badge-gray',
      info: 'badge-info',
      warning: 'badge-warning',
      error: 'badge-danger',
      critical: 'badge-danger'
    };
    return <span className={`badge ${colors[severity] || 'badge-gray'}`}>{severity}</span>;
  };

  const getActionBadge = (action) => {
    const colors = {
      create: 'badge-success',
      update: 'badge-info',
      delete: 'badge-danger',
      read: 'badge-gray',
      execute: 'badge-primary',
      export: 'badge-warning',
      import: 'badge-warning'
    };
    return <span className={`badge ${colors[action] || 'badge-gray'}`}>{action}</span>;
  };

  const getCategoryBadge = (category) => {
    const colors = {
      data_change: 'badge-info',
      authentication: 'badge-primary',
      authorization: 'badge-warning',
      system: 'badge-gray',
      compliance: 'badge-success',
      security: 'badge-danger'
    };
    return <span className={`badge ${colors[category] || 'badge-gray'}`}>{category?.replace('_', ' ')}</span>;
  };

  const categories = ['data_change', 'authentication', 'authorization', 'system', 'compliance', 'security'];
  const severities = ['debug', 'info', 'warning', 'error', 'critical'];
  const complianceTags = ['sox', 'gdpr', 'soc2', 'pci', 'hipaa'];

  return (
    <>
      <div className="info-banner mb-6">
        Enterprise Audit Trail - Immutable logging with cryptographic integrity verification (Phase 15)
      </div>

      {/* Tabs */}
      <div className="tabs mb-6">
        <button
          className={`tab ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          Audit Logs
        </button>
        <button
          className={`tab ${activeTab === 'integrity' ? 'active' : ''}`}
          onClick={() => setActiveTab('integrity')}
        >
          Integrity
        </button>
        <button
          className={`tab ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          Reports
        </button>
      </div>

      {/* Statistics */}
      {statistics && activeTab === 'logs' && (
        <div className="stats-grid mb-6">
          <div className="stat-card">
            <div className="stat-icon">#</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.total_events || 0}</div>
              <div className="stat-label">Total Events (30d)</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">!</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.by_severity?.error || 0}</div>
              <div className="stat-label">Errors</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">@</div>
            <div className="stat-content">
              <div className="stat-value">{Object.keys(statistics.by_user || {}).length}</div>
              <div className="stat-label">Active Users</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">*</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.by_action?.delete || 0}</div>
              <div className="stat-label">Deletions</div>
            </div>
          </div>
        </div>
      )}

      {/* Integrity Tab */}
      {activeTab === 'integrity' && (
        <div className="section">
          <h3 className="section-title">Hash Chain Integrity</h3>
          <p className="text-muted mb-4">
            Verify the integrity of audit logs using cryptographic hash chain verification.
            Each log entry is linked to the previous one via SHA-256 hashing, making tampering detectable.
          </p>

          {integrityStatus && (
            <div className="grid-2 mb-4">
              <div className="card p-4">
                <strong>Total Logs:</strong> {integrityStatus.total_logs || 0}
              </div>
              <div className="card p-4">
                <strong>First Sequence:</strong> {integrityStatus.first_sequence || 0}
              </div>
              <div className="card p-4">
                <strong>Last Sequence:</strong> {integrityStatus.last_sequence || 0}
              </div>
              <div className="card p-4">
                <strong>Status:</strong>{' '}
                <span className={`badge ${integrityStatus.is_valid !== false ? 'badge-success' : 'badge-danger'}`}>
                  {integrityStatus.is_valid !== false ? 'Valid' : 'Issues Detected'}
                </span>
              </div>
            </div>
          )}

          <button
            className="btn btn-primary"
            onClick={verifyIntegrity}
            disabled={verifying}
          >
            {verifying ? 'Verifying...' : 'Run Integrity Verification'}
          </button>
        </div>
      )}

      {/* Reports Tab */}
      {activeTab === 'reports' && (
        <div className="section">
          <h3 className="section-title">Audit Reports</h3>
          <p className="text-muted mb-4">
            Generate compliance and audit reports in various formats.
          </p>

          <div className="grid-2 gap-4">
            <div className="card p-4">
              <h4>Activity Summary</h4>
              <p className="text-sm text-muted mb-2">Summary of system activity over a period</p>
              <div className="flex gap-2">
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('activity_summary', 'json')}>
                  JSON
                </button>
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('activity_summary', 'pdf')}>
                  PDF
                </button>
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('activity_summary', 'excel')}>
                  Excel
                </button>
              </div>
            </div>

            <div className="card p-4">
              <h4>Access Review</h4>
              <p className="text-sm text-muted mb-2">Authentication and access events</p>
              <div className="flex gap-2">
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('access_review', 'json')}>
                  JSON
                </button>
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('access_review', 'pdf')}>
                  PDF
                </button>
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('access_review', 'excel')}>
                  Excel
                </button>
              </div>
            </div>

            <div className="card p-4">
              <h4>Change Report</h4>
              <p className="text-sm text-muted mb-2">Entity changes over time</p>
              <div className="flex gap-2">
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('change_report', 'json')}>
                  JSON
                </button>
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('change_report', 'pdf')}>
                  PDF
                </button>
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('change_report', 'excel')}>
                  Excel
                </button>
              </div>
            </div>

            <div className="card p-4">
              <h4>Compliance Summary</h4>
              <p className="text-sm text-muted mb-2">Overall compliance status across frameworks</p>
              <div className="flex gap-2">
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('compliance_summary', 'json')}>
                  JSON
                </button>
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('compliance_summary', 'pdf')}>
                  PDF
                </button>
                <button className="btn btn-sm btn-secondary" onClick={() => generateReport('compliance_summary', 'excel')}>
                  Excel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <>
          {/* Filters */}
          <div className="section mb-4">
            <div className="flex flex-wrap gap-4">
              <select
                className="form-select"
                value={filters.event_category}
                onChange={(e) => setFilters({ ...filters, event_category: e.target.value })}
              >
                <option value="">All Categories</option>
                {categories.map(c => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
              </select>

              <select
                className="form-select"
                value={filters.severity}
                onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              >
                <option value="">All Severities</option>
                {severities.map(s => <option key={s} value={s}>{s}</option>)}
              </select>

              <select
                className="form-select"
                value={filters.compliance_tag}
                onChange={(e) => setFilters({ ...filters, compliance_tag: e.target.value })}
              >
                <option value="">All Compliance</option>
                {complianceTags.map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
              </select>

              <input
                type="text"
                className="form-input"
                placeholder="Entity type..."
                value={filters.entity_type}
                onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}
              />

              <input
                type="date"
                className="form-input"
                value={filters.from_date}
                onChange={(e) => setFilters({ ...filters, from_date: e.target.value })}
              />

              <input
                type="date"
                className="form-input"
                value={filters.to_date}
                onChange={(e) => setFilters({ ...filters, to_date: e.target.value })}
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
                        <th>Event</th>
                        <th>Category</th>
                        <th>Severity</th>
                        <th>Action</th>
                        <th>Entity</th>
                        <th>User</th>
                        <th>Compliance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map(log => (
                        <tr key={log.id} onClick={() => setSelectedLog(log)} style={{ cursor: 'pointer' }}>
                          <td><code>{new Date(log.occurred_at).toLocaleString()}</code></td>
                          <td className="text-sm">{log.event_type}</td>
                          <td>{getCategoryBadge(log.event_category)}</td>
                          <td>{getSeverityBadge(log.severity)}</td>
                          <td>{getActionBadge(log.action)}</td>
                          <td>
                            {log.entity_type && (
                              <span
                                className="text-link"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (log.entity_id) loadChangeHistory(log.entity_type, log.entity_id);
                                }}
                              >
                                {log.entity_type}/{log.entity_id || '-'}
                              </span>
                            )}
                          </td>
                          <td>{log.user_email || 'system'}</td>
                          <td>
                            {(log.compliance_tags || []).map(tag => (
                              <span key={tag} className="badge badge-sm badge-success mr-1">{tag}</span>
                            ))}
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
        </>
      )}

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="modal-overlay" onClick={() => setSelectedLog(null)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Audit Log Details</h3>
              <button className="modal-close" onClick={() => setSelectedLog(null)}>x</button>
            </div>
            <div className="modal-body">
              <div className="grid-2 mb-4">
                <div><strong>ID:</strong> <code className="text-xs">{selectedLog.id}</code></div>
                <div><strong>Sequence:</strong> #{selectedLog.sequence_number}</div>
                <div><strong>Event Type:</strong> {selectedLog.event_type}</div>
                <div><strong>Category:</strong> {getCategoryBadge(selectedLog.event_category)}</div>
                <div><strong>Severity:</strong> {getSeverityBadge(selectedLog.severity)}</div>
                <div><strong>Action:</strong> {getActionBadge(selectedLog.action)}</div>
                <div><strong>Occurred At:</strong> {new Date(selectedLog.occurred_at).toLocaleString()}</div>
                <div><strong>Recorded At:</strong> {new Date(selectedLog.recorded_at).toLocaleString()}</div>
                <div><strong>Entity:</strong> {selectedLog.entity_type}/{selectedLog.entity_id || '-'}</div>
                <div><strong>Entity Name:</strong> {selectedLog.entity_name || '-'}</div>
                <div><strong>User:</strong> {selectedLog.user_email || 'system'}</div>
                <div><strong>User Role:</strong> {selectedLog.user_role || '-'}</div>
                <div><strong>IP Address:</strong> <code>{selectedLog.ip_address || '-'}</code></div>
                <div><strong>Session:</strong> <code className="text-xs">{selectedLog.session_id || '-'}</code></div>
              </div>

              {/* Hash Chain Info */}
              <div className="card p-3 mb-4 bg-dark">
                <strong>Hash Chain Verification</strong>
                <div className="mt-2 text-xs">
                  <div><strong>Data Hash:</strong> <code>{selectedLog.data_hash}</code></div>
                  <div><strong>Previous Hash:</strong> <code>{selectedLog.previous_hash || 'GENESIS'}</code></div>
                </div>
              </div>

              {/* Compliance Tags */}
              {selectedLog.compliance_tags?.length > 0 && (
                <div className="mb-4">
                  <strong>Compliance Tags:</strong>
                  <div className="mt-1">
                    {selectedLog.compliance_tags.map(tag => (
                      <span key={tag} className="badge badge-success mr-2">{tag.toUpperCase()}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Changes */}
              {selectedLog.changes && Object.keys(selectedLog.changes).length > 0 && (
                <div className="mb-4">
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

              {/* Metadata */}
              {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
                <div className="mb-4">
                  <strong>Metadata:</strong>
                  <pre className="code-block mt-2">{JSON.stringify(selectedLog.metadata, null, 2)}</pre>
                </div>
              )}

              {selectedLog.user_agent && (
                <div>
                  <strong>User Agent:</strong>
                  <div className="text-sm text-muted mt-1">{selectedLog.user_agent}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Change History Modal */}
      {changeHistory && (
        <div className="modal-overlay" onClick={() => setChangeHistory(null)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Change History: {changeHistory.entityType}/{changeHistory.entityId}</h3>
              <button className="modal-close" onClick={() => setChangeHistory(null)}>x</button>
            </div>
            <div className="modal-body">
              {changeHistory.versions.length === 0 ? (
                <p className="text-muted">No change history found for this entity.</p>
              ) : (
                <div className="timeline">
                  {changeHistory.versions.map((version, idx) => (
                    <div key={version.id} className="timeline-item">
                      <div className="timeline-marker">v{version.version_number}</div>
                      <div className="timeline-content">
                        <div className="text-sm text-muted">
                          {new Date(version.created_at).toLocaleString()}
                        </div>
                        <div className="mt-1">
                          <strong>Changed fields:</strong> {version.changed_fields?.join(', ') || '-'}
                        </div>
                        {version.change_summary && (
                          <div className="text-sm mt-1">{version.change_summary}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
