import api from '../../../services/api';

export const securityAPI = {
  getSecurityStatus: () => api.get('/api/v1/security/status'),

  changePassword: (data) => api.put('/api/v1/auth/password', data),

  mfa: {
    getStatus: () => api.get('/api/v1/2fa/status'),

    setup: () => api.post('/api/v1/2fa/setup'),

    verifySetup: (code) => api.post('/api/v1/2fa/verify-setup', { code }),

    disable: (code) => api.post('/api/v1/2fa/disable', { code }),

    verify: (email, code) =>
      api.post('/api/v1/auth/verify-2fa', null, {
        params: { email, code }
      }),

    getBackupCodes: () => api.get('/api/v1/2fa/backup-codes'),

    regenerateBackupCodes: () => api.post('/api/v1/2fa/backup-codes/regenerate')
  },

  oauth: {
    getProviders: () => api.get('/api/v1/oauth/providers'),

    getConnections: () => api.get('/api/v1/oauth/connections'),

    connect: (provider) => api.post(`/api/v1/oauth/connect/${provider}`),

    disconnect: (provider) => api.delete(`/api/v1/oauth/connections/${provider}`),

    callback: (provider, code, state) =>
      api.post(`/api/v1/oauth/callback/${provider}`, { code, state }),

    getAuthUrl: (provider, redirectUri) =>
      api.get(`/api/v1/oauth/auth-url/${provider}`, {
        params: { redirect_uri: redirectUri }
      })
  },

  sessions: {
    list: () => api.get('/api/v1/sessions'),

    getCurrent: () => api.get('/api/v1/sessions/current'),

    revoke: (sessionId) => api.delete(`/api/v1/sessions/${sessionId}`),

    revokeAllOther: () => api.delete('/api/v1/sessions/all-other'),

    getActivity: (sessionId) => api.get(`/api/v1/sessions/${sessionId}/activity`)
  },

  rbac: {
    getRoles: () => api.get('/api/v1/rbac/roles'),

    getRole: (roleId) => api.get(`/api/v1/rbac/roles/${roleId}`),

    createRole: (data) => api.post('/api/v1/rbac/roles', data),

    updateRole: (roleId, data) => api.put(`/api/v1/rbac/roles/${roleId}`, data),

    deleteRole: (roleId) => api.delete(`/api/v1/rbac/roles/${roleId}`),

    getPermissions: () => api.get('/api/v1/rbac/permissions'),

    assignRole: (userId, roleId) =>
      api.post(`/api/v1/rbac/users/${userId}/roles`, { role_id: roleId }),

    removeRole: (userId, roleId) =>
      api.delete(`/api/v1/rbac/users/${userId}/roles/${roleId}`),

    getUserRoles: (userId) => api.get(`/api/v1/rbac/users/${userId}/roles`),

    checkPermission: (permission) =>
      api.get('/api/v1/rbac/check-permission', { params: { permission } })
  },

  audit: {
    search: (params) => api.get('/api/v1/audit', { params }),

    get: (logId) => api.get(`/api/v1/audit/${logId}`),

    getActions: () => api.get('/api/v1/audit/actions'),

    getEntities: () => api.get('/api/v1/audit/entities'),

    getStatistics: (days = 30) =>
      api.get('/api/v1/audit/statistics', { params: { days } }),

    getAnomalies: () => api.get('/api/v1/audit/anomalies'),

    getEntityHistory: (entityType, entityId) =>
      api.get(`/api/v1/audit/entity/${entityType}/${entityId}`),

    getUserActivity: (userId, days = 30) =>
      api.get(`/api/v1/audit/user/${userId}`, { params: { days } }),

    export: (format, dateFrom, dateTo) =>
      api.get('/api/v1/audit/export', {
        params: { format, date_from: dateFrom, date_to: dateTo },
        responseType: 'blob'
      })
  },

  tokens: {
    list: () => api.get('/api/v1/tokens'),

    create: (data) => api.post('/api/v1/tokens', data),

    revoke: (tokenId) => api.delete(`/api/v1/tokens/${tokenId}`),

    revokeAll: () => api.delete('/api/v1/tokens/all')
  },

  passwordPolicy: {
    get: () => api.get('/api/v1/security/password-policy'),

    update: (policy) => api.put('/api/v1/security/password-policy', policy),

    validate: (password) =>
      api.post('/api/v1/security/validate-password', { password })
  },

  ipWhitelist: {
    list: () => api.get('/api/v1/security/ip-whitelist'),

    add: (ip, description) =>
      api.post('/api/v1/security/ip-whitelist', { ip, description }),

    remove: (ip) => api.delete('/api/v1/security/ip-whitelist', { data: { ip } }),

    check: (ip) =>
      api.get('/api/v1/security/ip-whitelist/check', { params: { ip } })
  },

  loginAttempts: {
    list: (params) => api.get('/api/v1/security/login-attempts', { params }),

    getByUser: (userId) => api.get(`/api/v1/security/login-attempts/user/${userId}`),

    clear: (userId) => api.delete(`/api/v1/security/login-attempts/user/${userId}`)
  },

  securityEvents: {
    list: (params) => api.get('/api/v1/security/events', { params }),

    subscribe: (eventTypes) =>
      api.post('/api/v1/security/events/subscribe', { event_types: eventTypes }),

    unsubscribe: (eventTypes) =>
      api.post('/api/v1/security/events/unsubscribe', { event_types: eventTypes })
  }
};

export default securityAPI;
