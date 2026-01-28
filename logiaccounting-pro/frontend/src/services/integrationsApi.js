/**
 * Phase 14: Integrations API Service
 * API client for external integrations management
 * Uses shared axios instance from api.js for consistent auth & error handling.
 */

import api from './api';

const BASE = '/api/v1/integrations';

// ==================== Providers ====================

export const getProviders = async (category = null) => {
  const params = category ? { category } : {};
  const { data } = await api.get(`${BASE}/providers`, { params });
  return data.providers;
};

export const getProviderInfo = async (provider) => {
  const { data } = await api.get(`${BASE}/providers/${provider}`);
  return data;
};

// ==================== Integrations CRUD ====================

export const getIntegrations = async (category = null) => {
  const params = category ? { category } : {};
  const { data } = await api.get(BASE, { params });
  return data.integrations;
};

export const getIntegration = async (integrationId) => {
  const { data } = await api.get(`${BASE}/${integrationId}`);
  return data;
};

export const createIntegration = async (payload) => {
  const { data } = await api.post(BASE, payload);
  return data;
};

export const updateIntegration = async (integrationId, payload) => {
  const { data } = await api.patch(`${BASE}/${integrationId}`, payload);
  return data;
};

export const deleteIntegration = async (integrationId) => {
  const { data } = await api.delete(`${BASE}/${integrationId}`);
  return data;
};

// ==================== OAuth ====================

export const initiateOAuth = async (provider, redirectUri, extraParams = null) => {
  const { data } = await api.post(`${BASE}/oauth/initiate`, {
    provider,
    redirect_uri: redirectUri,
    extra_params: extraParams,
  });
  return data;
};

export const completeOAuth = async (provider, code, state, redirectUri) => {
  const { data } = await api.post(`${BASE}/oauth/callback/${provider}`, {
    code,
    state,
    redirect_uri: redirectUri,
  });
  return data;
};

export const refreshToken = async (integrationId) => {
  const { data } = await api.post(`${BASE}/${integrationId}/refresh-token`);
  return data;
};

// ==================== Connection Test ====================

export const testConnection = async (integrationId) => {
  const { data } = await api.post(`${BASE}/${integrationId}/test`);
  return data;
};

// ==================== Sync Configuration ====================

export const getSyncConfigs = async (integrationId) => {
  const { data } = await api.get(`${BASE}/${integrationId}/sync-configs`);
  return data.sync_configs;
};

export const createSyncConfig = async (integrationId, payload) => {
  const { data } = await api.post(`${BASE}/${integrationId}/sync-configs`, payload);
  return data;
};

export const updateSyncConfig = async (integrationId, configId, payload) => {
  const { data } = await api.patch(`${BASE}/${integrationId}/sync-configs/${configId}`, payload);
  return data;
};

export const deleteSyncConfig = async (integrationId, configId) => {
  const { data } = await api.delete(`${BASE}/${integrationId}/sync-configs/${configId}`);
  return data;
};

// ==================== Field Mappings ====================

export const getFieldMappings = async (integrationId, configId) => {
  const { data } = await api.get(`${BASE}/${integrationId}/sync-configs/${configId}/mappings`);
  return data.mappings;
};

export const createFieldMapping = async (integrationId, configId, payload) => {
  const { data } = await api.post(
    `${BASE}/${integrationId}/sync-configs/${configId}/mappings`,
    payload
  );
  return data;
};

export const updateFieldMapping = async (integrationId, configId, mappingId, payload) => {
  const { data } = await api.patch(
    `${BASE}/${integrationId}/sync-configs/${configId}/mappings/${mappingId}`,
    payload
  );
  return data;
};

export const deleteFieldMapping = async (integrationId, configId, mappingId) => {
  const { data } = await api.delete(
    `${BASE}/${integrationId}/sync-configs/${configId}/mappings/${mappingId}`
  );
  return data;
};

// ==================== Synchronization ====================

export const triggerSync = async (integrationId, entityType = null, fullSync = false) => {
  const { data } = await api.post(`${BASE}/${integrationId}/sync`, {
    entity_type: entityType,
    full_sync: fullSync,
  });
  return data;
};

export const getSyncLogs = async (integrationId, limit = 20, entityType = null) => {
  const params = { limit };
  if (entityType) params.entity_type = entityType;
  const { data } = await api.get(`${BASE}/${integrationId}/sync-logs`, { params });
  return data.sync_logs;
};

export const getSyncLog = async (integrationId, logId) => {
  const { data } = await api.get(`${BASE}/${integrationId}/sync-logs/${logId}`);
  return data;
};

// ==================== Webhooks ====================

export const getWebhooks = async (integrationId) => {
  const { data } = await api.get(`${BASE}/${integrationId}/webhooks`);
  return data.webhooks;
};

export const createWebhook = async (integrationId, payload) => {
  const { data } = await api.post(`${BASE}/${integrationId}/webhooks`, payload);
  return data;
};

export const deleteWebhook = async (integrationId, webhookId) => {
  const { data } = await api.delete(`${BASE}/${integrationId}/webhooks/${webhookId}`);
  return data;
};

// ==================== Data Access ====================

export const getRemoteRecords = async (integrationId, entityType, page = 1, pageSize = 50) => {
  const { data } = await api.get(`${BASE}/${integrationId}/entities/${entityType}`, {
    params: { page, page_size: pageSize },
  });
  return data;
};

export const getRemoteRecord = async (integrationId, entityType, recordId) => {
  const { data } = await api.get(`${BASE}/${integrationId}/entities/${entityType}/${recordId}`);
  return data;
};

export const getEntitySchema = async (integrationId, entityType) => {
  const { data } = await api.get(`${BASE}/${integrationId}/schema/${entityType}`);
  return data;
};

// ==================== Helpers ====================

export const getCategoryIcon = (category) => {
  const icons = {
    accounting: '📊',
    crm: '👥',
    ecommerce: '🛒',
    banking: '🏦',
    payments: '💳',
    erp: '🏢',
    shipping: '📦',
    generic: '🔌',
  };
  return icons[category] || icons.generic;
};

export const getProviderIcon = (provider) => {
  const icons = {
    quickbooks: '💚',
    xero: '💙',
    sage: '🟢',
    salesforce: '☁️',
    hubspot: '🧡',
    zoho: '🔴',
    shopify: '🟢',
    woocommerce: '🟣',
    stripe: '💜',
    plaid: '🟦',
    sap: '🔵',
    netsuite: '🟠',
    dynamics: '🔷',
    fedex: '🟧',
    ups: '🟤',
    dhl: '🟡',
  };
  return icons[provider] || '🔌';
};

export const getStatusColor = (status) => {
  const colors = {
    active: 'green',
    connected: 'green',
    pending: 'yellow',
    error: 'red',
    disconnected: 'gray',
    syncing: 'blue',
  };
  return colors[status] || 'gray';
};

export const getHealthStatus = (health) => {
  if (!health) return { color: 'gray', label: 'Unknown' };
  if (health.score >= 90) return { color: 'green', label: 'Healthy' };
  if (health.score >= 70) return { color: 'yellow', label: 'Degraded' };
  return { color: 'red', label: 'Unhealthy' };
};

export const formatSyncDirection = (direction) => {
  const labels = {
    inbound: '← Import only',
    outbound: '→ Export only',
    bidirectional: '↔ Two-way sync',
  };
  return labels[direction] || direction;
};

export const formatConflictResolution = (resolution) => {
  const labels = {
    last_write_wins: 'Last Write Wins',
    source_priority: 'Source Priority',
    manual_review: 'Manual Review',
    merge: 'Smart Merge',
  };
  return labels[resolution] || resolution;
};
