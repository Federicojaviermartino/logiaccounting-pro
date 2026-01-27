/**
 * CRMDashboard - Sales Analytics Dashboard
 */

import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Users,
  Target,
  DollarSign,
  Activity,
  Phone,
  Mail,
  Calendar,
  Award,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';
import { crmAPI } from '../../../services/api/crm';

export default function CRMDashboard() {
  const [stats, setStats] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [winLoss, setWinLoss] = useState(null);
  const [activityStats, setActivityStats] = useState(null);
  const [topAccounts, setTopAccounts] = useState([]);
  const [upcomingActivities, setUpcomingActivities] = useState([]);
  const [overdueTasks, setOverdueTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    loadDashboardData();
  }, [period]);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const [
        pipelineRes,
        forecastRes,
        winLossRes,
        activityRes,
        accountsRes,
        upcomingRes,
        overdueRes,
      ] = await Promise.all([
        crmAPI.getPipelineStats('default_pipeline'),
        crmAPI.getForecast({ days: 90 }),
        crmAPI.getWinLossAnalysis(period),
        crmAPI.getActivityStats(period),
        crmAPI.getTopAccounts(5),
        crmAPI.getUpcomingActivities(7),
        crmAPI.getOverdueTasks(),
      ]);

      setStats(pipelineRes.data);
      setForecast(forecastRes.data);
      setWinLoss(winLossRes.data);
      setActivityStats(activityRes.data);
      setTopAccounts(accountsRes.data || []);
      setUpcomingActivities(upcomingRes.data || []);
      setOverdueTasks(overdueRes.data || []);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0);
  };

  const formatPercent = (value) => `${(value || 0).toFixed(1)}%`;

  if (isLoading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  return (
    <div className="crm-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>Sales Dashboard</h1>
          <p>Track your sales performance and pipeline health</p>
        </div>
        <div className="period-selector">
          <select value={period} onChange={(e) => setPeriod(Number(e.target.value))}>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <KPICard
          title="Pipeline Value"
          value={formatCurrency(stats?.totals?.value)}
          subtitle={`${stats?.totals?.count || 0} deals`}
          icon={<DollarSign />}
          color="primary"
        />
        <KPICard
          title="Weighted Forecast"
          value={formatCurrency(forecast?.weighted_forecast)}
          subtitle="Next 90 days"
          icon={<Target />}
          color="success"
        />
        <KPICard
          title="Win Rate"
          value={formatPercent(winLoss?.win_rate)}
          subtitle={`${winLoss?.won_count || 0} won / ${winLoss?.lost_count || 0} lost`}
          icon={<Award />}
          color={winLoss?.win_rate >= 30 ? 'success' : 'warning'}
          trend={winLoss?.win_rate >= 30 ? 'up' : 'down'}
        />
        <KPICard
          title="Activities"
          value={activityStats?.total_activities || 0}
          subtitle={`${activityStats?.completion_rate?.toFixed(0) || 0}% completed`}
          icon={<Activity />}
          color="info"
        />
      </div>

      {/* Charts Row */}
      <div className="charts-row">
        {/* Pipeline by Stage */}
        <div className="chart-card">
          <h3>Pipeline by Stage</h3>
          <div className="stage-bars">
            {stats?.stages?.map((stage) => (
              <div key={stage.stage_id} className="stage-bar-item">
                <div className="stage-bar-header">
                  <span className="stage-name">{stage.stage_name}</span>
                  <span className="stage-value">{formatCurrency(stage.value)}</span>
                </div>
                <div className="stage-bar">
                  <div
                    className="stage-bar-fill"
                    style={{
                      width: `${(stage.value / (stats?.totals?.value || 1)) * 100}%`,
                      backgroundColor: stage.color || '#6366f1',
                    }}
                  />
                </div>
                <span className="stage-count">{stage.count} deals</span>
              </div>
            ))}
          </div>
        </div>

        {/* Forecast */}
        <div className="chart-card">
          <h3>Revenue Forecast</h3>
          <div className="forecast-summary">
            <div className="forecast-item">
              <span className="forecast-label">Pipeline Value</span>
              <span className="forecast-value">{formatCurrency(forecast?.total_pipeline)}</span>
            </div>
            <div className="forecast-item highlight">
              <span className="forecast-label">Weighted Forecast</span>
              <span className="forecast-value">{formatCurrency(forecast?.weighted_forecast)}</span>
            </div>
            <div className="forecast-item">
              <span className="forecast-label">Deal Count</span>
              <span className="forecast-value">{forecast?.deal_count || 0}</span>
            </div>
          </div>
          {forecast?.periods?.length > 0 && (
            <div className="forecast-periods">
              {forecast.periods.map((p) => (
                <div key={p.period} className="period-item">
                  <span className="period-label">{p.label}</span>
                  <span className="period-value">{formatCurrency(p.weighted_value)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Activity & Lost Reasons */}
      <div className="charts-row">
        {/* Activity Breakdown */}
        <div className="chart-card">
          <h3>Activity Breakdown</h3>
          <div className="activity-stats">
            <ActivityStat
              icon={<Phone className="w-4 h-4" />}
              label="Calls"
              value={activityStats?.by_type?.call || 0}
              color="blue"
            />
            <ActivityStat
              icon={<Mail className="w-4 h-4" />}
              label="Emails"
              value={activityStats?.emails_sent || 0}
              color="green"
            />
            <ActivityStat
              icon={<Calendar className="w-4 h-4" />}
              label="Meetings"
              value={activityStats?.meetings_held || 0}
              color="purple"
            />
            <ActivityStat
              icon={<Activity className="w-4 h-4" />}
              label="Tasks"
              value={activityStats?.by_type?.task || 0}
              color="orange"
            />
          </div>
        </div>

        {/* Lost Reasons */}
        <div className="chart-card">
          <h3>Lost Deal Reasons</h3>
          {winLoss?.lost_reasons?.length > 0 ? (
            <div className="lost-reasons">
              {winLoss.lost_reasons.slice(0, 5).map((reason, i) => (
                <div key={i} className="reason-item">
                  <span className="reason-name">{reason.reason}</span>
                  <span className="reason-count">{reason.count} deals</span>
                  <span className="reason-value">{formatCurrency(reason.value)}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">No lost deals in this period</div>
          )}
        </div>
      </div>

      {/* Bottom Row */}
      <div className="bottom-row">
        {/* Top Accounts */}
        <div className="list-card">
          <h3>Top Accounts</h3>
          <div className="account-list">
            {topAccounts.map((account, i) => (
              <div key={account.id} className="account-item">
                <span className="rank">#{i + 1}</span>
                <div className="account-info">
                  <span className="account-name">{account.name}</span>
                  <span className="account-revenue">
                    {formatCurrency(account.total_revenue)}
                  </span>
                </div>
                <span className={`health-badge health-${account.health_score >= 70 ? 'good' : account.health_score >= 40 ? 'medium' : 'low'}`}>
                  {account.health_score}
                </span>
              </div>
            ))}
            {topAccounts.length === 0 && (
              <div className="empty-state">No accounts yet</div>
            )}
          </div>
        </div>

        {/* Upcoming Activities */}
        <div className="list-card">
          <h3>Upcoming Activities</h3>
          <div className="activity-list">
            {upcomingActivities.slice(0, 5).map((activity) => (
              <div key={activity.id} className="activity-item">
                <div className={`activity-icon ${activity.type}`}>
                  {activity.type === 'call' && <Phone className="w-4 h-4" />}
                  {activity.type === 'email' && <Mail className="w-4 h-4" />}
                  {activity.type === 'meeting' && <Calendar className="w-4 h-4" />}
                  {activity.type === 'task' && <Activity className="w-4 h-4" />}
                </div>
                <div className="activity-info">
                  <span className="activity-subject">{activity.subject}</span>
                  <span className="activity-date">
                    {new Date(activity.due_date).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
            {upcomingActivities.length === 0 && (
              <div className="empty-state">No upcoming activities</div>
            )}
          </div>
        </div>

        {/* Overdue Tasks Alert */}
        {overdueTasks.length > 0 && (
          <div className="alert-card">
            <div className="alert-header">
              <AlertCircle className="w-5 h-5" />
              <h3>{overdueTasks.length} Overdue Tasks</h3>
            </div>
            <div className="overdue-list">
              {overdueTasks.slice(0, 3).map((task) => (
                <div key={task.id} className="overdue-item">
                  <span>{task.subject}</span>
                  <span className="overdue-date">
                    Due {new Date(task.due_date).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
            <a href="/crm/activities?status=overdue" className="view-all">
              View all <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        )}
      </div>

      <style jsx>{`
        .crm-dashboard {
          padding: 24px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .dashboard-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 400px;
          color: var(--text-muted);
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }

        .dashboard-header h1 {
          margin: 0;
          font-size: 24px;
        }

        .dashboard-header p {
          margin: 4px 0 0;
          color: var(--text-muted);
        }

        .period-selector select {
          padding: 8px 16px;
          border: 1px solid var(--border-color);
          border-radius: 8px;
        }

        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 20px;
          margin-bottom: 24px;
        }

        .charts-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          margin-bottom: 24px;
        }

        .chart-card, .list-card, .alert-card {
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 20px;
        }

        .chart-card h3, .list-card h3 {
          margin: 0 0 16px;
          font-size: 16px;
        }

        .stage-bars {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .stage-bar-header {
          display: flex;
          justify-content: space-between;
          font-size: 13px;
        }

        .stage-bar {
          height: 8px;
          background: var(--bg-secondary);
          border-radius: 4px;
          overflow: hidden;
        }

        .stage-bar-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s;
        }

        .stage-count {
          font-size: 11px;
          color: var(--text-muted);
        }

        .forecast-summary {
          display: flex;
          gap: 16px;
          margin-bottom: 20px;
        }

        .forecast-item {
          flex: 1;
          padding: 12px;
          background: var(--bg-secondary);
          border-radius: 8px;
          text-align: center;
        }

        .forecast-item.highlight {
          background: rgba(16, 185, 129, 0.1);
        }

        .forecast-label {
          display: block;
          font-size: 12px;
          color: var(--text-muted);
          margin-bottom: 4px;
        }

        .forecast-value {
          font-size: 18px;
          font-weight: 600;
        }

        .forecast-periods {
          display: flex;
          gap: 8px;
        }

        .period-item {
          flex: 1;
          padding: 8px;
          background: var(--bg-secondary);
          border-radius: 6px;
          text-align: center;
        }

        .period-label {
          display: block;
          font-size: 11px;
          color: var(--text-muted);
        }

        .period-value {
          font-size: 14px;
          font-weight: 500;
        }

        .activity-stats {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;
        }

        .lost-reasons {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .reason-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid var(--border-color);
        }

        .reason-name {
          flex: 1;
        }

        .reason-count {
          color: var(--text-muted);
          margin-right: 16px;
        }

        .reason-value {
          font-weight: 500;
        }

        .bottom-row {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 20px;
        }

        .account-list, .activity-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .account-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 0;
        }

        .rank {
          font-weight: 600;
          color: var(--text-muted);
          width: 24px;
        }

        .account-info {
          flex: 1;
          display: flex;
          flex-direction: column;
        }

        .account-name {
          font-weight: 500;
        }

        .account-revenue {
          font-size: 12px;
          color: var(--text-muted);
        }

        .health-badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
        }

        .health-good {
          background: rgba(16, 185, 129, 0.1);
          color: #10b981;
        }

        .health-medium {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
        }

        .health-low {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .activity-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 8px 0;
        }

        .activity-icon {
          padding: 8px;
          border-radius: 8px;
          background: var(--bg-secondary);
        }

        .activity-icon.call { color: #3b82f6; }
        .activity-icon.email { color: #10b981; }
        .activity-icon.meeting { color: #8b5cf6; }
        .activity-icon.task { color: #f59e0b; }

        .activity-info {
          flex: 1;
          display: flex;
          flex-direction: column;
        }

        .activity-subject {
          font-weight: 500;
        }

        .activity-date {
          font-size: 12px;
          color: var(--text-muted);
        }

        .alert-card {
          background: rgba(239, 68, 68, 0.05);
          border-color: rgba(239, 68, 68, 0.2);
        }

        .alert-header {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #ef4444;
          margin-bottom: 16px;
        }

        .alert-header h3 {
          margin: 0;
        }

        .overdue-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-bottom: 16px;
        }

        .overdue-item {
          display: flex;
          justify-content: space-between;
          font-size: 14px;
        }

        .overdue-date {
          color: #ef4444;
        }

        .view-all {
          display: flex;
          align-items: center;
          gap: 4px;
          color: var(--primary);
          font-weight: 500;
          text-decoration: none;
        }

        .empty-state {
          text-align: center;
          color: var(--text-muted);
          padding: 40px;
        }

        @media (max-width: 1024px) {
          .kpi-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .charts-row, .bottom-row {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}

// KPI Card Component
function KPICard({ title, value, subtitle, icon, color, trend }) {
  return (
    <div className={`kpi-card ${color}`}>
      <div className="kpi-icon">{icon}</div>
      <div className="kpi-content">
        <span className="kpi-title">{title}</span>
        <span className="kpi-value">
          {value}
          {trend && (
            <span className={`trend ${trend}`}>
              {trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            </span>
          )}
        </span>
        <span className="kpi-subtitle">{subtitle}</span>
      </div>

      <style jsx>{`
        .kpi-card {
          display: flex;
          gap: 16px;
          padding: 20px;
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
        }

        .kpi-icon {
          padding: 12px;
          border-radius: 12px;
          background: var(--primary-light, rgba(99, 102, 241, 0.1));
          color: var(--primary);
        }

        .kpi-card.success .kpi-icon {
          background: rgba(16, 185, 129, 0.1);
          color: #10b981;
        }

        .kpi-card.warning .kpi-icon {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
        }

        .kpi-card.info .kpi-icon {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .kpi-content {
          display: flex;
          flex-direction: column;
        }

        .kpi-title {
          font-size: 13px;
          color: var(--text-muted);
        }

        .kpi-value {
          font-size: 24px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .trend {
          display: flex;
        }

        .trend.up {
          color: #10b981;
        }

        .trend.down {
          color: #ef4444;
        }

        .kpi-subtitle {
          font-size: 12px;
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}

// Activity Stat Component
function ActivityStat({ icon, label, value, color }) {
  return (
    <div className="activity-stat">
      <div className={`stat-icon ${color}`}>{icon}</div>
      <div className="stat-content">
        <span className="stat-value">{value}</span>
        <span className="stat-label">{label}</span>
      </div>

      <style jsx>{`
        .activity-stat {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px;
          background: var(--bg-secondary);
          border-radius: 8px;
        }

        .stat-icon {
          padding: 8px;
          border-radius: 8px;
        }

        .stat-icon.blue {
          background: rgba(59, 130, 246, 0.1);
          color: #3b82f6;
        }

        .stat-icon.green {
          background: rgba(16, 185, 129, 0.1);
          color: #10b981;
        }

        .stat-icon.purple {
          background: rgba(139, 92, 246, 0.1);
          color: #8b5cf6;
        }

        .stat-icon.orange {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
        }

        .stat-content {
          display: flex;
          flex-direction: column;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 600;
        }

        .stat-label {
          font-size: 13px;
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}
