import { useState, useEffect } from 'react';
import { paymentLinksAPI, gatewayAPI } from '../services/api';
import toast from '../utils/toast';

export default function PaymentLinks() {
  const [links, setLinks] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [gateways, setGateways] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedLink, setSelectedLink] = useState(null);
  const [filter, setFilter] = useState('all');

  const [newLink, setNewLink] = useState({
    payment_id: '',
    amount: '',
    currency: 'USD',
    description: '',
    client_name: '',
    client_email: '',
    invoice_number: '',
    gateways: ['stripe', 'paypal'],
    expires_in_days: 30,
    single_use: true,
    allow_partial: false,
    send_receipt: true
  });

  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [linksRes, statsRes, gatewaysRes] = await Promise.all([
        paymentLinksAPI.list({ status: filter === 'all' ? null : filter }),
        paymentLinksAPI.getStatistics(),
        gatewayAPI.list(true)
      ]);
      setLinks(linksRes.data.links);
      setStatistics(statsRes.data);
      setGateways(gatewaysRes.data.gateways);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      const data = {
        ...newLink,
        amount: parseFloat(newLink.amount),
        payment_id: newLink.payment_id || `PAY-${Date.now()}`
      };
      await paymentLinksAPI.create(data);
      setShowCreate(false);
      setNewLink({
        payment_id: '', amount: '', currency: 'USD', description: '',
        client_name: '', client_email: '', invoice_number: '',
        gateways: ['stripe', 'paypal'], expires_in_days: 30,
        single_use: true, allow_partial: false, send_receipt: true
      });
      loadData();
    } catch (err) {
      toast.error('Failed to create link');
    }
  };

  const handleCancel = async (linkId) => {
    if (!confirm('Cancel this payment link?')) return;
    try {
      await paymentLinksAPI.cancel(linkId);
      loadData();
    } catch (err) {
      toast.error('Failed to cancel');
    }
  };

  const handleSend = async (linkId) => {
    try {
      const res = await paymentLinksAPI.send(linkId);
      toast.success(`Link sent to ${res.data.sent_to}`);
    } catch (err) {
      toast.error('Failed to send: ' + (err.response?.data?.detail || err.message));
    }
  };

  const copyLink = (url) => {
    navigator.clipboard.writeText(url);
    toast.success('Link copied to clipboard!');
  };

  const getStatusBadge = (status) => {
    const badges = {
      active: 'badge-success',
      paid: 'badge-primary',
      expired: 'badge-warning',
      cancelled: 'badge-danger'
    };
    return <span className={`badge ${badges[status] || 'badge-gray'}`}>{status}</span>;
  };

  return (
    <>
      <div className="info-banner mb-6">
        🔗 Create payment links to collect payments from your clients online.
      </div>

      {/* Statistics */}
      {statistics && (
        <div className="stats-grid mb-6">
          <div className="stat-card">
            <div className="stat-icon">🔗</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.total_links}</div>
              <div className="stat-label">Total Links</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.by_status.paid}</div>
              <div className="stat-label">Paid</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">💰</div>
            <div className="stat-content">
              <div className="stat-value">${statistics.total_collected.toLocaleString()}</div>
              <div className="stat-label">Collected</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <div className="stat-value">{statistics.conversion_rate}%</div>
              <div className="stat-label">Conversion</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters & Actions */}
      <div className="section mb-6">
        <div className="flex justify-between items-center">
          <div className="flex gap-2">
            {['all', 'active', 'paid', 'expired', 'cancelled'].map(f => (
              <button
                key={f}
                className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setFilter(f)}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            ➕ Create Payment Link
          </button>
        </div>
      </div>

      {/* Links List */}
      <div className="section">
        {loading ? (
          <div className="text-center text-muted">Loading...</div>
        ) : links.length === 0 ? (
          <div className="text-center text-muted p-8">No payment links found</div>
        ) : (
          <div className="links-list">
            {links.map(link => (
              <div key={link.id} className="link-card">
                <div className="link-header">
                  <div className="link-amount">
                    ${link.amount.toLocaleString()} <span className="currency">{link.currency}</span>
                  </div>
                  {getStatusBadge(link.status)}
                </div>

                <div className="link-description">{link.description}</div>

                <div className="link-meta">
                  {link.client_name && <span>👤 {link.client_name}</span>}
                  {link.invoice_number && <span>📄 {link.invoice_number}</span>}
                  <span>👁️ {link.views} views</span>
                  <span>🔄 {link.attempts} attempts</span>
                </div>

                <div className="link-url">
                  <code>{link.url}</code>
                  <button className="btn btn-sm btn-secondary" onClick={() => copyLink(link.url)}>
                    📋 Copy
                  </button>
                </div>

                {link.status === 'paid' && (
                  <div className="link-paid-info">
                    ✅ Paid ${link.paid_amount} via {link.paid_via} on {new Date(link.paid_at).toLocaleDateString()}
                  </div>
                )}

                <div className="link-actions">
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => setSelectedLink(link)}
                  >
                    View Details
                  </button>
                  {link.status === 'active' && (
                    <>
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => handleSend(link.id)}
                      >
                        📧 Send
                      </button>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleCancel(link.id)}
                      >
                        Cancel
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal-content modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Payment Link</h3>
              <button className="modal-close" onClick={() => setShowCreate(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Amount *</label>
                  <input
                    type="number"
                    className="form-input"
                    value={newLink.amount}
                    onChange={(e) => setNewLink({ ...newLink, amount: e.target.value })}
                    placeholder="1500.00"
                    step="0.01"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Currency</label>
                  <select
                    className="form-select"
                    value={newLink.currency}
                    onChange={(e) => setNewLink({ ...newLink, currency: e.target.value })}
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                    <option value="ARS">ARS</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Description *</label>
                <input
                  type="text"
                  className="form-input"
                  value={newLink.description}
                  onChange={(e) => setNewLink({ ...newLink, description: e.target.value })}
                  placeholder="Invoice #INV-001 - Consulting Services"
                />
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Client Name</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newLink.client_name}
                    onChange={(e) => setNewLink({ ...newLink, client_name: e.target.value })}
                    placeholder="Acme Corp"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Client Email</label>
                  <input
                    type="email"
                    className="form-input"
                    value={newLink.client_email}
                    onChange={(e) => setNewLink({ ...newLink, client_email: e.target.value })}
                    placeholder="billing@acme.com"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Invoice Number</label>
                  <input
                    type="text"
                    className="form-input"
                    value={newLink.invoice_number}
                    onChange={(e) => setNewLink({ ...newLink, invoice_number: e.target.value })}
                    placeholder="INV-2025-001"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Expires In (days)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={newLink.expires_in_days}
                    onChange={(e) => setNewLink({ ...newLink, expires_in_days: parseInt(e.target.value) || 30 })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Payment Gateways</label>
                <div className="checkbox-group">
                  {gateways.map(gw => (
                    <label key={gw.provider} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={newLink.gateways.includes(gw.provider)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewLink({ ...newLink, gateways: [...newLink.gateways, gw.provider] });
                          } else {
                            setNewLink({ ...newLink, gateways: newLink.gateways.filter(g => g !== gw.provider) });
                          }
                        }}
                      />
                      {gw.icon} {gw.name}
                    </label>
                  ))}
                </div>
              </div>
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={newLink.single_use}
                    onChange={(e) => setNewLink({ ...newLink, single_use: e.target.checked })}
                  />
                  Single use (disable after payment)
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={newLink.send_receipt}
                    onChange={(e) => setNewLink({ ...newLink, send_receipt: e.target.checked })}
                  />
                  Send receipt email after payment
                </label>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleCreate}
                disabled={!newLink.amount || !newLink.description}
              >
                Create Link
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
