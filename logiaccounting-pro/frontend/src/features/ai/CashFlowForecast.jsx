/**
 * Cash Flow Forecast Component
 * AI-powered cash flow prediction visualization
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getAuthHeaders } from '../../utils/tokenService';

const API_BASE = '/api/v1/ai/cashflow';

export default function CashFlowForecast() {
  const { t } = useTranslation();
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [horizonDays, setHorizonDays] = useState(30);

  useEffect(() => {
    fetchForecastSummary();
  }, []);

  const fetchForecastSummary = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/summary`, {
        headers: {
          ...getAuthHeaders(),
        },
      });
      const data = await res.json();
      setForecast(data);
    } catch (err) {
      setError('Failed to load forecast');
    } finally {
      setLoading(false);
    }
  };

  const generateForecast = async () => {
    try {
      setLoading(true);
      // In production, this would use actual transaction data
      const res = await fetch(`${API_BASE}/forecast`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          transactions: [],
          current_balance: 100000,
          horizon_days: horizonDays,
        }),
      });
      const data = await res.json();
      setForecast(data);
    } catch (err) {
      setError('Failed to generate forecast');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="ai-card loading">
        <div className="ai-card-header">
          <span className="ai-icon">📈</span>
          <h3>Cash Flow Forecast</h3>
        </div>
        <div className="ai-loading-spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="ai-card error">
        <div className="ai-card-header">
          <span className="ai-icon">📈</span>
          <h3>Cash Flow Forecast</h3>
        </div>
        <p className="error-message">{error}</p>
        <button onClick={fetchForecastSummary} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="ai-card cashflow-forecast">
      <div className="ai-card-header">
        <span className="ai-icon">📈</span>
        <h3>Cash Flow Forecast</h3>
        <div className="horizon-selector">
          <select
            value={horizonDays}
            onChange={(e) => setHorizonDays(Number(e.target.value))}
          >
            <option value={30}>30 Days</option>
            <option value={60}>60 Days</option>
            <option value={90}>90 Days</option>
          </select>
          <button onClick={generateForecast} className="generate-btn">
            Generate
          </button>
        </div>
      </div>

      {forecast?.has_forecast ? (
        <div className="forecast-content">
          <div className="forecast-summary">
            <div className="summary-item">
              <span className="label">Current Balance</span>
              <span className="value">
                ${forecast.current_balance?.toLocaleString() || 0}
              </span>
            </div>
            <div className="summary-item">
              <span className="label">Predicted End Balance</span>
              <span className={`value ${forecast.predicted_end_balance > forecast.current_balance ? 'positive' : 'negative'}`}>
                ${forecast.predicted_end_balance?.toLocaleString() || 0}
              </span>
            </div>
            <div className="summary-item">
              <span className="label">Risk Score</span>
              <span className={`value risk-${forecast.risk_score > 0.5 ? 'high' : forecast.risk_score > 0.3 ? 'medium' : 'low'}`}>
                {((forecast.risk_score || 0) * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {forecast.insights && forecast.insights.length > 0 && (
            <div className="forecast-insights">
              <h4>Insights</h4>
              <ul>
                {forecast.insights.map((insight, idx) => (
                  <li key={idx}>{insight}</li>
                ))}
              </ul>
            </div>
          )}

          {forecast.top_recommendations && forecast.top_recommendations.length > 0 && (
            <div className="forecast-recommendations">
              <h4>Recommendations</h4>
              <ul>
                {forecast.top_recommendations.map((rec, idx) => (
                  <li key={idx} className={`priority-${rec.priority}`}>
                    <span className="rec-type">{rec.type}</span>
                    <span className="rec-desc">{rec.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="no-forecast">
          <p>No forecast available. Generate a forecast to see predictions.</p>
          <button onClick={generateForecast} className="generate-btn primary">
            Generate Forecast
          </button>
        </div>
      )}
    </div>
  );
}
