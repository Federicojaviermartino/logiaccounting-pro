import { useState, useEffect } from 'react';
import { transactionsAPI, inventoryAPI, projectsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import toast from '../utils/toast';

export default function Transactions() {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [projects, setProjects] = useState([]);
  const [filters, setFilters] = useState({ type: '', category_id: '' });
  const [modalOpen, setModalOpen] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [filters]);

  const loadData = async () => {
    try {
      const [transRes, catIncRes, catExpRes, projRes] = await Promise.all([
        transactionsAPI.getTransactions(filters),
        inventoryAPI.getCategories('income'),
        inventoryAPI.getCategories('expense'),
        projectsAPI.getProjects({})
      ]);
      setTransactions(transRes.data.transactions || []);
      setCategories([...(catIncRes.data || []), ...(catExpRes.data || [])]);
      setProjects(projRes.data.projects || []);
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setLoading(false);
    }
  };

  const openModal = (item = null) => {
    setEditItem(item);
    setFormData(item || {
      type: 'income', category_id: '', project_id: '', amount: '',
      tax_amount: 0, description: '', date: new Date().toISOString().split('T')[0], invoice_number: ''
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = { ...formData, amount: parseFloat(formData.amount), tax_amount: parseFloat(formData.tax_amount || 0) };
      if (editItem) {
        await transactionsAPI.updateTransaction(editItem.id, data);
      } else {
        await transactionsAPI.createTransaction(data);
      }
      setModalOpen(false);
      loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save transaction');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this transaction?')) return;
    try {
      await transactionsAPI.deleteTransaction(id);
      loadData();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);

  const totals = {
    income: transactions.filter(t => t.type === 'income').reduce((sum, t) => sum + t.amount, 0),
    expense: transactions.filter(t => t.type === 'expense').reduce((sum, t) => sum + t.amount, 0)
  };

  if (loading) return <div className="text-center text-muted">Loading...</div>;

  return (
    <>
      <div className="stats-grid mb-6">
        <div className="stat-card">
          <span className="stat-icon">💵</span>
          <div className="stat-content">
            <div className="stat-label">Total Income</div>
            <div className="stat-value success">{formatCurrency(totals.income)}</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">💸</span>
          <div className="stat-content">
            <div className="stat-label">Total Expenses</div>
            <div className="stat-value danger">{formatCurrency(totals.expense)}</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">📊</span>
          <div className="stat-content">
            <div className="stat-label">Net Balance</div>
            <div className={`stat-value ${totals.income - totals.expense >= 0 ? 'success' : 'danger'}`}>
              {formatCurrency(totals.income - totals.expense)}
            </div>
          </div>
        </div>
      </div>

      <div className="toolbar">
        <select className="form-select" value={filters.type} onChange={(e) => setFilters({ ...filters, type: e.target.value })}>
          <option value="">All Types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
        <select className="form-select" value={filters.category_id} onChange={(e) => setFilters({ ...filters, category_id: e.target.value })}>
          <option value="">All Categories</option>
          {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <button className="btn btn-primary" onClick={() => openModal()}>+ New Transaction</button>
      </div>

      <div className="section">
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Category</th>
                <th>Description</th>
                <th>Amount</th>
                <th>Tax</th>
                <th>Project</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {transactions.length === 0 ? (
                <tr className="empty-row"><td colSpan="8">No transactions found</td></tr>
              ) : transactions.map(t => (
                <tr key={t.id}>
                  <td>{t.date ? new Date(t.date).toLocaleDateString() : '-'}</td>
                  <td>
                    <span className={`badge badge-${t.type === 'income' ? 'success' : 'danger'}`}>
                      {t.type}
                    </span>
                  </td>
                  <td>{t.category_name || '-'}</td>
                  <td>{t.description || '-'}</td>
                  <td className={`font-bold ${t.type === 'income' ? 'text-success' : 'text-danger'}`}>
                    {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                  </td>
                  <td className="font-mono">{formatCurrency(t.tax_amount)}</td>
                  <td>{t.project_code || '-'}</td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => openModal(t)}>Edit</button>
                    {user?.role === 'admin' && (
                      <button className="btn btn-danger btn-sm ml-2" onClick={() => handleDelete(t.id)}>Delete</button>
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
              <h3 className="modal-title">{editItem ? 'Edit Transaction' : 'New Transaction'}</h3>
              <button className="modal-close" onClick={() => setModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Type *</label>
                    <select className="form-select" value={formData.type || 'income'} onChange={(e) => setFormData({ ...formData, type: e.target.value })} required>
                      <option value="income">Income</option>
                      <option value="expense">Expense</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Date *</label>
                    <input type="date" className="form-input" value={formData.date?.split('T')[0] || ''} onChange={(e) => setFormData({ ...formData, date: e.target.value })} required />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Category</label>
                    <select className="form-select" value={formData.category_id || ''} onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}>
                      <option value="">Select</option>
                      {categories.filter(c => c.type === formData.type).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Project</label>
                    <select className="form-select" value={formData.project_id || ''} onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}>
                      <option value="">None</option>
                      {projects.map(p => <option key={p.id} value={p.id}>{p.code} - {p.name}</option>)}
                    </select>
                  </div>
                </div>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Amount *</label>
                    <input type="number" step="0.01" className="form-input" value={formData.amount || ''} onChange={(e) => setFormData({ ...formData, amount: e.target.value })} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Tax Amount</label>
                    <input type="number" step="0.01" className="form-input" value={formData.tax_amount || 0} onChange={(e) => setFormData({ ...formData, tax_amount: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea className="form-textarea" rows="2" value={formData.description || ''} onChange={(e) => setFormData({ ...formData, description: e.target.value })} />
                </div>
                <div className="form-group">
                  <label className="form-label">Invoice Number</label>
                  <input className="form-input" value={formData.invoice_number || ''} onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })} />
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
