import { useState, useEffect } from 'react';
import { webhookAPI } from '../services/api';

export default function Webhooks() {
  const [webhooks, setWebhooks] = useState([]);
  const [events, setEvents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showDeliveries, setShowDeliveries] = useState(null);
  const [showStats, setShowStats] = useState(null);
  const [deliveries, setDeliveries] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [newSecretResult, setNewSecretResult] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, per_page: 20, total: 0 });
  const [deliveryPagination, setDeliveryPagination] = useState({ page: 1, per_page: 20, total: 0 });

  const [formData, setFormData] = useState({
    url: '',
    events: [],
    description: '',
    is_active: true
  });

  useEffect(() => {
    loadData();
    loadEvents();
  }, [pagination.page]);

  const loadData = async () => {
    try {
      const response = await webhookAPI.list({
        page: pagination.page,
        per_page: pagination.per_page
      });
      setWebhooks(response.data.webhooks || []);
      setPagination(prev => ({ ...prev, total: response.data.total || 0 }));
    } catch (err) {
      console.error('Failed to load webhooks:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadEvents = async () => {
    try {
      const response = await webhookAPI.getEvents();
      setEvents(response.data.events || []);
      setCategories(response.data.categories || []);
    } catch (err) {
      console.error('Failed to load events:', err);
    }
  };

  const handleCreate = async () => {
    try {
      const response = await webhookAPI.create(formData);
      if (response.data.secret) {
        setNewSecretResult(response.data.secret);
      }
      setShowForm(false);
      setFormData({ url: '', events: [], description: '', is_active: true });
      loadData();
    } catch (err) {
      alert('Failed to create webhook: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleToggle = async (webhook) => {
    try {
      await webhookAPI.update(webhook.id, { is_active: !webhook.is_active });
      loadData();
    } catch (err) {
      alert('Failed to update webhook');
    }
  };

  const handleDelete = async (webhook) => {
    if (!confirm('Delete this webhook? All delivery history will be lost.')) return;
    try {
      await webhookAPI.delete(webhook.id);
      loadData();
    } catch (err) {
      alert('Failed to delete webhook');
    }
  };

  const handleTest = async (webhook) => {
    try {
      const res = await webhookAPI.test(webhook.id);
      if (res.data.success) {
        alert(`Test successful! Response time: ${res.data.delivery?.response_time_ms || 0}ms`);
      } else {
        alert(`Test failed: ${res.data.delivery?.error_message || 'Unknown error'}`);
      }
    } catch (err) {
      alert('Test failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRotateSecret = async (webhook) => {
    if (!confirm('Rotate this webhook\'s signing secret? The old secret will stop working immediately.')) return;
    try {
      const res = await webhookAPI.rotateSecret(webhook.id);
      setNewSecretResult(res.data.secret);
      loadData();
    } catch (err) {
      alert('Failed to rotate secret');
    }
  };

  const handleViewDeliveries = async (webhook) => {
    try {
      const res = await webhookAPI.getDeliveries(webhook.id, {
        page: 1,
        per_page: 20
      });
      setDeliveries(res.data.deliveries || []);
      setDeliveryPagination({
        page: res.data.page || 1,
        per_page: res.data.per_page || 20,
        total: res.data.total || 0
      });
      setShowDeliveries(webhook);
    } catch (err) {
      alert('Failed to load deliveries');
    }
  };

  const handleViewStats = async (webhook) => {
    try {
      const res = await webhookAPI.getStats(webhook.id);
      setStats(res.data.stats);
      setShowStats(webhook);
    } catch (err) {
      alert('Failed to load stats');
    }
  };

  const handleRetryDelivery = async (webhookId, deliveryId) => {
    try {
      const res = await webhookAPI.retryDelivery(webhookId, deliveryId);
      if (res.data.success) {
        alert('Retry successful!');
        handleViewDeliveries({ id: webhookId });
      } else {
        alert('Retry failed');
      }
    } catch (err) {
      alert('Retry failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const toggleEvent = (eventName) => {
    if (formData.events.includes(eventName)) {
      setFormData({ ...formData, events: formData.events.filter(e => e !== eventName) });
    } else {
      setFormData({ ...formData, events: [...formData.events, eventName] });
    }
  };

  const selectAllInCategory = (category) => {
    const categoryEvents = events.filter(e => e.category === category).map(e => e.event);
    const allSelected = categoryEvents.every(e => formData.events.includes(e));

    if (allSelected) {
      setFormData({
        ...formData,
        events: formData.events.filter(e => !categoryEvents.includes(e))
      });
    } else {
      setFormData({
        ...formData,
        events: [...new Set([...formData.events, ...categoryEvents])]
      });
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  const filteredEvents = selectedCategory
    ? events.filter(e => e.category === selectedCategory)
    : events;

  const eventsByCategory = events.reduce((acc, e) => {
    if (!acc[e.category]) acc[e.category] = [];
    acc[e.category].push(e);
    return acc;
  }, {});

  const getStatusBadge = (status) => {
    switch (status) {
      case 'delivered':
        return <span className="badge badge-success">Delivered</span>;
      case 'failed':
        return <span className="badge badge-danger">Failed</span>;
      case 'pending':
        return <span className="badge badge-warning">Pending</span>;
      default:
        return <span className="badge badge-gray">{status}</span>;
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Webhooks Management</h1>
          <p className="text-muted">Configure webhooks to receive real-time notifications with HMAC signatures</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          + Add Webhook
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid-4 mb-6">
        <div className="stat-card">
          <div className="stat-icon blue">🔗</div>
          <div>
            <p className="stat-value">{pagination.total}</p>
            <p className="stat-label">Total Webhooks</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✓</div>
          <div>
            <p className="stat-value">{webhooks.filter(w => w.is_active && w.is_healthy).length}</p>
            <p className="stat-label">Healthy</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">⚠</div>
          <div>
            <p className="stat-value">{webhooks.filter(w => w.is_active && !w.is_healthy).length}</p>
            <p className="stat-label">Unhealthy</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon gray">⏸</div>
          <div>
            <p className="stat-value">{webhooks.filter(w => !w.is_active).length}</p>
            <p className="stat-label">Paused</p>
          </div>
        </div>
      </div>

      {/* New Secret Alert */}
      {newSecretResult && (
        <div className="section mb-6 bg-success-light p-4 rounded">
          <h3 className="font-bold text-success mb-2">Webhook Secret</h3>
          <p className="text-sm mb-3">
            Copy this secret now. For security reasons, it won't be shown again. Use it to verify webhook signatures.
          </p>
          <div className="flex items-center gap-2 bg-white p-3 rounded font-mono text-sm">
            <code className="flex-1 break-all">{newSecretResult}</code>
            <button
              className="btn btn-sm btn-primary"
              onClick={() => copyToClipboard(newSecretResult)}
            >
              Copy
            </button>
          </div>
          <button
            className="btn btn-sm btn-secondary mt-3"
            onClick={() => setNewSecretResult(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Webhooks List */}
      <div className="section">
        <h3 className="section-title">Configured Webhooks</h3>

        {loading ? (
          <div className="text-center text-muted py-8">Loading...</div>
        ) : webhooks.length === 0 ? (
          <div className="text-center text-muted py-8">
            No webhooks configured. Add one to start receiving notifications.
          </div>
        ) : (
          <div className="space-y-4">
            {webhooks.map(webhook => (
              <div key={webhook.id} className="card p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <code className="text-sm bg-gray-100 px-2 py-1 rounded">{webhook.url}</code>
                      <span className={`badge ${webhook.is_active ? (webhook.is_healthy ? 'badge-success' : 'badge-warning') : 'badge-gray'}`}>
                        {webhook.is_active ? (webhook.is_healthy ? 'Healthy' : 'Unhealthy') : 'Paused'}
                      </span>
                    </div>
                    {webhook.description && (
                      <p className="text-muted text-sm">{webhook.description}</p>
                    )}
                  </div>
                  <div className="text-right text-sm">
                    <p className="text-muted">
                      Created: {new Date(webhook.created_at).toLocaleDateString()}
                    </p>
                    {webhook.last_success_at && (
                      <p className="text-success text-xs">
                        Last success: {new Date(webhook.last_success_at).toLocaleString()}
                      </p>
                    )}
                    {webhook.consecutive_failures > 0 && (
                      <p className="text-danger text-xs">
                        {webhook.consecutive_failures} consecutive failures
                      </p>
                    )}
                  </div>
                </div>

                <div className="mb-3">
                  <span className="text-muted text-sm">Events:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {(webhook.events || []).slice(0, 5).map(e => (
                      <span key={e} className="badge badge-info text-xs">{e}</span>
                    ))}
                    {(webhook.events || []).length > 5 && (
                      <span className="badge badge-secondary text-xs">
                        +{webhook.events.length - 5} more
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex gap-2 flex-wrap">
                  <button className="btn btn-sm btn-secondary" onClick={() => handleTest(webhook)}>
                    Test
                  </button>
                  <button className="btn btn-sm btn-secondary" onClick={() => handleViewDeliveries(webhook)}>
                    Deliveries
                  </button>
                  <button className="btn btn-sm btn-secondary" onClick={() => handleViewStats(webhook)}>
                    Stats
                  </button>
                  <button className="btn btn-sm btn-info" onClick={() => handleRotateSecret(webhook)}>
                    Rotate Secret
                  </button>
                  <button className="btn btn-sm btn-secondary" onClick={() => handleToggle(webhook)}>
                    {webhook.is_active ? 'Pause' : 'Enable'}
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(webhook)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {pagination.total > pagination.per_page && (
          <div className="flex justify-center gap-2 mt-4">
            <button
              className="btn btn-sm btn-secondary"
              disabled={pagination.page === 1}
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
            >
              Previous
            </button>
            <span className="flex items-center px-4">
              Page {pagination.page} of {Math.ceil(pagination.total / pagination.per_page)}
            </span>
            <button
              className="btn btn-sm btn-secondary"
              disabled={pagination.page >= Math.ceil(pagination.total / pagination.per_page)}
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Available Events Reference */}
      <div className="section mt-6">
        <h3 className="section-title">Available Events ({events.length})</h3>
        <div className="flex gap-2 mb-4 flex-wrap">
          <button
            className={`btn btn-sm ${!selectedCategory ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedCategory('')}
          >
            All
          </button>
          {categories.map(cat => (
            <button
              key={cat}
              className={`btn btn-sm ${selectedCategory === cat ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
        <div className="grid-3 gap-2">
          {filteredEvents.map(event => (
            <div key={event.event} className="p-2 border rounded text-sm">
              <code className="font-bold">{event.event}</code>
              <p className="text-muted text-xs mt-1">{event.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Create Webhook Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Webhook</h3>
              <button className="modal-close" onClick={() => setShowForm(false)}>×</button>
            </div>
            <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              <div className="form-group">
                <label className="form-label">Endpoint URL *</label>
                <input
                  type="url"
                  className="form-input"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  placeholder="https://your-server.com/webhook"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="What is this webhook for?"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Events *</label>
                <p className="text-muted text-sm mb-3">Select the events you want to receive</p>

                {Object.entries(eventsByCategory).map(([category, categoryEvents]) => (
                  <div key={category} className="p-3 border rounded mb-3">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-bold capitalize">{category}</h4>
                      <button
                        type="button"
                        className="btn btn-xs btn-secondary"
                        onClick={() => selectAllInCategory(category)}
                      >
                        {categoryEvents.every(e => formData.events.includes(e.event)) ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                    <div className="grid-2 gap-2">
                      {categoryEvents.map(event => (
                        <label key={event.event} className="checkbox-label flex items-start gap-2 p-2 border rounded hover:bg-gray-50">
                          <input
                            type="checkbox"
                            checked={formData.events.includes(event.event)}
                            onChange={() => toggleEvent(event.event)}
                            className="mt-1"
                          />
                          <div>
                            <code className="text-xs">{event.event}</code>
                            <p className="text-muted text-xs">{event.description}</p>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  <span>Active (start receiving events immediately)</span>
                </label>
              </div>

              <div className="p-3 bg-gray-50 rounded text-sm">
                <p className="font-bold mb-1">Webhook Security</p>
                <p className="text-muted">
                  A signing secret will be generated automatically. Use it to verify that webhook
                  payloads are from LogiAccounting. Check the <code>X-Webhook-Signature</code> header.
                </p>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleCreate}
                disabled={!formData.url || formData.events.length === 0}
              >
                Create Webhook
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deliveries Modal */}
      {showDeliveries && (
        <div className="modal-overlay" onClick={() => setShowDeliveries(null)}>
          <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Delivery History</h3>
              <button className="modal-close" onClick={() => setShowDeliveries(null)}>×</button>
            </div>
            <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              {deliveries.length === 0 ? (
                <div className="text-center text-muted py-8">No deliveries yet</div>
              ) : (
                <div className="space-y-3">
                  {deliveries.map(delivery => (
                    <div key={delivery.id} className="p-3 border rounded">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <span className="font-mono text-sm">{delivery.event}</span>
                          {getStatusBadge(delivery.status)}
                        </div>
                        <span className="text-muted text-xs">
                          {new Date(delivery.created_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="grid-4 text-sm">
                        <div>
                          <span className="text-muted">Attempts:</span>
                          <p>{delivery.attempt_count}/{delivery.max_attempts}</p>
                        </div>
                        <div>
                          <span className="text-muted">Response:</span>
                          <p>{delivery.response_status || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-muted">Response Time:</span>
                          <p>{delivery.response_time_ms ? `${delivery.response_time_ms}ms` : 'N/A'}</p>
                        </div>
                        <div>
                          {delivery.status === 'failed' && delivery.attempt_count < delivery.max_attempts && (
                            <button
                              className="btn btn-xs btn-warning"
                              onClick={() => handleRetryDelivery(showDeliveries.id, delivery.id)}
                            >
                              Retry Now
                            </button>
                          )}
                        </div>
                      </div>
                      {delivery.error_message && (
                        <p className="text-danger text-xs mt-2">{delivery.error_message}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowDeliveries(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stats Modal */}
      {showStats && stats && (
        <div className="modal-overlay" onClick={() => setShowStats(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Webhook Statistics</h3>
              <button className="modal-close" onClick={() => setShowStats(null)}>×</button>
            </div>
            <div className="modal-body">
              <div className="grid-2 gap-4 mb-4">
                <div className="stat-card">
                  <p className="stat-value">{stats.total_deliveries}</p>
                  <p className="stat-label">Total Deliveries</p>
                </div>
                <div className="stat-card">
                  <p className="stat-value text-success">{stats.success_rate}%</p>
                  <p className="stat-label">Success Rate</p>
                </div>
              </div>
              <div className="grid-3 gap-4 mb-4">
                <div className="text-center p-3 border rounded">
                  <p className="text-2xl font-bold text-success">{stats.successful}</p>
                  <p className="text-muted text-sm">Successful</p>
                </div>
                <div className="text-center p-3 border rounded">
                  <p className="text-2xl font-bold text-danger">{stats.failed}</p>
                  <p className="text-muted text-sm">Failed</p>
                </div>
                <div className="text-center p-3 border rounded">
                  <p className="text-2xl font-bold text-warning">{stats.pending}</p>
                  <p className="text-muted text-sm">Pending</p>
                </div>
              </div>
              <div className="grid-2 gap-4">
                <div>
                  <span className="text-muted text-sm">Avg Response Time:</span>
                  <p className="font-bold">{stats.avg_response_time_ms}ms</p>
                </div>
                <div>
                  <span className="text-muted text-sm">Period:</span>
                  <p className="font-bold">{stats.period_days} days</p>
                </div>
              </div>
              {stats.events_breakdown && Object.keys(stats.events_breakdown).length > 0 && (
                <div className="mt-4">
                  <span className="text-muted text-sm">Events Breakdown:</span>
                  <div className="mt-2 space-y-1">
                    {Object.entries(stats.events_breakdown).map(([event, count]) => (
                      <div key={event} className="flex justify-between text-sm">
                        <code>{event}</code>
                        <span>{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowStats(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
