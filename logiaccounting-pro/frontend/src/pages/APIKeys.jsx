import { useState, useEffect } from 'react';
import { apiKeysAPI } from '../services/api';

export default function APIKeys() {
  const [loading, setLoading] = useState(true);
  const [keys, setKeys] = useState([]);
  const [permissions, setPermissions] = useState({});
  const [showModal, setShowModal] = useState(false);
  const [newKeyResult, setNewKeyResult] = useState(null);
  const [selectedKey, setSelectedKey] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    permissions: {},
    expires_days: 365
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [keysRes, permsRes] = await Promise.all([
        apiKeysAPI.list(),
        apiKeysAPI.getPermissions()
      ]);
      setKeys(keysRes.data.keys || []);
      setPermissions(permsRes.data.permissions || {});
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      const response = await apiKeysAPI.create(formData);
      setNewKeyResult(response.data);
      setShowModal(false);
      resetForm();
      loadData();
    } catch (error) {
      alert('Failed to create key: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRevoke = async (keyId) => {
    if (!confirm('Are you sure you want to revoke this key? This action cannot be undone.')) return;
    try {
      await apiKeysAPI.revoke(keyId);
      loadData();
    } catch (error) {
      alert('Failed to revoke key');
    }
  };

  const handleDelete = async (keyId) => {
    if (!confirm('Are you sure you want to permanently delete this key?')) return;
    try {
      await apiKeysAPI.delete(keyId);
      loadData();
    } catch (error) {
      alert('Failed to delete key');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      permissions: {},
      expires_days: 365
    });
  };

  const togglePermission = (entity, action) => {
    const current = formData.permissions[entity] || [];
    let updated;
    if (current.includes(action)) {
      updated = current.filter(a => a !== action);
    } else {
      updated = [...current, action];
    }
    setFormData({
      ...formData,
      permissions: {
        ...formData.permissions,
        [entity]: updated
      }
    });
  };

  const getStatusBadge = (key) => {
    if (key.revoked) return <span className="badge badge-danger">Revoked</span>;
    if (key.expires_at && new Date(key.expires_at) < new Date()) {
      return <span className="badge badge-warning">Expired</span>;
    }
    return <span className="badge badge-success">Active</span>;
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

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
          <p className="text-muted">Manage API keys for external integrations</p>
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
            <p className="stat-value">{keys.length}</p>
            <p className="stat-label">Total Keys</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✓</div>
          <div>
            <p className="stat-value">{keys.filter(k => !k.revoked && (!k.expires_at || new Date(k.expires_at) > new Date())).length}</p>
            <p className="stat-label">Active</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon red">⊘</div>
          <div>
            <p className="stat-value">{keys.filter(k => k.revoked).length}</p>
            <p className="stat-label">Revoked</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">⏱</div>
          <div>
            <p className="stat-value">
              {keys.filter(k => k.expires_at && new Date(k.expires_at) < new Date()).length}
            </p>
            <p className="stat-label">Expired</p>
          </div>
        </div>
      </div>

      {/* New Key Created Alert */}
      {newKeyResult && (
        <div className="section mb-6 bg-success-light p-4 rounded">
          <h3 className="font-bold text-success mb-2">New API Key Created!</h3>
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
                    </h4>
                    <p className="text-muted text-sm font-mono">
                      {key.prefix}••••••••
                    </p>
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

                <div className="grid-3 mb-4 text-sm">
                  <div>
                    <span className="text-muted">Last Used:</span>
                    <p>{key.last_used ? new Date(key.last_used).toLocaleString() : 'Never'}</p>
                  </div>
                  <div>
                    <span className="text-muted">Usage Count:</span>
                    <p>{key.usage_count?.toLocaleString() || 0}</p>
                  </div>
                  <div>
                    <span className="text-muted">Created By:</span>
                    <p>{key.created_by || 'Unknown'}</p>
                  </div>
                </div>

                {/* Permissions */}
                <div className="mb-4">
                  <span className="text-muted text-sm">Permissions:</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {Object.entries(key.permissions || {}).map(([entity, actions]) => (
                      actions.map(action => (
                        <span key={`${entity}-${action}`} className="badge badge-info">
                          {entity}:{action}
                        </span>
                      ))
                    ))}
                    {Object.keys(key.permissions || {}).length === 0 && (
                      <span className="text-muted">No permissions</span>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => setSelectedKey(key)}
                  >
                    View Details
                  </button>
                  {!key.revoked && (
                    <button
                      className="btn btn-sm btn-warning"
                      onClick={() => handleRevoke(key.id)}
                    >
                      Revoke
                    </button>
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
      </div>

      {/* Key Details Modal */}
      {selectedKey && (
        <div className="modal-overlay" onClick={() => setSelectedKey(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>API Key Details</h3>
              <button className="modal-close" onClick={() => setSelectedKey(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="space-y-4">
                <div>
                  <label className="text-muted text-sm">Name</label>
                  <p className="font-bold">{selectedKey.name}</p>
                </div>
                <div>
                  <label className="text-muted text-sm">Key ID</label>
                  <p className="font-mono text-sm">{selectedKey.id}</p>
                </div>
                <div>
                  <label className="text-muted text-sm">Prefix</label>
                  <p className="font-mono">{selectedKey.prefix}</p>
                </div>
                <div>
                  <label className="text-muted text-sm">Status</label>
                  <p>{getStatusBadge(selectedKey)}</p>
                </div>
                <div>
                  <label className="text-muted text-sm">Permissions</label>
                  <div className="mt-1">
                    {Object.entries(selectedKey.permissions || {}).map(([entity, actions]) => (
                      <div key={entity} className="flex items-center gap-2 mb-1">
                        <span className="font-bold">{entity}:</span>
                        {actions.map(action => (
                          <span key={action} className="badge badge-info">{action}</span>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
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
                    <p>{selectedKey.last_used ? new Date(selectedKey.last_used).toLocaleString() : 'Never'}</p>
                  </div>
                  <div>
                    <label className="text-muted text-sm">Total Requests</label>
                    <p>{selectedKey.usage_count?.toLocaleString() || 0}</p>
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

      {/* Create Key Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Generate New API Key</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body">
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
                <label className="form-label">Expires In (days)</label>
                <select
                  className="form-select"
                  value={formData.expires_days}
                  onChange={(e) => setFormData({ ...formData, expires_days: parseInt(e.target.value) })}
                >
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                  <option value={180}>180 days</option>
                  <option value={365}>1 year</option>
                  <option value={730}>2 years</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Permissions</label>
                <p className="text-muted text-sm mb-3">Select which resources this key can access</p>

                <div className="space-y-4">
                  {Object.entries(permissions).map(([entity, actions]) => (
                    <div key={entity} className="p-3 border rounded">
                      <h4 className="font-bold capitalize mb-2">{entity}</h4>
                      <div className="flex gap-4">
                        {actions.map(action => (
                          <label key={action} className="checkbox-label">
                            <input
                              type="checkbox"
                              checked={(formData.permissions[entity] || []).includes(action)}
                              onChange={() => togglePermission(entity, action)}
                            />
                            <span className="capitalize">{action}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
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
