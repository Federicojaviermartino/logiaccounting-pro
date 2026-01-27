/**
 * New Ticket - Create a support ticket
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Send, Paperclip, AlertCircle,
  CreditCard, Settings, HelpCircle, Lightbulb, Bug, User,
} from 'lucide-react';

const categoryIcons = {
  billing: CreditCard,
  technical: Settings,
  general: HelpCircle,
  feature_request: Lightbulb,
  bug_report: Bug,
  account: User,
};

export default function NewTicket() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [priorities, setPriorities] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    category: '',
    priority: 'normal',
    subject: '',
    description: '',
  });

  useEffect(() => {
    loadOptions();
  }, []);

  const loadOptions = async () => {
    // Simulated data - replace with API calls
    setCategories([
      { id: 'billing', name: 'Billing & Payments' },
      { id: 'technical', name: 'Technical Support' },
      { id: 'general', name: 'General Inquiry' },
      { id: 'feature_request', name: 'Feature Request' },
      { id: 'bug_report', name: 'Bug Report' },
      { id: 'account', name: 'Account Management' },
    ]);
    setPriorities([
      { id: 'low', name: 'Low', sla_hours: 48 },
      { id: 'normal', name: 'Normal', sla_hours: 24 },
      { id: 'high', name: 'High', sla_hours: 8 },
      { id: 'urgent', name: 'Urgent', sla_hours: 4 },
    ]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.category || !formData.subject || !formData.description) {
      setError('Please fill in all required fields');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      // API call would go here
      // const res = await portalAPI.createTicket(formData);
      // navigate(`/portal/support/${res.data.id}`);

      // For now, simulate success
      setTimeout(() => {
        navigate('/portal/support');
      }, 1000);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to create ticket');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="new-ticket">
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate('/portal/support')}>
          <ArrowLeft className="w-4 h-4" />
          Back to Tickets
        </button>
        <h1>Create Support Ticket</h1>
        <p>Describe your issue and we'll help you resolve it</p>
      </div>

      {error && (
        <div className="error-alert">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="ticket-form">
        {/* Category Selection */}
        <div className="form-section">
          <label>What do you need help with? *</label>
          <div className="category-grid">
            {categories.map((cat) => {
              const Icon = categoryIcons[cat.id] || HelpCircle;
              return (
                <button
                  key={cat.id}
                  type="button"
                  className={`category-option ${formData.category === cat.id ? 'selected' : ''}`}
                  onClick={() => setFormData({ ...formData, category: cat.id })}
                >
                  <Icon className="w-5 h-5" />
                  <span>{cat.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Priority */}
        <div className="form-section">
          <label>Priority</label>
          <div className="priority-options">
            {priorities.map((pri) => (
              <button
                key={pri.id}
                type="button"
                className={`priority-option ${formData.priority === pri.id ? 'selected' : ''}`}
                onClick={() => setFormData({ ...formData, priority: pri.id })}
              >
                <span className={`dot ${pri.id}`} />
                {pri.name}
                <span className="sla">({pri.sla_hours}h SLA)</span>
              </button>
            ))}
          </div>
        </div>

        {/* Subject */}
        <div className="form-section">
          <label>Subject *</label>
          <input
            type="text"
            placeholder="Brief description of your issue"
            value={formData.subject}
            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
            maxLength={200}
          />
        </div>

        {/* Description */}
        <div className="form-section">
          <label>Description *</label>
          <textarea
            placeholder="Please provide as much detail as possible about your issue..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={8}
          />
          <div className="char-count">{formData.description.length} characters</div>
        </div>

        {/* Attachments */}
        <div className="form-section">
          <label>Attachments (optional)</label>
          <div className="attachment-zone">
            <Paperclip className="w-5 h-5" />
            <span>Drag files here or click to upload</span>
            <span className="hint">Max 10MB per file. Supported: PDF, PNG, JPG, DOC</span>
          </div>
        </div>

        {/* Submit */}
        <div className="form-actions">
          <button type="button" className="btn-secondary" onClick={() => navigate('/portal/support')}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={isSubmitting}>
            <Send className="w-4 h-4" />
            {isSubmitting ? 'Submitting...' : 'Submit Ticket'}
          </button>
        </div>
      </form>

      <style jsx>{`
        .new-ticket {
          max-width: 800px;
          margin: 0 auto;
        }

        .page-header {
          margin-bottom: 32px;
        }

        .back-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #64748b;
          margin-bottom: 16px;
          background: none;
          border: none;
          cursor: pointer;
        }

        .page-header h1 {
          font-size: 24px;
          font-weight: 700;
          margin: 0;
        }

        .page-header p {
          color: #64748b;
          margin: 4px 0 0;
        }

        .error-alert {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.2);
          color: #dc2626;
          border-radius: 8px;
          margin-bottom: 24px;
        }

        .ticket-form {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 24px;
        }

        .form-section {
          margin-bottom: 24px;
        }

        .form-section label {
          display: block;
          font-weight: 500;
          margin-bottom: 10px;
        }

        .category-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
        }

        @media (max-width: 640px) {
          .category-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        .category-option {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 16px;
          background: #f8fafc;
          border: 2px solid transparent;
          border-radius: 10px;
          transition: all 0.2s;
          cursor: pointer;
        }

        .category-option:hover {
          background: #f1f5f9;
        }

        .category-option.selected {
          border-color: #3b82f6;
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .priority-options {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }

        .priority-option {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 16px;
          background: #f8fafc;
          border: 2px solid transparent;
          border-radius: 8px;
          cursor: pointer;
        }

        .priority-option.selected {
          border-color: #3b82f6;
          background: rgba(59, 130, 246, 0.1);
        }

        .priority-option .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .dot.low { background: #6b7280; }
        .dot.normal { background: #3b82f6; }
        .dot.high { background: #f59e0b; }
        .dot.urgent { background: #ef4444; }

        .priority-option .sla {
          font-size: 12px;
          color: #64748b;
        }

        .form-section input,
        .form-section textarea {
          width: 100%;
          padding: 12px 16px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          font-size: 15px;
        }

        .form-section textarea {
          resize: vertical;
          min-height: 120px;
        }

        .char-count {
          text-align: right;
          font-size: 12px;
          color: #64748b;
          margin-top: 4px;
        }

        .attachment-zone {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 32px;
          border: 2px dashed #e2e8f0;
          border-radius: 10px;
          color: #64748b;
          cursor: pointer;
        }

        .attachment-zone:hover {
          border-color: #3b82f6;
          background: rgba(59, 130, 246, 0.05);
        }

        .attachment-zone .hint {
          font-size: 12px;
        }

        .form-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding-top: 24px;
          border-top: 1px solid #e2e8f0;
        }

        .btn-secondary {
          padding: 10px 20px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #ffffff;
          cursor: pointer;
        }

        .btn-primary {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 24px;
          background: #3b82f6;
          color: white;
          border-radius: 8px;
          font-weight: 500;
          border: none;
          cursor: pointer;
        }

        .btn-primary:disabled {
          opacity: 0.7;
        }
      `}</style>
    </div>
  );
}
