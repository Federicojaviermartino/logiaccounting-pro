/**
 * Portal Dashboard - Customer hub main page
 */

import React, { useState, useEffect } from 'react';
import {
  FileText, CreditCard, FolderOpen, MessageCircle,
  HelpCircle, Clock, AlertCircle, CheckCircle,
  ArrowRight, TrendingUp, Calendar,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function PortalDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      // Simulated data - replace with actual API call
      setDashboard({
        welcome: { greeting: 'Good morning', name: 'John', company_name: 'Acme Corp' },
        stats: { total_pending: 5250, total_paid: 45000, total_overdue: 1200, active_projects: 3 },
        recent_activity: [
          { type: 'invoice', action: 'created', title: 'Invoice #INV-001', description: 'Amount: $1,500', timestamp: new Date().toISOString(), icon: 'file-text' },
          { type: 'payment', action: 'completed', title: 'Payment Received', description: 'Amount: $2,500', timestamp: new Date().toISOString(), icon: 'credit-card' },
        ],
        quick_actions: [
          { id: 'new_ticket', label: 'Create Support Ticket', icon: 'help-circle', url: '/portal/support/new' },
          { id: 'pay_invoice', label: 'Pay Invoice', icon: 'credit-card', url: '/portal/payments' },
          { id: 'send_message', label: 'Send Message', icon: 'message-circle', url: '/portal/messages' },
          { id: 'view_documents', label: 'View Documents', icon: 'file', url: '/portal/documents' },
        ],
        pending_invoices: [
          { id: '1', invoice_number: 'INV-001', amount: 1500, due_date: '2026-02-01', status: 'pending', is_overdue: false },
          { id: '2', invoice_number: 'INV-002', amount: 2500, due_date: '2026-01-20', status: 'overdue', is_overdue: true },
        ],
        active_projects: [
          { id: '1', name: 'Website Redesign', progress: 65, status: 'active', due_date: '2026-03-15' },
          { id: '2', name: 'Mobile App', progress: 30, status: 'active', due_date: '2026-04-30' },
        ],
        pending_quotes: [],
      });
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="loading">Loading...</div>;
  }

  if (!dashboard) {
    return <div className="error">Failed to load dashboard</div>;
  }

  const { welcome, stats, recent_activity, quick_actions, pending_invoices, active_projects, pending_quotes } = dashboard;

  return (
    <div className="portal-dashboard">
      {/* Welcome Section */}
      <div className="welcome-section">
        <div className="welcome-text">
          <h1>{welcome.greeting}, {welcome.name}!</h1>
          <p>Welcome to your customer portal. Here's what's happening.</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon pending">
            <Clock className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">${stats.total_pending?.toLocaleString() || 0}</span>
            <span className="stat-label">Pending Invoices</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon success">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">${stats.total_paid?.toLocaleString() || 0}</span>
            <span className="stat-label">Paid This Year</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon primary">
            <FolderOpen className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">{stats.active_projects || 0}</span>
            <span className="stat-label">Active Projects</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon warning">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div className="stat-info">
            <span className="stat-value">${stats.total_overdue?.toLocaleString() || 0}</span>
            <span className="stat-label">Overdue</span>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Quick Actions */}
        <div className="dashboard-card quick-actions-card">
          <h2>Quick Actions</h2>
          <div className="quick-actions-grid">
            {quick_actions?.map((action) => (
              <Link key={action.id} to={action.url} className="quick-action">
                <div className="action-icon">
                  {action.icon === 'help-circle' && <HelpCircle className="w-5 h-5" />}
                  {action.icon === 'credit-card' && <CreditCard className="w-5 h-5" />}
                  {action.icon === 'message-circle' && <MessageCircle className="w-5 h-5" />}
                  {action.icon === 'file' && <FileText className="w-5 h-5" />}
                </div>
                <span>{action.label}</span>
                {action.badge && <span className="action-badge">{action.badge}</span>}
              </Link>
            ))}
          </div>
        </div>

        {/* Pending Invoices */}
        <div className="dashboard-card">
          <div className="card-header">
            <h2>Pending Invoices</h2>
            <Link to="/portal/payments" className="view-all">
              View All <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="invoice-list">
            {pending_invoices?.length > 0 ? (
              pending_invoices.map((inv) => (
                <div key={inv.id} className={`invoice-item ${inv.is_overdue ? 'overdue' : ''}`}>
                  <div className="invoice-info">
                    <span className="invoice-number">#{inv.invoice_number}</span>
                    <span className="invoice-due">Due: {new Date(inv.due_date).toLocaleDateString()}</span>
                  </div>
                  <div className="invoice-amount">
                    ${inv.amount?.toLocaleString()}
                    {inv.is_overdue && <span className="overdue-badge">Overdue</span>}
                  </div>
                  <Link to={`/portal/payments/${inv.id}`} className="pay-btn">
                    Pay Now
                  </Link>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <CheckCircle className="w-8 h-8" />
                <p>No pending invoices</p>
              </div>
            )}
          </div>
        </div>

        {/* Active Projects */}
        <div className="dashboard-card">
          <div className="card-header">
            <h2>Active Projects</h2>
            <Link to="/portal/projects" className="view-all">
              View All <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="project-list">
            {active_projects?.length > 0 ? (
              active_projects.map((proj) => (
                <Link key={proj.id} to={`/portal/projects/${proj.id}`} className="project-item">
                  <div className="project-info">
                    <span className="project-name">{proj.name}</span>
                    <div className="progress-bar">
                      <div className="progress-fill" style={{ width: `${proj.progress}%` }} />
                    </div>
                  </div>
                  <span className="project-progress">{proj.progress}%</span>
                </Link>
              ))
            ) : (
              <div className="empty-state">
                <FolderOpen className="w-8 h-8" />
                <p>No active projects</p>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="dashboard-card activity-card">
          <h2>Recent Activity</h2>
          <div className="activity-list">
            {recent_activity?.length > 0 ? (
              recent_activity.map((activity, i) => (
                <div key={i} className="activity-item">
                  <div className={`activity-icon ${activity.type}`}>
                    {activity.type === 'invoice' && <FileText className="w-4 h-4" />}
                    {activity.type === 'payment' && <CreditCard className="w-4 h-4" />}
                    {activity.type === 'project' && <FolderOpen className="w-4 h-4" />}
                  </div>
                  <div className="activity-content">
                    <span className="activity-title">{activity.title}</span>
                    <span className="activity-desc">{activity.description}</span>
                  </div>
                  <span className="activity-time">
                    {new Date(activity.timestamp).toLocaleDateString()}
                  </span>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <Clock className="w-8 h-8" />
                <p>No recent activity</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        .portal-dashboard {
          max-width: 1400px;
          margin: 0 auto;
        }

        .welcome-section {
          margin-bottom: 24px;
        }

        .welcome-text h1 {
          font-size: 28px;
          font-weight: 700;
          margin: 0;
        }

        .welcome-text p {
          color: #64748b;
          margin: 4px 0 0;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }

        @media (max-width: 1024px) {
          .stats-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 640px) {
          .stats-grid {
            grid-template-columns: 1fr;
          }
        }

        .stat-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .stat-icon.pending { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
        .stat-icon.success { background: rgba(16, 185, 129, 0.1); color: #10b981; }
        .stat-icon.primary { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
        .stat-icon.warning { background: rgba(239, 68, 68, 0.1); color: #ef4444; }

        .stat-info {
          display: flex;
          flex-direction: column;
        }

        .stat-value {
          font-size: 24px;
          font-weight: 700;
        }

        .stat-label {
          font-size: 13px;
          color: #64748b;
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 20px;
        }

        @media (max-width: 1024px) {
          .dashboard-grid {
            grid-template-columns: 1fr;
          }
        }

        .dashboard-card {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 20px;
        }

        .dashboard-card h2 {
          font-size: 16px;
          font-weight: 600;
          margin: 0 0 16px;
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .card-header h2 {
          margin: 0;
        }

        .view-all {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;
          color: #3b82f6;
          text-decoration: none;
        }

        .quick-actions-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
        }

        .quick-action {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px;
          background: #f8fafc;
          border-radius: 10px;
          font-weight: 500;
          transition: all 0.2s;
          text-decoration: none;
          color: inherit;
        }

        .quick-action:hover {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .action-icon {
          width: 36px;
          height: 36px;
          background: #ffffff;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .action-badge {
          margin-left: auto;
          background: #3b82f6;
          color: white;
          font-size: 11px;
          padding: 2px 8px;
          border-radius: 10px;
        }

        .invoice-list, .project-list, .activity-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .invoice-item {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 12px;
          background: #f8fafc;
          border-radius: 8px;
        }

        .invoice-item.overdue {
          background: rgba(239, 68, 68, 0.05);
          border: 1px solid rgba(239, 68, 68, 0.2);
        }

        .invoice-info {
          flex: 1;
        }

        .invoice-number {
          font-weight: 600;
          display: block;
        }

        .invoice-due {
          font-size: 12px;
          color: #64748b;
        }

        .invoice-amount {
          font-weight: 600;
          font-size: 15px;
        }

        .overdue-badge {
          display: inline-block;
          margin-left: 8px;
          font-size: 11px;
          padding: 2px 6px;
          background: #ef4444;
          color: white;
          border-radius: 4px;
        }

        .pay-btn {
          padding: 8px 16px;
          background: #3b82f6;
          color: white;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          text-decoration: none;
        }

        .project-item {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 12px;
          background: #f8fafc;
          border-radius: 8px;
          text-decoration: none;
          color: inherit;
        }

        .project-info {
          flex: 1;
        }

        .project-name {
          font-weight: 500;
          display: block;
          margin-bottom: 8px;
        }

        .progress-bar {
          height: 6px;
          background: #e2e8f0;
          border-radius: 3px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: #3b82f6;
          border-radius: 3px;
        }

        .project-progress {
          font-weight: 600;
          color: #3b82f6;
        }

        .activity-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 12px 0;
          border-bottom: 1px solid #e2e8f0;
        }

        .activity-item:last-child {
          border-bottom: none;
        }

        .activity-icon {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .activity-icon.invoice { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
        .activity-icon.payment { background: rgba(16, 185, 129, 0.1); color: #10b981; }
        .activity-icon.project { background: rgba(139, 92, 246, 0.1); color: #8b5cf6; }

        .activity-content {
          flex: 1;
        }

        .activity-title {
          font-weight: 500;
          display: block;
        }

        .activity-desc {
          font-size: 13px;
          color: #64748b;
        }

        .activity-time {
          font-size: 12px;
          color: #64748b;
        }

        .empty-state {
          text-align: center;
          padding: 32px;
          color: #64748b;
        }

        .empty-state svg {
          margin-bottom: 8px;
          opacity: 0.5;
        }
      `}</style>
    </div>
  );
}
