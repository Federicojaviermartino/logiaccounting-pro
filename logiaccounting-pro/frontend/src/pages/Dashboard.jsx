import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import { useAuth } from '../contexts/AuthContext';
import { reportsAPI, paymentsAPI, cashflowAPI, anomalyAPI } from '../services/api';
import toast from '../utils/toast';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [cashFlow, setCashFlow] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [pendingPayments, setPendingPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [aiInsights, setAiInsights] = useState(null);
  const [aiLoading, setAiLoading] = useState(true);

  useEffect(() => {
    loadData();
    loadAIInsights();
  }, []);

  const loadData = async () => {
    try {
      const [dashRes, payRes] = await Promise.all([
        reportsAPI.getDashboard(),
        paymentsAPI.getPendingPayments()
      ]);
      
      setStats(dashRes.data);
      setPendingPayments(payRes.data?.slice(0, 5) || []);
      
      if (user?.role === 'admin') {
        const [cfRes, expRes] = await Promise.all([
          reportsAPI.getCashFlow(6),
          reportsAPI.getExpensesByCategory()
        ]);
        setCashFlow(cfRes.data || []);
        setExpenses(expRes.data || []);
      }
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAIInsights = async () => {
    if (user?.role !== 'admin') {
      setAiLoading(false);
      return;
    }

    try {
      const [cashflowRes, anomalyRes] = await Promise.all([
        cashflowAPI.predict(30),
        anomalyAPI.getSummary()
      ]);

      setAiInsights({
        cashflow: cashflowRes.data,
        anomalies: anomalyRes.data
      });
    } catch (error) {
      console.error('Failed to load AI insights:', error);
    } finally {
      setAiLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);
  };

  const markPaid = async (paymentId) => {
    if (!window.confirm('Confirm this payment as paid? All parties will be notified.')) return;
    try {
      await paymentsAPI.markAsPaid(paymentId, new Date().toISOString());
      toast.success('Payment marked as paid! All parties have been notified.');
      loadData();
    } catch (error) {
      toast.error('Failed to mark payment as paid');
    }
  };

  const cashFlowData = {
    labels: cashFlow.map(d => d.month),
    datasets: [
      { label: 'Income', data: cashFlow.map(d => d.income), backgroundColor: '#10b981' },
      { label: 'Expenses', data: cashFlow.map(d => d.expenses), backgroundColor: '#ef4444' }
    ]
  };

  const expensesData = {
    labels: expenses.map(d => d.name),
    datasets: [{
      data: expenses.map(d => d.amount),
      backgroundColor: ['#667eea', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
    }]
  };

  if (loading) {
    return <div className="text-center text-muted">Loading dashboard...</div>;
  }

  return (
    <>
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-icon">📁</span>
          <div className="stat-content">
            <div className="stat-label">Active Projects</div>
            <div className="stat-value">{stats?.active_projects || 0}</div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">⏰</span>
          <div className="stat-content">
            <div className="stat-label">{user?.role === 'admin' ? 'Pending Payments' : 'My Pending'}</div>
            <div className="stat-value">{user?.role === 'admin' ? stats?.pending_payments_count : stats?.my_pending_payments || 0}</div>
          </div>
        </div>
        {user?.role === 'admin' && (
          <>
            <div className="stat-card">
              <span className="stat-icon">💵</span>
              <div className="stat-content">
                <div className="stat-label">Monthly Revenue</div>
                <div className="stat-value success">{formatCurrency(stats?.monthly_revenue)}</div>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">📉</span>
              <div className="stat-content">
                <div className="stat-label">Monthly Expenses</div>
                <div className="stat-value danger">{formatCurrency(stats?.monthly_expenses)}</div>
              </div>
            </div>
          </>
        )}
        {['client', 'supplier'].includes(user?.role) && (
          <div className="stat-card">
            <span className="stat-icon">💰</span>
            <div className="stat-content">
              <div className="stat-label">Outstanding Amount</div>
              <div className="stat-value warning">{formatCurrency(stats?.my_pending_amount)}</div>
            </div>
          </div>
        )}
      </div>

      {user?.role === 'admin' && aiInsights && (
        <div className="section mb-6">
          <div className="section-header">
            <h3 className="section-title">AI Insights</h3>
            <button className="btn btn-sm btn-secondary" onClick={() => navigate('/ai-dashboard')}>View Details</button>
          </div>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-icon">📈</span>
              <div className="stat-content">
                <div className="stat-label">30-Day Cash Forecast</div>
                <div className={`stat-value ${aiInsights.cashflow?.summary?.total_net >= 0 ? 'success' : 'danger'}`}>
                  {formatCurrency(aiInsights.cashflow?.summary?.total_net)}
                </div>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">⚠️</span>
              <div className="stat-content">
                <div className="stat-label">Anomalies Detected</div>
                <div className={`stat-value ${aiInsights.anomalies?.total_anomalies > 0 ? 'warning' : 'success'}`}>
                  {aiInsights.anomalies?.total_anomalies || 0}
                </div>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">🎯</span>
              <div className="stat-content">
                <div className="stat-label">Risk Score</div>
                <div className={`stat-value ${(aiInsights.anomalies?.risk_score || 0) > 0.5 ? 'danger' : 'success'}`}>
                  {((aiInsights.anomalies?.risk_score || 0) * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
          {aiInsights.cashflow?.risk_alerts?.length > 0 && (
            <div className="mt-4">
              {aiInsights.cashflow.risk_alerts.slice(0, 2).map((alert, i) => (
                <div key={i} className="info-banner" style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#dc2626', marginBottom: '8px' }}>
                  ⚠️ {alert}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {user?.role === 'admin' && (
        <div className="grid-2 mb-6">
          <div className="section">
            <h3 className="section-title">Cash Flow Overview</h3>
            <div className="chart-container">
              {cashFlow.length > 0 ? (
                <Bar data={cashFlowData} options={{ responsive: true, maintainAspectRatio: false }} />
              ) : (
                <p className="text-muted text-center">No data available</p>
              )}
            </div>
          </div>
          <div className="section">
            <h3 className="section-title">Expenses by Category</h3>
            <div className="chart-container">
              {expenses.length > 0 ? (
                <Doughnut data={expensesData} options={{ responsive: true, maintainAspectRatio: false }} />
              ) : (
                <p className="text-muted text-center">No expense data</p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="grid-2">
        <div className="section">
          <h3 className="section-title">Pending Payments</h3>
          {pendingPayments.length > 0 ? (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Amount</th>
                    <th>Due Date</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingPayments.map(p => (
                    <tr key={p.id}>
                      <td className="font-bold">{formatCurrency(p.amount)}</td>
                      <td>{new Date(p.due_date).toLocaleDateString()}</td>
                      <td>
                        <span className={`badge badge-${p.status === 'overdue' ? 'danger' : 'warning'}`}>
                          {p.status}
                        </span>
                      </td>
                      <td>
                        <button className="btn btn-success btn-sm" onClick={() => markPaid(p.id)}>
                          Pay
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-muted text-center">No pending payments</p>
          )}
        </div>

        <div className="section">
          <h3 className="section-title">Quick Actions</h3>
          <div className="quick-actions">
            {['admin', 'supplier'].includes(user?.role) && (
              <>
                <div className="action-card" onClick={() => navigate('/inventory')}>
                  <span className="action-card-icon">📦</span>
                  <span className="action-card-title">Add Material</span>
                </div>
                <div className="action-card" onClick={() => navigate('/movements')}>
                  <span className="action-card-icon">🔄</span>
                  <span className="action-card-title">Stock Movement</span>
                </div>
              </>
            )}
            <div className="action-card" onClick={() => navigate('/transactions')}>
              <span className="action-card-icon">💰</span>
              <span className="action-card-title">New Transaction</span>
            </div>
            <div className="action-card" onClick={() => navigate('/payments')}>
              <span className="action-card-icon">💳</span>
              <span className="action-card-title">View Payments</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
