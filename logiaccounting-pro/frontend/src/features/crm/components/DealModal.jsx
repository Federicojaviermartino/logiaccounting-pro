/**
 * DealModal - Create/Edit deal modal
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  Building2,
  User,
  Calendar,
  DollarSign,
  Target,
  Save,
  Trash2,
  Trophy,
  XCircle,
} from 'lucide-react';
import { crmAPI } from '../../../services/api/crm';

export default function DealModal({
  deal,
  stageId,
  pipelineId,
  onClose,
  onSaved,
}) {
  const isEdit = !!deal;
  const [formData, setFormData] = useState({
    name: '',
    amount: '',
    probability: '',
    expected_close_date: '',
    contact_id: '',
    company_id: '',
    description: '',
    pipeline_id: pipelineId || '',
    stage_id: stageId || '',
  });
  const [contacts, setContacts] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [stages, setStages] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [showWinModal, setShowWinModal] = useState(false);
  const [showLoseModal, setShowLoseModal] = useState(false);
  const [winData, setWinData] = useState({ actual_amount: '', notes: '' });
  const [loseData, setLoseData] = useState({ lost_reason: '', competitor: '', notes: '' });

  useEffect(() => {
    loadData();
    if (deal) {
      setFormData({
        name: deal.name || '',
        amount: deal.amount || '',
        probability: deal.probability || '',
        expected_close_date: deal.expected_close_date?.split('T')[0] || '',
        contact_id: deal.contact_id || '',
        company_id: deal.company_id || '',
        description: deal.description || '',
        pipeline_id: deal.pipeline_id || pipelineId || '',
        stage_id: deal.stage_id || stageId || '',
      });
    }
  }, [deal]);

  const loadData = async () => {
    try {
      const [contactsRes, companiesRes, pipelineRes] = await Promise.all([
        crmAPI.contacts.list({ page_size: 100 }),
        crmAPI.companies.list({ page_size: 100 }),
        pipelineId ? crmAPI.pipelines.get(pipelineId) : Promise.resolve({ data: {} }),
      ]);

      setContacts(contactsRes.data?.items || []);
      setCompanies(companiesRes.data?.items || []);
      setStages(pipelineRes.data?.stages || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);

    try {
      const data = {
        ...formData,
        amount: parseFloat(formData.amount) || 0,
        probability: formData.probability ? parseInt(formData.probability) : undefined,
      };

      if (isEdit) {
        await crmAPI.opportunities.update(deal.id, data);
      } else {
        await crmAPI.opportunities.create(data);
      }

      onSaved?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save deal');
    } finally {
      setIsSaving(false);
    }
  };

  const handleWin = async () => {
    setIsSaving(true);
    try {
      await crmAPI.opportunities.win(deal.id, {
        actual_amount: parseFloat(winData.actual_amount) || undefined,
        notes: winData.notes || undefined,
      });
      onSaved?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to mark as won');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLose = async () => {
    setIsSaving(true);
    try {
      await crmAPI.opportunities.lose(deal.id, loseData);
      onSaved?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to mark as lost');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this deal?')) return;

    setIsSaving(true);
    try {
      await crmAPI.opportunities.delete(deal.id);
      onSaved?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete deal');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{isEdit ? 'Edit Deal' : 'New Deal'}</h2>
          <button className="close-btn" onClick={onClose}>
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {/* Deal Name */}
            <div className="form-group">
              <label>Deal Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Enterprise License - Acme Corp"
                required
              />
            </div>

            {/* Amount and Probability */}
            <div className="form-row">
              <div className="form-group">
                <label>Amount ($)</label>
                <div className="input-with-icon">
                  <DollarSign className="w-4 h-4" />
                  <input
                    type="number"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                    placeholder="0"
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Win Probability (%)</label>
                <div className="input-with-icon">
                  <Target className="w-4 h-4" />
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.probability}
                    onChange={(e) => setFormData({ ...formData, probability: e.target.value })}
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            {/* Expected Close Date */}
            <div className="form-group">
              <label>Expected Close Date</label>
              <div className="input-with-icon">
                <Calendar className="w-4 h-4" />
                <input
                  type="date"
                  value={formData.expected_close_date}
                  onChange={(e) => setFormData({ ...formData, expected_close_date: e.target.value })}
                />
              </div>
            </div>

            {/* Stage */}
            {stages.length > 0 && (
              <div className="form-group">
                <label>Stage</label>
                <select
                  value={formData.stage_id}
                  onChange={(e) => setFormData({ ...formData, stage_id: e.target.value })}
                >
                  <option value="">Select stage...</option>
                  {stages.map((stage) => (
                    <option key={stage.id} value={stage.id}>
                      {stage.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Contact */}
            <div className="form-group">
              <label>Contact</label>
              <div className="input-with-icon">
                <User className="w-4 h-4" />
                <select
                  value={formData.contact_id}
                  onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
                >
                  <option value="">Select contact...</option>
                  {contacts.map((contact) => (
                    <option key={contact.id} value={contact.id}>
                      {contact.first_name} {contact.last_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Company */}
            <div className="form-group">
              <label>Company</label>
              <div className="input-with-icon">
                <Building2 className="w-4 h-4" />
                <select
                  value={formData.company_id}
                  onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                >
                  <option value="">Select company...</option>
                  {companies.map((company) => (
                    <option key={company.id} value={company.id}>
                      {company.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Description */}
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Add notes about this deal..."
                rows={3}
              />
            </div>

            {error && <div className="error-message">{error}</div>}
          </div>

          <div className="modal-footer">
            {isEdit && (
              <div className="footer-left">
                <button
                  type="button"
                  className="btn-success"
                  onClick={() => setShowWinModal(true)}
                >
                  <Trophy className="w-4 h-4" />
                  Won
                </button>
                <button
                  type="button"
                  className="btn-danger"
                  onClick={() => setShowLoseModal(true)}
                >
                  <XCircle className="w-4 h-4" />
                  Lost
                </button>
                <button type="button" className="btn-ghost" onClick={handleDelete}>
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            )}
            <div className="footer-right">
              <button type="button" className="btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={isSaving}>
                <Save className="w-4 h-4" />
                {isSaving ? 'Saving...' : 'Save Deal'}
              </button>
            </div>
          </div>
        </form>

        {/* Win Modal */}
        {showWinModal && (
          <div className="sub-modal">
            <h3>Mark as Won</h3>
            <div className="form-group">
              <label>Final Amount ($)</label>
              <input
                type="number"
                value={winData.actual_amount}
                onChange={(e) => setWinData({ ...winData, actual_amount: e.target.value })}
                placeholder={formData.amount}
              />
            </div>
            <div className="form-group">
              <label>Notes</label>
              <textarea
                value={winData.notes}
                onChange={(e) => setWinData({ ...winData, notes: e.target.value })}
                rows={2}
              />
            </div>
            <div className="sub-modal-footer">
              <button className="btn-secondary" onClick={() => setShowWinModal(false)}>
                Cancel
              </button>
              <button className="btn-success" onClick={handleWin}>
                Confirm Won
              </button>
            </div>
          </div>
        )}

        {/* Lose Modal */}
        {showLoseModal && (
          <div className="sub-modal">
            <h3>Mark as Lost</h3>
            <div className="form-group">
              <label>Lost Reason</label>
              <select
                value={loseData.lost_reason}
                onChange={(e) => setLoseData({ ...loseData, lost_reason: e.target.value })}
              >
                <option value="">Select reason...</option>
                <option value="price">Price too high</option>
                <option value="competitor">Lost to competitor</option>
                <option value="no_budget">No budget</option>
                <option value="timing">Bad timing</option>
                <option value="no_decision">No decision made</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="form-group">
              <label>Competitor (if applicable)</label>
              <input
                type="text"
                value={loseData.competitor}
                onChange={(e) => setLoseData({ ...loseData, competitor: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Notes</label>
              <textarea
                value={loseData.notes}
                onChange={(e) => setLoseData({ ...loseData, notes: e.target.value })}
                rows={2}
              />
            </div>
            <div className="sub-modal-footer">
              <button className="btn-secondary" onClick={() => setShowLoseModal(false)}>
                Cancel
              </button>
              <button className="btn-danger" onClick={handleLose}>
                Confirm Lost
              </button>
            </div>
          </div>
        )}

        <style jsx>{`
          .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
          }

          .modal-content {
            background: var(--bg-primary);
            border-radius: 12px;
            width: 100%;
            max-width: 520px;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
          }

          .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 24px;
            border-bottom: 1px solid var(--border-color);
          }

          .modal-header h2 {
            margin: 0;
            font-size: 18px;
          }

          .close-btn {
            padding: 8px;
            border-radius: 6px;
            color: var(--text-muted);
          }

          .modal-body {
            padding: 24px;
          }

          .form-group {
            margin-bottom: 16px;
          }

          .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 6px;
          }

          .form-group input,
          .form-group select,
          .form-group textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
          }

          .input-with-icon {
            position: relative;
          }

          .input-with-icon svg {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
          }

          .input-with-icon input,
          .input-with-icon select {
            padding-left: 36px;
          }

          .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
          }

          .error-message {
            padding: 12px;
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            border-radius: 8px;
          }

          .modal-footer {
            display: flex;
            justify-content: space-between;
            padding: 16px 24px;
            border-top: 1px solid var(--border-color);
          }

          .footer-left, .footer-right {
            display: flex;
            gap: 8px;
          }

          .btn-secondary {
            padding: 10px 20px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
          }

          .btn-primary {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: var(--primary);
            color: white;
            border-radius: 8px;
          }

          .btn-success {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            background: #10b981;
            color: white;
            border-radius: 8px;
          }

          .btn-danger {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            background: #ef4444;
            color: white;
            border-radius: 8px;
          }

          .btn-ghost {
            padding: 10px;
            color: var(--text-muted);
            border-radius: 8px;
          }

          .sub-modal {
            position: absolute;
            inset: 0;
            background: var(--bg-primary);
            padding: 24px;
            border-radius: 12px;
          }

          .sub-modal h3 {
            margin: 0 0 16px;
          }

          .sub-modal-footer {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            margin-top: 24px;
          }
        `}</style>
      </div>
    </div>
  );
}
