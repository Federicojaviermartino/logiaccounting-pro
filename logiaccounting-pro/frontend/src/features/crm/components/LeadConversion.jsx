/**
 * LeadConversion - Convert lead to contact + opportunity
 */

import React, { useState } from 'react';
import {
  X,
  ArrowRight,
  User,
  Building2,
  Target,
  CheckCircle,
} from 'lucide-react';
import { crmAPI } from '../../../services/api/crm';

export default function LeadConversion({ lead, onClose, onConverted }) {
  const [step, setStep] = useState(1);
  const [options, setOptions] = useState({
    createContact: true,
    createCompany: !!lead.company_name,
    createOpportunity: true,
  });
  const [opportunityData, setOpportunityData] = useState({
    name: `Deal with ${lead.company_name || lead.first_name}`,
    amount: '',
    expected_close_date: '',
  });
  const [isConverting, setIsConverting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleConvert = async () => {
    setIsConverting(true);
    setError(null);

    try {
      const res = await crmAPI.convertLead(lead.id, {
        create_contact: options.createContact,
        create_opportunity: options.createOpportunity,
        opportunity_amount: parseFloat(opportunityData.amount) || 0,
        opportunity_name: opportunityData.name,
      });

      setResult(res.data);
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.detail || 'Conversion failed');
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Convert Lead</h2>
          <button className="close-btn" onClick={onClose}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="steps">
          <div className={`step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
            <span className="step-number">1</span>
            <span className="step-label">Options</span>
          </div>
          <div className="step-connector" />
          <div className={`step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
            <span className="step-number">2</span>
            <span className="step-label">Details</span>
          </div>
          <div className="step-connector" />
          <div className={`step ${step >= 3 ? 'active' : ''}`}>
            <span className="step-number">3</span>
            <span className="step-label">Done</span>
          </div>
        </div>

        <div className="modal-body">
          {/* Step 1: Options */}
          {step === 1 && (
            <div className="step-content">
              <div className="lead-summary">
                <h3>Converting Lead</h3>
                <div className="lead-info">
                  <span className="lead-name">
                    {lead.first_name} {lead.last_name}
                  </span>
                  {lead.company_name && (
                    <span className="lead-company">{lead.company_name}</span>
                  )}
                  {lead.email && <span className="lead-email">{lead.email}</span>}
                </div>
              </div>

              <div className="conversion-options">
                <label className="option-item">
                  <input
                    type="checkbox"
                    checked={options.createContact}
                    onChange={(e) => setOptions({ ...options, createContact: e.target.checked })}
                  />
                  <User className="w-5 h-5" />
                  <div className="option-info">
                    <span className="option-title">Create Contact</span>
                    <span className="option-desc">
                      Convert lead to a contact record
                    </span>
                  </div>
                </label>

                {lead.company_name && (
                  <label className="option-item">
                    <input
                      type="checkbox"
                      checked={options.createCompany}
                      onChange={(e) => setOptions({ ...options, createCompany: e.target.checked })}
                    />
                    <Building2 className="w-5 h-5" />
                    <div className="option-info">
                      <span className="option-title">Create Company</span>
                      <span className="option-desc">
                        Create company: {lead.company_name}
                      </span>
                    </div>
                  </label>
                )}

                <label className="option-item">
                  <input
                    type="checkbox"
                    checked={options.createOpportunity}
                    onChange={(e) => setOptions({ ...options, createOpportunity: e.target.checked })}
                  />
                  <Target className="w-5 h-5" />
                  <div className="option-info">
                    <span className="option-title">Create Opportunity</span>
                    <span className="option-desc">
                      Start a new sales opportunity
                    </span>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* Step 2: Opportunity Details */}
          {step === 2 && options.createOpportunity && (
            <div className="step-content">
              <h3>Opportunity Details</h3>

              <div className="form-group">
                <label>Opportunity Name</label>
                <input
                  type="text"
                  value={opportunityData.name}
                  onChange={(e) => setOpportunityData({ ...opportunityData, name: e.target.value })}
                  placeholder="e.g., Enterprise License - Acme Corp"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Amount ($)</label>
                  <input
                    type="number"
                    value={opportunityData.amount}
                    onChange={(e) => setOpportunityData({ ...opportunityData, amount: e.target.value })}
                    placeholder="0"
                  />
                </div>

                <div className="form-group">
                  <label>Expected Close Date</label>
                  <input
                    type="date"
                    value={opportunityData.expected_close_date}
                    onChange={(e) => setOpportunityData({ ...opportunityData, expected_close_date: e.target.value })}
                  />
                </div>
              </div>

              {error && <div className="error-message">{error}</div>}
            </div>
          )}

          {/* Step 3: Success */}
          {step === 3 && (
            <div className="step-content success">
              <CheckCircle className="success-icon" />
              <h3>Lead Converted Successfully!</h3>
              <p>The following records were created:</p>

              <div className="created-records">
                {result?.contact_id && (
                  <div className="record-item">
                    <User className="w-5 h-5" />
                    <span>Contact created</span>
                  </div>
                )}
                {result?.company_id && (
                  <div className="record-item">
                    <Building2 className="w-5 h-5" />
                    <span>Company created</span>
                  </div>
                )}
                {result?.opportunity_id && (
                  <div className="record-item">
                    <Target className="w-5 h-5" />
                    <span>Opportunity created</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          {step === 1 && (
            <>
              <button className="btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={() => {
                  if (options.createOpportunity) {
                    setStep(2);
                  } else {
                    handleConvert();
                  }
                }}
              >
                {options.createOpportunity ? 'Next' : 'Convert'}
                <ArrowRight className="w-4 h-4" />
              </button>
            </>
          )}

          {step === 2 && (
            <>
              <button className="btn-secondary" onClick={() => setStep(1)}>
                Back
              </button>
              <button
                className="btn-primary"
                onClick={handleConvert}
                disabled={isConverting}
              >
                {isConverting ? 'Converting...' : 'Convert Lead'}
              </button>
            </>
          )}

          {step === 3 && (
            <button
              className="btn-primary"
              onClick={() => {
                onConverted?.(result);
                onClose();
              }}
            >
              Done
            </button>
          )}
        </div>

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
            max-width: 500px;
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

          .steps {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
            gap: 8px;
          }

          .step {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-muted);
          }

          .step.active {
            color: var(--primary);
          }

          .step.completed {
            color: #10b981;
          }

          .step-number {
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid currentColor;
            border-radius: 50%;
            font-weight: 600;
            font-size: 14px;
          }

          .step.completed .step-number {
            background: #10b981;
            border-color: #10b981;
            color: white;
          }

          .step-connector {
            width: 40px;
            height: 2px;
            background: var(--border-color);
          }

          .modal-body {
            padding: 24px;
          }

          .lead-summary {
            text-align: center;
            margin-bottom: 24px;
          }

          .lead-summary h3 {
            margin: 0 0 8px;
          }

          .lead-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }

          .lead-name {
            font-weight: 600;
            font-size: 18px;
          }

          .lead-company, .lead-email {
            color: var(--text-muted);
          }

          .conversion-options {
            display: flex;
            flex-direction: column;
            gap: 12px;
          }

          .option-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
          }

          .option-item:hover {
            border-color: var(--primary);
          }

          .option-item input {
            width: 20px;
            height: 20px;
          }

          .option-info {
            display: flex;
            flex-direction: column;
          }

          .option-title {
            font-weight: 500;
          }

          .option-desc {
            font-size: 13px;
            color: var(--text-muted);
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

          .form-group input {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
          }

          .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
          }

          .step-content.success {
            text-align: center;
          }

          .success-icon {
            width: 64px;
            height: 64px;
            color: #10b981;
            margin-bottom: 16px;
          }

          .created-records {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 24px;
          }

          .record-item {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px;
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
            border-radius: 8px;
          }

          .error-message {
            padding: 12px;
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            border-radius: 8px;
            margin-top: 16px;
          }

          .modal-footer {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            padding: 16px 24px;
            border-top: 1px solid var(--border-color);
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

          .btn-primary:disabled {
            opacity: 0.7;
          }
        `}</style>
      </div>
    </div>
  );
}
