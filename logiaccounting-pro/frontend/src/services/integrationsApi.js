/**
 * Phase 14: Integrations API Service
 * API client for external integrations management
 */

const API_BASE = '/api/v1/integrations';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
};

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || error.message || 'Request failed');
  }
  return response.json();
};

// ==================== Providers ====================

export const getProviders = async (category = null) => {
  const url = category ? `${API_BASE}/providers?category=${category}` : `${API_BASE}/providers`;
  const response = await fetch(url, {
    headers: getAuthHeaders()
  });
  const data = await handleResponse(response);
  return data.providers;
};

export const getProviderInfo = async (provider) => {
  const response = await fetch(`${API_BASE}/providers/${provider}`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ==================== Integrations CRUD ====================

export const getIntegrations = async (category = null) => {
  const url = category ? `${API_BASE}?category=${category}` : API_BASE;
  const response = await fetch(url, {
    headers: getAuthHeaders()
  });
  const data = await handleResponse(response);
  return data.integrations;
};

export const getIntegration = async (integrationId) => {
  const response = await fetch(`${API_BASE}/${integrationId}`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const createIntegration = async (data) => {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const updateIntegration = async (integrationId, data) => {
  const response = await fetch(`${API_BASE}/${integrationId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const deleteIntegration = async (integrationId) => {
  const response = await fetch(`${API_BASE}/${integrationId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ==================== OAuth ====================

export const initiateOAuth = async (provider, redirectUri, extraParams = null) => {
  const response = await fetch(`${API_BASE}/oauth/initiate`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      provider,
      redirect_uri: redirectUri,
      extra_params: extraParams
    })
  });
  return handleResponse(response);
};

export const completeOAuth = async (provider, code, state, redirectUri) => {
  const response = await fetch(`${API_BASE}/oauth/callback/${provider}`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      code,
      state,
      redirect_uri: redirectUri
    })
  });
  return handleResponse(response);
};

export const refreshToken = async (integrationId) => {
  const response = await fetch(`${API_BASE}/${integrationId}/refresh-token`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ==================== Connection Test ====================

export const testConnection = async (integrationId) => {
  const response = await fetch(`${API_BASE}/${integrationId}/test`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ==================== Sync Configuration ====================

export const getSyncConfigs = async (integrationId) => {
  const response = await fetch(`${API_BASE}/${integrationId}/sync-configs`, {
    headers: getAuthHeaders()
  });
  const data = await handleResponse(response);
  return data.sync_configs;
};

export const createSyncConfig = async (integrationId, data) => {
  const response = await fetch(`${API_BASE}/${integrationId}/sync-configs`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const updateSyncConfig = async (integrationId, configId, data) => {
  const response = await fetch(`${API_BASE}/${integrationId}/sync-configs/${configId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const deleteSyncConfig = async (integrationId, configId) => {
  const response = await fetch(`${API_BASE}/${integrationId}/sync-configs/${configId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ==================== Field Mappings ====================

export const getFieldMappings = async (integrationId, configId) => {
  const response = await fetch(`${API_BASE}/${integrationId}/sync-configs/${configId}/mappings`, {
    headers: getAuthHeaders()
  });
  const data = await handleResponse(response);
  return data.mappings;
};

export const createFieldMapping = async (integrationId, configId, data) => {
  const response = await fetch(`${API_BASE}/${integrationId}/sync-configs/${configId}/mappings`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const updateFieldMapping = async (integrationId, configId, mappingId, data) => {
  const response = await fetch(`${API_BASE}/${integrationId}/sync-configs/${configId}/mappings/${mappingId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const deleteFieldMapping = async (integrationId, configId, mappingId) => {
  const response = await fetch(`${API_BASE}/${integrationId}/sync-configs/${configId}/mappings/${mappingId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ==================== Synchronization ====================

export const triggerSync = async (integrationId, entityType = null, fullSync = false) => {
  const response = await fetch(`${API_BASE}/${integrationId}/sync`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      entity_type: entityType,
      full_sync: fullSync
    })
  });
  return handleResponse(response);
};

export const getSyncLogs = async (integrationId, limit = 20, entityType = null) => {
  let url = `${API_BASE}/${integrationId}/sync-logs?limit=${limit}`;
  if (entityType) {
    url += `&entity_type=${entityType}`;
  }
  const response = await fetch(url, {
    headers: getAuthHeaders()
  });
  const data = await handleResponse(response);
  return data.sync_logs;
};

export const getSyncLog = async (integrationId, logId) => {
  const response = await fetch(`${API_BASE}/${integrationId}/sync-logs/${logId}`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ==================== Webhooks ====================

export const getWebhooks = async (integrationId) => {
  const response = await fetch(`${API_BASE}/${integrationId}/webhooks`, {
    headers: getAuthHeaders()
  });
  const data = await handleResponse(response);
  return data.webhooks;
};

export const createWebhook = async (integrationId, data) => {
  const response = await fetch(`${API_BASE}/${integrationId}/webhooks`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const deleteWebhook = async (integrationId, webhookId) => {
  const response = await fetch(`${API_BASE}/${integrationId}/webhooks/${webhookId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ==================== Data Access ====================

export const getRemoteRecords = async (integrationId, entityType, page = 1, pageSize = 50) => {
  const response = await fetch(
    `${API_BASE}/${integrationId}/entities/${entityType}?page=${page}&page_size=${pageSize}`,
    {
      headers: getAuthHeaders()
    }
  );
  return handleResponse(response);
};

export const getRemoteRecord = async (integrationId, entityType, recordId) => {
  const response = await fetch(`${API_BASE}/${integrationId}/entities/${entityType}/${recordId}`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const getEntitySchema = async (integrationId, entityType) => {
  const response = await fetch(`${API_BASE}/${integrationId}/schema/${entityType}`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
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
    generic: '🔌'
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
    dhl: '🟡'
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
    syncing: 'blue'
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
    bidirectional: '↔ Two-way sync'
  };
  return labels[direction] || direction;
};

export const formatConflictResolution = (resolution) => {
  const labels = {
    last_write_wins: 'Last Write Wins',
    source_priority: 'Source Priority',
    manual_review: 'Manual Review',
    merge: 'Smart Merge'
  };
  return labels[resolution] || resolution;
};
