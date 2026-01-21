/**
 * Phase 14: Integrations Hub Page
 * Manage external integrations with ERPs, CRMs, Accounting, E-commerce, Banking, etc.
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  getProviders,
  getIntegrations,
  getIntegration,
  createIntegration,
  deleteIntegration,
  initiateOAuth,
  testConnection,
  triggerSync,
  getSyncConfigs,
  createSyncConfig,
  updateSyncConfig,
  getSyncLogs,
  getCategoryIcon,
  getProviderIcon,
  getStatusColor,
  getHealthStatus,
  formatSyncDirection,
  formatConflictResolution
} from '../services/integrationsApi';

const Integrations = () => {
  const { t } = useTranslation();
  const [providers, setProviders] = useState([]);
  const [integrations, setIntegrations] = useState([]);
  const [selectedIntegration, setSelectedIntegration] = useState(null);
  const [syncConfigs, setSyncConfigs] = useState([]);
  const [syncLogs, setSyncLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState({});
  const [testing, setTesting] = useState({});
  const [activeCategory, setActiveCategory] = useState('all');
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState(null);

  const categories = [
    { id: 'all', label: 'All', icon: '🔌' },
    { id: 'accounting', label: 'Accounting', icon: '📊' },
    { id: 'crm', label: 'CRM', icon: '👥' },
    { id: 'ecommerce', label: 'E-commerce', icon: '🛒' },
    { id: 'banking', label: 'Banking', icon: '🏦' },
    { id: 'payments', label: 'Payments', icon: '💳' },
    { id: 'erp', label: 'ERP', icon: '🏢' },
  ];

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedIntegration) {
      loadIntegrationDetails(selectedIntegration.id);
    }
  }, [selectedIntegration?.id]);

  const loadData = async () => {
    try {
      const [providersData, integrationsData] = await Promise.all([
        getProviders(),
        getIntegrations()
      ]);
      setProviders(providersData);
      setIntegrations(integrationsData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadIntegrationDetails = async (integrationId) => {
    try {
      const [configs, logs] = await Promise.all([
        getSyncConfigs(integrationId),
        getSyncLogs(integrationId, 10)
      ]);
      setSyncConfigs(configs);
      setSyncLogs(logs);
    } catch (error) {
      console.error('Error loading integration details:', error);
    }
  };

  const handleConnect = async (provider) => {
    try {
      // For OAuth providers, initiate the OAuth flow
      const redirectUri = `${window.location.origin}/integrations/callback`;
      const result = await initiateOAuth(provider.name, redirectUri);

      if (result.authorization_url) {
        // Open OAuth popup or redirect
        window.location.href = result.authorization_url;
      }
    } catch (error) {
      console.error('Error initiating connection:', error);
      alert('Failed to start connection process');
    }
  };

  const handleDisconnect = async (integrationId) => {
    if (!confirm('Are you sure you want to disconnect this integration? All sync configurations will be lost.')) {
      return;
    }

    try {
      await deleteIntegration(integrationId);
      setIntegrations(integrations.filter(i => i.id !== integrationId));
      if (selectedIntegration?.id === integrationId) {
        setSelectedIntegration(null);
      }
    } catch (error) {
      console.error('Error disconnecting:', error);
      alert('Failed to disconnect integration');
    }
  };

  const handleTestConnection = async (integrationId) => {
    setTesting({ ...testing, [integrationId]: true });

    try {
      const result = await testConnection(integrationId);
      alert(result.success ? `✅ ${result.message}` : `❌ ${result.message}`);
      loadData();
    } catch (error) {
      alert(`❌ Connection test failed: ${error.message}`);
    } finally {
      setTesting({ ...testing, [integrationId]: false });
    }
  };

  const handleSync = async (integrationId, entityType = null) => {
    const key = entityType ? `${integrationId}-${entityType}` : integrationId;
    setSyncing({ ...syncing, [key]: true });

    try {
      await triggerSync(integrationId, entityType, false);
      alert('Sync started successfully');

      // Reload sync logs after a short delay
      setTimeout(() => {
        if (selectedIntegration?.id === integrationId) {
          loadIntegrationDetails(integrationId);
        }
      }, 2000);
    } catch (error) {
      alert(`Sync failed: ${error.message}`);
    } finally {
      setSyncing({ ...syncing, [key]: false });
    }
  };

  const handleAddSyncConfig = async (integrationId, config) => {
    try {
      await createSyncConfig(integrationId, config);
      loadIntegrationDetails(integrationId);
      setShowConfigModal(false);
    } catch (error) {
      alert(`Failed to add sync config: ${error.message}`);
    }
  };

  const handleToggleSyncConfig = async (integrationId, configId, enabled) => {
    try {
      await updateSyncConfig(integrationId, configId, { enabled });
      loadIntegrationDetails(integrationId);
    } catch (error) {
      alert(`Failed to update sync config: ${error.message}`);
    }
  };

  const filteredProviders = activeCategory === 'all'
    ? providers
    : providers.filter(p => p.category === activeCategory);

  const filteredIntegrations = activeCategory === 'all'
    ? integrations
    : integrations.filter(i => i.category === activeCategory);

  const connectedProviders = new Set(integrations.map(i => i.provider));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">External Integrations Hub</h1>
          <p className="text-gray-600">Connect your business tools and automate data synchronization</p>
        </div>
        <button
          onClick={() => setShowConnectModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <span>+</span> Add Integration
        </button>
      </div>

      {/* Category Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 whitespace-nowrap transition-colors ${
              activeCategory === cat.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <span>{cat.icon}</span>
            {cat.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Connected Integrations */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Connected Integrations</h2>

          {filteredIntegrations.length === 0 ? (
            <div className="bg-white rounded-xl p-8 text-center border border-gray-200">
              <div className="text-4xl mb-4">🔌</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No integrations connected</h3>
              <p className="text-gray-600 mb-4">Get started by connecting your first integration</p>
              <button
                onClick={() => setShowConnectModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Connect Now
              </button>
            </div>
          ) : (
            <div className="grid gap-4">
              {filteredIntegrations.map(integration => {
                const health = getHealthStatus(integration.health);

                return (
                  <div
                    key={integration.id}
                    className={`bg-white rounded-xl p-4 border-2 transition-all cursor-pointer ${
                      selectedIntegration?.id === integration.id
                        ? 'border-blue-500 shadow-lg'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedIntegration(integration)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="text-3xl">{getProviderIcon(integration.provider)}</div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{integration.name}</h3>
                          <p className="text-sm text-gray-500">{integration.provider}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          integration.status === 'active'
                            ? 'bg-green-100 text-green-700'
                            : integration.status === 'error'
                              ? 'bg-red-100 text-red-700'
                              : 'bg-gray-100 text-gray-700'
                        }`}>
                          {integration.status}
                        </span>

                        <span className={`px-2 py-1 rounded-full text-xs font-medium bg-${health.color}-100 text-${health.color}-700`}>
                          {health.label}
                        </span>
                      </div>
                    </div>

                    <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
                      {integration.last_sync_at && (
                        <span>Last sync: {new Date(integration.last_sync_at).toLocaleString()}</span>
                      )}
                    </div>

                    <div className="mt-4 flex gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTestConnection(integration.id);
                        }}
                        disabled={testing[integration.id]}
                        className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
                      >
                        {testing[integration.id] ? 'Testing...' : 'Test Connection'}
                      </button>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSync(integration.id);
                        }}
                        disabled={syncing[integration.id]}
                        className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
                      >
                        {syncing[integration.id] ? 'Syncing...' : 'Sync Now'}
                      </button>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDisconnect(integration.id);
                        }}
                        className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 ml-auto"
                      >
                        Disconnect
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Integration Details Panel */}
        <div className="space-y-4">
          {selectedIntegration ? (
            <>
              <div className="bg-white rounded-xl p-4 border border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Sync Configuration</h2>

                <div className="space-y-3">
                  {syncConfigs.map(config => (
                    <div key={config.id} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium">{config.entity_type}</span>
                          <span className="text-sm text-gray-500 ml-2">
                            {formatSyncDirection(config.direction)}
                          </span>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={config.enabled}
                            onChange={(e) => handleToggleSyncConfig(selectedIntegration.id, config.id, e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>

                      <div className="mt-2 text-xs text-gray-500">
                        Interval: {Math.round(config.sync_interval / 60)} min |{' '}
                        Conflict: {formatConflictResolution(config.conflict_resolution)}
                      </div>

                      <button
                        onClick={() => handleSync(selectedIntegration.id, config.entity_type)}
                        disabled={syncing[`${selectedIntegration.id}-${config.entity_type}`]}
                        className="mt-2 px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 disabled:opacity-50"
                      >
                        {syncing[`${selectedIntegration.id}-${config.entity_type}`] ? 'Syncing...' : 'Sync'}
                      </button>
                    </div>
                  ))}

                  <button
                    onClick={() => setShowConfigModal(true)}
                    className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-blue-400 hover:text-blue-600"
                  >
                    + Add Entity Sync
                  </button>
                </div>
              </div>

              {/* Sync Logs */}
              <div className="bg-white rounded-xl p-4 border border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Sync Activity</h2>

                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {syncLogs.length === 0 ? (
                    <p className="text-gray-500 text-sm text-center py-4">No sync activity yet</p>
                  ) : (
                    syncLogs.map(log => (
                      <div key={log.id} className="p-2 bg-gray-50 rounded text-sm">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{log.entity_type}</span>
                          <span className={`px-1.5 py-0.5 rounded text-xs ${
                            log.status === 'completed'
                              ? 'bg-green-100 text-green-700'
                              : log.status === 'failed'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-yellow-100 text-yellow-700'
                          }`}>
                            {log.status}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {new Date(log.started_at).toLocaleString()}
                          {log.records_processed > 0 && (
                            <span className="ml-2">
                              | {log.records_processed} records
                              {log.records_failed > 0 && ` (${log.records_failed} failed)`}
                            </span>
                          )}
                        </div>
                        {log.error_message && (
                          <div className="text-xs text-red-600 mt-1">{log.error_message}</div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-xl p-8 text-center border border-gray-200">
              <div className="text-4xl mb-4">👆</div>
              <p className="text-gray-600">Select an integration to view details and configuration</p>
            </div>
          )}
        </div>
      </div>

      {/* Connect Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Add Integration</h2>
              <button onClick={() => setShowConnectModal(false)} className="text-gray-500 hover:text-gray-700">
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {filteredProviders.map(provider => {
                const isConnected = connectedProviders.has(provider.name);

                return (
                  <div
                    key={provider.name}
                    className={`p-4 border rounded-lg transition-all ${
                      isConnected
                        ? 'border-green-300 bg-green-50'
                        : 'border-gray-200 hover:border-blue-300 cursor-pointer'
                    }`}
                    onClick={() => !isConnected && handleConnect(provider)}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{getProviderIcon(provider.name)}</span>
                      <div>
                        <h3 className="font-medium">{provider.label}</h3>
                        <span className="text-xs text-gray-500 px-1.5 py-0.5 bg-gray-100 rounded">
                          {provider.category}
                        </span>
                      </div>
                    </div>

                    {provider.description && (
                      <p className="text-xs text-gray-500 mt-2">{provider.description}</p>
                    )}

                    {isConnected ? (
                      <span className="inline-block mt-2 text-xs text-green-600 font-medium">
                        ✓ Connected
                      </span>
                    ) : (
                      <button className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium">
                        Connect →
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Sync Config Modal */}
      {showConfigModal && selectedIntegration && (
        <SyncConfigModal
          integration={selectedIntegration}
          onClose={() => setShowConfigModal(false)}
          onSave={(config) => handleAddSyncConfig(selectedIntegration.id, config)}
        />
      )}
    </div>
  );
};

// Sync Configuration Modal Component
const SyncConfigModal = ({ integration, onClose, onSave }) => {
  const [config, setConfig] = useState({
    entity_type: 'customer',
    direction: 'bidirectional',
    sync_interval: 3600,
    conflict_resolution: 'last_write_wins'
  });

  const entityTypes = [
    { id: 'customer', label: 'Customers' },
    { id: 'contact', label: 'Contacts' },
    { id: 'invoice', label: 'Invoices' },
    { id: 'product', label: 'Products' },
    { id: 'order', label: 'Orders' },
    { id: 'payment', label: 'Payments' },
    { id: 'account', label: 'Accounts' },
    { id: 'transaction', label: 'Transactions' },
  ];

  const directions = [
    { id: 'inbound', label: 'Import Only (← from source)' },
    { id: 'outbound', label: 'Export Only (→ to source)' },
    { id: 'bidirectional', label: 'Two-way Sync (↔)' },
  ];

  const intervals = [
    { id: 300, label: 'Every 5 minutes' },
    { id: 900, label: 'Every 15 minutes' },
    { id: 1800, label: 'Every 30 minutes' },
    { id: 3600, label: 'Every hour' },
    { id: 21600, label: 'Every 6 hours' },
    { id: 86400, label: 'Daily' },
  ];

  const conflictStrategies = [
    { id: 'last_write_wins', label: 'Last Write Wins', desc: 'Most recent change takes precedence' },
    { id: 'source_priority', label: 'Source Priority', desc: 'External source always wins' },
    { id: 'manual_review', label: 'Manual Review', desc: 'Flag for manual resolution' },
    { id: 'merge', label: 'Smart Merge', desc: 'Attempt to merge field-by-field' },
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(config);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-lg w-full">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Add Sync Configuration</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Entity Type</label>
            <select
              value={config.entity_type}
              onChange={(e) => setConfig({ ...config, entity_type: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              {entityTypes.map(et => (
                <option key={et.id} value={et.id}>{et.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sync Direction</label>
            <select
              value={config.direction}
              onChange={(e) => setConfig({ ...config, direction: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              {directions.map(d => (
                <option key={d.id} value={d.id}>{d.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sync Interval</label>
            <select
              value={config.sync_interval}
              onChange={(e) => setConfig({ ...config, sync_interval: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              {intervals.map(i => (
                <option key={i.id} value={i.id}>{i.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Conflict Resolution</label>
            <select
              value={config.conflict_resolution}
              onChange={(e) => setConfig({ ...config, conflict_resolution: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              {conflictStrategies.map(cs => (
                <option key={cs.id} value={cs.id}>{cs.label}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {conflictStrategies.find(cs => cs.id === config.conflict_resolution)?.desc}
            </p>
          </div>

          <div className="flex gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add Configuration
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Integrations;
