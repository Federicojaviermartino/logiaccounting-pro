# Phase 32: Advanced Security - Part 11: Frontend Components & Services

## Overview
This part covers reusable frontend components and the security API service.

---

## File 1: MFA Verification Component
**Path:** `frontend/src/features/security/components/MFAVerification.jsx`

```jsx
/**
 * MFA Verification Component
 * Reusable MFA code input for login and sensitive operations
 */

import React, { useState, useRef, useEffect } from 'react';
import { Shield, Smartphone, Mail, Key, AlertCircle } from 'lucide-react';

const MFAVerification = ({ 
  method = 'totp',
  onVerify,
  onCancel,
  onResend,
  error,
  loading = false,
  title = 'Two-Factor Authentication',
  subtitle,
}) => {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [resendCountdown, setResendCountdown] = useState(0);
  const inputRefs = useRef([]);

  useEffect(() => {
    // Focus first input on mount
    inputRefs.current[0]?.focus();
  }, []);

  useEffect(() => {
    // Countdown timer for resend
    if (resendCountdown > 0) {
      const timer = setTimeout(() => setResendCountdown(resendCountdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCountdown]);

  const handleChange = (index, value) => {
    // Only allow digits
    if (value && !/^\d$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    // Auto-advance to next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when complete
    if (newCode.every(c => c) && newCode.length === 6) {
      handleSubmit(newCode.join(''));
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) {
      const newCode = pasted.split('');
      setCode(newCode);
      handleSubmit(pasted);
    }
  };

  const handleSubmit = (codeString) => {
    if (codeString.length === 6) {
      onVerify(codeString);
    }
  };

  const handleResend = () => {
    if (resendCountdown > 0) return;
    onResend?.();
    setResendCountdown(60);
  };

  const getMethodIcon = () => {
    switch (method) {
      case 'totp': return <Smartphone className="w-6 h-6" />;
      case 'sms': return <Key className="w-6 h-6" />;
      case 'email': return <Mail className="w-6 h-6" />;
      default: return <Shield className="w-6 h-6" />;
    }
  };

  const getMethodDescription = () => {
    switch (method) {
      case 'totp': return 'Enter the code from your authenticator app';
      case 'sms': return 'Enter the code sent to your phone';
      case 'email': return 'Enter the code sent to your email';
      default: return 'Enter your verification code';
    }
  };

  return (
    <div className="max-w-sm mx-auto text-center">
      <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 text-blue-600">
        {getMethodIcon()}
      </div>

      <h2 className="text-xl font-semibold mb-2">{title}</h2>
      <p className="text-gray-600 mb-6">
        {subtitle || getMethodDescription()}
      </p>

      {/* Code Input */}
      <div className="flex justify-center gap-2 mb-4">
        {code.map((digit, index) => (
          <input
            key={index}
            ref={el => inputRefs.current[index] = el}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={(e) => handleChange(index, e.target.value)}
            onKeyDown={(e) => handleKeyDown(index, e)}
            onPaste={handlePaste}
            disabled={loading}
            className={`w-12 h-14 text-center text-2xl font-semibold border-2 rounded-lg
              focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none
              ${error ? 'border-red-300 bg-red-50' : 'border-gray-300'}
              ${loading ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          />
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center justify-center gap-2 text-red-600 text-sm mb-4">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-gray-500 text-sm mb-4">
          Verifying...
        </div>
      )}

      {/* Resend Option (for SMS/Email) */}
      {(method === 'sms' || method === 'email') && onResend && (
        <div className="mb-6">
          <button
            onClick={handleResend}
            disabled={resendCountdown > 0 || loading}
            className={`text-sm ${
              resendCountdown > 0 
                ? 'text-gray-400 cursor-not-allowed' 
                : 'text-blue-600 hover:text-blue-700'
            }`}
          >
            {resendCountdown > 0 
              ? `Resend code in ${resendCountdown}s` 
              : "Didn't receive a code? Resend"}
          </button>
        </div>
      )}

      {/* Backup Code Option */}
      <div className="text-sm text-gray-500 mb-6">
        <button className="text-blue-600 hover:text-blue-700">
          Use a backup code instead
        </button>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        {onCancel && (
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
        )}
        <button
          onClick={() => handleSubmit(code.join(''))}
          disabled={code.some(c => !c) || loading}
          className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          Verify
        </button>
      </div>
    </div>
  );
};

export default MFAVerification;
```

---

## File 2: Session Manager Component
**Path:** `frontend/src/features/security/components/SessionManager.jsx`

```jsx
/**
 * Session Manager Component
 * Display and manage active sessions
 */

import React from 'react';
import { 
  Monitor, Smartphone, Tablet, Globe,
  Clock, MapPin, X, AlertTriangle
} from 'lucide-react';

const SessionManager = ({ 
  sessions = [],
  onRevoke,
  onRevokeAll,
  compact = false,
}) => {
  const getDeviceIcon = (deviceType) => {
    switch (deviceType?.toLowerCase()) {
      case 'mobile': return Smartphone;
      case 'tablet': return Tablet;
      case 'desktop': return Monitor;
      default: return Globe;
    }
  };

  const formatLastActivity = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (compact) {
    return (
      <div className="space-y-2">
        {sessions.slice(0, 3).map(session => (
          <CompactSessionItem 
            key={session.id} 
            session={session} 
            getDeviceIcon={getDeviceIcon}
          />
        ))}
        {sessions.length > 3 && (
          <div className="text-sm text-gray-500 text-center">
            +{sessions.length - 3} more sessions
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-gray-900">Active Sessions</h3>
        {sessions.length > 1 && (
          <button
            onClick={onRevokeAll}
            className="text-sm text-red-600 hover:text-red-700"
          >
            Sign out all other sessions
          </button>
        )}
      </div>

      <div className="space-y-3">
        {sessions.map(session => {
          const DeviceIcon = getDeviceIcon(session.device?.type);
          
          return (
            <div
              key={session.id}
              className={`p-4 border rounded-lg ${
                session.is_current 
                  ? 'border-blue-200 bg-blue-50/30' 
                  : 'border-gray-200 bg-white'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex gap-4">
                  <div className={`p-2 rounded-lg ${
                    session.is_current ? 'bg-blue-100' : 'bg-gray-100'
                  }`}>
                    <DeviceIcon className={`w-5 h-5 ${
                      session.is_current ? 'text-blue-600' : 'text-gray-600'
                    }`} />
                  </div>
                  
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">
                        {session.device?.browser || 'Unknown Browser'}
                      </span>
                      <span className="text-gray-400">on</span>
                      <span className="text-gray-700">
                        {session.device?.os || 'Unknown OS'}
                      </span>
                      {session.is_current && (
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                          Current
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {session.location?.city || 'Unknown'}, {session.location?.country || 'Unknown'}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatLastActivity(session.last_activity)}
                      </span>
                    </div>
                    
                    <div className="text-xs text-gray-400 mt-1">
                      IP: {session.location?.ip || 'Unknown'}
                    </div>
                  </div>
                </div>

                {!session.is_current && (
                  <button
                    onClick={() => onRevoke(session.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                    title="Revoke session"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {sessions.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No active sessions
        </div>
      )}
    </div>
  );
};

const CompactSessionItem = ({ session, getDeviceIcon }) => {
  const DeviceIcon = getDeviceIcon(session.device?.type);
  
  return (
    <div className="flex items-center gap-3 p-2 bg-gray-50 rounded">
      <DeviceIcon className="w-4 h-4 text-gray-500" />
      <div className="flex-1 text-sm">
        <span className="text-gray-700">{session.device?.browser}</span>
        <span className="text-gray-400 mx-1">•</span>
        <span className="text-gray-500">{session.location?.country}</span>
      </div>
      {session.is_current && (
        <span className="text-xs text-blue-600">Current</span>
      )}
    </div>
  );
};

export default SessionManager;
```

---

## File 3: Permissions Table Component
**Path:** `frontend/src/features/security/components/PermissionsTable.jsx`

```jsx
/**
 * Permissions Table Component
 * Display and manage role permissions
 */

import React, { useState } from 'react';
import { 
  Check, X, ChevronDown, ChevronRight,
  Shield, Eye, Edit, Trash, Plus, Download
} from 'lucide-react';

const PermissionsTable = ({ 
  roles = [],
  permissions = [],
  onPermissionChange,
  readOnly = false,
}) => {
  const [expandedResources, setExpandedResources] = useState(new Set());

  // Group permissions by resource
  const groupedPermissions = permissions.reduce((acc, perm) => {
    const [resource] = perm.split(':');
    if (!acc[resource]) acc[resource] = [];
    acc[resource].push(perm);
    return acc;
  }, {});

  const toggleResource = (resource) => {
    const newExpanded = new Set(expandedResources);
    if (newExpanded.has(resource)) {
      newExpanded.delete(resource);
    } else {
      newExpanded.add(resource);
    }
    setExpandedResources(newExpanded);
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'read': return Eye;
      case 'create': return Plus;
      case 'update': return Edit;
      case 'delete': return Trash;
      case 'export': return Download;
      default: return Shield;
    }
  };

  const hasPermission = (role, permission) => {
    if (role.permissions?.includes('*')) return true;
    if (role.permissions?.includes(permission)) return true;
    
    const [resource] = permission.split(':');
    if (role.permissions?.includes(`${resource}:*`)) return true;
    
    return false;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-50">
            <th className="px-4 py-3 text-left text-sm font-medium text-gray-600 border-b">
              Permission
            </th>
            {roles.map(role => (
              <th 
                key={role.id} 
                className="px-4 py-3 text-center text-sm font-medium text-gray-600 border-b min-w-[100px]"
              >
                <div className="flex flex-col items-center gap-1">
                  <span>{role.display_name}</span>
                  {role.is_system && (
                    <span className="text-xs text-gray-400">System</span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(groupedPermissions).map(([resource, resourcePerms]) => (
            <React.Fragment key={resource}>
              {/* Resource Header Row */}
              <tr 
                className="bg-gray-50/50 cursor-pointer hover:bg-gray-100"
                onClick={() => toggleResource(resource)}
              >
                <td 
                  colSpan={roles.length + 1}
                  className="px-4 py-2 border-b"
                >
                  <div className="flex items-center gap-2 font-medium text-gray-700">
                    {expandedResources.has(resource) ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                    <Shield className="w-4 h-4 text-gray-400" />
                    {resource.charAt(0).toUpperCase() + resource.slice(1)}
                    <span className="text-xs text-gray-400 font-normal">
                      ({resourcePerms.length} permissions)
                    </span>
                  </div>
                </td>
              </tr>
              
              {/* Permission Rows */}
              {expandedResources.has(resource) && resourcePerms.map(perm => {
                const parts = perm.split(':');
                const action = parts[1];
                const scope = parts[2];
                const ActionIcon = getActionIcon(action);
                
                return (
                  <tr key={perm} className="hover:bg-gray-50">
                    <td className="px-4 py-2 border-b pl-10">
                      <div className="flex items-center gap-2 text-sm">
                        <ActionIcon className="w-4 h-4 text-gray-400" />
                        <span className="capitalize">{action}</span>
                        {scope && (
                          <span className="text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-500">
                            {scope}
                          </span>
                        )}
                      </div>
                    </td>
                    {roles.map(role => {
                      const hasPerm = hasPermission(role, perm);
                      const isWildcard = role.permissions?.includes('*') || 
                                        role.permissions?.includes(`${resource}:*`);
                      
                      return (
                        <td 
                          key={`${role.id}-${perm}`}
                          className="px-4 py-2 border-b text-center"
                        >
                          {readOnly || role.is_system ? (
                            <span className={`inline-flex items-center justify-center w-6 h-6 rounded ${
                              hasPerm 
                                ? isWildcard 
                                  ? 'bg-blue-100 text-blue-600' 
                                  : 'bg-green-100 text-green-600'
                                : 'bg-gray-100 text-gray-400'
                            }`}>
                              {hasPerm ? (
                                <Check className="w-4 h-4" />
                              ) : (
                                <X className="w-4 h-4" />
                              )}
                            </span>
                          ) : (
                            <button
                              onClick={() => onPermissionChange(role.id, perm, !hasPerm)}
                              className={`w-6 h-6 rounded border-2 flex items-center justify-center transition
                                ${hasPerm 
                                  ? 'bg-green-500 border-green-500 text-white' 
                                  : 'border-gray-300 hover:border-green-500'
                                }
                              `}
                            >
                              {hasPerm && <Check className="w-4 h-4" />}
                            </button>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PermissionsTable;
```

---

## File 4: Security API Service
**Path:** `frontend/src/features/security/services/securityAPI.js`

```javascript
/**
 * Security API Service
 * API calls for security features
 */

import api from '../../../services/api';

export const securityAPI = {
  // ============== MFA ==============
  
  async setupMFA({ method, phone_number }) {
    const response = await api.post('/security/mfa/setup', {
      method,
      phone_number,
    });
    return response.data;
  },

  async verifyMFASetup(code) {
    const response = await api.post('/security/mfa/verify', { code });
    return response.data;
  },

  async verifyMFACode(code) {
    const response = await api.post('/security/mfa/verify-code', { code });
    return response.data;
  },

  async disableMFA(code) {
    const response = await api.post('/security/mfa/disable', { code });
    return response.data;
  },

  async getMFAStatus() {
    const response = await api.get('/security/mfa/status');
    return response.data;
  },

  async regenerateBackupCodes(code) {
    const response = await api.post('/security/mfa/backup-codes', { code });
    return response.data;
  },

  async sendMFACode() {
    const response = await api.post('/security/mfa/send-code');
    return response.data;
  },

  // ============== OAuth ==============
  
  async getOAuthProviders() {
    const response = await api.get('/security/oauth/providers');
    return response.data;
  },

  async getOAuthAuthorizationUrl(provider, redirectUri) {
    const response = await api.get(`/security/oauth/${provider}/authorize`, {
      params: { redirect_uri: redirectUri },
    });
    return response.data;
  },

  async handleOAuthCallback(provider, code, state, redirectUri) {
    const response = await api.post(`/security/oauth/${provider}/callback`, {
      code,
      state,
      redirect_uri: redirectUri,
    });
    return response.data;
  },

  // ============== Sessions ==============
  
  async getSessions() {
    const response = await api.get('/security/sessions');
    return response.data;
  },

  async revokeSession(sessionId) {
    const response = await api.delete(`/security/sessions/${sessionId}`);
    return response.data;
  },

  async revokeAllSessions() {
    const response = await api.delete('/security/sessions');
    return response.data;
  },

  // ============== RBAC ==============
  
  async getRoles() {
    const response = await api.get('/security/rbac/roles');
    return response.data;
  },

  async getPermissions() {
    const response = await api.get('/security/rbac/permissions');
    return response.data;
  },

  async assignRole({ userId, roleName, customerId, expiresAt }) {
    const response = await api.post('/security/rbac/assign', {
      user_id: userId,
      role_name: roleName,
      customer_id: customerId,
      expires_at: expiresAt,
    });
    return response.data;
  },

  async revokeRole(userId, roleName, customerId) {
    const response = await api.delete('/security/rbac/assign', {
      params: {
        user_id: userId,
        role_name: roleName,
        customer_id: customerId,
      },
    });
    return response.data;
  },

  async getUserRoles(userId) {
    const response = await api.get(`/security/rbac/user/${userId}`);
    return response.data;
  },

  async checkPermission(permission) {
    const response = await api.get('/security/rbac/check', {
      params: { permission },
    });
    return response.data;
  },

  // ============== Audit ==============
  
  async queryAuditLogs({ eventType, userId, startDate, endDate, limit = 100 }) {
    const response = await api.get('/security/audit/logs', {
      params: {
        event_type: eventType || undefined,
        user_id: userId || undefined,
        start_time: startDate ? new Date(startDate).toISOString() : undefined,
        end_time: endDate ? new Date(endDate).toISOString() : undefined,
        limit,
      },
    });
    return response.data;
  },

  async getAuditSummary(startTime, endTime) {
    const response = await api.get('/security/audit/summary', {
      params: {
        start_time: startTime,
        end_time: endTime,
      },
    });
    return response.data;
  },

  async exportAuditLogs(format, filters = {}) {
    const response = await api.post('/security/audit/export', null, {
      params: {
        format,
        ...filters,
      },
      responseType: 'blob',
    });
    return response.data;
  },

  // ============== IP Management ==============
  
  async getBlockedIPs() {
    const response = await api.get('/security/ip/blocked');
    return response.data;
  },

  async blockIP({ ipAddress, reason, durationSeconds, permanent }) {
    const response = await api.post('/security/ip/block', {
      ip_address: ipAddress,
      reason,
      duration_seconds: durationSeconds,
      permanent,
    });
    return response.data;
  },

  async unblockIP(ipAddress) {
    const response = await api.delete(`/security/ip/block/${encodeURIComponent(ipAddress)}`);
    return response.data;
  },

  // ============== Security Status ==============
  
  async getSecurityStatus() {
    const response = await api.get('/security/status');
    return response.data;
  },

  async getSecurityConfig() {
    const response = await api.get('/security/config');
    return response.data;
  },

  async updateSecurityConfig(config) {
    const response = await api.put('/security/config', config);
    return response.data;
  },

  // ============== Rate Limits ==============
  
  async getRateLimitStatus(key) {
    const response = await api.get(`/security/rate-limits/${key}`);
    return response.data;
  },
};

export default securityAPI;
```

---

## File 5: Security Module Index
**Path:** `frontend/src/features/security/index.js`

```javascript
/**
 * Security Module Exports
 */

// Pages
export { default as SecuritySettings } from './pages/SecuritySettings';
export { default as MFASetup } from './pages/MFASetup';
export { default as AuditLogs } from './pages/AuditLogs';

// Components
export { default as MFAVerification } from './components/MFAVerification';
export { default as SessionManager } from './components/SessionManager';
export { default as PermissionsTable } from './components/PermissionsTable';

// Services
export { securityAPI } from './services/securityAPI';

// Routes configuration
export const securityRoutes = [
  {
    path: '/security',
    element: '<SecuritySettings />',
  },
  {
    path: '/security/mfa-setup',
    element: '<MFASetup />',
  },
  {
    path: '/security/audit-logs',
    element: '<AuditLogs />',
    adminOnly: true,
  },
];
```

---

## Summary Part 11

| File | Description | Lines |
|------|-------------|-------|
| `components/MFAVerification.jsx` | MFA code input | ~200 |
| `components/SessionManager.jsx` | Session management | ~180 |
| `components/PermissionsTable.jsx` | Permissions display | ~200 |
| `services/securityAPI.js` | Security API service | ~200 |
| `index.js` | Module exports | ~35 |
| **Total** | | **~815 lines** |
