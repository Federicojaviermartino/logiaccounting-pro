/**
 * Payments - Invoice and payment management
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText, Download, CreditCard, Calendar, CheckCircle,
  Clock, AlertTriangle, DollarSign, Eye, Filter,
  ChevronLeft, ChevronRight, X,
} from 'lucide-react';

export default function Payments() {
  const [invoices, setInvoices] = useState([]);
  const [stats, setStats] = useState({});
  const [filter, setFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('card');

  useEffect(() => {
    loadData();
  }, [filter, currentPage]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      // Simulated data - replace with API calls
      setStats({
        total_outstanding: 2500.00,
        total_paid: 15000.00,
        overdue_count: 1,
        pending_count: 2,
      });
      setInvoices([
        {
          id: '1',
          invoice_number: 'INV-2025-001',
          description: 'Web Development Services - January',
          amount: 1500.00,
          status: 'paid',
          due_date: '2025-01-15',
          paid_date: '2025-01-10',
          created_at: '2025-01-01',
        },
        {
          id: '2',
          invoice_number: 'INV-2025-002',
          description: 'Monthly Retainer - February',
          amount: 1000.00,
          status: 'pending',
          due_date: '2025-02-15',
          paid_date: null,
          created_at: '2025-02-01',
        },
        {
          id: '3',
          invoice_number: 'INV-2025-003',
          description: 'Additional Development Work',
          amount: 750.00,
          status: 'overdue',
          due_date: '2025-01-20',
          paid_date: null,
          created_at: '2025-01-05',
        },
        {
          id: '4',
          invoice_number: 'INV-2025-004',
          description: 'Hosting & Maintenance - Q1',
          amount: 500.00,
          status: 'pending',
          due_date: '2025-02-28',
          paid_date: null,
          created_at: '2025-02-10',
        },
      ]);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePayInvoice = async () => {
    if (!selectedInvoice) return;
    try {
      // API call would go here
      setInvoices(invoices.map(inv =>
        inv.id === selectedInvoice.id
          ? { ...inv, status: 'paid', paid_date: new Date().toISOString() }
          : inv
      ));
      setShowPaymentModal(false);
      setSelectedInvoice(null);
    } catch (error) {
      console.error('Payment failed:', error);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      paid: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', label: 'Paid' },
      pending: { icon: Clock, color: 'text-blue-600', bg: 'bg-blue-100', label: 'Pending' },
      overdue: { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-100', label: 'Overdue' },
      partial: { icon: DollarSign, color: 'text-yellow-600', bg: 'bg-yellow-100', label: 'Partial' },
    };
    return badges[status] || badges.pending;
  };

  const filteredInvoices = filter === 'all'
    ? invoices
    : invoices.filter(inv => inv.status === filter);

  return (
    <div className="payments-page">
      <div className="page-header">
        <div>
          <h1>Payments & Invoices</h1>
          <p>View and pay your invoices</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon outstanding">
            <DollarSign className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">${stats.total_outstanding?.toFixed(2)}</span>
            <span className="stat-label">Outstanding</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon paid">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">${stats.total_paid?.toFixed(2)}</span>
            <span className="stat-label">Total Paid</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon overdue">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.overdue_count}</span>
            <span className="stat-label">Overdue</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon pending">
            <Clock className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.pending_count}</span>
            <span className="stat-label">Pending</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-row">
        <div className="filter-tabs">
          {['all', 'pending', 'overdue', 'paid'].map((status) => (
            <button
              key={status}
              className={`filter-tab ${filter === status ? 'active' : ''}`}
              onClick={() => setFilter(status)}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Invoices List */}
      <div className="invoices-list">
        {isLoading ? (
          <div className="loading">Loading invoices...</div>
        ) : filteredInvoices.length === 0 ? (
          <div className="empty-state">
            <FileText className="w-12 h-12" />
            <p>No invoices found</p>
          </div>
        ) : (
          filteredInvoices.map((invoice) => {
            const statusInfo = getStatusBadge(invoice.status);
            const StatusIcon = statusInfo.icon;
            return (
              <div key={invoice.id} className="invoice-card">
                <div className="invoice-main">
                  <div className="invoice-icon">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="invoice-details">
                    <div className="invoice-header">
                      <span className="invoice-number">{invoice.invoice_number}</span>
                      <span className={`status-badge ${statusInfo.bg} ${statusInfo.color}`}>
                        <StatusIcon className="w-3 h-3" />
                        {statusInfo.label}
                      </span>
                    </div>
                    <p className="invoice-description">{invoice.description}</p>
                    <div className="invoice-meta">
                      <span>
                        <Calendar className="w-3 h-3" />
                        Due: {new Date(invoice.due_date).toLocaleDateString()}
                      </span>
                      {invoice.paid_date && (
                        <span>
                          <CheckCircle className="w-3 h-3" />
                          Paid: {new Date(invoice.paid_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="invoice-actions">
                  <span className="invoice-amount">${invoice.amount.toFixed(2)}</span>
                  <div className="action-buttons">
                    <button className="btn-icon" title="View Invoice">
                      <Eye className="w-4 h-4" />
                    </button>
                    <button className="btn-icon" title="Download PDF">
                      <Download className="w-4 h-4" />
                    </button>
                    {invoice.status !== 'paid' && (
                      <button
                        className="btn-pay"
                        onClick={() => {
                          setSelectedInvoice(invoice);
                          setShowPaymentModal(true);
                        }}
                      >
                        <CreditCard className="w-4 h-4" />
                        Pay Now
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button
          className="page-btn"
          disabled={currentPage === 1}
          onClick={() => setCurrentPage(currentPage - 1)}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="page-info">Page {currentPage}</span>
        <button
          className="page-btn"
          onClick={() => setCurrentPage(currentPage + 1)}
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Payment Modal */}
      {showPaymentModal && selectedInvoice && (
        <div className="modal-overlay" onClick={() => setShowPaymentModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Pay Invoice</h2>
              <button className="close-btn" onClick={() => setShowPaymentModal(false)}>
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="invoice-summary">
              <div className="summary-row">
                <span>Invoice</span>
                <span>{selectedInvoice.invoice_number}</span>
              </div>
              <div className="summary-row">
                <span>Description</span>
                <span>{selectedInvoice.description}</span>
              </div>
              <div className="summary-row total">
                <span>Amount Due</span>
                <span>${selectedInvoice.amount.toFixed(2)}</span>
              </div>
            </div>

            <div className="payment-methods">
              <h3>Select Payment Method</h3>
              <div className="method-options">
                <button
                  className={`method-option ${paymentMethod === 'card' ? 'active' : ''}`}
                  onClick={() => setPaymentMethod('card')}
                >
                  <CreditCard className="w-5 h-5" />
                  <span>Credit Card</span>
                </button>
                <button
                  className={`method-option ${paymentMethod === 'bank' ? 'active' : ''}`}
                  onClick={() => setPaymentMethod('bank')}
                >
                  <DollarSign className="w-5 h-5" />
                  <span>Bank Transfer</span>
                </button>
              </div>
            </div>

            {paymentMethod === 'card' && (
              <div className="card-form">
                <div className="form-group">
                  <label>Card Number</label>
                  <input type="text" placeholder="1234 5678 9012 3456" />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Expiry</label>
                    <input type="text" placeholder="MM/YY" />
                  </div>
                  <div className="form-group">
                    <label>CVC</label>
                    <input type="text" placeholder="123" />
                  </div>
                </div>
              </div>
            )}

            {paymentMethod === 'bank' && (
              <div className="bank-info">
                <p>Bank transfer details will be sent to your email.</p>
                <p className="note">Payment processing may take 2-3 business days.</p>
              </div>
            )}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowPaymentModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handlePayInvoice}>
                Pay ${selectedInvoice.amount.toFixed(2)}
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .payments-page {
          max-width: 1000px;
          margin: 0 auto;
        }

        .page-header {
          margin-bottom: 24px;
        }

        .page-header h1 {
          font-size: 24px;
          font-weight: 700;
          margin: 0 0 4px;
        }

        .page-header p {
          color: #64748b;
          margin: 0;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }

        @media (max-width: 768px) {
          .stats-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        .stat-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 16px;
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .stat-icon.outstanding {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .stat-icon.paid {
          background: rgba(16, 185, 129, 0.1);
          color: #10b981;
        }

        .stat-icon.overdue {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .stat-icon.pending {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
        }

        .stat-info {
          display: flex;
          flex-direction: column;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 700;
        }

        .stat-label {
          font-size: 13px;
          color: #64748b;
        }

        .filters-row {
          margin-bottom: 20px;
        }

        .filter-tabs {
          display: flex;
          gap: 8px;
          background: #f8fafc;
          padding: 4px;
          border-radius: 10px;
          width: fit-content;
        }

        .filter-tab {
          padding: 8px 16px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          background: transparent;
          border: none;
          color: #64748b;
          cursor: pointer;
        }

        .filter-tab.active {
          background: #ffffff;
          color: #1e293b;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .invoices-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-bottom: 24px;
        }

        .invoice-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
        }

        @media (max-width: 640px) {
          .invoice-card {
            flex-direction: column;
            align-items: stretch;
          }
        }

        .invoice-main {
          display: flex;
          gap: 12px;
          flex: 1;
        }

        .invoice-icon {
          width: 40px;
          height: 40px;
          background: #f1f5f9;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
          flex-shrink: 0;
        }

        .invoice-details {
          flex: 1;
        }

        .invoice-header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 4px;
        }

        .invoice-number {
          font-weight: 600;
          font-family: monospace;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 3px 8px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .invoice-description {
          margin: 0 0 8px;
          color: #374151;
          font-size: 14px;
        }

        .invoice-meta {
          display: flex;
          gap: 16px;
          font-size: 12px;
          color: #94a3b8;
        }

        .invoice-meta span {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .invoice-actions {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 10px;
        }

        .invoice-amount {
          font-size: 20px;
          font-weight: 700;
        }

        .action-buttons {
          display: flex;
          gap: 8px;
        }

        .btn-icon {
          width: 36px;
          height: 36px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #ffffff;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
          cursor: pointer;
        }

        .btn-icon:hover {
          background: #f8fafc;
        }

        .btn-pay {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: #3b82f6;
          color: white;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          border: none;
          cursor: pointer;
        }

        .btn-pay:hover {
          background: #2563eb;
        }

        .pagination {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 16px;
        }

        .page-btn {
          width: 36px;
          height: 36px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #ffffff;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }

        .page-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .page-info {
          color: #64748b;
          font-size: 14px;
        }

        .empty-state, .loading {
          text-align: center;
          padding: 48px;
          color: #64748b;
        }

        .empty-state svg {
          margin: 0 auto 12px;
          color: #cbd5e1;
        }

        .modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 100;
        }

        .modal-content {
          background: #ffffff;
          border-radius: 16px;
          width: 100%;
          max-width: 480px;
          max-height: 90vh;
          overflow-y: auto;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px 24px;
          border-bottom: 1px solid #e2e8f0;
        }

        .modal-header h2 {
          margin: 0;
          font-size: 18px;
        }

        .close-btn {
          background: none;
          border: none;
          color: #64748b;
          cursor: pointer;
        }

        .invoice-summary {
          padding: 20px 24px;
          background: #f8fafc;
        }

        .summary-row {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          font-size: 14px;
        }

        .summary-row.total {
          border-top: 1px solid #e2e8f0;
          margin-top: 8px;
          padding-top: 16px;
          font-weight: 600;
          font-size: 16px;
        }

        .payment-methods {
          padding: 20px 24px;
        }

        .payment-methods h3 {
          margin: 0 0 12px;
          font-size: 14px;
          font-weight: 600;
        }

        .method-options {
          display: flex;
          gap: 12px;
        }

        .method-option {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 16px;
          border: 2px solid #e2e8f0;
          border-radius: 12px;
          background: #ffffff;
          cursor: pointer;
        }

        .method-option.active {
          border-color: #3b82f6;
          background: rgba(59, 130, 246, 0.05);
        }

        .card-form, .bank-info {
          padding: 0 24px 20px;
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
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          font-size: 15px;
        }

        .form-row {
          display: flex;
          gap: 12px;
        }

        .form-row .form-group {
          flex: 1;
        }

        .bank-info {
          background: #f8fafc;
          margin: 0 24px 20px;
          padding: 16px;
          border-radius: 10px;
        }

        .bank-info p {
          margin: 0;
        }

        .bank-info .note {
          color: #64748b;
          font-size: 13px;
          margin-top: 8px;
        }

        .modal-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding: 20px 24px;
          border-top: 1px solid #e2e8f0;
        }

        .btn-secondary {
          padding: 10px 20px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          background: #ffffff;
          cursor: pointer;
        }

        .btn-primary {
          padding: 10px 20px;
          background: #3b82f6;
          color: white;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          border: none;
          cursor: pointer;
        }

        .btn-primary:hover {
          background: #2563eb;
        }
      `}</style>
    </div>
  );
}
