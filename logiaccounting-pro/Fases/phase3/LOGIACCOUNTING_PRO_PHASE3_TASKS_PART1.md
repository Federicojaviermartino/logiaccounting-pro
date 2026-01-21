# LogiAccounting Pro - Phase 3 Tasks (Part 1/3)

## UX FEATURES: Dark Mode + Settings + Advanced Filters

---

## TASK 1: DARK MODE SYSTEM

### 1.1 Create ThemeContext

**File:** `frontend/src/contexts/ThemeContext.jsx`

```jsx
import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e) => {
      if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    };
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
```

### 1.2 Create ThemeToggle Component

**File:** `frontend/src/components/ThemeToggle.jsx`

```jsx
import { useTheme } from '../contexts/ThemeContext';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button 
      className="theme-toggle"
      onClick={toggleTheme}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? '🌙' : '☀️'}
    </button>
  );
}
```

### 1.3 Update CSS with Theme Variables

**Add to beginning of:** `frontend/src/index.css`

```css
/* ============================================
   THEME VARIABLES
   ============================================ */

:root {
  /* Light Theme (Default) */
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  --bg-hover: #e2e8f0;
  
  --text-primary: #1e293b;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  
  --border-color: #e2e8f0;
  --border-light: #f1f5f9;
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);
  
  --sidebar-bg: #1e293b;
  --sidebar-text: #e2e8f0;
  --sidebar-hover: #334155;
  --sidebar-active: #667eea;
  
  --input-bg: #ffffff;
  --input-border: #d1d5db;
  --input-focus: #667eea;
  
  --card-bg: #ffffff;
  --modal-bg: #ffffff;
  --modal-overlay: rgba(0, 0, 0, 0.5);
  
  --table-header-bg: #f8fafc;
  --table-row-hover: #f1f5f9;
  --table-border: #e2e8f0;
}

[data-theme="dark"] {
  /* Dark Theme */
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-tertiary: #334155;
  --bg-hover: #475569;
  
  --text-primary: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  
  --border-color: #334155;
  --border-light: #1e293b;
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.4);
  
  --sidebar-bg: #0f172a;
  --sidebar-text: #e2e8f0;
  --sidebar-hover: #1e293b;
  --sidebar-active: #667eea;
  
  --input-bg: #1e293b;
  --input-border: #475569;
  --input-focus: #667eea;
  
  --card-bg: #1e293b;
  --modal-bg: #1e293b;
  --modal-overlay: rgba(0, 0, 0, 0.7);
  
  --table-header-bg: #334155;
  --table-row-hover: #334155;
  --table-border: #475569;
  
  /* Override specific colors */
  --primary: #818cf8;
  --primary-dark: #6366f1;
  --gray-50: #1e293b;
  --gray-100: #334155;
  --gray-200: #475569;
  --gray-800: #f1f5f9;
}

/* Theme transition */
* {
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}
```

### 1.4 Update Base Styles to Use Variables

**Replace in:** `frontend/src/index.css` (update existing styles)

```css
/* Update body */
body {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-secondary);
  color: var(--text-primary);
  line-height: 1.5;
}

/* Update sidebar */
.sidebar {
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  /* ... rest stays the same */
}

/* Update main content */
.main-content {
  margin-left: var(--sidebar-width);
  padding: 24px 32px;
  min-height: 100vh;
  background: var(--bg-secondary);
}

/* Update sections/cards */
.section {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

/* Update stat cards */
.stat-card {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

/* Update tables */
.data-table th {
  background: var(--table-header-bg);
  color: var(--text-secondary);
  border-bottom: 2px solid var(--table-border);
}

.data-table td {
  border-bottom: 1px solid var(--border-light);
  color: var(--text-primary);
}

.data-table tbody tr:hover {
  background: var(--table-row-hover);
}

/* Update forms */
.form-input,
.form-select,
.form-textarea {
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  color: var(--text-primary);
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: var(--input-focus);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

/* Update modals */
.modal-overlay {
  background: var(--modal-overlay);
}

.modal-content {
  background: var(--modal-bg);
  border: 1px solid var(--border-color);
}

/* Update page header */
.page-header {
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
}

.page-title {
  color: var(--text-primary);
}

/* Theme toggle button */
.theme-toggle {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  font-size: 1.25rem;
  transition: background 0.2s;
}

.theme-toggle:hover {
  background: var(--bg-hover);
}

/* Info banner dark mode */
.info-banner {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}
```

### 1.5 Update main.jsx

**File:** `frontend/src/main.jsx`

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
);
```

### 1.6 Add ThemeToggle to Layout

**Update:** `frontend/src/components/Layout.jsx`

**Add import:**
```jsx
import ThemeToggle from './ThemeToggle';
```

**Update header-right section:**
```jsx
<div className="header-right">
  <ThemeToggle />
  <NotificationBell />
  <div className="user-info">
    <div className="user-name">{user?.first_name} {user?.last_name}</div>
    <div className="user-role">{user?.role}</div>
  </div>
</div>
```

---

## TASK 2: SETTINGS PAGE

### 2.1 Create Settings Backend Route

**File:** `backend/app/routes/settings.py`

```python
"""
User and system settings routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.models.store import db
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class UserPreferences(BaseModel):
    """User preference settings"""
    language: str = "en"
    theme: str = "light"
    date_format: str = "MM/DD/YYYY"
    time_format: str = "12h"
    currency: str = "USD"
    notifications_email: bool = True
    notifications_push: bool = True
    dashboard_default_view: str = "overview"


class SystemSettings(BaseModel):
    """System-wide settings (admin only)"""
    company_name: str = "LogiAccounting Pro"
    default_tax_rate: float = 0.21
    payment_terms_days: int = 30
    low_stock_threshold: int = 10
    enable_ai_features: bool = True
    enable_email_notifications: bool = True


# In-memory settings storage
user_preferences = {}
system_settings = SystemSettings()


@router.get("/user")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """Get current user's preferences"""
    user_id = current_user["id"]
    prefs = user_preferences.get(user_id, UserPreferences())
    return {"preferences": prefs.model_dump()}


@router.put("/user")
async def update_user_preferences(
    prefs: UserPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's preferences"""
    user_id = current_user["id"]
    user_preferences[user_id] = prefs
    return {"preferences": prefs.model_dump(), "message": "Preferences updated"}


@router.get("/system")
async def get_system_settings(current_user: dict = Depends(get_current_user)):
    """Get system settings (visible to all, editable by admin)"""
    return {"settings": system_settings.model_dump()}


@router.put("/system")
async def update_system_settings(
    settings: SystemSettings,
    current_user: dict = Depends(require_roles("admin"))
):
    """Update system settings (admin only)"""
    global system_settings
    system_settings = settings
    return {"settings": settings.model_dump(), "message": "System settings updated"}


@router.get("/available-options")
async def get_available_options():
    """Get available options for settings dropdowns"""
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Español"}
        ],
        "themes": [
            {"code": "light", "name": "Light"},
            {"code": "dark", "name": "Dark"},
            {"code": "system", "name": "System"}
        ],
        "date_formats": [
            {"code": "MM/DD/YYYY", "example": "01/15/2024"},
            {"code": "DD/MM/YYYY", "example": "15/01/2024"},
            {"code": "YYYY-MM-DD", "example": "2024-01-15"}
        ],
        "time_formats": [
            {"code": "12h", "example": "2:30 PM"},
            {"code": "24h", "example": "14:30"}
        ],
        "currencies": [
            {"code": "USD", "symbol": "$", "name": "US Dollar"},
            {"code": "EUR", "symbol": "€", "name": "Euro"},
            {"code": "GBP", "symbol": "£", "name": "British Pound"},
            {"code": "ARS", "symbol": "$", "name": "Argentine Peso"}
        ]
    }
```

### 2.2 Register Settings Route

**Update:** `backend/app/main.py`

**Add import:**
```python
from app.routes import settings
```

**Add router:**
```python
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
```

### 2.3 Add Settings API to Frontend

**Add to:** `frontend/src/services/api.js`

```javascript
// Settings API
export const settingsAPI = {
  getUserPreferences: () => api.get('/api/v1/settings/user'),
  updateUserPreferences: (prefs) => api.put('/api/v1/settings/user', prefs),
  getSystemSettings: () => api.get('/api/v1/settings/system'),
  updateSystemSettings: (settings) => api.put('/api/v1/settings/system', settings),
  getAvailableOptions: () => api.get('/api/v1/settings/available-options')
};
```

### 2.4 Create Settings Page

**File:** `frontend/src/pages/Settings.jsx`

```jsx
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
            👤 User Preferences
          </button>
          {user?.role === 'admin' && (
            <button
              className={`btn ${activeTab === 'system' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('system')}
            >
              ⚙️ System Settings
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
            {saving ? 'Saving...' : '💾 Save Preferences'}
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
            {saving ? 'Saving...' : '💾 Save System Settings'}
          </button>
        </div>
      )}
    </>
  );
}
```

### 2.5 Add Checkbox Styles

**Add to:** `frontend/src/index.css`

```css
/* Checkbox styling */
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px 0;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--primary);
}

.checkbox-label span {
  color: var(--text-primary);
}
```

### 2.6 Add Settings Route to App.jsx

**Update:** `frontend/src/App.jsx`

**Add import:**
```jsx
import Settings from './pages/Settings';
```

**Add route:**
```jsx
<Route path="/settings" element={
  <PrivateRoute>
    <Layout><Settings /></Layout>
  </PrivateRoute>
} />
```

### 2.7 Add Settings to Navigation

**Update navItems in:** `frontend/src/components/Layout.jsx`

```javascript
// Add at the end before the closing bracket
{ path: '/settings', icon: '⚙️', label: 'Settings', roles: ['admin', 'client', 'supplier'] }
```

**Add to pageTitles:**
```javascript
'/settings': 'Settings'
```

---

## TASK 3: ADVANCED FILTERS COMPONENT

### 3.1 Create AdvancedFilters Component

**File:** `frontend/src/components/AdvancedFilters.jsx`

```jsx
import { useState, useEffect } from 'react';

export default function AdvancedFilters({
  filters,
  onFiltersChange,
  filterConfig,
  onSavePreset,
  savedPresets = [],
  onLoadPreset,
  onDeletePreset
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [showPresetModal, setShowPresetModal] = useState(false);

  const handleFilterChange = (key, value) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const clearFilters = () => {
    const clearedFilters = {};
    Object.keys(filters).forEach(key => {
      clearedFilters[key] = '';
    });
    onFiltersChange(clearedFilters);
  };

  const handleSavePreset = () => {
    if (presetName.trim()) {
      onSavePreset({ name: presetName, filters: { ...filters } });
      setPresetName('');
      setShowPresetModal(false);
    }
  };

  const activeFilterCount = Object.values(filters).filter(v => v !== '' && v !== null && v !== undefined).length;

  return (
    <div className="advanced-filters">
      {/* Filter Header */}
      <div className="filter-header">
        <button 
          className="btn btn-secondary"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          🔍 Filters {activeFilterCount > 0 && <span className="filter-badge">{activeFilterCount}</span>}
        </button>
        
        {activeFilterCount > 0 && (
          <button className="btn btn-sm btn-secondary" onClick={clearFilters}>
            ✕ Clear All
          </button>
        )}

        {savedPresets.length > 0 && (
          <div className="preset-dropdown">
            <select 
              className="form-select form-select-sm"
              onChange={(e) => e.target.value && onLoadPreset(e.target.value)}
              value=""
            >
              <option value="">Load Preset...</option>
              {savedPresets.map(preset => (
                <option key={preset.id} value={preset.id}>{preset.name}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Expanded Filters */}
      {isExpanded && (
        <div className="filter-panel">
          <div className="filter-grid">
            {filterConfig.map(config => (
              <div key={config.key} className="filter-item">
                <label className="filter-label">{config.label}</label>
                
                {config.type === 'select' && (
                  <select
                    className="form-select form-select-sm"
                    value={filters[config.key] || ''}
                    onChange={(e) => handleFilterChange(config.key, e.target.value)}
                  >
                    <option value="">All</option>
                    {config.options.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                )}

                {config.type === 'text' && (
                  <input
                    type="text"
                    className="form-input form-input-sm"
                    placeholder={config.placeholder || ''}
                    value={filters[config.key] || ''}
                    onChange={(e) => handleFilterChange(config.key, e.target.value)}
                  />
                )}

                {config.type === 'date' && (
                  <input
                    type="date"
                    className="form-input form-input-sm"
                    value={filters[config.key] || ''}
                    onChange={(e) => handleFilterChange(config.key, e.target.value)}
                  />
                )}

                {config.type === 'dateRange' && (
                  <div className="date-range">
                    <input
                      type="date"
                      className="form-input form-input-sm"
                      value={filters[`${config.key}_from`] || ''}
                      onChange={(e) => handleFilterChange(`${config.key}_from`, e.target.value)}
                    />
                    <span>to</span>
                    <input
                      type="date"
                      className="form-input form-input-sm"
                      value={filters[`${config.key}_to`] || ''}
                      onChange={(e) => handleFilterChange(`${config.key}_to`, e.target.value)}
                    />
                  </div>
                )}

                {config.type === 'amountRange' && (
                  <div className="amount-range">
                    <input
                      type="number"
                      className="form-input form-input-sm"
                      placeholder="Min"
                      value={filters[`${config.key}_min`] || ''}
                      onChange={(e) => handleFilterChange(`${config.key}_min`, e.target.value)}
                    />
                    <span>-</span>
                    <input
                      type="number"
                      className="form-input form-input-sm"
                      placeholder="Max"
                      value={filters[`${config.key}_max`] || ''}
                      onChange={(e) => handleFilterChange(`${config.key}_max`, e.target.value)}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Filter Actions */}
          <div className="filter-actions">
            <button 
              className="btn btn-sm btn-secondary"
              onClick={() => setShowPresetModal(true)}
            >
              💾 Save as Preset
            </button>
          </div>
        </div>
      )}

      {/* Quick Filter Chips */}
      {activeFilterCount > 0 && (
        <div className="filter-chips">
          {Object.entries(filters).map(([key, value]) => {
            if (!value) return null;
            const config = filterConfig.find(c => c.key === key);
            return (
              <span key={key} className="filter-chip">
                {config?.label}: {value}
                <button onClick={() => handleFilterChange(key, '')}>×</button>
              </span>
            );
          })}
        </div>
      )}

      {/* Save Preset Modal */}
      {showPresetModal && (
        <div className="modal-overlay" onClick={() => setShowPresetModal(false)}>
          <div className="modal-content modal-sm" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Save Filter Preset</h3>
              <button className="modal-close" onClick={() => setShowPresetModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Preset Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  placeholder="e.g., Monthly Expenses"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowPresetModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSavePreset}>Save Preset</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

### 3.2 Add Advanced Filter Styles

**Add to:** `frontend/src/index.css`

```css
/* Advanced Filters */
.advanced-filters {
  margin-bottom: 20px;
}

.filter-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-badge {
  background: var(--primary);
  color: white;
  border-radius: 10px;
  padding: 2px 8px;
  font-size: 0.75rem;
  margin-left: 6px;
}

.filter-panel {
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
  border: 1px solid var(--border-color);
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-input-sm,
.form-select-sm {
  padding: 6px 10px;
  font-size: 0.9rem;
}

.date-range,
.amount-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-range span,
.amount-range span {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.date-range input,
.amount-range input {
  flex: 1;
  min-width: 0;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--primary);
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.85rem;
}

.filter-chip button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 0;
  font-size: 1rem;
  line-height: 1;
  opacity: 0.8;
}

.filter-chip button:hover {
  opacity: 1;
}

.preset-dropdown {
  min-width: 150px;
}

.modal-sm {
  max-width: 400px;
}
```

---

## TASK 4: TEST AND BUILD

### 4.1 Test Dark Mode

```bash
cd frontend
npm run dev
# Toggle theme and verify all components update
# Check localStorage persistence
# Test system preference detection
```

### 4.2 Test Settings Page

```bash
# Navigate to /settings
# Test user preferences save
# Test admin system settings (login as admin)
```

### 4.3 Build and Commit

```bash
cd frontend
npm run build

git add .
git commit -m "feat: Phase 3.1 - Dark mode, Settings page, Advanced filters"
git push origin main
```

---

## COMPLETION CHECKLIST - PART 1

### Dark Mode
- [ ] ThemeContext created
- [ ] ThemeToggle component created
- [ ] CSS variables for light/dark themes
- [ ] Theme persists in localStorage
- [ ] System preference detection works
- [ ] All components use theme variables

### Settings Page
- [ ] Backend settings routes created
- [ ] User preferences save/load
- [ ] System settings (admin only)
- [ ] Available options endpoint
- [ ] Settings page UI complete
- [ ] Navigation updated

### Advanced Filters
- [ ] AdvancedFilters component created
- [ ] Multiple filter types (select, text, date, range)
- [ ] Filter chips display
- [ ] Clear all filters
- [ ] Save/load presets (UI ready)

---

**Continue to Part 2 for Enterprise Features (Activity Log, Bulk Operations, Email)**
