import { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { cashflowAPI, anomalyAPI, schedulerAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import toast from '../utils/toast';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler
);

export default function AIDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('cashflow');
  const [cashflow, setCashflow] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [predictionDays, setPredictionDays] = useState(90);

  useEffect(() => {
    loadData();
  }, [predictionDays]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cfRes, anomRes, schedRes] = await Promise.all([
        cashflowAPI.predict(predictionDays),
        anomalyAPI.getSummary(),
        schedulerAPI.getSummary()
      ]);
      setCashflow(cfRes.data);
      setAnomalies(anomRes.data);
      setSchedule(schedRes.data);
    } catch (error) {
      console.error('Failed to load AI data:', error);
    } finally {
      setLoading(false);
    }
  };

  const runAnomalyScan = async () => {
    try {
      const res = await anomalyAPI.runScan();
      setAnomalies(res.data);
    } catch (error) {
      toast.error('Scan failed: ' + (error.response?.data?.detail || error.message));
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value || 0);
  };

  // Cash Flow Chart Data
  const cashflowChartData = {
    labels: cashflow?.predictions?.slice(0, 30).map(p =>
      new Date(p.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    ) || [],
    datasets: [
      {
        label: 'Predicted Income',
        data: cashflow?.predictions?.slice(0, 30).map(p => p.predicted_income) || [],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Predicted Expenses',
        data: cashflow?.predictions?.slice(0, 30).map(p => p.predicted_expenses) || [],
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Net Cash Flow',
        data: cashflow?.predictions?.slice(0, 30).map(p => p.predicted_net) || [],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.2)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  // Anomaly Severity Chart
  const anomalyChartData = {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    datasets: [{
      data: [
        anomalies?.by_severity?.critical || anomalies?.critical_count || 0,
        anomalies?.by_severity?.high || anomalies?.high_count || 0,
        anomalies?.by_severity?.medium || anomalies?.medium_count || 0,
        anomalies?.by_severity?.low || anomalies?.low_count || 0
      ],
      backgroundColor: ['#dc2626', '#f97316', '#eab308', '#22c55e'],
      borderWidth: 0
    }]
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading AI Analytics...</p>
      </div>
    );
  }

  return (
    <>
      {/* Stats Overview */}
      <div className="stats-grid mb-6">
        <div className="stat-card">
          <span className="stat-icon">📈</span>
          <div className="stat-content">
            <div className="stat-label">Predicted Net ({predictionDays}d)</div>
            <div className={`stat-value ${(cashflow?.summary?.total_predicted_net || 0) >= 0 ? 'success' : 'danger'}`}>
              {formatCurrency(cashflow?.summary?.total_predicted_net)}
            </div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">⚠️</span>
          <div className="stat-content">
            <div className="stat-label">Anomalies Detected</div>
            <div className={`stat-value ${(anomalies?.total_anomalies || 0) > 0 ? 'warning' : 'success'}`}>
              {anomalies?.total_anomalies || 0}
            </div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">💰</span>
          <div className="stat-content">
            <div className="stat-label">Potential Savings</div>
            <div className="stat-value success">
              {formatCurrency(schedule?.potential_savings)}
            </div>
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-icon">📊</span>
          <div className="stat-content">
            <div className="stat-label">Risk Score</div>
            <div className={`stat-value ${(anomalies?.risk_score || 0) > 50 ? 'danger' : 'success'}`}>
              {anomalies?.risk_score || 0}%
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="section mb-6">
        <div className="flex gap-2 mb-4">
          <button
            className={`btn ${activeTab === 'cashflow' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('cashflow')}
          >
            Cash Flow Predictor
          </button>
          <button
            className={`btn ${activeTab === 'anomaly' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('anomaly')}
          >
            Anomaly Detection
          </button>
          <button
            className={`btn ${activeTab === 'scheduler' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('scheduler')}
          >
            Payment Optimizer
          </button>
        </div>

        {/* Cash Flow Tab */}
        {activeTab === 'cashflow' && (
          <>
            <div className="section-header">
              <h3 className="section-title">Cash Flow Prediction</h3>
              <div className="flex gap-2">
                {[30, 60, 90].map(days => (
                  <button
                    key={days}
                    className={`btn btn-sm ${predictionDays === days ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setPredictionDays(days)}
                  >
                    {days} Days
                  </button>
                ))}
              </div>
            </div>
            <div className="chart-container" style={{ height: '400px' }}>
              <Line
                data={cashflowChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { position: 'top' }
                  }
                }}
              />
            </div>
            {cashflow?.risk_alerts?.length > 0 && (
              <div className="mt-4">
                <h4 className="font-bold mb-2">Risk Alerts</h4>
                {cashflow.risk_alerts.map((alert, i) => (
                  <div key={i} className="info-banner" style={{ background: '#fef2f2', borderColor: '#fecaca', color: '#dc2626', marginBottom: '8px' }}>
                    ⚠️ {alert}
                  </div>
                ))}
              </div>
            )}
            {cashflow?.insights?.length > 0 && (
              <div className="mt-4">
                <h4 className="font-bold mb-2">Insights</h4>
                {cashflow.insights.map((insight, i) => (
                  <div key={i} className="info-banner" style={{ marginBottom: '8px' }}>
                    💡 {insight}
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* Anomaly Tab */}
        {activeTab === 'anomaly' && (
          <>
            <div className="section-header">
              <h3 className="section-title">Anomaly Detection</h3>
              <button className="btn btn-primary" onClick={runAnomalyScan}>
                🔍 Run Full Scan
              </button>
            </div>
            <div className="grid-2">
              <div>
                <div className="chart-container" style={{ height: '300px' }}>
                  <Doughnut
                    data={anomalyChartData}
                    options={{ responsive: true, maintainAspectRatio: false }}
                  />
                </div>
              </div>
              <div>
                <h4 className="font-bold mb-2">Summary</h4>
                <p className="text-muted mb-4">{anomalies?.summary || 'Run a scan to detect anomalies'}</p>
                <div className="info-banner">
                  Risk Level: <strong>{anomalies?.risk_level || 'Unknown'}</strong>
                </div>
              </div>
            </div>
            {anomalies?.anomalies?.length > 0 && (
              <div className="table-container mt-4">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Severity</th>
                      <th>Description</th>
                      <th>Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalies.anomalies.slice(0, 10).map((a, i) => (
                      <tr key={i}>
                        <td>{a.type?.replace(/_/g, ' ')}</td>
                        <td>
                          <span className={`badge badge-${
                            a.severity === 'critical' ? 'danger' :
                            a.severity === 'high' ? 'warning' : 'gray'
                          }`}>
                            {a.severity}
                          </span>
                        </td>
                        <td>{a.title}</td>
                        <td>{((a.confidence || 0) * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {/* Scheduler Tab */}
        {activeTab === 'scheduler' && (
          <>
            <div className="section-header">
              <h3 className="section-title">Payment Optimization</h3>
            </div>
            <div className="stats-grid mb-4">
              <div className="stat-card">
                <span className="stat-icon">💵</span>
                <div className="stat-content">
                  <div className="stat-label">Cash Required (7d)</div>
                  <div className="stat-value">{formatCurrency(schedule?.cash_required_7_days)}</div>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-icon">📅</span>
                <div className="stat-content">
                  <div className="stat-label">Cash Required (30d)</div>
                  <div className="stat-value">{formatCurrency(schedule?.cash_required_30_days)}</div>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-icon">🎯</span>
                <div className="stat-content">
                  <div className="stat-label">Total Pending</div>
                  <div className="stat-value">{formatCurrency(schedule?.total_pending)}</div>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-icon">⚠️</span>
                <div className="stat-content">
                  <div className="stat-label">Urgent Payments</div>
                  <div className="stat-value danger">{schedule?.urgent_count || 0}</div>
                </div>
              </div>
            </div>
            {schedule?.optimization_notes?.length > 0 && (
              <div className="mb-4">
                {schedule.optimization_notes.map((note, i) => (
                  <div key={i} className="info-banner" style={{ marginBottom: '8px' }}>
                    📋 {note}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
