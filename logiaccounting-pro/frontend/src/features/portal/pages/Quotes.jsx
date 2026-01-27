/**
 * Quotes - Quote management and acceptance
 */

import React, { useState, useEffect } from 'react';
import {
  FileText, Calendar, CheckCircle, Clock, XCircle,
  Download, Eye, ChevronRight, DollarSign, AlertCircle,
  ArrowLeft, Edit3, X,
} from 'lucide-react';

export default function Quotes() {
  const [quotes, setQuotes] = useState([]);
  const [stats, setStats] = useState({});
  const [filter, setFilter] = useState('all');
  const [selectedQuote, setSelectedQuote] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showRevisionModal, setShowRevisionModal] = useState(false);
  const [revisionComment, setRevisionComment] = useState('');
  const [showDeclineModal, setShowDeclineModal] = useState(false);
  const [declineReason, setDeclineReason] = useState('');

  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      // Simulated data - replace with API calls
      setStats({
        pending: 2,
        accepted: 5,
        declined: 1,
        expired: 1,
      });
      setQuotes([
        {
          id: '1',
          quote_number: 'QT-2025-001',
          title: 'Website Development Package',
          description: 'Full website redesign with responsive design, CMS integration, and SEO optimization.',
          status: 'pending',
          amount: 12500.00,
          valid_until: '2025-02-28',
          created_at: '2025-01-15',
          items: [
            { name: 'Design & Prototyping', description: 'UI/UX design with mockups', quantity: 1, price: 3500 },
            { name: 'Frontend Development', description: 'Responsive HTML/CSS/JS', quantity: 1, price: 4500 },
            { name: 'CMS Integration', description: 'WordPress setup and customization', quantity: 1, price: 2500 },
            { name: 'SEO Setup', description: 'On-page SEO optimization', quantity: 1, price: 2000 },
          ],
          terms: 'Payment: 50% upfront, 50% on completion. Timeline: 8-10 weeks.',
          notes: 'This quote is valid for 30 days from issue date.',
        },
        {
          id: '2',
          quote_number: 'QT-2025-002',
          title: 'Mobile App Development',
          description: 'Native iOS and Android application development.',
          status: 'pending',
          amount: 35000.00,
          valid_until: '2025-03-15',
          created_at: '2025-01-20',
          items: [
            { name: 'iOS Development', description: 'Native iOS app with Swift', quantity: 1, price: 15000 },
            { name: 'Android Development', description: 'Native Android app with Kotlin', quantity: 1, price: 15000 },
            { name: 'Backend API', description: 'REST API development', quantity: 1, price: 5000 },
          ],
          terms: 'Payment: 30% upfront, 40% at milestone, 30% on completion.',
          notes: 'Includes 3 months of bug fixes after launch.',
        },
        {
          id: '3',
          quote_number: 'QT-2024-012',
          title: 'Annual Support Contract',
          description: 'Technical support and maintenance package.',
          status: 'accepted',
          amount: 6000.00,
          valid_until: '2024-12-15',
          created_at: '2024-11-15',
          accepted_at: '2024-11-20',
          items: [
            { name: 'Priority Support', description: '24/7 email and phone support', quantity: 12, price: 300 },
            { name: 'Monthly Maintenance', description: 'Updates and security patches', quantity: 12, price: 200 },
          ],
          terms: 'Annual payment due upfront. Auto-renewal unless canceled 30 days prior.',
          notes: '',
        },
        {
          id: '4',
          quote_number: 'QT-2024-008',
          title: 'Logo Redesign',
          description: 'Brand logo redesign with variations.',
          status: 'declined',
          amount: 1500.00,
          valid_until: '2024-10-30',
          created_at: '2024-10-01',
          declined_at: '2024-10-15',
          decline_reason: 'Budget constraints',
          items: [
            { name: 'Logo Design', description: 'Primary logo with 3 concepts', quantity: 1, price: 1200 },
            { name: 'Logo Variations', description: 'Icon, horizontal, vertical versions', quantity: 1, price: 300 },
          ],
          terms: 'Full payment on delivery.',
          notes: '',
        },
        {
          id: '5',
          quote_number: 'QT-2024-005',
          title: 'Consultation Services',
          description: 'Technical consulting hours.',
          status: 'expired',
          amount: 2000.00,
          valid_until: '2024-09-15',
          created_at: '2024-08-15',
          items: [
            { name: 'Technical Consulting', description: 'Hourly consulting rate', quantity: 20, price: 100 },
          ],
          terms: 'Hours billed monthly.',
          notes: 'Quote expired - please request a new quote.',
        },
      ]);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcceptQuote = async () => {
    if (!selectedQuote) return;
    try {
      setQuotes(quotes.map(q =>
        q.id === selectedQuote.id
          ? { ...q, status: 'accepted', accepted_at: new Date().toISOString() }
          : q
      ));
      setSelectedQuote({ ...selectedQuote, status: 'accepted', accepted_at: new Date().toISOString() });
    } catch (error) {
      console.error('Failed to accept quote:', error);
    }
  };

  const handleDeclineQuote = async () => {
    if (!selectedQuote || !declineReason.trim()) return;
    try {
      setQuotes(quotes.map(q =>
        q.id === selectedQuote.id
          ? { ...q, status: 'declined', declined_at: new Date().toISOString(), decline_reason: declineReason }
          : q
      ));
      setSelectedQuote({ ...selectedQuote, status: 'declined', declined_at: new Date().toISOString() });
      setShowDeclineModal(false);
      setDeclineReason('');
    } catch (error) {
      console.error('Failed to decline quote:', error);
    }
  };

  const handleRequestRevision = async () => {
    if (!selectedQuote || !revisionComment.trim()) return;
    try {
      // API call would go here
      setShowRevisionModal(false);
      setRevisionComment('');
      alert('Revision request submitted!');
    } catch (error) {
      console.error('Failed to request revision:', error);
    }
  };

  const getStatusInfo = (status) => {
    const info = {
      pending: { icon: Clock, color: 'text-blue-600', bg: 'bg-blue-100', label: 'Pending Review' },
      accepted: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', label: 'Accepted' },
      declined: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-100', label: 'Declined' },
      expired: { icon: AlertCircle, color: 'text-gray-600', bg: 'bg-gray-100', label: 'Expired' },
      revision_requested: { icon: Edit3, color: 'text-yellow-600', bg: 'bg-yellow-100', label: 'Revision Requested' },
    };
    return info[status] || info.pending;
  };

  const filteredQuotes = filter === 'all'
    ? quotes
    : quotes.filter(q => q.status === filter);

  if (selectedQuote) {
    const statusInfo = getStatusInfo(selectedQuote.status);
    const StatusIcon = statusInfo.icon;
    const canAccept = selectedQuote.status === 'pending';
    const canDecline = selectedQuote.status === 'pending';
    const canRequestRevision = selectedQuote.status === 'pending';
    const isExpired = new Date(selectedQuote.valid_until) < new Date() && selectedQuote.status === 'pending';

    return (
      <div className="quote-detail">
        <button className="back-btn" onClick={() => setSelectedQuote(null)}>
          <ArrowLeft className="w-4 h-4" />
          Back to Quotes
        </button>

        <div className="quote-header">
          <div className="quote-title">
            <span className="quote-number">{selectedQuote.quote_number}</span>
            <span className={`status-badge ${statusInfo.bg} ${statusInfo.color}`}>
              <StatusIcon className="w-4 h-4" />
              {statusInfo.label}
            </span>
          </div>
          <h1>{selectedQuote.title}</h1>
          <p>{selectedQuote.description}</p>
          <div className="quote-meta">
            <span><Calendar className="w-4 h-4" /> Created: {new Date(selectedQuote.created_at).toLocaleDateString()}</span>
            <span><Clock className="w-4 h-4" /> Valid Until: {new Date(selectedQuote.valid_until).toLocaleDateString()}</span>
          </div>
          {isExpired && (
            <div className="expired-warning">
              <AlertCircle className="w-4 h-4" />
              This quote has expired. Please request a new quote.
            </div>
          )}
        </div>

        <div className="quote-items">
          <h2>Quote Items</h2>
          <table className="items-table">
            <thead>
              <tr>
                <th>Item</th>
                <th>Description</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {selectedQuote.items.map((item, index) => (
                <tr key={index}>
                  <td>{item.name}</td>
                  <td>{item.description}</td>
                  <td>{item.quantity}</td>
                  <td>${item.price.toFixed(2)}</td>
                  <td>${(item.quantity * item.price).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan="4">Total</td>
                <td className="total-amount">${selectedQuote.amount.toFixed(2)}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        {selectedQuote.terms && (
          <div className="quote-section">
            <h3>Terms & Conditions</h3>
            <p>{selectedQuote.terms}</p>
          </div>
        )}

        {selectedQuote.notes && (
          <div className="quote-section">
            <h3>Notes</h3>
            <p>{selectedQuote.notes}</p>
          </div>
        )}

        {selectedQuote.status === 'declined' && selectedQuote.decline_reason && (
          <div className="decline-info">
            <h3>Decline Reason</h3>
            <p>{selectedQuote.decline_reason}</p>
          </div>
        )}

        <div className="quote-actions">
          <button className="btn-icon" title="Download PDF">
            <Download className="w-4 h-4" />
            Download PDF
          </button>
          {canRequestRevision && !isExpired && (
            <button className="btn-secondary" onClick={() => setShowRevisionModal(true)}>
              <Edit3 className="w-4 h-4" />
              Request Revision
            </button>
          )}
          {canDecline && !isExpired && (
            <button className="btn-decline" onClick={() => setShowDeclineModal(true)}>
              <XCircle className="w-4 h-4" />
              Decline
            </button>
          )}
          {canAccept && !isExpired && (
            <button className="btn-accept" onClick={handleAcceptQuote}>
              <CheckCircle className="w-4 h-4" />
              Accept Quote
            </button>
          )}
        </div>

        {/* Revision Modal */}
        {showRevisionModal && (
          <div className="modal-overlay" onClick={() => setShowRevisionModal(false)}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Request Revision</h2>
                <button className="close-btn" onClick={() => setShowRevisionModal(false)}>
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="modal-body">
                <p>Please describe the changes you would like to see in this quote.</p>
                <textarea
                  placeholder="Enter your revision requests..."
                  value={revisionComment}
                  onChange={(e) => setRevisionComment(e.target.value)}
                  rows={4}
                />
              </div>
              <div className="modal-actions">
                <button className="btn-secondary" onClick={() => setShowRevisionModal(false)}>
                  Cancel
                </button>
                <button className="btn-primary" onClick={handleRequestRevision}>
                  Submit Request
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Decline Modal */}
        {showDeclineModal && (
          <div className="modal-overlay" onClick={() => setShowDeclineModal(false)}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Decline Quote</h2>
                <button className="close-btn" onClick={() => setShowDeclineModal(false)}>
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="modal-body">
                <p>Please let us know why you are declining this quote.</p>
                <textarea
                  placeholder="Enter your reason..."
                  value={declineReason}
                  onChange={(e) => setDeclineReason(e.target.value)}
                  rows={4}
                />
              </div>
              <div className="modal-actions">
                <button className="btn-secondary" onClick={() => setShowDeclineModal(false)}>
                  Cancel
                </button>
                <button className="btn-decline" onClick={handleDeclineQuote}>
                  Decline Quote
                </button>
              </div>
            </div>
          </div>
        )}

        <style jsx>{`
          .quote-detail {
            max-width: 900px;
            margin: 0 auto;
          }

          .back-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #64748b;
            margin-bottom: 20px;
            background: none;
            border: none;
            cursor: pointer;
          }

          .quote-header {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
          }

          .quote-title {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
          }

          .quote-number {
            font-family: monospace;
            color: #64748b;
            font-size: 14px;
          }

          .status-badge {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
          }

          .quote-header h1 {
            font-size: 24px;
            margin: 0 0 8px;
          }

          .quote-header > p {
            color: #64748b;
            margin: 0 0 16px;
          }

          .quote-meta {
            display: flex;
            gap: 24px;
            font-size: 14px;
            color: #64748b;
          }

          .quote-meta span {
            display: flex;
            align-items: center;
            gap: 6px;
          }

          .expired-warning {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 16px;
            padding: 12px;
            background: #fef2f2;
            border-radius: 8px;
            color: #dc2626;
            font-size: 14px;
          }

          .quote-items {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
          }

          .quote-items h2 {
            margin: 0 0 16px;
            font-size: 18px;
          }

          .items-table {
            width: 100%;
            border-collapse: collapse;
          }

          .items-table th, .items-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
          }

          .items-table th {
            font-weight: 600;
            font-size: 13px;
            color: #64748b;
            text-transform: uppercase;
          }

          .items-table tbody td {
            font-size: 14px;
          }

          .items-table tfoot td {
            font-weight: 600;
            border-bottom: none;
          }

          .total-amount {
            font-size: 18px;
            color: #1e293b;
          }

          .quote-section {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
          }

          .quote-section h3 {
            margin: 0 0 10px;
            font-size: 15px;
          }

          .quote-section p {
            margin: 0;
            color: #64748b;
            font-size: 14px;
          }

          .decline-info {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
          }

          .decline-info h3 {
            margin: 0 0 8px;
            color: #dc2626;
          }

          .decline-info p {
            margin: 0;
            color: #7f1d1d;
          }

          .quote-actions {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
          }

          .btn-icon {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background: #ffffff;
            color: #64748b;
            cursor: pointer;
          }

          .btn-secondary {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background: #ffffff;
            cursor: pointer;
          }

          .btn-decline {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
            border-radius: 8px;
            cursor: pointer;
          }

          .btn-accept {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: #10b981;
            color: white;
            border-radius: 8px;
            font-weight: 500;
            border: none;
            cursor: pointer;
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

          .modal-body {
            padding: 20px 24px;
          }

          .modal-body p {
            margin: 0 0 16px;
            color: #64748b;
          }

          .modal-body textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            resize: none;
            font-size: 15px;
          }

          .modal-actions {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            padding: 20px 24px;
            border-top: 1px solid #e2e8f0;
          }

          .btn-primary {
            padding: 10px 20px;
            background: #3b82f6;
            color: white;
            border-radius: 8px;
            font-weight: 500;
            border: none;
            cursor: pointer;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="quotes-page">
      <div className="page-header">
        <div>
          <h1>Quotes & Proposals</h1>
          <p>Review and accept quotes</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon pending">
            <Clock className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.pending}</span>
            <span className="stat-label">Pending</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon accepted">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.accepted}</span>
            <span className="stat-label">Accepted</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon declined">
            <XCircle className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.declined}</span>
            <span className="stat-label">Declined</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon expired">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.expired}</span>
            <span className="stat-label">Expired</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-row">
        <div className="filter-tabs">
          {['all', 'pending', 'accepted', 'declined', 'expired'].map((status) => (
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

      {/* Quotes List */}
      <div className="quotes-list">
        {isLoading ? (
          <div className="loading">Loading quotes...</div>
        ) : filteredQuotes.length === 0 ? (
          <div className="empty-state">
            <FileText className="w-12 h-12" />
            <p>No quotes found</p>
          </div>
        ) : (
          filteredQuotes.map((quote) => {
            const statusInfo = getStatusInfo(quote.status);
            const StatusIcon = statusInfo.icon;
            return (
              <button
                key={quote.id}
                className="quote-card"
                onClick={() => setSelectedQuote(quote)}
              >
                <div className="quote-main">
                  <div className="quote-icon">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="quote-details">
                    <div className="quote-header-row">
                      <span className="quote-number">{quote.quote_number}</span>
                      <span className={`status-badge ${statusInfo.bg} ${statusInfo.color}`}>
                        <StatusIcon className="w-3 h-3" />
                        {statusInfo.label}
                      </span>
                    </div>
                    <h3>{quote.title}</h3>
                    <p>{quote.description}</p>
                    <div className="quote-meta">
                      <span><Calendar className="w-3 h-3" /> Created: {new Date(quote.created_at).toLocaleDateString()}</span>
                      <span><Clock className="w-3 h-3" /> Valid until: {new Date(quote.valid_until).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="quote-amount-section">
                  <span className="quote-amount">${quote.amount.toLocaleString()}</span>
                  <ChevronRight className="chevron" />
                </div>
              </button>
            );
          })
        )}
      </div>

      <style jsx>{`
        .quotes-page {
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

        .stat-icon.pending {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .stat-icon.accepted {
          background: rgba(16, 185, 129, 0.1);
          color: #10b981;
        }

        .stat-icon.declined {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .stat-icon.expired {
          background: rgba(107, 114, 128, 0.1);
          color: #6b7280;
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
          overflow-x: auto;
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
          white-space: nowrap;
        }

        .filter-tab.active {
          background: #ffffff;
          color: #1e293b;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .quotes-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .quote-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
          display: flex;
          align-items: center;
          cursor: pointer;
          width: 100%;
          text-align: left;
        }

        .quote-card:hover {
          border-color: #3b82f6;
        }

        .quote-main {
          display: flex;
          gap: 16px;
          flex: 1;
        }

        .quote-icon {
          width: 44px;
          height: 44px;
          background: #f1f5f9;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #64748b;
          flex-shrink: 0;
        }

        .quote-details {
          flex: 1;
        }

        .quote-header-row {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 4px;
        }

        .quote-number {
          font-family: monospace;
          color: #64748b;
          font-size: 13px;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .quote-details h3 {
          margin: 0 0 4px;
          font-size: 16px;
        }

        .quote-details p {
          margin: 0 0 12px;
          color: #64748b;
          font-size: 14px;
        }

        .quote-meta {
          display: flex;
          gap: 16px;
          font-size: 13px;
          color: #94a3b8;
        }

        .quote-meta span {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .quote-amount-section {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .quote-amount {
          font-size: 20px;
          font-weight: 700;
        }

        .chevron {
          color: #cbd5e1;
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
      `}</style>
    </div>
  );
}
