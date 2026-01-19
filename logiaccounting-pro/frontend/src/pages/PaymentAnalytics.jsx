import { useState, useEffect } from 'react';
import { paymentAnalyticsAPI, refundsAPI } from '../services/api';
import { Line, Doughnut, Bar } from 'react-chartjs-2';

export default function PaymentAnalytics() {
  const [summary, setSummary] = useState(null);
  const [trend, setTrend] = useState([]);
  const [byGateway, setByGateway] = useState([]);
  const [topClients, setTopClients] = useState([]);
  const [feeReport, setFeeReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryRes, trendRes, gatewayRes, clientsRes, feesRes] = await Promise.all([
        paymentAnalyticsAPI.getSummary(30),
        paymentAnalyticsAPI.getTrend(30),
        paymentAnalyticsAPI.getByGateway(),
        paymentAnalyticsAPI.getTopClients(5),
        paymentAnalyticsAPI.getFees(30)
      ]);

      setSummary(summaryRes.data);
      setTrend(trendRes.data.trend);
      setByGateway(gatewayRes.data.gateways);
      setTopClients(clientsRes.data.clients);
      setFeeReport(feesRes.data);
    } catch (err) {
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const trendChartData = {
    labels: trend.slice(-14).map(t => new Date(t.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
    datasets: [
      {
        label: 'Gross',
        data: trend.slice(-14).map(t => t.gross),
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        fill: true,
        tension: 0.4
      },
      {
        label: 'Net',
        data: trend.slice(-14).map(t => t.net),
        borderColor: '#10b981',
        backgroundColor: 'transparent',
        tension: 0.4
      }
    ]
  };

  const gatewayChartData = {
    labels: byGateway.map(g => g.gateway),
    datasets: [{
      data: byGateway.map(g => g.gross),
      backgroundColor: ['#667eea', '#f59e0b', '#10b981']
    }]
  };

  if (loading) {
    return <div className="text-center p-8">Loading analytics...</div>;
  }

  return (
    <>
      <div className="info-banner mb-6">
        📊 Payment analytics and insights to optimize your collection process.
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="stats-grid mb-6">
          <div className="stat-card">
            <div className="stat-icon">💰</div>
            <div className="stat-content">
              <div className="stat-value">${summary.gross_collected.toLocaleString()}</div>
              <div className="stat-label">Gross Collected</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <div className="stat-value">{summary.collection_rate}%</div>
              <div className="stat-label">Collection Rate</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">💳</div>
            <div className="stat-content">
              <div className="stat-value">${summary.total_fees.toLocaleString()}</div>
              <div className="stat-label">Total Fees</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">↩️</div>
            <div className="stat-content">
              <div className="stat-value">{summary.refund_rate}%</div>
              <div className="stat-label">Refund Rate</div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid-2 mb-6">
        <div className="section">
          <h3 className="section-title">Collection Trend (14 days)</h3>
          <div className="chart-container">
            <Line data={trendChartData} options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { position: 'bottom' } }
            }} />
          </div>
        </div>

        <div className="section">
          <h3 className="section-title">By Payment Gateway</h3>
          <div className="chart-container-sm">
            <Doughnut data={gatewayChartData} options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { position: 'bottom' } }
            }} />
          </div>
        </div>
      </div>

      {/* Fee Report & Top Clients */}
      <div className="grid-2">
        <div className="section">
          <h3 className="section-title">Fee Analysis</h3>
          {feeReport && (
            <div className="fee-report">
              <div className="fee-summary">
                <div className="fee-item">
                  <span>Total Processed</span>
                  <strong>${feeReport.total_processed.toLocaleString()}</strong>
                </div>
                <div className="fee-item">
                  <span>Total Fees</span>
                  <strong className="text-warning">${feeReport.total_fees.toLocaleString()}</strong>
                </div>
                <div className="fee-item">
                  <span>Net Revenue</span>
                  <strong className="text-success">${feeReport.net_revenue.toLocaleString()}</strong>
                </div>
                <div className="fee-item">
                  <span>Avg Fee Rate</span>
                  <strong>{feeReport.average_fee_rate}%</strong>
                </div>
              </div>
              <div className="fee-breakdown mt-4">
                <h4>By Gateway</h4>
                {feeReport.by_gateway.map(gw => (
                  <div key={gw.gateway} className="gateway-fee-row">
                    <span className="gateway-name">{gw.gateway}</span>
                    <span className="gateway-amount">${gw.fees.toLocaleString()}</span>
                    <span className="gateway-rate">({gw.effective_rate}%)</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="section">
          <h3 className="section-title">Top Paying Clients</h3>
          <div className="top-clients">
            {topClients.map((client, i) => (
              <div key={client.client} className="client-row">
                <div className="client-rank">#{i + 1}</div>
                <div className="client-info">
                  <div className="client-name">{client.client}</div>
                  <div className="client-count">{client.count} payments</div>
                </div>
                <div className="client-total">${client.total.toLocaleString()}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
