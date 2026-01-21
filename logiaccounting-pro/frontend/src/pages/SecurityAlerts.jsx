/**
 * Security Alerts Page - Phase 15
 * Security and Compliance Alert Management
 */

import { useState, useEffect } from 'react';
import { alertsAPI, alertRulesAPI } from '../services/auditApi';

export default function SecurityAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('alerts'); // alerts, rules

  const [filters, setFilters] = useState({
    status: '',
    severity: '',
    alert_type: ''
  });

  const [selectedAlert, setSelectedAlert] = useState(null);
  const [resolveNotes, setResolveNotes] = useState('');
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [editingRule, setEditingRule] = useState(null);

  const [ruleForm, setRuleForm] = useState({
    name: '',
    description: '',
    event_types: [],
    conditions: {},
    alert_type: '',
    severity: 'medium',
    cooldown_minutes: 60,
    is_active: true
  });

  useEffect(() => {
    loadAlerts();
    loadRules();
  }, [filters]);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const params = { ...filters, limit: 100 };
      Object.keys(params).forEach(k => !params[k] && delete params[k]);

      const res = await alertsAPI.getAlerts(params);
      setAlerts(res.data.alerts || []);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadRules = async () => {
    try {
      const res = await alertRulesAPI.getRules();
      setRules(res.data.rules || []);
    } catch (err) {
      console.error('Failed to load rules:', err);
    }
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      await alertsAPI.acknowledge(alertId);
      loadAlerts();
    } catch (err) {
      alert('Failed to acknowledge: ' + (err.response?.data?.detail || err.message));
    }
  };

  const resolveAlert = async () => {
    if (!selectedAlert) return;
    try {
      await alertsAPI.resolve(selectedAlert.id, resolveNotes);
      setSelectedAlert(null);
      setResolveNotes('');
      loadAlerts();
    } catch (err) {
      alert('Failed to resolve: ' + (err.response?.data?.detail || err.message));
    }
  };

  const dismissAlert = async (alertId) => {
    if (!confirm('Are you sure you want to dismiss this alert?')) return;
    try {
      await alertsAPI.dismiss(alertId, 'Dismissed by user');
      loadAlerts();
    } catch (err) {
      alert('Failed to dismiss: ' + (err.response?.data?.detail || err.message));
    }
  };

  const saveRule = async () => {
    try {
      if (editingRule) {
        await alertRulesAPI.updateRule(editingRule.id, ruleForm);
      } else {
        await alertRulesAPI.createRule(ruleForm);
      }
      setShowRuleModal(false);
      setEditingRule(null);
      resetRuleForm();
      loadRules();
    } catch (err) {
      alert('Failed to save rule: ' + (err.response?.data?.detail || err.message));
    }
  };

  const deleteRule = async (ruleId) => {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    try {
      await alertRulesAPI.deleteRule(ruleId);
      loadRules();
    } catch (err) {
      alert('Failed to delete: ' + (err.response?.data?.detail || err.message));
    }
  };

  const editRule = (rule) => {
    setEditingRule(rule);
    setRuleForm({
      name: rule.name,
      description: rule.description || '',
      event_types: rule.event_types || [],
      conditions: rule.conditions || {},
      alert_type: rule.alert_type,
      severity: rule.severity,
      cooldown_minutes: rule.cooldown_minutes || 60,
      is_active: rule.is_active
    });
    setShowRuleModal(true);
  };

  const resetRuleForm = () => {
    setRuleForm({
      name: '',
      description: '',
      event_types: [],
      conditions: {},
      alert_type: '',
      severity: 'medium',
      cooldown_minutes: 60,
      is_active: true
    });
  };

  const getStatusBadge = (status) => {
    const colors = {
      open: 'badge-danger',
      acknowledged: 'badge-warning',
      investigating: 'badge-info',
      resolved: 'badge-success',
      dismissed: 'badge-gray'
    };
    return <span className={`badge ${colors[status] || 'badge-gray'}`}>{status}</span>;
  };

  const getSeverityBadge = (severity) => {
    const colors = {
      low: 'badge-info',
      medium: 'badge-warning',
      high: 'badge-danger',
      critical: 'badge-danger'
    };
    return <span className={`badge ${colors[severity] || 'badge-gray'}`}>{severity}</span>;
  };

  const getAlertIcon = (alertType) => {
    const icons = {
      brute_force: '🔐',
      bulk_delete: '🗑️',
      permission_escalation: '⬆️',
      data_export: '📤',
      suspicious_activity: '⚠️',
      compliance_violation: '📋'
    };
    return icons[alertType] || '🔔';
  };

  const statuses = ['open', 'acknowledged', 'investigating', 'resolved', 'dismissed'];
  const severities = ['low', 'medium', 'high', 'critical'];
  const alertTypes = [
    'brute_force', 'bulk_delete', 'permission_escalation',
    'data_export', 'suspicious_activity', 'compliance_violation'
  ];

  // Count alerts by status
  const alertCounts = {
    open: alerts.filter(a => a.status === 'open').length,
    acknowledged: alerts.filter(a => a.status === 'acknowledged').length,
    investigating: alerts.filter(a => a.status === 'investigating').length,
    resolved: alerts.filter(a => a.status === 'resolved').length
  };

  return (
    <>
      <div className="info-banner mb-6">
        Security & Compliance Alerts - Real-time threat detection and incident management (Phase 15)
      </div>

      {/* Tabs */}
      <div className="tabs mb-6">
        <button
          className={`tab ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          Alerts ({alerts.length})
        </button>
        <button
          className={`tab ${activeTab === 'rules' ? 'active' : ''}`}
          onClick={() => setActiveTab('rules')}
        >
          Alert Rules ({rules.length})
        </button>
      </div>

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <>
          {/* Stats */}
          <div className="stats-grid mb-6">
            <div className="stat-card">
              <div className="stat-icon text-danger">!</div>
              <div className="stat-content">
                <div className="stat-value text-danger">{alertCounts.open}</div>
                <div className="stat-label">Open Alerts</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon text-warning">*</div>
              <div className="stat-content">
                <div className="stat-value text-warning">{alertCounts.acknowledged}</div>
                <div className="stat-label">Acknowledged</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon text-info">?</div>
              <div className="stat-content">
                <div className="stat-value text-info">{alertCounts.investigating}</div>
                <div className="stat-label">Investigating</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon text-success">+</div>
              <div className="stat-content">
                <div className="stat-value text-success">{alertCounts.resolved}</div>
                <div className="stat-label">Resolved</div>
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="section mb-4">
            <div className="flex flex-wrap gap-4">
              <select
                className="form-select"
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              >
                <option value="">All Statuses</option>
                {statuses.map(s => <option key={s} value={s}>{s}</option>)}
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
                value={filters.alert_type}
                onChange={(e) => setFilters({ ...filters, alert_type: e.target.value })}
              >
                <option value="">All Types</option>
                {alertTypes.map(t => (
                  <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
                ))}
              </select>

              <button className="btn btn-secondary" onClick={loadAlerts}>
                Refresh
              </button>
            </div>
          </div>

          {/* Alerts List */}
          <div className="section">
            {loading ? (
              <div className="text-center p-8">Loading alerts...</div>
            ) : alerts.length === 0 ? (
              <div className="card p-8 text-center text-muted">
                No alerts found matching your criteria.
              </div>
            ) : (
              <div className="space-y-4">
                {alerts.map(alert => (
                  <div
                    key={alert.id}
                    className={`card p-4 border-l-4 ${
                      alert.severity === 'critical' ? 'border-l-danger' :
                      alert.severity === 'high' ? 'border-l-danger' :
                      alert.severity === 'medium' ? 'border-l-warning' : 'border-l-info'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{getAlertIcon(alert.alert_type)}</span>
                        <div>
                          <h4 className="font-bold">{alert.title}</h4>
                          <p className="text-sm text-muted">{alert.description}</p>
                          <div className="flex gap-2 mt-2">
                            {getStatusBadge(alert.status)}
                            {getSeverityBadge(alert.severity)}
                            <span className="badge badge-gray">{alert.alert_type?.replace(/_/g, ' ')}</span>
                          </div>
                          <div className="text-xs text-muted mt-2">
                            Created: {new Date(alert.created_at).toLocaleString()}
                            {alert.assigned_to && ` | Assigned to: ${alert.assigned_to}`}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {alert.status === 'open' && (
                          <button
                            className="btn btn-sm btn-warning"
                            onClick={() => acknowledgeAlert(alert.id)}
                          >
                            Acknowledge
                          </button>
                        )}
                        {['open', 'acknowledged', 'investigating'].includes(alert.status) && (
                          <button
                            className="btn btn-sm btn-success"
                            onClick={() => setSelectedAlert(alert)}
                          >
                            Resolve
                          </button>
                        )}
                        {alert.status !== 'dismissed' && (
                          <button
                            className="btn btn-sm btn-secondary"
                            onClick={() => dismissAlert(alert.id)}
                          >
                            Dismiss
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Evidence */}
                    {alert.evidence && Object.keys(alert.evidence).length > 0 && (
                      <details className="mt-3">
                        <summary className="cursor-pointer text-link text-sm">
                          View Evidence
                        </summary>
                        <pre className="code-block mt-2 text-xs">
                          {JSON.stringify(alert.evidence, null, 2)}
                        </pre>
                      </details>
                    )}

                    {/* Resolution Notes */}
                    {alert.resolution_notes && (
                      <div className="mt-3 p-2 bg-success-light rounded">
                        <strong className="text-sm">Resolution:</strong>
                        <p className="text-sm">{alert.resolution_notes}</p>
                        {alert.resolved_at && (
                          <span className="text-xs text-muted">
                            Resolved: {new Date(alert.resolved_at).toLocaleString()}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {/* Rules Tab */}
      {activeTab === 'rules' && (
        <div className="section">
          <div className="flex justify-between items-center mb-4">
            <h3 className="section-title">Alert Rules</h3>
            <button
              className="btn btn-primary"
              onClick={() => {
                resetRuleForm();
                setEditingRule(null);
                setShowRuleModal(true);
              }}
            >
              + Create Rule
            </button>
          </div>

          {rules.length === 0 ? (
            <div className="card p-8 text-center text-muted">
              No alert rules configured. Create one to start monitoring.
            </div>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>Event Types</th>
                    <th>Cooldown</th>
                    <th>Status</th>
                    <th>Last Triggered</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map(rule => (
                    <tr key={rule.id}>
                      <td>
                        <strong>{rule.name}</strong>
                        {rule.description && (
                          <div className="text-xs text-muted">{rule.description}</div>
                        )}
                      </td>
                      <td>{rule.alert_type?.replace(/_/g, ' ')}</td>
                      <td>{getSeverityBadge(rule.severity)}</td>
                      <td>
                        {(rule.event_types || []).slice(0, 2).map(et => (
                          <span key={et} className="badge badge-sm badge-info mr-1">{et}</span>
                        ))}
                        {(rule.event_types || []).length > 2 && (
                          <span className="text-xs text-muted">+{rule.event_types.length - 2}</span>
                        )}
                      </td>
                      <td>{rule.cooldown_minutes}m</td>
                      <td>
                        <span className={`badge ${rule.is_active ? 'badge-success' : 'badge-gray'}`}>
                          {rule.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        {rule.last_triggered_at
                          ? new Date(rule.last_triggered_at).toLocaleDateString()
                          : 'Never'}
                      </td>
                      <td>
                        <div className="flex gap-1">
                          <button
                            className="btn btn-sm btn-secondary"
                            onClick={() => editRule(rule)}
                          >
                            Edit
                          </button>
                          <button
                            className="btn btn-sm btn-danger"
                            onClick={() => deleteRule(rule.id)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Resolve Alert Modal */}
      {selectedAlert && (
        <div className="modal-overlay" onClick={() => setSelectedAlert(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Resolve Alert</h3>
              <button className="modal-close" onClick={() => setSelectedAlert(null)}>x</button>
            </div>
            <div className="modal-body">
              <p className="mb-4">
                <strong>Alert:</strong> {selectedAlert.title}
              </p>
              <div className="form-group">
                <label className="form-label">Resolution Notes</label>
                <textarea
                  className="form-textarea"
                  rows={4}
                  value={resolveNotes}
                  onChange={(e) => setResolveNotes(e.target.value)}
                  placeholder="Describe the resolution..."
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSelectedAlert(null)}>
                Cancel
              </button>
              <button className="btn btn-success" onClick={resolveAlert}>
                Mark as Resolved
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rule Modal */}
      {showRuleModal && (
        <div className="modal-overlay" onClick={() => setShowRuleModal(false)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingRule ? 'Edit Alert Rule' : 'Create Alert Rule'}</h3>
              <button className="modal-close" onClick={() => setShowRuleModal(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="grid-2 gap-4">
                <div className="form-group">
                  <label className="form-label">Rule Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={ruleForm.name}
                    onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })}
                    placeholder="e.g., Brute Force Detection"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Alert Type *</label>
                  <select
                    className="form-select"
                    value={ruleForm.alert_type}
                    onChange={(e) => setRuleForm({ ...ruleForm, alert_type: e.target.value })}
                  >
                    <option value="">Select type...</option>
                    {alertTypes.map(t => (
                      <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group col-span-2">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-textarea"
                    rows={2}
                    value={ruleForm.description}
                    onChange={(e) => setRuleForm({ ...ruleForm, description: e.target.value })}
                    placeholder="Describe what this rule detects..."
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Severity *</label>
                  <select
                    className="form-select"
                    value={ruleForm.severity}
                    onChange={(e) => setRuleForm({ ...ruleForm, severity: e.target.value })}
                  >
                    {severities.map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Cooldown (minutes)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={ruleForm.cooldown_minutes}
                    onChange={(e) => setRuleForm({ ...ruleForm, cooldown_minutes: parseInt(e.target.value) || 60 })}
                    min={1}
                  />
                </div>

                <div className="form-group col-span-2">
                  <label className="form-label">Event Types (comma-separated)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={ruleForm.event_types.join(', ')}
                    onChange={(e) => setRuleForm({
                      ...ruleForm,
                      event_types: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                    })}
                    placeholder="e.g., auth.login_failed, security.brute_force"
                  />
                </div>

                <div className="form-group col-span-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={ruleForm.is_active}
                      onChange={(e) => setRuleForm({ ...ruleForm, is_active: e.target.checked })}
                    />
                    <span>Active</span>
                  </label>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowRuleModal(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={saveRule}
                disabled={!ruleForm.name || !ruleForm.alert_type}
              >
                {editingRule ? 'Update Rule' : 'Create Rule'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
