/**
 * Anomaly Dashboard Component
 * AI-powered fraud detection and anomaly monitoring
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getAuthHeaders } from '../../utils/tokenService';

const API_BASE = '/api/v1/ai/anomaly';

export default function AnomalyDashboard() {
  const { t } = useTranslation();
  const [anomalies, setAnomalies] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    status: 'open',
    severity: '',
  });

  useEffect(() => {
    fetchAnomalies();
    fetchStats();
  }, [filters]);

  const fetchAnomalies = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.severity) params.append('severity', filters.severity);

      const res = await fetch(`${API_BASE}/anomalies?${params}`, {
        headers: {
          ...getAuthHeaders(),
        },
      });
      const data = await res.json();
      setAnomalies(data);
    } catch (err) {
      setError('Failed to load anomalies');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`, {
        headers: {
          ...getAuthHeaders(),
        },
      });
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const resolveAnomaly = async (id, notes = '') => {
    try {
      await fetch(`${API_BASE}/anomalies/${id}/resolve`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ resolution_notes: notes }),
      });
      fetchAnomalies();
      fetchStats();
    } catch (err) {
      setError('Failed to resolve anomaly');
    }
  };

  const dismissAnomaly = async (id) => {
    try {
      await fetch(`${API_BASE}/anomalies/${id}/dismiss`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ reason: 'False positive' }),
      });
      fetchAnomalies();
      fetchStats();
    } catch (err) {
      setError('Failed to dismiss anomaly');
    }
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      'critical': '🚨',
      'high': '⚠️',
      'medium': '⚡',
      'low': 'ℹ️',
    };
    return icons[severity] || '❓';
  };

  const getTypeIcon = (type) => {
    if (type.includes('amount')) return '💰';
    if (type.includes('duplicate')) return '📋';
    if (type.includes('timing')) return '🕐';
    if (type.includes('frequency')) return '📊';
    if (type.includes('rule_')) return '📜';
    return '🔍';
  };

  return (
    <div className="ai-card anomaly-dashboard">
      <div className="ai-card-header">
        <span className="ai-icon">🛡️</span>
        <h3>Anomaly Detection</h3>
      </div>

      {stats && (
        <div className="anomaly-stats">
          <div className="stat-card total">
            <span className="stat-value">{stats.total || 0}</span>
            <span className="stat-label">Total</span>
          </div>
          {stats.by_severity && Object.entries(stats.by_severity).map(([severity, count]) => (
            <div key={severity} className={`stat-card severity-${severity}`}>
              <span className="stat-value">{count}</span>
              <span className="stat-label">{severity}</span>
            </div>
          ))}
        </div>
      )}

      <div className="anomaly-filters">
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
        >
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
          <option value="dismissed">Dismissed</option>
          <option value="all">All</option>
        </select>

        <select
          value={filters.severity}
          onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="ai-loading-spinner" />
        </div>
      ) : error ? (
        <div className="error-state">
          <p>{error}</p>
          <button onClick={fetchAnomalies}>Retry</button>
        </div>
      ) : anomalies.length === 0 ? (
        <div className="empty-state">
          <span>✅</span>
          <p>No anomalies detected</p>
          <small>Your transactions look clean!</small>
        </div>
      ) : (
        <div className="anomaly-list">
          {anomalies.map((anomaly) => (
            <div key={anomaly.id} className={`anomaly-card severity-${anomaly.severity}`}>
              <div className="anomaly-header">
                <span className="severity-badge">
                  {getSeverityIcon(anomaly.severity)} {anomaly.severity}
                </span>
                <span className="anomaly-type">
                  {getTypeIcon(anomaly.anomaly_type)}
                </span>
                <span className="risk-score">
                  Risk: {((anomaly.risk_score || 0) * 100).toFixed(0)}%
                </span>
              </div>

              <h4>{anomaly.title}</h4>
              {anomaly.description && (
                <p className="anomaly-description">{anomaly.description}</p>
              )}

              <div className="anomaly-meta">
                <span className="meta-item">
                  <strong>Entity:</strong> {anomaly.entity_type}
                </span>
                <span className="meta-item">
                  <strong>Detected:</strong> {new Date(anomaly.created_at).toLocaleDateString()}
                </span>
                {anomaly.detection_method && (
                  <span className="meta-item">
                    <strong>Method:</strong> {anomaly.detection_method}
                  </span>
                )}
              </div>

              {anomaly.evidence && (
                <details className="evidence-details">
                  <summary>View Evidence</summary>
                  <pre>{JSON.stringify(anomaly.evidence, null, 2)}</pre>
                </details>
              )}

              {anomaly.status === 'open' && (
                <div className="anomaly-actions">
                  <button
                    className="btn-dismiss"
                    onClick={() => dismissAnomaly(anomaly.id)}
                  >
                    Dismiss
                  </button>
                  <button
                    className="btn-resolve"
                    onClick={() => resolveAnomaly(anomaly.id, 'Reviewed and resolved')}
                  >
                    Mark Resolved
                  </button>
                </div>
              )}

              {anomaly.status !== 'open' && (
                <div className={`anomaly-status ${anomaly.status}`}>
                  {anomaly.status === 'resolved' ? '✅ Resolved' :
                   anomaly.status === 'dismissed' ? '❌ Dismissed' :
                   `📋 ${anomaly.status}`}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
