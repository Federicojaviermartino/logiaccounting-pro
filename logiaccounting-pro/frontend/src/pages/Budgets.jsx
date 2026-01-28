import { useState, useEffect } from 'react';
import { budgetsAPI } from '../services/api';
import toast from '../utils/toast';

export default function Budgets() {
  const [loading, setLoading] = useState(true);
  const [budgets, setBudgets] = useState([]);
  const [variance, setVariance] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const [formData, setFormData] = useState({
    name: '',
    category_id: '',
    project_id: '',
    amount: 0,
    period: 'monthly',
    start_date: new Date().toISOString().split('T')[0],
    alerts: [{ threshold: 80 }, { threshold: 100 }]
  });

  const periods = [
    { value: 'monthly', label: 'Monthly' },
    { value: 'quarterly', label: 'Quarterly' },
    { value: 'yearly', label: 'Yearly' }
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [budgetsRes, varianceRes] = await Promise.all([
        budgetsAPI.getAll(),
        budgetsAPI.getVariance()
      ]);
      setBudgets(budgetsRes.data.budgets || []);
      setVariance(varianceRes.data);
    } catch (error) {
      console.error('Failed to load budgets:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      if (editingBudget) {
        await budgetsAPI.update(editingBudget.id, formData);
      } else {
        await budgetsAPI.create(formData);
      }
      setShowModal(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error('Failed to save budget: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (budget) => {
    setEditingBudget(budget);
    setFormData({
      name: budget.name,
      category_id: budget.category_id || '',
      project_id: budget.project_id || '',
      amount: budget.amount,
      period: budget.period,
      start_date: budget.start_date?.split('T')[0] || '',
      alerts: budget.alerts || [{ threshold: 80 }, { threshold: 100 }]
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this budget?')) return;
    try {
      await budgetsAPI.delete(id);
      loadData();
    } catch (error) {
      toast.error('Failed to delete budget');
    }
  };

  const resetForm = () => {
    setEditingBudget(null);
    setFormData({
      name: '',
      category_id: '',
      project_id: '',
      amount: 0,
      period: 'monthly',
      start_date: new Date().toISOString().split('T')[0],
      alerts: [{ threshold: 80 }, { threshold: 100 }]
    });
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 100) return 'bg-danger';
    if (percentage >= 80) return 'bg-warning';
    return 'bg-success';
  };

  const getStatusBadge = (budget) => {
    const percentage = budget.spent_percentage || 0;
    if (percentage >= 100) return <span className="badge badge-danger">Over Budget</span>;
    if (percentage >= 80) return <span className="badge badge-warning">Near Limit</span>;
    return <span className="badge badge-success">On Track</span>;
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading budgets...</p>
      </div>
    );
  }

  const totalBudget = budgets.reduce((sum, b) => sum + (b.amount || 0), 0);
  const totalSpent = budgets.reduce((sum, b) => sum + (b.spent || 0), 0);
  const totalRemaining = totalBudget - totalSpent;
  const overBudgetCount = budgets.filter(b => (b.spent_percentage || 0) >= 100).length;

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Budget Management</h1>
          <p className="text-muted">Plan and track spending by category and project</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            resetForm();
            setShowModal(true);
          }}
        >
          + New Budget
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid-4 mb-6">
        <div className="stat-card">
          <div className="stat-icon blue">💰</div>
          <div>
            <p className="stat-value">${totalBudget.toLocaleString()}</p>
            <p className="stat-label">Total Budget</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon orange">📉</div>
          <div>
            <p className="stat-value">${totalSpent.toLocaleString()}</p>
            <p className="stat-label">Total Spent</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✓</div>
          <div>
            <p className="stat-value">${totalRemaining.toLocaleString()}</p>
            <p className="stat-label">Remaining</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon red">⚠</div>
          <div>
            <p className="stat-value">{overBudgetCount}</p>
            <p className="stat-label">Over Budget</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="section mb-6">
        <div className="flex gap-2">
          <button
            className={`btn ${activeTab === 'overview' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('overview')}
          >
            Budget Overview
          </button>
          <button
            className={`btn ${activeTab === 'variance' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('variance')}
          >
            Variance Analysis
          </button>
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="section">
          <h3 className="section-title">Active Budgets</h3>
          {budgets.length === 0 ? (
            <p className="text-muted text-center py-8">
              No budgets configured. Create one to start tracking your spending.
            </p>
          ) : (
            <div className="space-y-4">
              {budgets.map((budget) => (
                <div key={budget.id} className="card p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-bold flex items-center gap-2">
                        {budget.name}
                        {getStatusBadge(budget)}
                      </h4>
                      <p className="text-muted text-sm">
                        {budget.period} | {budget.category_id || 'General'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-lg">
                        ${budget.spent?.toLocaleString() || 0} / ${budget.amount?.toLocaleString()}
                      </p>
                      <p className="text-muted text-sm">
                        {budget.spent_percentage?.toFixed(1) || 0}% used
                      </p>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="progress-bar">
                      <div
                        className={`progress-fill ${getProgressColor(budget.spent_percentage || 0)}`}
                        style={{ width: `${Math.min(budget.spent_percentage || 0, 100)}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="grid-3 mb-4 text-sm">
                    <div>
                      <span className="text-muted">Remaining:</span>
                      <p className={budget.remaining < 0 ? 'text-danger font-bold' : ''}>
                        ${budget.remaining?.toLocaleString() || budget.amount}
                      </p>
                    </div>
                    <div>
                      <span className="text-muted">Period Start:</span>
                      <p>{budget.start_date ? new Date(budget.start_date).toLocaleDateString() : '-'}</p>
                    </div>
                    <div>
                      <span className="text-muted">Alerts:</span>
                      <p>
                        {budget.alerts?.map(a => `${a.threshold}%`).join(', ') || 'None'}
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => handleEdit(budget)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => handleDelete(budget.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Variance Analysis Tab */}
      {activeTab === 'variance' && (
        <div className="section">
          <h3 className="section-title">Variance Analysis</h3>
          {!variance || !variance.budgets?.length ? (
            <p className="text-muted text-center py-8">
              No variance data available. Add budgets and transactions to see analysis.
            </p>
          ) : (
            <>
              <div className="mb-6">
                <div className="grid-3">
                  <div className="card p-4 text-center">
                    <p className="text-2xl font-bold">${variance.total_budget?.toLocaleString() || 0}</p>
                    <p className="text-muted">Total Budget</p>
                  </div>
                  <div className="card p-4 text-center">
                    <p className="text-2xl font-bold">${variance.total_actual?.toLocaleString() || 0}</p>
                    <p className="text-muted">Total Actual</p>
                  </div>
                  <div className="card p-4 text-center">
                    <p className={`text-2xl font-bold ${(variance.total_variance || 0) < 0 ? 'text-danger' : 'text-success'}`}>
                      ${Math.abs(variance.total_variance || 0).toLocaleString()}
                      {(variance.total_variance || 0) < 0 ? ' over' : ' under'}
                    </p>
                    <p className="text-muted">Total Variance</p>
                  </div>
                </div>
              </div>

              <table className="table">
                <thead>
                  <tr>
                    <th>Budget</th>
                    <th>Budgeted</th>
                    <th>Actual</th>
                    <th>Variance</th>
                    <th>Variance %</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {variance.budgets?.map((item) => (
                    <tr key={item.id}>
                      <td className="font-bold">{item.name}</td>
                      <td>${item.budget?.toLocaleString()}</td>
                      <td>${item.actual?.toLocaleString()}</td>
                      <td className={item.variance < 0 ? 'text-danger' : 'text-success'}>
                        ${Math.abs(item.variance || 0).toLocaleString()}
                        {item.variance < 0 ? ' over' : ' under'}
                      </td>
                      <td>{Math.abs(item.variance_percentage || 0).toFixed(1)}%</td>
                      <td>
                        {item.variance < 0 ? (
                          <span className="badge badge-danger">Over Budget</span>
                        ) : (
                          <span className="badge badge-success">Under Budget</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingBudget ? 'Edit Budget' : 'New Budget'}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Budget Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Marketing Q1 2025"
                />
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Amount *</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-input"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Period</label>
                  <select
                    className="form-select"
                    value={formData.period}
                    onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                  >
                    {periods.map(p => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Category ID (optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.category_id}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                    placeholder="e.g., marketing"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Project ID (optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.project_id}
                    onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                    placeholder="e.g., PRJ-001"
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Start Date *</label>
                <input
                  type="date"
                  className="form-input"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Alert Thresholds (%)</label>
                <div className="flex gap-2">
                  {formData.alerts.map((alert, idx) => (
                    <input
                      key={idx}
                      type="number"
                      min="0"
                      max="200"
                      className="form-input"
                      style={{ width: '80px' }}
                      value={alert.threshold}
                      onChange={(e) => {
                        const newAlerts = [...formData.alerts];
                        newAlerts[idx] = { threshold: parseInt(e.target.value) };
                        setFormData({ ...formData, alerts: newAlerts });
                      }}
                    />
                  ))}
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={() => setFormData({
                      ...formData,
                      alerts: [...formData.alerts, { threshold: 90 }]
                    })}
                  >
                    +
                  </button>
                </div>
                <p className="text-muted text-sm mt-1">Get notified when spending reaches these percentages</p>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleSubmit}>
                {editingBudget ? 'Update' : 'Create'} Budget
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
