import { useState, useEffect } from 'react';
import { tenantAPI, settingsAPI, domainsAPI } from '../services/tenantApi';

export default function TenantSettings() {
  const [tenant, setTenant] = useState(null);
  const [settings, setSettings] = useState(null);
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('general');
  const [showDomainModal, setShowDomainModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [tenantRes, settingsRes, domainsRes] = await Promise.all([
        tenantAPI.getCurrent(),
        settingsAPI.get(),
        domainsAPI.list()
      ]);
      setTenant(tenantRes.data.tenant);
      setSettings(settingsRes.data.settings);
      setDomains(domainsRes.data.domains);
    } catch (err) {
      setError('Failed to load tenant settings');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTenant = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      name: formData.get('name'),
      display_name: formData.get('display_name'),
      billing_email: formData.get('billing_email'),
      timezone: formData.get('timezone'),
      locale: formData.get('locale')
    };

    try {
      await tenantAPI.updateCurrent(data);
      setSuccess('Organization settings updated successfully');
      loadData();
    } catch (err) {
      setError('Failed to update settings');
    }
  };

  const handleUpdateBranding = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      logo_url: formData.get('logo_url'),
      primary_color: formData.get('primary_color'),
      secondary_color: formData.get('secondary_color')
    };

    try {
      await settingsAPI.update(data);
      setSuccess('Branding settings updated successfully');
      loadData();
    } catch (err) {
      setError('Failed to update branding');
    }
  };

  const handleUpdateSecurity = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      require_2fa: formData.get('require_2fa') === 'on',
      session_timeout_minutes: parseInt(formData.get('session_timeout')),
      password_min_length: parseInt(formData.get('password_min_length'))
    };

    try {
      await settingsAPI.updateSecurity(data);
      setSuccess('Security settings updated successfully');
      loadData();
    } catch (err) {
      setError('Failed to update security settings');
    }
  };

  const handleAddDomain = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      domain: formData.get('domain'),
      domain_type: 'custom',
      is_primary: formData.get('is_primary') === 'on'
    };

    try {
      await domainsAPI.add(data);
      setShowDomainModal(false);
      setSuccess('Domain added successfully');
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add domain');
    }
  };

  const handleVerifyDomain = async (domainId) => {
    try {
      await domainsAPI.verify(domainId);
      setSuccess('Domain verified successfully');
      loadData();
    } catch (err) {
      setError('Failed to verify domain');
    }
  };

  const handleRemoveDomain = async (domainId) => {
    if (!window.confirm('Are you sure you want to remove this domain?')) return;
    try {
      await domainsAPI.remove(domainId);
      setSuccess('Domain removed successfully');
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove domain');
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Organization Settings</h1>
          <p className="page-subtitle">Manage your organization configuration</p>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button className="alert-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
          <button className="alert-close" onClick={() => setSuccess(null)}>×</button>
        </div>
      )}

      {/* Status Card */}
      <div className="info-card">
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Organization</span>
            <span className="info-value">{tenant?.display_name || tenant?.name}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Slug</span>
            <span className="info-value">{tenant?.slug}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Status</span>
            <span className={`badge badge-${tenant?.status === 'active' ? 'success' : 'warning'}`}>
              {tenant?.status}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Tier</span>
            <span className="badge badge-primary">{tenant?.tier?.toUpperCase()}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'general' ? 'active' : ''}`}
          onClick={() => setActiveTab('general')}
        >
          General
        </button>
        <button
          className={`tab ${activeTab === 'branding' ? 'active' : ''}`}
          onClick={() => setActiveTab('branding')}
        >
          Branding
        </button>
        <button
          className={`tab ${activeTab === 'domains' ? 'active' : ''}`}
          onClick={() => setActiveTab('domains')}
        >
          Domains
        </button>
        <button
          className={`tab ${activeTab === 'security' ? 'active' : ''}`}
          onClick={() => setActiveTab('security')}
        >
          Security
        </button>
      </div>

      {/* General Settings Tab */}
      {activeTab === 'general' && (
        <div className="card">
          <div className="card-header">
            <h3>General Settings</h3>
          </div>
          <div className="card-body">
            <form onSubmit={handleUpdateTenant}>
              <div className="form-grid">
                <div className="form-group">
                  <label>Organization Name</label>
                  <input
                    type="text"
                    name="name"
                    defaultValue={tenant?.name}
                    className="form-control"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Display Name</label>
                  <input
                    type="text"
                    name="display_name"
                    defaultValue={tenant?.display_name}
                    className="form-control"
                  />
                </div>
                <div className="form-group">
                  <label>Billing Email</label>
                  <input
                    type="email"
                    name="billing_email"
                    defaultValue={tenant?.billing_email}
                    className="form-control"
                  />
                </div>
                <div className="form-group">
                  <label>Timezone</label>
                  <select name="timezone" defaultValue={tenant?.timezone} className="form-control">
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">Eastern Time</option>
                    <option value="America/Chicago">Central Time</option>
                    <option value="America/Denver">Mountain Time</option>
                    <option value="America/Los_Angeles">Pacific Time</option>
                    <option value="Europe/London">London</option>
                    <option value="Europe/Paris">Paris</option>
                    <option value="Asia/Tokyo">Tokyo</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Language</label>
                  <select name="locale" defaultValue={tenant?.locale} className="form-control">
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="de">German</option>
                    <option value="pt">Portuguese</option>
                  </select>
                </div>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn btn-primary">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Branding Tab */}
      {activeTab === 'branding' && (
        <div className="card">
          <div className="card-header">
            <h3>Branding Settings</h3>
          </div>
          <div className="card-body">
            <form onSubmit={handleUpdateBranding}>
              <div className="form-grid">
                <div className="form-group">
                  <label>Logo URL</label>
                  <input
                    type="url"
                    name="logo_url"
                    defaultValue={settings?.logo_url}
                    className="form-control"
                    placeholder="https://..."
                  />
                </div>
                <div className="form-group">
                  <label>Primary Color</label>
                  <div className="color-input">
                    <input
                      type="color"
                      name="primary_color"
                      defaultValue={settings?.primary_color || '#3B82F6'}
                    />
                    <input
                      type="text"
                      defaultValue={settings?.primary_color || '#3B82F6'}
                      className="form-control"
                      readOnly
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label>Secondary Color</label>
                  <div className="color-input">
                    <input
                      type="color"
                      name="secondary_color"
                      defaultValue={settings?.secondary_color || '#10B981'}
                    />
                    <input
                      type="text"
                      defaultValue={settings?.secondary_color || '#10B981'}
                      className="form-control"
                      readOnly
                    />
                  </div>
                </div>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn btn-primary">Save Branding</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Domains Tab */}
      {activeTab === 'domains' && (
        <div className="card">
          <div className="card-header">
            <h3>Custom Domains</h3>
            <button className="btn btn-primary btn-sm" onClick={() => setShowDomainModal(true)}>
              + Add Domain
            </button>
          </div>
          <div className="card-body">
            {domains.length === 0 ? (
              <div className="empty-state">
                <p>No custom domains configured</p>
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Domain</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>SSL</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {domains.map(domain => (
                    <tr key={domain.id}>
                      <td>
                        {domain.domain}
                        {domain.is_primary && <span className="badge badge-primary ml-2">Primary</span>}
                      </td>
                      <td>{domain.domain_type}</td>
                      <td>
                        <span className={`badge badge-${domain.is_verified ? 'success' : 'warning'}`}>
                          {domain.is_verified ? 'Verified' : 'Pending'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge-${domain.ssl_status === 'active' ? 'success' : 'secondary'}`}>
                          {domain.ssl_status}
                        </span>
                      </td>
                      <td>
                        <div className="action-buttons">
                          {!domain.is_verified && (
                            <button
                              className="btn btn-sm btn-outline"
                              onClick={() => handleVerifyDomain(domain.id)}
                            >
                              Verify
                            </button>
                          )}
                          {!domain.is_primary && (
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={() => handleRemoveDomain(domain.id)}
                            >
                              Remove
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="card">
          <div className="card-header">
            <h3>Security Settings</h3>
          </div>
          <div className="card-body">
            <form onSubmit={handleUpdateSecurity}>
              <div className="form-grid">
                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="require_2fa"
                      defaultChecked={settings?.require_2fa}
                    />
                    <span>Require Two-Factor Authentication for all users</span>
                  </label>
                </div>
                <div className="form-group">
                  <label>Session Timeout (minutes)</label>
                  <input
                    type="number"
                    name="session_timeout"
                    defaultValue={settings?.session_timeout_minutes || 480}
                    className="form-control"
                    min="5"
                    max="10080"
                  />
                </div>
                <div className="form-group">
                  <label>Minimum Password Length</label>
                  <input
                    type="number"
                    name="password_min_length"
                    defaultValue={settings?.password_min_length || 8}
                    className="form-control"
                    min="8"
                    max="128"
                  />
                </div>
              </div>
              <div className="form-actions">
                <button type="submit" className="btn btn-primary">Save Security Settings</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Domain Modal */}
      {showDomainModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Add Custom Domain</h3>
              <button className="modal-close" onClick={() => setShowDomainModal(false)}>×</button>
            </div>
            <form onSubmit={handleAddDomain}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Domain</label>
                  <input
                    type="text"
                    name="domain"
                    className="form-control"
                    placeholder="app.yourdomain.com"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="checkbox-label">
                    <input type="checkbox" name="is_primary" />
                    <span>Set as primary domain</span>
                  </label>
                </div>
                <div className="info-box">
                  <p>After adding your domain, you'll need to verify ownership by adding a DNS TXT record.</p>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowDomainModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">Add Domain</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
