import { useState, useEffect } from 'react';
import { settingsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

export default function Settings() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('preferences');
  const [options, setOptions] = useState(null);

  const [preferences, setPreferences] = useState({
    language: 'en',
    theme: 'light',
    date_format: 'MM/DD/YYYY',
    time_format: '12h',
    currency: 'USD',
    notifications_email: true,
    notifications_push: true,
    dashboard_default_view: 'overview'
  });

  const [systemSettings, setSystemSettings] = useState({
    company_name: 'LogiAccounting Pro',
    default_tax_rate: 0.21,
    payment_terms_days: 30,
    low_stock_threshold: 10,
    enable_ai_features: true,
    enable_email_notifications: true
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [prefsRes, optionsRes, systemRes] = await Promise.all([
        settingsAPI.getUserPreferences(),
        settingsAPI.getAvailableOptions(),
        user?.role === 'admin' ? settingsAPI.getSystemSettings() : Promise.resolve(null)
      ]);

      setPreferences(prefsRes.data.preferences);
      setOptions(optionsRes.data);
      if (systemRes) {
        setSystemSettings(systemRes.data.settings);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePreferences = async () => {
    setSaving(true);
    try {
      await settingsAPI.updateUserPreferences(preferences);

      // Apply theme change
      if (preferences.theme !== 'system') {
        setTheme(preferences.theme);
      }

      alert('Preferences saved successfully!');
    } catch (error) {
      alert('Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveSystemSettings = async () => {
    setSaving(true);
    try {
      await settingsAPI.updateSystemSettings(systemSettings);
      alert('System settings saved successfully!');
    } catch (error) {
      alert('Failed to save system settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading settings...</p>
      </div>
    );
  }

  return (
    <>
      {/* Tab Navigation */}
      <div className="section mb-6">
        <div className="flex gap-2">
          <button
            className={`btn ${activeTab === 'preferences' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('preferences')}
          >
            User Preferences
          </button>
          {user?.role === 'admin' && (
            <button
              className={`btn ${activeTab === 'system' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('system')}
            >
              System Settings
            </button>
          )}
        </div>
      </div>

      {/* User Preferences Tab */}
      {activeTab === 'preferences' && (
        <div className="section">
          <h3 className="section-title">User Preferences</h3>

          <div className="grid-2 mb-6">
            {/* Language */}
            <div className="form-group">
              <label className="form-label">Language</label>
              <select
                className="form-select"
                value={preferences.language}
                onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
              >
                {options?.languages?.map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </select>
            </div>

            {/* Theme */}
            <div className="form-group">
              <label className="form-label">Theme</label>
              <select
                className="form-select"
                value={preferences.theme}
                onChange={(e) => setPreferences({ ...preferences, theme: e.target.value })}
              >
                {options?.themes?.map(t => (
                  <option key={t.code} value={t.code}>{t.name}</option>
                ))}
              </select>
            </div>

            {/* Date Format */}
            <div className="form-group">
              <label className="form-label">Date Format</label>
              <select
                className="form-select"
                value={preferences.date_format}
                onChange={(e) => setPreferences({ ...preferences, date_format: e.target.value })}
              >
                {options?.date_formats?.map(df => (
                  <option key={df.code} value={df.code}>{df.code} ({df.example})</option>
                ))}
              </select>
            </div>

            {/* Time Format */}
            <div className="form-group">
              <label className="form-label">Time Format</label>
              <select
                className="form-select"
                value={preferences.time_format}
                onChange={(e) => setPreferences({ ...preferences, time_format: e.target.value })}
              >
                {options?.time_formats?.map(tf => (
                  <option key={tf.code} value={tf.code}>{tf.code} ({tf.example})</option>
                ))}
              </select>
            </div>

            {/* Currency */}
            <div className="form-group">
              <label className="form-label">Currency</label>
              <select
                className="form-select"
                value={preferences.currency}
                onChange={(e) => setPreferences({ ...preferences, currency: e.target.value })}
              >
                {options?.currencies?.map(c => (
                  <option key={c.code} value={c.code}>{c.symbol} {c.name}</option>
                ))}
              </select>
            </div>

            {/* Default Dashboard View */}
            <div className="form-group">
              <label className="form-label">Default Dashboard View</label>
              <select
                className="form-select"
                value={preferences.dashboard_default_view}
                onChange={(e) => setPreferences({ ...preferences, dashboard_default_view: e.target.value })}
              >
                <option value="overview">Overview</option>
                <option value="financial">Financial</option>
                <option value="projects">Projects</option>
              </select>
            </div>
          </div>

          {/* Notification Settings */}
          <h4 className="font-bold mb-4">Notifications</h4>
          <div className="mb-6">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={preferences.notifications_email}
                onChange={(e) => setPreferences({ ...preferences, notifications_email: e.target.checked })}
              />
              <span>Email Notifications</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={preferences.notifications_push}
                onChange={(e) => setPreferences({ ...preferences, notifications_push: e.target.checked })}
              />
              <span>Push Notifications</span>
            </label>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleSavePreferences}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      )}

      {/* System Settings Tab (Admin Only) */}
      {activeTab === 'system' && user?.role === 'admin' && (
        <div className="section">
          <h3 className="section-title">System Settings</h3>

          <div className="grid-2 mb-6">
            {/* Company Name */}
            <div className="form-group">
              <label className="form-label">Company Name</label>
              <input
                type="text"
                className="form-input"
                value={systemSettings.company_name}
                onChange={(e) => setSystemSettings({ ...systemSettings, company_name: e.target.value })}
              />
            </div>

            {/* Default Tax Rate */}
            <div className="form-group">
              <label className="form-label">Default Tax Rate (%)</label>
              <input
                type="number"
                step="0.01"
                className="form-input"
                value={systemSettings.default_tax_rate * 100}
                onChange={(e) => setSystemSettings({ ...systemSettings, default_tax_rate: parseFloat(e.target.value) / 100 })}
              />
            </div>

            {/* Payment Terms */}
            <div className="form-group">
              <label className="form-label">Default Payment Terms (days)</label>
              <input
                type="number"
                className="form-input"
                value={systemSettings.payment_terms_days}
                onChange={(e) => setSystemSettings({ ...systemSettings, payment_terms_days: parseInt(e.target.value) })}
              />
            </div>

            {/* Low Stock Threshold */}
            <div className="form-group">
              <label className="form-label">Low Stock Alert Threshold</label>
              <input
                type="number"
                className="form-input"
                value={systemSettings.low_stock_threshold}
                onChange={(e) => setSystemSettings({ ...systemSettings, low_stock_threshold: parseInt(e.target.value) })}
              />
            </div>
          </div>

          {/* Feature Toggles */}
          <h4 className="font-bold mb-4">Feature Toggles</h4>
          <div className="mb-6">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={systemSettings.enable_ai_features}
                onChange={(e) => setSystemSettings({ ...systemSettings, enable_ai_features: e.target.checked })}
              />
              <span>Enable AI Features (OCR, Predictions, Anomaly Detection)</span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={systemSettings.enable_email_notifications}
                onChange={(e) => setSystemSettings({ ...systemSettings, enable_email_notifications: e.target.checked })}
              />
              <span>Enable Email Notifications</span>
            </label>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleSaveSystemSettings}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save System Settings'}
          </button>
        </div>
      )}
    </>
  );
}
