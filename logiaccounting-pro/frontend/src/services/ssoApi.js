import api from './api';

// SSO API
export const ssoAPI = {
  // Domain Discovery
  discoverSSO: (email) => api.post('/api/v1/sso/discover', { email }),

  // SSO Connection Management (Admin)
  getConnections: (params) => api.get('/api/v1/sso/connections', { params }),
  getConnection: (id) => api.get(`/api/v1/sso/connections/${id}`),
  createConnection: (data) => api.post('/api/v1/sso/connections', data),
  updateConnection: (id, data) => api.put(`/api/v1/sso/connections/${id}`, data),
  deleteConnection: (id) => api.delete(`/api/v1/sso/connections/${id}`),
  activateConnection: (id) => api.post(`/api/v1/sso/connections/${id}/activate`),
  deactivateConnection: (id) => api.post(`/api/v1/sso/connections/${id}/deactivate`),

  // SCIM Configuration
  generateSCIMToken: (connectionId) => api.post(`/api/v1/sso/connections/${connectionId}/scim/token`),
  updateSCIMConfig: (connectionId, data) => api.put(`/api/v1/sso/connections/${connectionId}/scim`, data),

  // SSO Login Initiation (API-based for SPA)
  initiateSSOLogin: (data) => api.post('/api/v1/sso/login/initiate', data),

  // SAML Metadata
  getSAMLMetadata: (connectionId) => api.get(`/api/v1/sso/saml/${connectionId}/metadata`, {
    responseType: 'text',
    headers: { Accept: 'application/xml' }
  }),

  // External Identities
  getExternalIdentities: (params) => api.get('/api/v1/sso/identities', { params }),
  unlinkIdentity: (identityId) => api.delete(`/api/v1/sso/identities/${identityId}`),

  // SSO Logs
  getSSOLogs: (params) => api.get('/api/v1/sso/logs', { params }),
};

// SSO Provider configurations
export const SSO_PROVIDERS = {
  microsoft: {
    name: 'Microsoft Entra ID',
    icon: '🔷',
    protocols: ['oauth2', 'oidc', 'saml'],
    configFields: {
      oauth2: ['client_id', 'client_secret', 'tenant_id'],
      oidc: ['client_id', 'client_secret', 'tenant_id'],
      saml: ['idp_entity_id', 'idp_sso_url', 'idp_slo_url', 'idp_certificate'],
    },
    defaultScopes: ['openid', 'email', 'profile', 'User.Read', 'offline_access'],
    docs: 'https://docs.microsoft.com/en-us/azure/active-directory/develop/',
  },
  google: {
    name: 'Google Workspace',
    icon: '🔴',
    protocols: ['oauth2', 'oidc', 'saml'],
    configFields: {
      oauth2: ['client_id', 'client_secret', 'hosted_domain'],
      oidc: ['client_id', 'client_secret', 'hosted_domain'],
      saml: ['idp_entity_id', 'idp_sso_url', 'idp_certificate'],
    },
    defaultScopes: ['openid', 'email', 'profile'],
    docs: 'https://developers.google.com/identity/protocols/oauth2',
  },
  okta: {
    name: 'Okta',
    icon: '🔵',
    protocols: ['oauth2', 'oidc', 'saml'],
    configFields: {
      oauth2: ['client_id', 'client_secret', 'domain', 'authorization_server'],
      oidc: ['client_id', 'client_secret', 'domain', 'authorization_server'],
      saml: ['idp_entity_id', 'idp_sso_url', 'idp_slo_url', 'idp_certificate'],
    },
    defaultScopes: ['openid', 'email', 'profile', 'groups', 'offline_access'],
    docs: 'https://developer.okta.com/docs/',
  },
  github: {
    name: 'GitHub',
    icon: '⚫',
    protocols: ['oauth2'],
    configFields: {
      oauth2: ['client_id', 'client_secret', 'allowed_organizations'],
    },
    defaultScopes: ['read:user', 'user:email'],
    docs: 'https://docs.github.com/en/developers/apps/building-oauth-apps',
  },
  custom: {
    name: 'Custom SAML/OIDC',
    icon: '⚙️',
    protocols: ['saml', 'oidc'],
    configFields: {
      saml: ['idp_entity_id', 'idp_sso_url', 'idp_slo_url', 'idp_certificate', 'name_id_format'],
      oidc: ['client_id', 'client_secret', 'authorization_endpoint', 'token_endpoint', 'userinfo_endpoint', 'jwks_uri'],
    },
    defaultScopes: ['openid', 'email', 'profile'],
    docs: null,
  },
};

export default ssoAPI;
