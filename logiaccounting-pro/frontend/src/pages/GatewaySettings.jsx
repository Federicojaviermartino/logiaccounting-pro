import { useState, useEffect } from 'react';
import { gatewayAPI } from '../services/api';

export default function GatewaySettings() {
  const [gateways, setGateways] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(null);
  const [editingGateway, setEditingGateway] = useState(null);
  const [credentials, setCredentials] = useState({});

  useEffect(() => {
    loadGateways();
  }, []);

  const loadGateways = async () => {
    try {
      const res = await gatewayAPI.list();
      setGateways(res.data.gateways);
    } catch (err) {
      console.error('Failed to load gateways:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (provider) => {
    setTesting(provider);
    try {
      const res = await gatewayAPI.test(provider);
      alert(res.data.message);
      loadGateways();
    } catch (err) {
      alert('Test failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setTesting(null);
    }
  };

  const handleToggle = async (provider, enabled) => {
    try {
      await gatewayAPI.update(provider, { enabled: !enabled });
      loadGateways();
    } catch (err) {
      alert('Failed to update');
    }
  };

  const handleSetDefault = async (provider) => {
    try {
      await gatewayAPI.update(provider, { is_default: true });
      loadGateways();
    } catch (err) {
      alert('Failed to set default');
    }
  };

  const handleModeChange = async (provider, mode) => {
    try {
      await gatewayAPI.update(provider, { mode });
      loadGateways();
    } catch (err) {
      alert('Failed to change mode');
    }
  };

  const handleSaveCredentials = async () => {
    if (!editingGateway) return;
    try {
      await gatewayAPI.update(editingGateway, { credentials });
      setEditingGateway(null);
      setCredentials({});
      loadGateways();
    } catch (err) {
      alert('Failed to save credentials');
    }
  };

  const getStatusBadge = (gateway) => {
    if (!gateway.enabled) return <span className="badge badge-gray">Disabled</span>;
    if (gateway.test_status === 'success') return <span className="badge badge-success">Connected</span>;
    if (gateway.test_status === 'failed') return <span className="badge badge-danger">Failed</span>;
    return <span className="badge badge-warning">Not Tested</span>;
  };

  return (
    <>
      <div className="info-banner mb-6">
        💳 Configure payment gateways to accept online payments from your clients.
      </div>

      <div className="section">
        <h3 className="section-title">Payment Gateways</h3>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : (
          <div className="gateway-list">
            {gateways.map(gateway => (
              <div key={gateway.provider} className={`gateway-card ${!gateway.enabled ? 'disabled' : ''}`}>
                <div className="gateway-header">
                  <div className="gateway-icon">{gateway.icon}</div>
                  <div className="gateway-info">
                    <div className="gateway-name">
                      {gateway.name}
                      {gateway.is_default && <span className="badge badge-primary ml-2">Default</span>}
                    </div>
                    <div className="gateway-meta">
                      Fee: {gateway.fee_percentage}% + ${gateway.fee_fixed}
                    </div>
                  </div>
                  <div className="gateway-status">
                    {getStatusBadge(gateway)}
                  </div>
                </div>

                <div className="gateway-details">
                  <div className="detail-row">
                    <span className="detail-label">Mode:</span>
                    <select
                      className="form-select form-select-sm"
                      value={gateway.mode}
                      onChange={(e) => handleModeChange(gateway.provider, e.target.value)}
                      disabled={!gateway.enabled}
                    >
                      <option value="test">Test Mode</option>
                      <option value="live">Live Mode</option>
                    </select>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Currencies:</span>
                    <span>{gateway.supported_currencies.slice(0, 5).join(', ')}{gateway.supported_currencies.length > 5 ? '...' : ''}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Methods:</span>
                    <span>{gateway.supported_methods.join(', ')}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Public Key:</span>
                    <code>{gateway.credentials?.public_key || 'Not set'}</code>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Webhook URL:</span>
                    <code className="text-xs">{window.location.origin}{gateway.webhook_url}</code>
                  </div>
                </div>

                <div className="gateway-actions">
                  <button
                    className={`btn btn-sm ${gateway.enabled ? 'btn-warning' : 'btn-success'}`}
                    onClick={() => handleToggle(gateway.provider, gateway.enabled)}
                  >
                    {gateway.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => {
                      setEditingGateway(gateway.provider);
                      setCredentials({});
                    }}
                  >
                    🔑 Credentials
                  </button>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => handleTest(gateway.provider)}
                    disabled={testing === gateway.provider || !gateway.enabled}
                  >
                    {testing === gateway.provider ? 'Testing...' : '🔌 Test'}
                  </button>
                  {!gateway.is_default && gateway.enabled && (
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => handleSetDefault(gateway.provider)}
                    >
                      Set Default
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Credentials Modal */}
      {editingGateway && (
        <div className="modal-overlay" onClick={() => setEditingGateway(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>API Credentials - {editingGateway}</h3>
              <button className="modal-close" onClick={() => setEditingGateway(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="alert alert-info mb-4">
                🔒 Credentials are encrypted and stored securely. Leave fields empty to keep existing values.
              </div>
              <div className="form-group">
                <label className="form-label">Public Key / Client ID</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="pk_test_..."
                  value={credentials.public_key || ''}
                  onChange={(e) => setCredentials({ ...credentials, public_key: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Secret Key / Client Secret</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="sk_test_..."
                  value={credentials.secret_key || ''}
                  onChange={(e) => setCredentials({ ...credentials, secret_key: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Webhook Secret</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="whsec_..."
                  value={credentials.webhook_secret || ''}
                  onChange={(e) => setCredentials({ ...credentials, webhook_secret: e.target.value })}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setEditingGateway(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSaveCredentials}>
                Save Credentials
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
