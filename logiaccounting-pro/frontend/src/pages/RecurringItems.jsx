import { useState, useEffect } from 'react';
import { recurringAPI } from '../services/api';
import toast from '../utils/toast';

export default function RecurringItems() {
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [previewOccurrences, setPreviewOccurrences] = useState([]);

  const [formData, setFormData] = useState({
    name: '',
    type: 'transaction',
    template_data: {
      type: 'expense',
      category: 'Utilities',
      amount: 0,
      description: ''
    },
    frequency: 'monthly',
    day_of_month: 1,
    day_of_week: 0,
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    active: true
  });

  const frequencies = [
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'quarterly', label: 'Quarterly' },
    { value: 'yearly', label: 'Yearly' }
  ];

  const daysOfWeek = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
  ];

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await recurringAPI.getAll();
      setTemplates(response.data.templates || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      if (editingTemplate) {
        await recurringAPI.update(editingTemplate.id, formData);
      } else {
        await recurringAPI.create(formData);
      }
      setShowModal(false);
      resetForm();
      loadTemplates();
    } catch (error) {
      toast.error('Failed to save template: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    setFormData({
      name: template.name,
      type: template.type,
      template_data: template.template_data,
      frequency: template.frequency,
      day_of_month: template.day_of_month || 1,
      day_of_week: template.day_of_week || 0,
      start_date: template.start_date?.split('T')[0] || '',
      end_date: template.end_date?.split('T')[0] || '',
      active: template.active
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this template?')) return;
    try {
      await recurringAPI.delete(id);
      loadTemplates();
    } catch (error) {
      toast.error('Failed to delete template');
    }
  };

  const handleToggleActive = async (template) => {
    try {
      if (template.active) {
        await recurringAPI.pause(template.id);
      } else {
        await recurringAPI.resume(template.id);
      }
      loadTemplates();
    } catch (error) {
      toast.error('Failed to update template status');
    }
  };

  const handlePreview = async (templateId) => {
    try {
      const response = await recurringAPI.preview(templateId, 5);
      setPreviewOccurrences(response.data.occurrences || []);
    } catch (error) {
      toast.error('Failed to load preview');
    }
  };

  const handleGenerateNow = async (templateId) => {
    try {
      await recurringAPI.generateNow(templateId);
      toast.success('Transaction generated successfully!');
      loadTemplates();
    } catch (error) {
      toast.error('Failed to generate transaction: ' + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setEditingTemplate(null);
    setFormData({
      name: '',
      type: 'transaction',
      template_data: {
        type: 'expense',
        category: 'Utilities',
        amount: 0,
        description: ''
      },
      frequency: 'monthly',
      day_of_month: 1,
      day_of_week: 0,
      start_date: new Date().toISOString().split('T')[0],
      end_date: '',
      active: true
    });
    setPreviewOccurrences([]);
  };

  const getFrequencyLabel = (freq) => {
    return frequencies.find(f => f.value === freq)?.label || freq;
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading recurring items...</p>
      </div>
    );
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Recurring Transactions</h1>
          <p className="text-muted">Automate repeating transactions and payments</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            resetForm();
            setShowModal(true);
          }}
        >
          + New Template
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid-4 mb-6">
        <div className="stat-card">
          <div className="stat-icon blue">🔄</div>
          <div>
            <p className="stat-value">{templates.length}</p>
            <p className="stat-label">Total Templates</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✓</div>
          <div>
            <p className="stat-value">{templates.filter(t => t.active).length}</p>
            <p className="stat-label">Active</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon yellow">⏸</div>
          <div>
            <p className="stat-value">{templates.filter(t => !t.active).length}</p>
            <p className="stat-label">Paused</p>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon purple">📅</div>
          <div>
            <p className="stat-value">
              {templates.filter(t => t.active && t.next_occurrence).length}
            </p>
            <p className="stat-label">Scheduled</p>
          </div>
        </div>
      </div>

      {/* Templates List */}
      <div className="section">
        <h3 className="section-title">Recurring Templates</h3>
        {templates.length === 0 ? (
          <p className="text-muted text-center py-8">
            No recurring templates yet. Create one to automate your transactions.
          </p>
        ) : (
          <div className="space-y-4">
            {templates.map((template) => (
              <div key={template.id} className="card p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-bold flex items-center gap-2">
                      {template.name}
                      <span className={`badge ${template.active ? 'badge-success' : 'badge-secondary'}`}>
                        {template.active ? 'Active' : 'Paused'}
                      </span>
                    </h4>
                    <p className="text-muted text-sm">{template.type}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg">
                      ${template.template_data?.amount?.toLocaleString() || 0}
                    </p>
                    <p className="text-muted text-sm">{getFrequencyLabel(template.frequency)}</p>
                  </div>
                </div>

                <div className="grid-3 mb-4 text-sm">
                  <div>
                    <span className="text-muted">Category:</span>
                    <p>{template.template_data?.category || '-'}</p>
                  </div>
                  <div>
                    <span className="text-muted">Next Occurrence:</span>
                    <p>
                      {template.next_occurrence
                        ? new Date(template.next_occurrence).toLocaleDateString()
                        : '-'}
                    </p>
                  </div>
                  <div>
                    <span className="text-muted">Generated:</span>
                    <p>{template.generated_count || 0} times</p>
                  </div>
                </div>

                {template.template_data?.description && (
                  <p className="text-muted text-sm mb-4">{template.template_data.description}</p>
                )}

                <div className="flex gap-2 flex-wrap">
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => handleEdit(template)}
                  >
                    Edit
                  </button>
                  <button
                    className={`btn btn-sm ${template.active ? 'btn-warning' : 'btn-success'}`}
                    onClick={() => handleToggleActive(template)}
                  >
                    {template.active ? 'Pause' : 'Resume'}
                  </button>
                  <button
                    className="btn btn-sm btn-info"
                    onClick={() => handlePreview(template.id)}
                  >
                    Preview
                  </button>
                  <button
                    className="btn btn-sm btn-primary"
                    onClick={() => handleGenerateNow(template.id)}
                    disabled={!template.active}
                  >
                    Generate Now
                  </button>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => handleDelete(template.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {previewOccurrences.length > 0 && (
        <div className="modal-overlay" onClick={() => setPreviewOccurrences([])}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Upcoming Occurrences</h3>
              <button className="modal-close" onClick={() => setPreviewOccurrences([])}>×</button>
            </div>
            <div className="modal-body">
              <ul className="space-y-2">
                {previewOccurrences.map((date, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <span className="text-primary">📅</span>
                    {new Date(date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </li>
                ))}
              </ul>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setPreviewOccurrences([])}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingTemplate ? 'Edit Template' : 'New Recurring Template'}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="grid-2 mb-4">
                <div className="form-group">
                  <label className="form-label">Template Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Monthly Rent"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Type</label>
                  <select
                    className="form-select"
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  >
                    <option value="transaction">Transaction</option>
                    <option value="payment">Payment</option>
                  </select>
                </div>
              </div>

              <h4 className="font-bold mb-3">Transaction Details</h4>
              <div className="grid-2 mb-4">
                <div className="form-group">
                  <label className="form-label">Transaction Type</label>
                  <select
                    className="form-select"
                    value={formData.template_data.type}
                    onChange={(e) => setFormData({
                      ...formData,
                      template_data: { ...formData.template_data, type: e.target.value }
                    })}
                  >
                    <option value="expense">Expense</option>
                    <option value="income">Income</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Amount *</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-input"
                    value={formData.template_data.amount}
                    onChange={(e) => setFormData({
                      ...formData,
                      template_data: { ...formData.template_data, amount: parseFloat(e.target.value) }
                    })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Category</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.template_data.category}
                    onChange={(e) => setFormData({
                      ...formData,
                      template_data: { ...formData.template_data, category: e.target.value }
                    })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.template_data.description}
                    onChange={(e) => setFormData({
                      ...formData,
                      template_data: { ...formData.template_data, description: e.target.value }
                    })}
                  />
                </div>
              </div>

              <h4 className="font-bold mb-3">Schedule</h4>
              <div className="grid-2 mb-4">
                <div className="form-group">
                  <label className="form-label">Frequency *</label>
                  <select
                    className="form-select"
                    value={formData.frequency}
                    onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                  >
                    {frequencies.map(f => (
                      <option key={f.value} value={f.value}>{f.label}</option>
                    ))}
                  </select>
                </div>

                {formData.frequency === 'weekly' && (
                  <div className="form-group">
                    <label className="form-label">Day of Week</label>
                    <select
                      className="form-select"
                      value={formData.day_of_week}
                      onChange={(e) => setFormData({ ...formData, day_of_week: parseInt(e.target.value) })}
                    >
                      {daysOfWeek.map((day, idx) => (
                        <option key={idx} value={idx}>{day}</option>
                      ))}
                    </select>
                  </div>
                )}

                {(formData.frequency === 'monthly' || formData.frequency === 'quarterly' || formData.frequency === 'yearly') && (
                  <div className="form-group">
                    <label className="form-label">Day of Month</label>
                    <input
                      type="number"
                      min="1"
                      max="31"
                      className="form-input"
                      value={formData.day_of_month}
                      onChange={(e) => setFormData({ ...formData, day_of_month: parseInt(e.target.value) })}
                    />
                  </div>
                )}
              </div>

              <div className="grid-2 mb-4">
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
                  <label className="form-label">End Date (optional)</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  />
                </div>
              </div>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.active}
                  onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                />
                <span>Active (generate transactions automatically)</span>
              </label>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleSubmit}>
                {editingTemplate ? 'Update' : 'Create'} Template
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
