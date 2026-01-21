/**
 * Multi-Tenancy API Service
 * Phase 16 - Enterprise multi-tenant architecture
 */

import api from './api';

// ==================== Tenant Management ====================

export const tenantAPI = {
  // Get current tenant info
  getCurrent: () => api.get('/api/v1/tenant/current'),

  // Update current tenant
  updateCurrent: (data) => api.put('/api/v1/tenant/current', data),

  // Get tenant statistics
  getStats: () => api.get('/api/v1/tenant/stats'),
};

// ==================== Admin Tenant Management ====================

export const adminTenantAPI = {
  // List all tenants (superadmin)
  list: (params) => api.get('/api/v1/tenant/admin/list', { params }),

  // Create new tenant
  create: (data) => api.post('/api/v1/tenant/admin/create', data),

  // Get tenant by ID
  get: (tenantId) => api.get(`/api/v1/tenant/admin/${tenantId}`),

  // Activate tenant
  activate: (tenantId) => api.put(`/api/v1/tenant/admin/${tenantId}/activate`),

  // Suspend tenant
  suspend: (tenantId, reason) =>
    api.put(`/api/v1/tenant/admin/${tenantId}/suspend`, null, { params: { reason } }),

  // Delete tenant
  delete: (tenantId, hardDelete = false) =>
    api.delete(`/api/v1/tenant/admin/${tenantId}`, { params: { hard_delete: hardDelete } }),
};

// ==================== Domains ====================

export const domainsAPI = {
  // List domains
  list: () => api.get('/api/v1/tenant/domains'),

  // Add domain
  add: (data) => api.post('/api/v1/tenant/domains', data),

  // Verify domain
  verify: (domainId) => api.post(`/api/v1/tenant/domains/${domainId}/verify`),

  // Remove domain
  remove: (domainId) => api.delete(`/api/v1/tenant/domains/${domainId}`),
};

// ==================== Settings ====================

export const settingsAPI = {
  // Get tenant settings
  get: () => api.get('/api/v1/tenant/settings'),

  // Update settings
  update: (data) => api.put('/api/v1/tenant/settings', data),

  // Update security settings
  updateSecurity: (data) => api.put('/api/v1/tenant/settings/security', data),
};

// ==================== Subscription ====================

export const subscriptionAPI = {
  // Get current subscription
  get: () => api.get('/api/v1/tenant/subscription'),

  // Upgrade subscription
  upgrade: (data) => api.post('/api/v1/tenant/subscription/upgrade', data),

  // Downgrade subscription
  downgrade: (data) => api.post('/api/v1/tenant/subscription/downgrade', data),

  // Cancel subscription
  cancel: (data) => api.post('/api/v1/tenant/subscription/cancel', data),

  // Get available plans
  getPlans: () => api.get('/api/v1/tenant/plans'),
};

// ==================== Quota & Usage ====================

export const quotaAPI = {
  // Get quota
  get: () => api.get('/api/v1/tenant/quota'),

  // Get usage summary
  getUsage: () => api.get('/api/v1/tenant/usage'),

  // Get usage alerts
  getAlerts: (threshold = 80) =>
    api.get('/api/v1/tenant/usage/alerts', { params: { threshold } }),
};

// ==================== Features ====================

export const featuresAPI = {
  // List all features
  list: () => api.get('/api/v1/tenant/features'),

  // Get specific feature
  get: (featureName) => api.get(`/api/v1/tenant/features/${featureName}`),

  // Enable feature (superadmin)
  enable: (data) => api.post('/api/v1/tenant/features/enable', data),

  // Get upgrade suggestions
  getUpgradeSuggestions: () => api.get('/api/v1/tenant/features/upgrade-suggestions'),
};

// ==================== Team ====================

export const teamAPI = {
  // List team members
  list: () => api.get('/api/v1/tenant/team'),

  // Update member role
  updateRole: (userId, data) => api.put(`/api/v1/tenant/team/${userId}/role`, data),

  // Remove member
  remove: (userId) => api.delete(`/api/v1/tenant/team/${userId}`),
};

// ==================== Invitations ====================

export const invitationsAPI = {
  // List invitations
  list: (status) => api.get('/api/v1/tenant/invitations', { params: { status } }),

  // Create invitation
  create: (data) => api.post('/api/v1/tenant/invitations', data),

  // Accept invitation
  accept: (token) => api.post('/api/v1/tenant/invitations/accept', { token }),

  // Revoke invitation
  revoke: (invitationId) => api.delete(`/api/v1/tenant/invitations/${invitationId}`),
};

// ==================== Hooks ====================

export const useTenant = () => {
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTenant = async () => {
    try {
      setLoading(true);
      const response = await tenantAPI.getCurrent();
      setTenant(response.data.tenant);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load tenant');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTenant();
  }, []);

  return { tenant, loading, error, refetch: fetchTenant };
};

export const useUsage = () => {
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchUsage = async () => {
    try {
      setLoading(true);
      const response = await quotaAPI.getUsage();
      setUsage(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load usage');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsage();
  }, []);

  return { usage, loading, error, refetch: fetchUsage };
};

export const useTeam = () => {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTeam = async () => {
    try {
      setLoading(true);
      const response = await teamAPI.list();
      setMembers(response.data.members);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load team');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeam();
  }, []);

  return { members, loading, error, refetch: fetchTeam };
};

export const useSubscription = () => {
  const [subscription, setSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSubscription = async () => {
    try {
      setLoading(true);
      const [subResponse, plansResponse] = await Promise.all([
        subscriptionAPI.get(),
        subscriptionAPI.getPlans()
      ]);
      setSubscription(subResponse.data.subscription);
      setPlans(plansResponse.data.plans);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load subscription');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscription();
  }, []);

  return { subscription, plans, loading, error, refetch: fetchSubscription };
};

// Note: Import useState and useEffect at the top of your component file
// import { useState, useEffect } from 'react';
