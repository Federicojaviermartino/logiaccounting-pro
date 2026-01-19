/**
 * Analytics Dashboard Page
 * Main hub for business intelligence and analytics
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
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
import { Line, Doughnut } from 'react-chartjs-2';
import analyticsApi from '../services/analyticsApi';
import KPICard from '../components/analytics/KPICard';
import HealthScoreGauge from '../components/analytics/HealthScoreGauge';
import InsightCard from '../components/analytics/InsightCard';
import TrendIndicator from '../components/analytics/TrendIndicator';
import '../styles/analytics.css';

// Register Chart.js components
ChartJS.register(
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
);

const AnalyticsDashboard = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [insights, setInsights] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [dashboardData, insightsData, forecastData] = await Promise.all([
        analyticsApi.getDashboard(),
        analyticsApi.getInsights(),
        analyticsApi.forecastCashflow(90)
      ]);

      setDashboard(dashboardData);
      setInsights(insightsData);
      setForecast(forecastData);
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError(t('common.errorLoading') || 'Error loading data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Prepare chart data
  const getCashFlowChartData = () => {
    if (!forecast?.predictions) return null;

    const labels = forecast.predictions.slice(0, 30).map(p => {
      const date = new Date(p.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    return {
      labels,
      datasets: [
        {
          label: 'Predicted Cash Flow',
          data: forecast.predictions.slice(0, 30).map(p => p.predicted),
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.4
        },
        {
          label: 'Upper Bound',
          data: forecast.predictions.slice(0, 30).map(p => p.upper_bound),
          borderColor: 'rgba(34, 197, 94, 0.5)',
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0
        },
        {
          label: 'Lower Bound',
          data: forecast.predictions.slice(0, 30).map(p => p.lower_bound),
          borderColor: 'rgba(239, 68, 68, 0.5)',
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0
        }
      ]
    };
  };

  const getKPIDistributionData = () => {
    if (!dashboard?.kpis) return null;

    const kpis = dashboard.kpis;

    return {
      labels: ['Revenue', 'Expenses', 'Profit'],
      datasets: [{
        data: [
          kpis.revenue?.value || 0,
          kpis.expenses?.value || 0,
          Math.max(0, kpis.profit?.value || 0)
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(59, 130, 246, 0.8)'
        ],
        borderWidth: 0
      }]
    };
  };

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="loading-spinner"></div>
        <p>{t('common.loading') || 'Loading...'}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-error">
        <div className="error-icon">Warning</div>
        <h3>{t('common.error') || 'Error'}</h3>
        <p>{error}</p>
        <button onClick={loadDashboardData} className="btn btn-primary">
          {t('common.retry') || 'Retry'}
        </button>
      </div>
    );
  }

  const kpis = dashboard?.kpis || {};
  const healthScore = dashboard?.health_score || {};

  return (
    <div className="analytics-dashboard">
      {/* Header */}
      <div className="analytics-header">
        <div className="header-content">
          <h1>{t('analytics.dashboard') || 'Analytics Dashboard'}</h1>
          <p className="subtitle">Business Intelligence & Forecasting</p>
        </div>
        <div className="header-actions">
          <button
            onClick={loadDashboardData}
            className="btn btn-outline"
            title="Refresh data"
          >
            <span className="icon">Refresh</span>
          </button>
          <button className="btn btn-primary">
            <span className="icon">Export Report</span>
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="analytics-tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'forecasts' ? 'active' : ''}`}
          onClick={() => setActiveTab('forecasts')}
        >
          Forecasts
        </button>
        <button
          className={`tab ${activeTab === 'insights' ? 'active' : ''}`}
          onClick={() => setActiveTab('insights')}
        >
          AI Insights
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {/* Health Score & KPIs Row */}
          <div className="analytics-row health-kpis-row">
            {/* Health Score */}
            <div className="health-score-card">
              <h3>Financial Health Score</h3>
              <HealthScoreGauge
                score={healthScore.score || 0}
                grade={healthScore.grade || 'N/A'}
                category={healthScore.category || 'Unknown'}
              />
              {healthScore.recommendations?.length > 0 && (
                <div className="health-recommendations">
                  <h4>Recommendations</h4>
                  <ul>
                    {healthScore.recommendations.slice(0, 3).map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* KPI Cards */}
            <div className="kpi-grid">
              <KPICard
                title="Revenue"
                value={formatCurrency(kpis.revenue?.value || 0)}
                change={kpis.revenue?.change_percent}
                trend={kpis.revenue?.trend}
                icon="$"
                color="green"
              />
              <KPICard
                title="Expenses"
                value={formatCurrency(kpis.expenses?.value || 0)}
                change={kpis.expenses?.change_percent}
                trend={kpis.expenses?.trend}
                icon="$"
                color="red"
                invertTrend
              />
              <KPICard
                title="Net Profit"
                value={formatCurrency(kpis.profit?.value || 0)}
                change={kpis.profit?.change_percent}
                trend={kpis.profit?.trend}
                icon="$"
                color="blue"
              />
              <KPICard
                title="Profit Margin"
                value={`${kpis.net_margin?.value || 0}%`}
                target={`Target: ${kpis.net_margin?.target || 10}%`}
                status={kpis.net_margin?.status}
                icon="%"
                color="purple"
              />
            </div>
          </div>

          {/* Charts Row */}
          <div className="analytics-row charts-row">
            {/* Cash Flow Forecast Chart */}
            <div className="chart-card large">
              <div className="chart-header">
                <h3>30-Day Cash Flow Forecast</h3>
                <div className="chart-legend">
                  <span className="legend-item">
                    <span className="dot blue"></span>
                    Predicted
                  </span>
                  <span className="legend-item">
                    <span className="dot green"></span>
                    Upper Bound
                  </span>
                  <span className="legend-item">
                    <span className="dot red"></span>
                    Lower Bound
                  </span>
                </div>
              </div>
              <div className="chart-container">
                {getCashFlowChartData() && (
                  <Line
                    data={getCashFlowChartData()}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          mode: 'index',
                          intersect: false,
                          callbacks: {
                            label: (context) => {
                              return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                            }
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: false,
                          ticks: {
                            callback: (value) => formatCurrency(value)
                          }
                        }
                      },
                      interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                      }
                    }}
                  />
                )}
              </div>
              {forecast?.summary && (
                <div className="chart-footer">
                  <div className="forecast-stat">
                    <span className="label">Current Balance</span>
                    <span className="value">{formatCurrency(forecast.summary.current_balance || 0)}</span>
                  </div>
                  <div className="forecast-stat">
                    <span className="label">Projected (90 days)</span>
                    <span className="value">{formatCurrency(forecast.summary.projected_balance || 0)}</span>
                  </div>
                  <div className="forecast-stat">
                    <span className="label">Model Type</span>
                    <span className="value">{forecast.model_type || 'Statistical'}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Distribution Chart */}
            <div className="chart-card small">
              <h3>Financial Distribution</h3>
              <div className="chart-container doughnut">
                {getKPIDistributionData() && (
                  <Doughnut
                    data={getKPIDistributionData()}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom',
                          labels: {
                            padding: 20,
                            usePointStyle: true
                          }
                        },
                        tooltip: {
                          callbacks: {
                            label: (context) => {
                              return `${context.label}: ${formatCurrency(context.raw)}`;
                            }
                          }
                        }
                      },
                      cutout: '60%'
                    }}
                  />
                )}
              </div>
            </div>
          </div>

          {/* Additional KPIs Row */}
          <div className="analytics-row secondary-kpis">
            <div className="kpi-card-mini">
              <span className="icon">$</span>
              <div className="content">
                <span className="label">Cash Runway</span>
                <span className="value">
                  {kpis.cash_runway?.runway_months || 0} months
                </span>
              </div>
              <TrendIndicator status={kpis.cash_runway?.status} />
            </div>
            <div className="kpi-card-mini">
              <span className="icon">B</span>
              <div className="content">
                <span className="label">Inventory Turnover</span>
                <span className="value">
                  {kpis.inventory_turnover?.turnover_ratio || 0}x
                </span>
              </div>
              <TrendIndicator status={kpis.inventory_turnover?.status} />
            </div>
            <div className="kpi-card-mini">
              <span className="icon">R</span>
              <div className="content">
                <span className="label">Receivables</span>
                <span className="value">
                  {formatCurrency(kpis.receivables_aging?.total || 0)}
                </span>
              </div>
              <TrendIndicator status={kpis.receivables_aging?.status} />
            </div>
            <div className="kpi-card-mini">
              <span className="icon">P</span>
              <div className="content">
                <span className="label">Project Profitability</span>
                <span className="value">
                  {kpis.project_profitability?.profitability_rate || 0}%
                </span>
              </div>
              <TrendIndicator status={kpis.project_profitability?.status} />
            </div>
          </div>
        </>
      )}

      {/* Forecasts Tab */}
      {activeTab === 'forecasts' && (
        <div className="forecasts-content">
          <div className="chart-card large">
            <h3>Cash Flow Forecast - Extended View</h3>
            <div className="chart-container" style={{ height: '400px' }}>
              {getCashFlowChartData() && (
                <Line
                  data={getCashFlowChartData()}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: true, position: 'top' }
                    },
                    scales: {
                      y: {
                        ticks: {
                          callback: (value) => formatCurrency(value)
                        }
                      }
                    }
                  }}
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Insights Tab */}
      {activeTab === 'insights' && insights && (
        <div className="insights-content">
          {/* Summary */}
          <div className="insights-summary">
            <div className={`summary-badge ${insights.summary?.status}`}>
              <span className="status-text">{insights.summary?.status || 'Unknown'}</span>
            </div>
            <p className="summary-message">{insights.summary?.message}</p>
          </div>

          {/* Key Insights */}
          <div className="insights-section">
            <h3>Key Insights</h3>
            <div className="insights-grid">
              {insights.key_insights?.map((insight, idx) => (
                <InsightCard
                  key={idx}
                  icon={insight.icon}
                  title={insight.title}
                  detail={insight.detail}
                  type={insight.type}
                />
              ))}
            </div>
          </div>

          {/* Opportunities */}
          {insights.opportunities?.length > 0 && (
            <div className="insights-section">
              <h3>Opportunities</h3>
              <div className="opportunities-list">
                {insights.opportunities.map((opp, idx) => (
                  <div key={idx} className="opportunity-card">
                    <span className="opp-icon">{opp.icon}</span>
                    <div className="opp-content">
                      <h4>{opp.title}</h4>
                      <p>{opp.detail}</p>
                      {opp.potential_impact && (
                        <span className="impact-badge">
                          Potential: {opp.potential_impact}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risks */}
          {insights.risks?.length > 0 && (
            <div className="insights-section">
              <h3>Risk Alerts</h3>
              <div className="risks-list">
                {insights.risks.map((risk, idx) => (
                  <div key={idx} className={`risk-card ${risk.severity}`}>
                    <span className="risk-icon">{risk.icon}</span>
                    <div className="risk-content">
                      <h4>{risk.title}</h4>
                      <p>{risk.detail}</p>
                      <span className="action-text">{risk.action}</span>
                    </div>
                    <span className={`severity-badge ${risk.severity}`}>
                      {risk.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {insights.recommendations?.length > 0 && (
            <div className="insights-section">
              <h3>Recommendations</h3>
              <div className="recommendations-list">
                {insights.recommendations.map((rec, idx) => (
                  <div key={idx} className={`recommendation-card ${rec.priority}`}>
                    <div className="rec-header">
                      <span className={`priority-badge ${rec.priority}`}>
                        {rec.priority}
                      </span>
                      <span className="category">{rec.category}</span>
                    </div>
                    <h4>{rec.title}</h4>
                    <ul className="action-list">
                      {rec.actions?.map((action, actionIdx) => (
                        <li key={actionIdx}>{action}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
