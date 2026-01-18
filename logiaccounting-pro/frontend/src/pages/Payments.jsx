import { useState, useEffect } from 'react';
import { paymentsAPI, projectsAPI, authAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

export default function Payments() {
  const { user } = useAuth();
  const [payments, setPayments] = useState([]);
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [filters, setFilters] = useState({ payment_status: '', type: '' });
  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [filters]);

  const loadData = async () => {
    try {
      const requests = [
        paymentsAPI.getPayments(filters),
        projectsAPI.getProjects({})
      ];
      if (user?.role === 'admin') {
        requests.push(authAPI.getUsers());
      }
      const results = await Promise.all(requests);
      setPayments(results[0].data.payments || []);
      setProjects(results[1].data.projects || []);
      if (user?.role === 'admin') {
        setUsers(results[2].data || []);
      }
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setLoading(false);
    }
  };

  const openModal = (item = null) => {
    setEditItem(item);
    const today = new Date();
    const nextWeek = new Date(today.setDate(today.getDate() + 7));
    setFormData(item || {
      type: 'payable', amount: '', due_date: nextWeek.toISOString().split('T')[0],
      description: '', reference: '', project_id: '', supplier_id: '', client_id: ''
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = { ...formData, amount: parseFloat(formData.amount) };
      if (editItem) {
        await paymentsAPI.updatePayment(editItem.id, data);
      } else {
        await paymentsAPI.createPayment(data);
      }
      setModalOpen(false);
      loadData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to save payment');
    }
  };

  const markAsPaid = async (id) => {
    if (!window.confirm('Confirm payment? All parties will be notified.')) return;
    try {
      await paymentsAPI.markAsPaid(id, new Date().toISOString());
      alert('Payment confirmed! Notifications sent to all parties.');
      loadData();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to mark as paid');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this payment?')) return;
    try {
      await paymentsAPI.deletePayment(id);
      loadData();
    } catch (error) {
      alert('Failed to delete');
    }
  };

  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);

  const getStatusBadge = (status) => {
    const colors = { paid: 'success', pending: 'warning', overdue: 'danger' };
    return colors[status] || 'gray';
  };

  const summary = {
    pending: payments.filter(p => p.status === 'pending').reduce((sum, p) => sum + p.amount, 0),
    overdue: payments.filter(p => p.status === 'overdue').reduce((sum, p) => sum + p.amount, 0),
    paid: payments.filter(p => p.status === 'paid').reduce((sum, p) => sum + p.amount, 0)
  };

  if (loading) return <div className="text-center text-muted">Loading...</div>;

  return (
    <>
      <div className="stats-grid mb-6">
        <div className="stat-card">
          <span className="stat-icon">⏳</span>
          <div className="stat-content">
            <div className="stat-label">Pending</div>
            <div className="stat-value warning">{formatCurrency(summary.pending)}</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">⚠️</span>
          <div className="stat-content">
            <div className="stat-label">Overdue</div>
            <div className="stat-value danger">{formatCurrency(summary.overdue)}</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">✅</span>
          <div className="stat-content">
            <div className="stat-label">Paid</div>
            <div className="stat-value success">{formatCurrency(summary.paid)}</div>
          </div>
        </div>
      </div>

      <div className="toolbar">
        <select className="form-select" value={filters.payment_status} onChange={(e) => setFilters({ ...filters, payment_status: e.target.value })}>
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="overdue">Overdue</option>
          <option value="paid">Paid</option>
        </select>
        <select className="form-select" value={filters.type} onChange={(e) => setFilters({ ...filters, type: e.target.value })}>
          <option value="">All Types</option>
          <option value="payable">Payable</option>
          <option value="receivable">Receivable</option>
        </select>
        <button className="btn btn-primary" onClick={() => openModal()}>+ New Payment</button>
      </div>

      <div className="section">
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Amount</th>
                <th>Due Date</th>
                <th>Status</th>
                <th>Description</th>
                <th>Party</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {payments.length === 0 ? (
                <tr className="empty-row"><td colSpan="7">No payments found</td></tr>
              ) : payments.map(p => (
                <tr key={p.id}>
                  <td>
                    <span className={`badge badge-${p.type === 'payable' ? 'danger' : 'success'}`}>
                      {p.type}
                    </span>
                  </td>
                  <td className="font-bold">{formatCurrency(p.amount)}</td>
                  <td>{new Date(p.due_date).toLocaleDateString()}</td>
                  <td>
                    <span className={`badge badge-${getStatusBadge(p.status)}`}>
                      {p.status}
                    </span>
                    {p.is_overdue && p.days_until_due !== null && (
                      <small className="text-danger ml-2">({Math.abs(p.days_until_due)} days late)</small>
                    )}
                  </td>
                  <td>{p.description || '-'}</td>
                  <td>{p.supplier_name || p.client_name || '-'}</td>
                  <td>
                    {p.status !== 'paid' && (
                      <button className="btn btn-success btn-sm" onClick={() => markAsPaid(p.id)}>Mark Paid</button>
                    )}
                    {user?.role === 'admin' && p.status !== 'paid' && (
                      <>
                        <button className="btn btn-secondary btn-sm ml-2" onClick={() => openModal(p)}>Edit</button>
                        <button className="btn btn-danger btn-sm ml-2" onClick={() => handleDelete(p.id)}>Delete</button>
                      </>
                    )}
                    {p.status === 'paid' && (
                      <span className="text-success">✓ Paid {p.paid_date ? new Date(p.paid_date).toLocaleDateString() : ''}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{editItem ? 'Edit Payment' : 'New Payment'}</h3>
              <button className="modal-close" onClick={() => setModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Type *</label>
                    <select className="form-select" value={formData.type || 'payable'} onChange={(e) => setFormData({ ...formData, type: e.target.value })} required>
                      <option value="payable">Payable (We pay)</option>
                      <option value="receivable">Receivable (We receive)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Amount *</label>
                    <input type="number" step="0.01" className="form-input" value={formData.amount || ''} onChange={(e) => setFormData({ ...formData, amount: e.target.value })} required />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Due Date *</label>
                    <input type="date" className="form-input" value={formData.due_date?.split('T')[0] || ''} onChange={(e) => setFormData({ ...formData, due_date: e.target.value })} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Reference</label>
                    <input className="form-input" value={formData.reference || ''} onChange={(e) => setFormData({ ...formData, reference: e.target.value })} placeholder="Invoice #, PO #" />
                  </div>
                </div>
                {user?.role === 'admin' && (
                  <div className="grid-2">
                    <div className="form-group">
                      <label className="form-label">Supplier</label>
                      <select className="form-select" value={formData.supplier_id || ''} onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })}>
                        <option value="">None</option>
                        {users.filter(u => u.role === 'supplier').map(u => <option key={u.id} value={u.id}>{u.company_name || `${u.first_name} ${u.last_name}`}</option>)}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Client</label>
                      <select className="form-select" value={formData.client_id || ''} onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}>
                        <option value="">None</option>
                        {users.filter(u => u.role === 'client').map(u => <option key={u.id} value={u.id}>{u.company_name || `${u.first_name} ${u.last_name}`}</option>)}
                      </select>
                    </div>
                  </div>
                )}
                <div className="form-group">
                  <label className="form-label">Project</label>
                  <select className="form-select" value={formData.project_id || ''} onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}>
                    <option value="">None</option>
                    {projects.map(p => <option key={p.id} value={p.id}>{p.code} - {p.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea className="form-textarea" rows="2" value={formData.description || ''} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
