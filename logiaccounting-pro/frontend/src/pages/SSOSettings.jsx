import { useState, useEffect } from 'react';
import { ssoAPI, SSO_PROVIDERS } from '../services/ssoApi';

export default function SSOSettings() {
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [scimToken, setScimToken] = useState(null);

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      setLoading(true);
      const response = await ssoAPI.getConnections();
      setConnections(response.data);
    } catch (err) {
      setError('Failed to load SSO connections');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleActivate = async (id) => {
    try {
      await ssoAPI.activateConnection(id);
      loadConnections();
    } catch (err) {
      setError('Failed to activate connection');
    }
  };

  const handleDeactivate = async (id) => {
    try {
      await ssoAPI.deactivateConnection(id);
      loadConnections();
    } catch (err) {
      setError('Failed to deactivate connection');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this SSO connection?')) return;
    try {
      await ssoAPI.deleteConnection(id);
      loadConnections();
    } catch (err) {
      setError('Failed to delete connection');
    }
  };

  const handleGenerateSCIMToken = async (connectionId) => {
    try {
      const response = await ssoAPI.generateSCIMToken(connectionId);
      setScimToken(response.data);
    } catch (err) {
      setError('Failed to generate SCIM token');
    }
  };

  const openConfigModal = (connection) => {
    setSelectedConnection(connection);
    setShowConfigModal(true);
  };

  const getStatusBadge = (status) => {
    const badges = {
      active: 'badge badge-success',
      inactive: 'badge badge-secondary',
      pending: 'badge badge-warning',
    };
    return <span className={badges[status] || 'badge'}>{status}</span>;
  };

  const getProviderIcon = (providerType) => {
    return SSO_PROVIDERS[providerType]?.icon || '🔐';
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">Loading SSO settings...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Enterprise SSO</h1>
          <p className="page-subtitle">Configure Single Sign-On for your organization</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
          + Add SSO Connection
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button className="alert-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className="info-card">
        <h3>Supported Providers</h3>
        <div className="provider-grid">
          {Object.entries(SSO_PROVIDERS).map(([key, provider]) => (
            <div key={key} className="provider-item">
              <span className="provider-icon">{provider.icon}</span>
              <span className="provider-name">{provider.name}</span>
              <span className="provider-protocols">
                {provider.protocols.join(', ').toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>SSO Connections</h3>
        </div>
        <div className="card-body">
          {connections.length === 0 ? (
            <div className="empty-state">
              <p>No SSO connections configured</p>
              <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
                Configure your first SSO connection
              </button>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Name</th>
                  <th>Protocol</th>
                  <th>Domains</th>
                  <th>Status</th>
                  <th>SCIM</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {connections.map((conn) => (
                  <tr key={conn.id}>
                    <td>
                      <span className="provider-badge">
                        {getProviderIcon(conn.provider_type)}
                        {SSO_PROVIDERS[conn.provider_type]?.name || conn.provider_type}
                      </span>
                    </td>
                    <td>{conn.name}</td>
                    <td>{conn.protocol?.toUpperCase()}</td>
                    <td>
                      {conn.domains?.map((d, i) => (
                        <span key={i} className="domain-badge">{d}</span>
                      ))}
                    </td>
                    <td>{getStatusBadge(conn.status)}</td>
                    <td>
                      {conn.scim_enabled ? (
                        <span className="badge badge-success">Enabled</span>
                      ) : (
                        <span className="badge badge-secondary">Disabled</span>
                      )}
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="btn btn-sm btn-secondary"
                          onClick={() => openConfigModal(conn)}
                          title="Configure"
                        >
                          ⚙️
                        </button>
                        {conn.status === 'active' ? (
                          <button
                            className="btn btn-sm btn-warning"
                            onClick={() => handleDeactivate(conn.id)}
                            title="Deactivate"
                          >
                            ⏸️
                          </button>
                        ) : (
                          <button
                            className="btn btn-sm btn-success"
                            onClick={() => handleActivate(conn.id)}
                            title="Activate"
                          >
                            ▶️
                          </button>
                        )}
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDelete(conn.id)}
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {showCreateModal && (
        <CreateConnectionModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => {
            setShowCreateModal(false);
            loadConnections();
          }}
        />
      )}

      {showConfigModal && selectedConnection && (
        <ConnectionConfigModal
          connection={selectedConnection}
          onClose={() => {
            setShowConfigModal(false);
            setSelectedConnection(null);
            setScimToken(null);
          }}
          onGenerateSCIMToken={handleGenerateSCIMToken}
          scimToken={scimToken}
          onUpdated={() => {
            loadConnections();
          }}
        />
      )}
    </div>
  );
}

function CreateConnectionModal({ onClose, onCreated }) {
  const [formData, setFormData] = useState({
    name: '',
    protocol: 'oidc',
    provider_type: 'microsoft',
    domains: '',
    configuration: {
      client_id: '',
      client_secret: '',
      tenant_id: '',
      jit_provisioning: true,
      default_role: 'client',
    },
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = {
        ...formData,
        domains: formData.domains.split(',').map((d) => d.trim()).filter(Boolean),
      };
      await ssoAPI.createConnection(data);
      onCreated();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create connection');
    } finally {
      setLoading(false);
    }
  };

  const updateConfig = (key, value) => {
    setFormData((prev) => ({
      ...prev,
      configuration: { ...prev.configuration, [key]: value },
    }));
  };

  const selectedProvider = SSO_PROVIDERS[formData.provider_type];
  const configFields = selectedProvider?.configFields?.[formData.protocol] || [];

  return (
    <div className="modal-overlay">
      <div className="modal modal-lg">
        <div className="modal-header">
          <h2>Add SSO Connection</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <div className="alert alert-error">{error}</div>}

            <div className="form-group">
              <label className="form-label">Connection Name</label>
              <input
                type="text"
                className="form-input"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Company SSO"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Identity Provider</label>
                <select
                  className="form-select"
                  value={formData.provider_type}
                  onChange={(e) => setFormData({ ...formData, provider_type: e.target.value })}
                >
                  {Object.entries(SSO_PROVIDERS).map(([key, provider]) => (
                    <option key={key} value={key}>
                      {provider.icon} {provider.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Protocol</label>
                <select
                  className="form-select"
                  value={formData.protocol}
                  onChange={(e) => setFormData({ ...formData, protocol: e.target.value })}
                >
                  {selectedProvider?.protocols.map((p) => (
                    <option key={p} value={p}>{p.toUpperCase()}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Email Domains (comma-separated)</label>
              <input
                type="text"
                className="form-input"
                value={formData.domains}
                onChange={(e) => setFormData({ ...formData, domains: e.target.value })}
                placeholder="e.g., company.com, corp.company.com"
                required
              />
              <small className="form-hint">
                Users with these email domains will be redirected to SSO
              </small>
            </div>

            <hr />
            <h4>Provider Configuration</h4>

            {configFields.includes('client_id') && (
              <div className="form-group">
                <label className="form-label">Client ID</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.configuration.client_id}
                  onChange={(e) => updateConfig('client_id', e.target.value)}
                  required
                />
              </div>
            )}

            {configFields.includes('client_secret') && (
              <div className="form-group">
                <label className="form-label">Client Secret</label>
                <input
                  type="password"
                  className="form-input"
                  value={formData.configuration.client_secret}
                  onChange={(e) => updateConfig('client_secret', e.target.value)}
                  required
                />
              </div>
            )}

            {configFields.includes('tenant_id') && (
              <div className="form-group">
                <label className="form-label">Tenant ID</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.configuration.tenant_id || ''}
                  onChange={(e) => updateConfig('tenant_id', e.target.value)}
                  placeholder="common for multi-tenant"
                />
              </div>
            )}

            {configFields.includes('domain') && (
              <div className="form-group">
                <label className="form-label">Okta Domain</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.configuration.domain || ''}
                  onChange={(e) => updateConfig('domain', e.target.value)}
                  placeholder="your-org.okta.com"
                />
              </div>
            )}

            {configFields.includes('hosted_domain') && (
              <div className="form-group">
                <label className="form-label">Google Hosted Domain</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.configuration.hosted_domain || ''}
                  onChange={(e) => updateConfig('hosted_domain', e.target.value)}
                  placeholder="company.com"
                />
              </div>
            )}

            {configFields.includes('idp_entity_id') && (
              <div className="form-group">
                <label className="form-label">IdP Entity ID</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.configuration.idp_entity_id || ''}
                  onChange={(e) => updateConfig('idp_entity_id', e.target.value)}
                />
              </div>
            )}

            {configFields.includes('idp_sso_url') && (
              <div className="form-group">
                <label className="form-label">IdP SSO URL</label>
                <input
                  type="url"
                  className="form-input"
                  value={formData.configuration.idp_sso_url || ''}
                  onChange={(e) => updateConfig('idp_sso_url', e.target.value)}
                />
              </div>
            )}

            {configFields.includes('idp_certificate') && (
              <div className="form-group">
                <label className="form-label">IdP Certificate (PEM)</label>
                <textarea
                  className="form-textarea"
                  rows={4}
                  value={formData.configuration.idp_certificate || ''}
                  onChange={(e) => updateConfig('idp_certificate', e.target.value)}
                  placeholder="-----BEGIN CERTIFICATE-----..."
                />
              </div>
            )}

            <hr />
            <h4>Provisioning Settings</h4>

            <div className="form-group">
              <label className="form-checkbox">
                <input
                  type="checkbox"
                  checked={formData.configuration.jit_provisioning}
                  onChange={(e) => updateConfig('jit_provisioning', e.target.checked)}
                />
                <span>Enable Just-in-Time (JIT) Provisioning</span>
              </label>
              <small className="form-hint">
                Automatically create user accounts on first SSO login
              </small>
            </div>

            <div className="form-group">
              <label className="form-label">Default Role for New Users</label>
              <select
                className="form-select"
                value={formData.configuration.default_role}
                onChange={(e) => updateConfig('default_role', e.target.value)}
              >
                <option value="client">Client</option>
                <option value="supplier">Supplier</option>
              </select>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Connection'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ConnectionConfigModal({ connection, onClose, onGenerateSCIMToken, scimToken, onUpdated }) {
  const [activeTab, setActiveTab] = useState('details');
  const baseUrl = window.location.origin;

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const downloadMetadata = async () => {
    try {
      const response = await ssoAPI.getSAMLMetadata(connection.id);
      const blob = new Blob([response.data], { type: 'application/xml' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `sp-metadata-${connection.id}.xml`;
      a.click();
    } catch (err) {
      console.error('Failed to download metadata', err);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal modal-lg">
        <div className="modal-header">
          <h2>
            {SSO_PROVIDERS[connection.provider_type]?.icon} {connection.name}
          </h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'details' ? 'active' : ''}`}
              onClick={() => setActiveTab('details')}
            >
              Details
            </button>
            <button
              className={`tab ${activeTab === 'endpoints' ? 'active' : ''}`}
              onClick={() => setActiveTab('endpoints')}
            >
              Endpoints
            </button>
            <button
              className={`tab ${activeTab === 'scim' ? 'active' : ''}`}
              onClick={() => setActiveTab('scim')}
            >
              SCIM Provisioning
            </button>
          </div>

          {activeTab === 'details' && (
            <div className="tab-content">
              <div className="info-grid">
                <div className="info-item">
                  <label>Connection ID</label>
                  <code>{connection.id}</code>
                </div>
                <div className="info-item">
                  <label>Protocol</label>
                  <span>{connection.protocol?.toUpperCase()}</span>
                </div>
                <div className="info-item">
                  <label>Status</label>
                  <span className={`badge badge-${connection.status === 'active' ? 'success' : 'secondary'}`}>
                    {connection.status}
                  </span>
                </div>
                <div className="info-item">
                  <label>Email Domains</label>
                  <span>{connection.domains?.join(', ')}</span>
                </div>
                <div className="info-item">
                  <label>Created</label>
                  <span>{new Date(connection.created_at).toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'endpoints' && (
            <div className="tab-content">
              <p className="info-text">
                Use these endpoints to configure your Identity Provider:
              </p>

              {connection.protocol === 'saml' && (
                <>
                  <div className="endpoint-item">
                    <label>Entity ID / Audience</label>
                    <div className="endpoint-value">
                      <code>{baseUrl}/sso/saml/{connection.id}/metadata</code>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => copyToClipboard(`${baseUrl}/sso/saml/${connection.id}/metadata`)}
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                  <div className="endpoint-item">
                    <label>Assertion Consumer Service (ACS) URL</label>
                    <div className="endpoint-value">
                      <code>{baseUrl}/api/v1/sso/saml/{connection.id}/acs</code>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => copyToClipboard(`${baseUrl}/api/v1/sso/saml/${connection.id}/acs`)}
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                  <div className="endpoint-item">
                    <label>Single Logout Service (SLS) URL</label>
                    <div className="endpoint-value">
                      <code>{baseUrl}/api/v1/sso/saml/{connection.id}/sls</code>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => copyToClipboard(`${baseUrl}/api/v1/sso/saml/${connection.id}/sls`)}
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                  <button className="btn btn-secondary" onClick={downloadMetadata}>
                    Download SP Metadata XML
                  </button>
                </>
              )}

              {(connection.protocol === 'oauth2' || connection.protocol === 'oidc') && (
                <div className="endpoint-item">
                  <label>Callback / Redirect URI</label>
                  <div className="endpoint-value">
                    <code>{baseUrl}/api/v1/sso/oauth/{connection.id}/callback</code>
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => copyToClipboard(`${baseUrl}/api/v1/sso/oauth/${connection.id}/callback`)}
                    >
                      Copy
                    </button>
                  </div>
                </div>
              )}

              <div className="endpoint-item">
                <label>SSO Login URL</label>
                <div className="endpoint-value">
                  <code>
                    {baseUrl}/api/v1/sso/{connection.protocol === 'saml' ? 'saml' : 'oauth'}/{connection.id}/login
                  </code>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() =>
                      copyToClipboard(
                        `${baseUrl}/api/v1/sso/${connection.protocol === 'saml' ? 'saml' : 'oauth'}/${connection.id}/login`
                      )
                    }
                  >
                    Copy
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'scim' && (
            <div className="tab-content">
              <p className="info-text">
                SCIM 2.0 enables automatic user provisioning and deprovisioning from your Identity Provider.
              </p>

              <div className="scim-status">
                <span>SCIM Status:</span>
                {connection.scim_enabled ? (
                  <span className="badge badge-success">Enabled</span>
                ) : (
                  <span className="badge badge-secondary">Disabled</span>
                )}
              </div>

              <div className="endpoint-item">
                <label>SCIM Base URL</label>
                <div className="endpoint-value">
                  <code>{baseUrl}/api/v1/scim/{connection.id}</code>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => copyToClipboard(`${baseUrl}/api/v1/scim/${connection.id}`)}
                  >
                    Copy
                  </button>
                </div>
              </div>

              {!scimToken ? (
                <button
                  className="btn btn-primary"
                  onClick={() => onGenerateSCIMToken(connection.id)}
                >
                  Generate New SCIM Token
                </button>
              ) : (
                <div className="scim-token-display">
                  <div className="alert alert-warning">
                    Save this token now - it won't be shown again!
                  </div>
                  <div className="endpoint-item">
                    <label>Bearer Token</label>
                    <div className="endpoint-value">
                      <code className="token-code">{scimToken.token}</code>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => copyToClipboard(scimToken.token)}
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <div className="scim-endpoints">
                <h4>SCIM Endpoints</h4>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Endpoint</th>
                      <th>Methods</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><code>/Users</code></td>
                      <td>GET, POST</td>
                    </tr>
                    <tr>
                      <td><code>/Users/:id</code></td>
                      <td>GET, PUT, PATCH, DELETE</td>
                    </tr>
                    <tr>
                      <td><code>/Groups</code></td>
                      <td>GET</td>
                    </tr>
                    <tr>
                      <td><code>/ServiceProviderConfig</code></td>
                      <td>GET</td>
                    </tr>
                    <tr>
                      <td><code>/ResourceTypes</code></td>
                      <td>GET</td>
                    </tr>
                    <tr>
                      <td><code>/Schemas</code></td>
                      <td>GET</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
