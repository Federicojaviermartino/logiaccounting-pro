import { useState, useEffect } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import { reportsAPI } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Title, Tooltip, Legend);

export default function Reports() {
  const [activeTab, setActiveTab] = useState('overview');
  const [cashFlow, setCashFlow] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [projects, setProjects] = useState([]);
  const [inventory, setInventory] = useState(null);
  const [payments, setPayments] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [cfRes, expRes, projRes, invRes, payRes] = await Promise.all([
        reportsAPI.getCashFlow(12),
        reportsAPI.getExpensesByCategory(),
        reportsAPI.getProjectProfitability(),
        reportsAPI.getInventorySummary(),
        reportsAPI.getPaymentSummary()
      ]);
      setCashFlow(cfRes.data || []);
      setExpenses(expRes.data || []);
      setProjects(projRes.data || []);
      setInventory(invRes.data || null);
      setPayments(payRes.data || null);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount || 0);

  const cashFlowChartData = {
    labels: cashFlow.map(d => d.month),
    datasets: [
      { label: 'Income', data: cashFlow.map(d => d.income), backgroundColor: '#10b981', borderColor: '#10b981', borderWidth: 2 },
      { label: 'Expenses', data: cashFlow.map(d => d.expenses), backgroundColor: '#ef4444', borderColor: '#ef4444', borderWidth: 2 }
    ]
  };

  const profitLineData = {
    labels: cashFlow.map(d => d.month),
    datasets: [{
      label: 'Net Profit',
      data: cashFlow.map(d => d.income - d.expenses),
      borderColor: '#667eea',
      backgroundColor: 'rgba(102, 126, 234, 0.1)',
      fill: true,
      tension: 0.4
    }]
  };

  const expensesDoughnutData = {
    labels: expenses.map(d => d.name),
    datasets: [{
      data: expenses.map(d => d.amount),
      backgroundColor: ['#667eea', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#84cc16']
    }]
  };

  const tabs = [
    { id: 'overview', label: '📊 Overview' },
    { id: 'financial', label: '💰 Financial' },
    { id: 'projects', label: '📁 Projects' },
    { id: 'inventory', label: '📦 Inventory' }
  ];

  if (loading) return <div className="text-center text-muted">Loading reports...</div>;

  return (
    <>
      <div className="toolbar mb-6">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <>
          <div className="stats-grid mb-6">
            <div className="stat-card">
              <span className="stat-icon">📊</span>
              <div className="stat-content">
                <div className="stat-label">Total Revenue (12m)</div>
                <div className="stat-value success">{formatCurrency(cashFlow.reduce((sum, d) => sum + d.income, 0))}</div>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">💸</span>
              <div className="stat-content">
                <div className="stat-label">Total Expenses (12m)</div>
                <div className="stat-value danger">{formatCurrency(cashFlow.reduce((sum, d) => sum + d.expenses, 0))}</div>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">📦</span>
              <div className="stat-content">
                <div className="stat-label">Inventory Value</div>
                <div className="stat-value">{formatCurrency(inventory?.total_value)}</div>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">💳</span>
              <div className="stat-content">
                <div className="stat-label">Pending Payments</div>
                <div className="stat-value warning">{formatCurrency(payments?.amounts?.pending)}</div>
              </div>
            </div>
          </div>

          <div className="grid-2">
            <div className="section">
              <h3 className="section-title">Cash Flow (12 Months)</h3>
              <div className="chart-container">
                <Bar data={cashFlowChartData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
            <div className="section">
              <h3 className="section-title">Profit Trend</h3>
              <div className="chart-container">
                <Line data={profitLineData} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        </>
      )}

      {activeTab === 'financial' && (
        <>
          <div className="grid-2 mb-6">
            <div className="section">
              <h3 className="section-title">Expenses by Category</h3>
              <div className="chart-container">
                {expenses.length > 0 ? (
                  <Doughnut data={expensesDoughnutData} options={{ responsive: true, maintainAspectRatio: false }} />
                ) : (
                  <p className="text-muted text-center">No expense data</p>
                )}
              </div>
            </div>
            <div className="section">
              <h3 className="section-title">Payment Summary</h3>
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-icon">⏳</span>
                  <div className="stat-content">
                    <div className="stat-label">Pending ({payments?.by_status?.pending || 0})</div>
                    <div className="stat-value warning">{formatCurrency(payments?.amounts?.pending)}</div>
                  </div>
                </div>
                <div className="stat-card">
                  <span className="stat-icon">⚠️</span>
                  <div className="stat-content">
                    <div className="stat-label">Overdue ({payments?.by_status?.overdue || 0})</div>
                    <div className="stat-value danger">{formatCurrency(payments?.amounts?.overdue)}</div>
                  </div>
                </div>
                <div className="stat-card">
                  <span className="stat-icon">✅</span>
                  <div className="stat-content">
                    <div className="stat-label">Paid ({payments?.by_status?.paid || 0})</div>
                    <div className="stat-value success">{formatCurrency(payments?.amounts?.paid)}</div>
                  </div>
                </div>
              </div>
              <div className="mt-4">
                <p><strong>Total Payable:</strong> <span className="text-danger">{formatCurrency(payments?.total_payable)}</span></p>
                <p><strong>Total Receivable:</strong> <span className="text-success">{formatCurrency(payments?.total_receivable)}</span></p>
              </div>
            </div>
          </div>
        </>
      )}

      {activeTab === 'projects' && (
        <div className="section">
          <h3 className="section-title">Project Profitability</h3>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Budget</th>
                  <th>Income</th>
                  <th>Expenses</th>
                  <th>Profit</th>
                  <th>Margin</th>
                </tr>
              </thead>
              <tbody>
                {projects.length === 0 ? (
                  <tr className="empty-row"><td colSpan="8">No projects found</td></tr>
                ) : projects.map(p => (
                  <tr key={p.id}>
                    <td className="font-mono">{p.code}</td>
                    <td className="font-bold">{p.name}</td>
                    <td><span className={`badge badge-${p.status === 'active' ? 'success' : p.status === 'completed' ? 'primary' : 'gray'}`}>{p.status}</span></td>
                    <td className="font-mono">{formatCurrency(p.budget)}</td>
                    <td className="text-success">{formatCurrency(p.income)}</td>
                    <td className="text-danger">{formatCurrency(p.expenses)}</td>
                    <td className={p.profit >= 0 ? 'text-success font-bold' : 'text-danger font-bold'}>{formatCurrency(p.profit)}</td>
                    <td className={p.margin >= 0 ? 'text-success' : 'text-danger'}>{p.margin}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'inventory' && (
        <>
          <div className="stats-grid mb-6">
            <div className="stat-card">
              <span className="stat-icon">📦</span>
              <div className="stat-content">
                <div className="stat-label">Total Items</div>
                <div className="stat-value">{inventory?.total_items || 0}</div>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">💰</span>
              <div className="stat-content">
                <div className="stat-label">Total Value</div>
                <div className="stat-value">{formatCurrency(inventory?.total_value)}</div>
              </div>
            </div>
            <div className="stat-card">
              <span className="stat-icon">⚠️</span>
              <div className="stat-content">
                <div className="stat-label">Low Stock Alerts</div>
                <div className="stat-value danger">{inventory?.low_stock_count || 0}</div>
              </div>
            </div>
          </div>

          <div className="section">
            <h3 className="section-title">Inventory by State</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-icon">✅</span>
                <div className="stat-content">
                  <div className="stat-label">Available</div>
                  <div className="stat-value success">{inventory?.by_state?.available || 0}</div>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-icon">🔒</span>
                <div className="stat-content">
                  <div className="stat-label">Reserved</div>
                  <div className="stat-value warning">{inventory?.by_state?.reserved || 0}</div>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-icon">⛔</span>
                <div className="stat-content">
                  <div className="stat-label">Damaged</div>
                  <div className="stat-value danger">{inventory?.by_state?.damaged || 0}</div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
