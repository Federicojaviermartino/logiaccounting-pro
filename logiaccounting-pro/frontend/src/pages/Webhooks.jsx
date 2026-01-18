import { useState, useEffect } from 'react';
import { webhookAPI } from '../services/api';

export default function Webhooks() {
  const [webhooks, setWebhooks] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showLogs, setShowLogs] = useState(null);
  const [logs, setLogs] = useState([]);
  const [formData, setFormData] = useState({ url: '', events: [], secret: '' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [webhooksRes, eventsRes] = await Promise.all([
        webhookAPI.list(),
        webhookAPI.getEvents()
      ]);
      setWebhooks(webhooksRes.data.webhooks);
      setEvents(eventsRes.data.events);
    } catch (err) {
      console.error('Failed to load webhooks:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await webhookAPI.create(formData);
      setShowForm(false);
      setFormData({ url: '', events: [], secret: '' });
      loadData();
    } catch (err) {
      alert('Failed to create webhook');
    }
  };

  const handleToggle = async (webhook) => {
    try {
      await webhookAPI.update(webhook.id, { active: !webhook.active });
      loadData();
    } catch (err) {
      alert('Failed to update webhook');
    }
  };

  const handleDelete = async (webhook) => {
    if (!confirm('Delete this webhook?')) return;
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
      alert(res.data.success ? 'Test successful!' : `Test failed: ${res.data.error || 'Unknown'}`);
    } catch (err) {
      alert('Test failed');
    }
  };

  const handleViewLogs = async (webhook) => {
    try {
      const res = await webhookAPI.getLogs(webhook.id);
      setLogs(res.data.logs);
      setShowLogs(webhook);
    } catch (err) {
      alert('Failed to load logs');
    }
  };

  const toggleEvent = (event) => {
    if (formData.events.includes(event)) {
      setFormData({ ...formData, events: formData.events.filter(e => e !== event) });
    } else {
      setFormData({ ...formData, events: [...formData.events, event] });
    }
  };

  return (
    <>
      <div className="info-banner mb-6">
        Configure webhooks to receive real-time notifications when events occur.
      </div>

      <div className="section mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="section-title" style={{ margin: 0 }}>Webhooks</h3>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>Add Webhook</button>
        </div>

        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : webhooks.length === 0 ? (
          <div className="text-center text-muted">No webhooks configured</div>
        ) : (
          <div className="webhooks-list">
            {webhooks.map(webhook => (
              <div key={webhook.id} className="webhook-card">
                <div className="webhook-header">
                  <div>
                    <code className="webhook-url">{webhook.url}</code>
                    <span className={`badge ${webhook.active ? 'badge-success' : 'badge-gray'}`}>
                      {webhook.active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="webhook-actions">
                    <button className="btn btn-sm btn-secondary" onClick={() => handleTest(webhook)}>Test</button>
                    <button className="btn btn-sm btn-secondary" onClick={() => handleViewLogs(webhook)}>Logs</button>
                    <button className="btn btn-sm btn-secondary" onClick={() => handleToggle(webhook)}>
                      {webhook.active ? 'Pause' : 'Enable'}
                    </button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(webhook)}>Delete</button>
                  </div>
                </div>
                <div className="webhook-events">
                  {webhook.events.map(e => <span key={e} className="event-tag">{e}</span>)}
                </div>
                <div className="webhook-stats">
                  <span>{webhook.success_count} success</span>
                  <span>{webhook.failure_count} failed</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Webhook</h3>
              <button className="modal-close" onClick={() => setShowForm(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Endpoint URL</label>
                <input
                  type="url"
                  className="form-input"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  placeholder="https://your-server.com/webhook"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Events</label>
                <div className="events-grid">
                  {events.map(event => (
                    <label key={event} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.events.includes(event)}
                        onChange={() => toggleEvent(event)}
                      />
                      <span>{event}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Secret (optional)</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.secret}
                  onChange={(e) => setFormData({ ...formData, secret: e.target.value })}
                  placeholder="Used to sign payloads"
                />
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

      {showLogs && (
        <div className="modal-overlay" onClick={() => setShowLogs(null)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Webhook Logs</h3>
              <button className="modal-close" onClick={() => setShowLogs(null)}>x</button>
            </div>
            <div className="modal-body">
              {logs.length === 0 ? (
                <div className="text-center text-muted">No logs</div>
              ) : (
                <div className="logs-list">
                  {logs.map(log => (
                    <div key={log.id} className={`log-item ${log.success ? 'success' : 'failed'}`}>
                      <div className="log-header">
                        <span className="log-event">{log.event}</span>
                        <span className={`badge ${log.success ? 'badge-success' : 'badge-danger'}`}>
                          {log.success ? 'Success' : 'Failed'}
                        </span>
                        <span className="log-time">{new Date(log.timestamp).toLocaleString()}</span>
                      </div>
                      <div className="log-details">
                        <span>Status: {log.response_status || 'N/A'}</span>
                        <span>Attempts: {log.attempts}</span>
                        {log.error && <span className="text-danger">Error: {log.error}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
