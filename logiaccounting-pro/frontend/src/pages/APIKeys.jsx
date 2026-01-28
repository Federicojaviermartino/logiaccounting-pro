import { useState, useEffect } from 'react';
import { apiKeysAPI } from '../services/api';
import toast from '../utils/toast';

export default function APIKeys() {
  const [loading, setLoading] = useState(true);
  const [keys, setKeys] = useState([]);
  const [scopes, setScopes] = useState([]);
  const [rateLimits, setRateLimits] = useState({});
  const [showModal, setShowModal] = useState(false);
  const [newKeyResult, setNewKeyResult] = useState(null);
  const [selectedKey, setSelectedKey] = useState(null);
  const [showUsageModal, setShowUsageModal] = useState(false);
  const [usageStats, setUsageStats] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, per_page: 20, total: 0 });
  const [filters, setFilters] = useState({ is_active: null, environment: '' });

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    scopes: [],
    environment: 'production',
    expires_days: 365,
    allowed_ips: '',
    rate_limit_per_minute: '',
    rate_limit_per_hour: '',
    rate_limit_per_day: ''
  });

  useEffect(() => {
    loadData();
    loadScopes();
    loadRateLimits();
  }, [pagination.page, filters]);

  const loadData = async () => {
    try {
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        ...(filters.is_active !== null && { is_active: filters.is_active }),
        ...(filters.environment && { environment: filters.environment })
      };
      const response = await apiKeysAPI.list(params);
      setKeys(response.data.keys || []);
      setPagination(prev => ({ ...prev, total: response.data.total || 0 }));
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadScopes = async () => {
    try {
      const response = await apiKeysAPI.getScopes();
      setScopes(response.data.scopes || []);
    } catch (error) {
      console.error('Failed to load scopes:', error);
    }
  };

  const loadRateLimits = async () => {
    try {
      const response = await apiKeysAPI.getRateLimits();
      setRateLimits(response.data.tiers || {});
    } catch (error) {
      console.error('Failed to load rate limits:', error);
    }
  };

  const handleCreate = async () => {
    try {
      const payload = {
        name: formData.name,
        description: formData.description || undefined,
        scopes: formData.scopes.length > 0 ? formData.scopes : undefined,
        environment: formData.environment,
        expires_days: formData.expires_days || undefined,
        allowed_ips: formData.allowed_ips ? formData.allowed_ips.split(',').map(ip => ip.trim()) : undefined,
        rate_limit_per_minute: formData.rate_limit_per_minute ? parseInt(formData.rate_limit_per_minute) : undefined,
        rate_limit_per_hour: formData.rate_limit_per_hour ? parseInt(formData.rate_limit_per_hour) : undefined,
        rate_limit_per_day: formData.rate_limit_per_day ? parseInt(formData.rate_limit_per_day) : undefined
      };
      const response = await apiKeysAPI.create(payload);
      setNewKeyResult(response.data);
      setShowModal(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error('Failed to create key: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRegenerate = async (keyId) => {
    if (!confirm('Are you sure you want to regenerate this key? The old key will stop working immediately.')) return;
    try {
      const response = await apiKeysAPI.regenerate(keyId);
      setNewKeyResult(response.data);
      loadData();
    } catch (error) {
      toast.error('Failed to regenerate key: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRevoke = async (keyId) => {
    if (!confirm('Are you sure you want to revoke this key? This action cannot be undone.')) return;
    try {
      await apiKeysAPI.revoke(keyId);
      loadData();
    } catch (error) {
      toast.error('Failed to revoke key');
    }
  };

  const handleDelete = async (keyId) => {
    if (!confirm('Are you sure you want to permanently delete this key?')) return;
    try {
      await apiKeysAPI.delete(keyId);
      loadData();
    } catch (error) {
      toast.error('Failed to delete key');
    }
  };

  const loadUsageStats = async (keyId) => {
    try {
      const response = await apiKeysAPI.getUsage(keyId);
      setUsageStats(response.data.usage);
      setShowUsageModal(true);
    } catch (error) {
      toast.error('Failed to load usage stats');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      scopes: [],
      environment: 'production',
      expires_days: 365,
      allowed_ips: '',
      rate_limit_per_minute: '',
      rate_limit_per_hour: '',
      rate_limit_per_day: ''
    });
  };

  const toggleScope = (scope) => {
    setFormData(prev => ({
      ...prev,
      scopes: prev.scopes.includes(scope)
        ? prev.scopes.filter(s => s !== scope)
        : [...prev.scopes, scope]
    }));
  };

  const getStatusBadge = (key) => {
    if (!key.is_active) return <span className="badge badge-danger">Revoked</span>;
    if (key.is_expired) return <span className="badge badge-warning">Expired</span>;
    return <span className="badge badge-success">Active</span>;
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const scopeCategories = scopes.reduce((acc, s) => {
    const category = s.scope.includes(':') ? s.scope.split(':')[0] : 'general';
    if (!acc[category]) acc[category] = [];
    acc[category].push(s);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading API keys...</p>
      </div>
    );
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">API Keys Management</h1>
          <p className="text-muted">Manage API keys for external integrations with scopes and rate limits</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            resetForm();
            setShowModal(true);
          }}
        >
          + Generate New Key
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid-4 mb-6">
        <div className="stat-card">
          <div className="stat-icon blue">🔑</div>
          <div>
            <p className="stat-value">{pagination.total}</p>
            <p className="stat-label">Total Keys</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✓</div>
          <div>
            <p className="stat-value">{keys.filter(k => k.is_active && !k.is_expired).length}</p>
            <p className="stat-label">Active</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon red">⊘</div>
          <div>
            <p className="stat-value">{keys.filter(k => !k.is_active).length}</p>
            <p className="stat-label">Revoked</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">⏱</div>
          <div>
            <p className="stat-value">{keys.filter(k => k.is_expired).length}</p>
            <p className="stat-label">Expired</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="section mb-4">
        <div className="flex gap-4 items-center">
          <div className="form-group mb-0">
            <label className="form-label text-sm">Status</label>
            <select
              className="form-select"
              value={filters.is_active === null ? '' : filters.is_active}
              onChange={(e) => setFilters({ ...filters, is_active: e.target.value === '' ? null : e.target.value === 'true' })}
            >
              <option value="">All</option>
              <option value="true">Active</option>
              <option value="false">Revoked</option>
            </select>
          </div>
          <div className="form-group mb-0">
            <label className="form-label text-sm">Environment</label>
            <select
              className="form-select"
              value={filters.environment}
              onChange={(e) => setFilters({ ...filters, environment: e.target.value })}
            >
              <option value="">All</option>
              <option value="production">Production</option>
              <option value="staging">Staging</option>
              <option value="development">Development</option>
            </select>
          </div>
        </div>
      </div>

      {/* New Key Created Alert */}
      {newKeyResult && (
        <div className="section mb-6 bg-success-light p-4 rounded">
          <h3 className="font-bold text-success mb-2">API Key Created!</h3>
          <p className="text-sm mb-3">
            Copy this key now. For security reasons, it won't be shown again.
          </p>
          <div className="flex items-center gap-2 bg-white p-3 rounded font-mono text-sm">
            <code className="flex-1 break-all">{newKeyResult.key}</code>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => copyToClipboard(newKeyResult.key)}
            >
              Copy
            </button>
          </div>
          <button
            className="btn btn-sm btn-secondary mt-3"
            onClick={() => setNewKeyResult(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Keys List */}
      <div className="section">
        <h3 className="section-title">API Keys</h3>
        {keys.length === 0 ? (
          <p className="text-muted text-center py-8">
            No API keys yet. Generate one to enable external integrations.
          </p>
        ) : (
          <div className="space-y-4">
            {keys.map((key) => (
              <div key={key.id} className="card p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-bold flex items-center gap-2">
                      {key.name}
                      {getStatusBadge(key)}
                      <span className="badge badge-secondary">{key.environment}</span>
                    </h4>
                    <p className="text-muted text-sm font-mono">
                      {key.key_prefix}
                    </p>
                    {key.description && (
                      <p className="text-muted text-sm mt-1">{key.description}</p>
                    )}
                  </div>
                  <div className="text-right text-sm">
                    <p className="text-muted">
                      Created: {new Date(key.created_at).toLocaleDateString()}
                    </p>
                    {key.expires_at && (
                      <p className="text-muted">
                        Expires: {new Date(key.expires_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>

                <div className="grid-4 mb-4 text-sm">
                  <div>
                    <span className="text-muted">Last Used:</span>
                    <p>{key.last_used_at ? new Date(key.last_used_at).toLocaleString() : 'Never'}</p>
                  </div>
                  <div>
                    <span className="text-muted">Total Requests:</span>
                    <p>{key.total_requests?.toLocaleString() || 0}</p>
                  </div>
                  <div>
                    <span className="text-muted">Rate Limit (min):</span>
                    <p>{key.rate_limits?.per_minute || 'Default'}</p>
                  </div>
                  <div>
                    <span className="text-muted">IP Restrictions:</span>
                    <p>{key.allowed_ips?.length || 0} IPs</p>
                  </div>
                </div>

                {/* Scopes */}
                <div className="mb-4">
                  <span className="text-muted text-sm">Scopes:</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {(key.scopes || []).map(scope => (
                      <span key={scope} className="badge badge-info">{scope}</span>
                    ))}
                    {(!key.scopes || key.scopes.length === 0) && (
                      <span className="text-muted">No scopes assigned</span>
                    )}
                  </div>
                </div>

                <div className="flex gap-2 flex-wrap">
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => setSelectedKey(key)}
                  >
                    View Details
                  </button>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => loadUsageStats(key.id)}
                  >
                    Usage Stats
                  </button>
                  {key.is_active && (
                    <>
                      <button
                        className="btn btn-sm btn-info"
                        onClick={() => handleRegenerate(key.id)}
                      >
                        Regenerate
                      </button>
                      <button
                        className="btn btn-sm btn-warning"
                        onClick={() => handleRevoke(key.id)}
                      >
                        Revoke
                      </button>
                    </>
                  )}
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleDelete(key.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {pagination.total > pagination.per_page && (
          <div className="flex justify-center gap-2 mt-4">
            <button
              className="btn btn-sm btn-secondary"
              disabled={pagination.page === 1}
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
            >
              Previous
            </button>
            <span className="flex items-center px-4">
              Page {pagination.page} of {Math.ceil(pagination.total / pagination.per_page)}
            </span>
            <button
              className="btn btn-sm btn-secondary"
              disabled={pagination.page >= Math.ceil(pagination.total / pagination.per_page)}
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Key Details Modal */}
      {selectedKey && (
        <div className="modal-overlay" onClick={() => setSelectedKey(null)}>
          <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>API Key Details</h3>
              <button className="modal-close" onClick={() => setSelectedKey(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="space-y-4">
                <div className="grid-2">
                  <div>
                    <label className="text-muted text-sm">Name</label>
                    <p className="font-bold">{selectedKey.name}</p>
                  </div>
                  <div>
                    <label className="text-muted text-sm">Environment</label>
                    <p><span className="badge badge-secondary">{selectedKey.environment}</span></p>
                  </div>
                </div>
                {selectedKey.description && (
                  <div>
                    <label className="text-muted text-sm">Description</label>
                    <p>{selectedKey.description}</p>
                  </div>
                )}
                <div>
                  <label className="text-muted text-sm">Key Prefix</label>
                  <p className="font-mono">{selectedKey.key_prefix}</p>
                </div>
                <div>
                  <label className="text-muted text-sm">Status</label>
                  <p>{getStatusBadge(selectedKey)}</p>
                </div>
                <div>
                  <label className="text-muted text-sm">Scopes</label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {(selectedKey.scopes || []).map(scope => (
                      <span key={scope} className="badge badge-info">{scope}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-muted text-sm">Rate Limits</label>
                  <div className="grid-3 mt-1">
                    <div>
                      <span className="text-muted">Per Minute:</span>
                      <p>{selectedKey.rate_limits?.per_minute || 'Default'}</p>
                    </div>
                    <div>
                      <span className="text-muted">Per Hour:</span>
                      <p>{selectedKey.rate_limits?.per_hour || 'Default'}</p>
                    </div>
                    <div>
                      <span className="text-muted">Per Day:</span>
                      <p>{selectedKey.rate_limits?.per_day || 'Default'}</p>
                    </div>
                  </div>
                </div>
                {selectedKey.allowed_ips?.length > 0 && (
                  <div>
                    <label className="text-muted text-sm">Allowed IPs</label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {selectedKey.allowed_ips.map((ip, i) => (
                        <span key={i} className="badge badge-secondary">{ip}</span>
                      ))}
                    </div>
                  </div>
                )}
                <div className="grid-2">
                  <div>
                    <label className="text-muted text-sm">Created</label>
                    <p>{new Date(selectedKey.created_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <label className="text-muted text-sm">Expires</label>
                    <p>{selectedKey.expires_at ? new Date(selectedKey.expires_at).toLocaleString() : 'Never'}</p>
                  </div>
                </div>
                <div className="grid-2">
                  <div>
                    <label className="text-muted text-sm">Last Used</label>
                    <p>{selectedKey.last_used_at ? new Date(selectedKey.last_used_at).toLocaleString() : 'Never'}</p>
                  </div>
                  <div>
                    <label className="text-muted text-sm">Total Requests</label>
                    <p>{selectedKey.total_requests?.toLocaleString() || 0}</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSelectedKey(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Usage Stats Modal */}
      {showUsageModal && usageStats && (
        <div className="modal-overlay" onClick={() => setShowUsageModal(false)}>
          <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>API Key Usage Statistics</h3>
              <button className="modal-close" onClick={() => setShowUsageModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="grid-3 mb-4">
                <div className="stat-card">
                  <p className="stat-value">{usageStats.total_requests?.toLocaleString() || 0}</p>
                  <p className="stat-label">Total Requests</p>
                </div>
                <div className="stat-card">
                  <p className="stat-value">{usageStats.period_days} days</p>
                  <p className="stat-label">Period</p>
                </div>
                <div className="stat-card">
                  <p className="stat-value">{usageStats.last_used_at ? new Date(usageStats.last_used_at).toLocaleDateString() : 'N/A'}</p>
                  <p className="stat-label">Last Used</p>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowUsageModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Key Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Generate New API Key</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              <div className="form-group">
                <label className="form-label">Key Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Shopify Integration"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="What is this key used for?"
                  rows={2}
                />
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Environment</label>
                  <select
                    className="form-select"
                    value={formData.environment}
                    onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                  >
                    <option value="production">Production</option>
                    <option value="staging">Staging</option>
                    <option value="development">Development</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Expires In (days)</label>
                  <select
                    className="form-select"
                    value={formData.expires_days}
                    onChange={(e) => setFormData({ ...formData, expires_days: parseInt(e.target.value) })}
                  >
                    <option value={0}>Never</option>
                    <option value={30}>30 days</option>
                    <option value={90}>90 days</option>
                    <option value={180}>180 days</option>
                    <option value={365}>1 year</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Scopes</label>
                <p className="text-muted text-sm mb-3">Select which resources this key can access</p>

                <div className="space-y-4">
                  {Object.entries(scopeCategories).map(([category, categoryScopes]) => (
                    <div key={category} className="p-3 border rounded">
                      <h4 className="font-bold capitalize mb-2">{category}</h4>
                      <div className="grid-2 gap-2">
                        {categoryScopes.map(s => (
                          <label key={s.scope} className="checkbox-label flex items-start gap-2">
                            <input
                              type="checkbox"
                              checked={formData.scopes.includes(s.scope)}
                              onChange={() => toggleScope(s.scope)}
                              className="mt-1"
                            />
                            <div>
                              <span className="font-mono text-sm">{s.scope}</span>
                              <p className="text-muted text-xs">{s.description}</p>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">IP Whitelist (optional)</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.allowed_ips}
                  onChange={(e) => setFormData({ ...formData, allowed_ips: e.target.value })}
                  placeholder="Comma-separated IPs: 192.168.1.1, 10.0.0.1"
                />
                <p className="text-muted text-xs mt-1">Leave empty to allow from any IP</p>
              </div>

              <div className="form-group">
                <label className="form-label">Custom Rate Limits (optional)</label>
                <div className="grid-3">
                  <div>
                    <label className="text-muted text-xs">Per Minute</label>
                    <input
                      type="number"
                      className="form-input"
                      value={formData.rate_limit_per_minute}
                      onChange={(e) => setFormData({ ...formData, rate_limit_per_minute: e.target.value })}
                      placeholder="Default"
                    />
                  </div>
                  <div>
                    <label className="text-muted text-xs">Per Hour</label>
                    <input
                      type="number"
                      className="form-input"
                      value={formData.rate_limit_per_hour}
                      onChange={(e) => setFormData({ ...formData, rate_limit_per_hour: e.target.value })}
                      placeholder="Default"
                    />
                  </div>
                  <div>
                    <label className="text-muted text-xs">Per Day</label>
                    <input
                      type="number"
                      className="form-input"
                      value={formData.rate_limit_per_day}
                      onChange={(e) => setFormData({ ...formData, rate_limit_per_day: e.target.value })}
                      placeholder="Default"
                    />
                  </div>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleCreate}
                disabled={!formData.name}
              >
                Generate Key
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
