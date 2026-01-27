/**
 * AI Usage Stats Component
 * Monitor AI feature usage and costs
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const API_BASE = '/api/v1/ai';

export default function AIUsageStats() {
  const { t } = useTranslation();
  const [usage, setUsage] = useState(null);
  const [config, setConfig] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    fetchAll();
  }, [period]);

  const fetchAll = async () => {
    setLoading(true);
    await Promise.all([
      fetchUsage(),
      fetchConfig(),
      fetchHealth(),
    ]);
    setLoading(false);
  };

  const fetchUsage = async () => {
    try {
      const res = await fetch(`${API_BASE}/usage?days=${period}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await res.json();
      setUsage(data);
    } catch (err) {
      console.error('Failed to fetch usage:', err);
    }
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/config`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await res.json();
      setConfig(data);
    } catch (err) {
      console.error('Failed to fetch config:', err);
    }
  };

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const data = await res.json();
      setHealth(data);
    } catch (err) {
      console.error('Failed to fetch health:', err);
    }
  };

  if (loading) {
    return (
      <div className="ai-card loading">
        <div className="ai-card-header">
          <span className="ai-icon">📊</span>
          <h3>AI Usage & Stats</h3>
        </div>
        <div className="ai-loading-spinner" />
      </div>
    );
  }

  return (
    <div className="ai-card ai-usage-stats">
      <div className="ai-card-header">
        <span className="ai-icon">📊</span>
        <h3>AI Usage & Stats</h3>
        <select value={period} onChange={(e) => setPeriod(Number(e.target.value))}>
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {health && (
        <div className={`health-status ${health.status}`}>
          <span className="status-icon">
            {health.status === 'healthy' ? '✅' : '⚠️'}
          </span>
          <span className="status-text">{health.message}</span>
        </div>
      )}

      {health?.checks && (
        <div className="health-checks">
          <div className={`check-item ${health.checks.llm_configured ? 'ok' : 'warn'}`}>
            <span>{health.checks.llm_configured ? '✅' : '❌'}</span>
            <span>LLM Provider</span>
          </div>
          <div className={`check-item ${health.checks.ocr_available ? 'ok' : 'warn'}`}>
            <span>{health.checks.ocr_available ? '✅' : '❌'}</span>
            <span>OCR Engine</span>
          </div>
          <div className={`check-item ${health.checks.prophet_available ? 'ok' : 'warn'}`}>
            <span>{health.checks.prophet_available ? '✅' : '❌'}</span>
            <span>ML Forecasting</span>
          </div>
        </div>
      )}

      {usage && (
        <div className="usage-summary">
          <h4>Usage Summary ({period} days)</h4>
          <div className="usage-grid">
            <div className="usage-item">
              <span className="usage-value">{usage.total_requests || 0}</span>
              <span className="usage-label">Total Requests</span>
            </div>
            <div className="usage-item">
              <span className="usage-value">
                {((usage.total_input_tokens || 0) + (usage.total_output_tokens || 0)).toLocaleString()}
              </span>
              <span className="usage-label">Total Tokens</span>
            </div>
            <div className="usage-item">
              <span className="usage-value">
                ${(usage.total_cost || 0).toFixed(2)}
              </span>
              <span className="usage-label">Estimated Cost</span>
            </div>
            <div className="usage-item">
              <span className="usage-value">
                {usage.avg_latency_ms ? `${usage.avg_latency_ms}ms` : 'N/A'}
              </span>
              <span className="usage-label">Avg Latency</span>
            </div>
          </div>

          {usage.by_feature && Object.keys(usage.by_feature).length > 0 && (
            <div className="usage-by-feature">
              <h5>By Feature</h5>
              <div className="feature-list">
                {Object.entries(usage.by_feature).map(([feature, data]) => (
                  <div key={feature} className="feature-item">
                    <span className="feature-name">{feature}</span>
                    <span className="feature-requests">{data.requests} requests</span>
                    <span className="feature-tokens">{data.tokens?.toLocaleString()} tokens</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {config && (
        <div className="config-summary">
          <h4>Configuration</h4>
          <div className="config-grid">
            <div className="config-section">
              <h5>LLM</h5>
              <div className="config-item">
                <span>Provider:</span>
                <span>{config.llm?.provider}</span>
              </div>
              <div className="config-item">
                <span>Anthropic:</span>
                <span>{config.llm?.anthropic_configured ? '✅ Configured' : '❌ Not set'}</span>
              </div>
              <div className="config-item">
                <span>OpenAI:</span>
                <span>{config.llm?.openai_configured ? '✅ Configured' : '❌ Not set'}</span>
              </div>
            </div>
            <div className="config-section">
              <h5>Cash Flow</h5>
              <div className="config-item">
                <span>Default Horizon:</span>
                <span>{config.cashflow?.default_horizon_days} days</span>
              </div>
              <div className="config-item">
                <span>Prophet ML:</span>
                <span>{config.cashflow?.use_prophet ? '✅ Enabled' : '❌ Disabled'}</span>
              </div>
            </div>
            <div className="config-section">
              <h5>Anomaly Detection</h5>
              <div className="config-item">
                <span>Z-Score Threshold:</span>
                <span>{config.anomaly?.zscore_threshold}</span>
              </div>
              <div className="config-item">
                <span>Min Historical Data:</span>
                <span>{config.anomaly?.min_historical_data}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
