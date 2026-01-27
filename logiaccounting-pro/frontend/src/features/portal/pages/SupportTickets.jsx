/**
 * Support Tickets - List and manage support tickets
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus, Search, Filter, HelpCircle, Clock, CheckCircle,
  AlertCircle, ChevronRight, MessageCircle,
} from 'lucide-react';

export default function SupportTickets() {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    category: '',
    search: '',
  });
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadData();
  }, [filters, page]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      // Simulated data - replace with API call
      setTickets([
        { id: '1', ticket_number: 'TKT-123456', subject: 'Login issue with portal', status: 'open', priority: 'high', category: 'technical', message_count: 3, last_message: 'We are looking into this...', updated_at: new Date().toISOString() },
        { id: '2', ticket_number: 'TKT-123457', subject: 'Invoice clarification needed', status: 'in_progress', priority: 'normal', category: 'billing', message_count: 5, last_message: 'Thank you for clarifying...', updated_at: new Date().toISOString() },
        { id: '3', ticket_number: 'TKT-123458', subject: 'Feature request: Export to Excel', status: 'resolved', priority: 'low', category: 'feature_request', message_count: 2, last_message: 'This has been added to...', updated_at: new Date().toISOString() },
      ]);
      setStats({ total: 10, open: 3, resolved: 7, average_rating: 4.5 });
      setCategories([
        { id: 'billing', name: 'Billing & Payments' },
        { id: 'technical', name: 'Technical Support' },
        { id: 'general', name: 'General Inquiry' },
        { id: 'feature_request', name: 'Feature Request' },
      ]);
      setTotal(10);
    } catch (error) {
      console.error('Failed to load tickets:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      open: { bg: 'bg-blue-100', text: 'text-blue-800', icon: Clock },
      in_progress: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: AlertCircle },
      waiting_customer: { bg: 'bg-orange-100', text: 'text-orange-800', icon: HelpCircle },
      resolved: { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle },
      closed: { bg: 'bg-gray-100', text: 'text-gray-800', icon: CheckCircle },
    };
    const style = styles[status] || styles.open;
    const Icon = style.icon;

    return (
      <span className={`status-badge ${style.bg} ${style.text}`}>
        <Icon className="w-3 h-3" />
        {status.replace('_', ' ')}
      </span>
    );
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      low: 'bg-gray-100 text-gray-600',
      normal: 'bg-blue-100 text-blue-600',
      high: 'bg-orange-100 text-orange-600',
      urgent: 'bg-red-100 text-red-600',
    };
    return <span className={`priority-badge ${colors[priority] || colors.normal}`}>{priority}</span>;
  };

  return (
    <div className="support-tickets">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Support Tickets</h1>
          <p>View and manage your support requests</p>
        </div>
        <Link to="/portal/support/new" className="btn-primary">
          <Plus className="w-4 h-4" />
          New Ticket
        </Link>
      </div>

      {/* Stats */}
      {stats && (
        <div className="stats-row">
          <div className="stat-item">
            <span className="stat-value">{stats.total}</span>
            <span className="stat-label">Total Tickets</span>
          </div>
          <div className="stat-item open">
            <span className="stat-value">{stats.open}</span>
            <span className="stat-label">Open</span>
          </div>
          <div className="stat-item resolved">
            <span className="stat-value">{stats.resolved}</span>
            <span className="stat-label">Resolved</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.average_rating || '-'}</span>
            <span className="stat-label">Avg. Rating</span>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="filters-bar">
        <div className="search-box">
          <Search className="w-4 h-4" />
          <input
            type="text"
            placeholder="Search tickets..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          />
        </div>
        <div className="filter-group">
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">All Status</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="waiting_customer">Waiting on Me</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
          <select
            value={filters.category}
            onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Ticket List */}
      <div className="ticket-list">
        {isLoading ? (
          <div className="loading">Loading tickets...</div>
        ) : tickets.length > 0 ? (
          tickets.map((ticket) => (
            <Link key={ticket.id} to={`/portal/support/${ticket.id}`} className="ticket-card">
              <div className="ticket-main">
                <div className="ticket-header">
                  <span className="ticket-number">{ticket.ticket_number}</span>
                  {getStatusBadge(ticket.status)}
                  {getPriorityBadge(ticket.priority)}
                </div>
                <h3 className="ticket-subject">{ticket.subject}</h3>
                <p className="ticket-preview">{ticket.last_message}</p>
                <div className="ticket-meta">
                  <span className="category">
                    {categories.find(c => c.id === ticket.category)?.name || ticket.category}
                  </span>
                  <span className="date">
                    {new Date(ticket.updated_at).toLocaleDateString()}
                  </span>
                  <span className="messages">
                    <MessageCircle className="w-3 h-3" />
                    {ticket.message_count}
                  </span>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-400" />
            </Link>
          ))
        ) : (
          <div className="empty-state">
            <HelpCircle className="w-12 h-12" />
            <h3>No tickets found</h3>
            <p>You haven't created any support tickets yet.</p>
            <Link to="/portal/support/new" className="btn-primary">
              Create Your First Ticket
            </Link>
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="pagination">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
          <span>Page {page} of {Math.ceil(total / 20)}</span>
          <button disabled={page >= Math.ceil(total / 20)} onClick={() => setPage(p => p + 1)}>Next</button>
        </div>
      )}

      <style jsx>{`
        .support-tickets {
          max-width: 1200px;
          margin: 0 auto;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
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

        .btn-primary {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 20px;
          background: #3b82f6;
          color: white;
          border-radius: 8px;
          font-weight: 500;
          text-decoration: none;
        }

        .stats-row {
          display: flex;
          gap: 16px;
          margin-bottom: 24px;
        }

        .stat-item {
          flex: 1;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 10px;
          padding: 16px;
          text-align: center;
        }

        .stat-item.open .stat-value { color: #3b82f6; }
        .stat-item.resolved .stat-value { color: #10b981; }

        .stat-value {
          display: block;
          font-size: 24px;
          font-weight: 700;
        }

        .stat-label {
          font-size: 13px;
          color: #64748b;
        }

        .filters-bar {
          display: flex;
          gap: 16px;
          margin-bottom: 20px;
        }

        .search-box {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          padding: 10px 16px;
          border-radius: 8px;
        }

        .search-box input {
          border: none;
          background: transparent;
          outline: none;
          flex: 1;
        }

        .filter-group {
          display: flex;
          gap: 12px;
        }

        .filter-group select {
          padding: 10px 16px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #ffffff;
        }

        .ticket-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .ticket-card {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 16px 20px;
          transition: all 0.2s;
          text-decoration: none;
          color: inherit;
        }

        .ticket-card:hover {
          border-color: #3b82f6;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .ticket-main {
          flex: 1;
        }

        .ticket-header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 8px;
        }

        .ticket-number {
          font-family: monospace;
          font-size: 13px;
          color: #64748b;
        }

        .status-badge {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
          text-transform: capitalize;
        }

        .priority-badge {
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 500;
          text-transform: capitalize;
        }

        .ticket-subject {
          font-size: 16px;
          font-weight: 600;
          margin: 0 0 6px;
        }

        .ticket-preview {
          font-size: 14px;
          color: #64748b;
          margin: 0 0 12px;
          display: -webkit-box;
          -webkit-line-clamp: 1;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .ticket-meta {
          display: flex;
          gap: 16px;
          font-size: 13px;
          color: #64748b;
        }

        .ticket-meta .messages {
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .empty-state {
          text-align: center;
          padding: 60px;
          color: #64748b;
        }

        .empty-state svg {
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .empty-state h3 {
          margin: 0 0 8px;
          color: #1e293b;
        }

        .empty-state p {
          margin: 0 0 24px;
        }

        .pagination {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 16px;
          margin-top: 24px;
        }

        .pagination button {
          padding: 8px 16px;
          border: 1px solid #e2e8f0;
          border-radius: 6px;
          background: #ffffff;
        }

        .pagination button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}
