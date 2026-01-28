/**
 * Payment Optimizer Component
 * AI-powered payment scheduling and optimization
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getAuthHeaders } from '../../utils/tokenService';

const API_BASE = '/api/v1/ai/payments';

export default function PaymentOptimizer() {
  const { t } = useTranslation();
  const [recommendations, setRecommendations] = useState([]);
  const [savings, setSavings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('pending');

  useEffect(() => {
    fetchRecommendations();
    fetchSavings();
  }, [filter]);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/recommendations?status=${filter}`, {
        headers: {
          ...getAuthHeaders(),
        },
      });
      const data = await res.json();
      setRecommendations(data);
    } catch (err) {
      setError('Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const fetchSavings = async () => {
    try {
      const res = await fetch(`${API_BASE}/savings`, {
        headers: {
          ...getAuthHeaders(),
        },
      });
      const data = await res.json();
      setSavings(data);
    } catch (err) {
      console.error('Failed to fetch savings:', err);
    }
  };

  const acceptRecommendation = async (id) => {
    try {
      await fetch(`${API_BASE}/recommendations/${id}/accept`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
        },
      });
      fetchRecommendations();
      fetchSavings();
    } catch (err) {
      setError('Failed to accept recommendation');
    }
  };

  const rejectRecommendation = async (id) => {
    try {
      await fetch(`${API_BASE}/recommendations/${id}/reject`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ reason: 'User declined' }),
      });
      fetchRecommendations();
    } catch (err) {
      setError('Failed to reject recommendation');
    }
  };

  const getTypeIcon = (type) => {
    const icons = {
      'early_discount': '💰',
      'batch_payment': '📦',
      'delay_payment': '⏰',
      'prioritize': '⚡',
    };
    return icons[type] || '💳';
  };

  const getTypeName = (type) => {
    const names = {
      'early_discount': 'Early Discount',
      'batch_payment': 'Batch Payment',
      'delay_payment': 'Timing Optimization',
      'prioritize': 'Priority Payment',
    };
    return names[type] || type;
  };

  return (
    <div className="ai-card payment-optimizer">
      <div className="ai-card-header">
        <span className="ai-icon">💳</span>
        <h3>Payment Optimizer</h3>
      </div>

      {savings && (
        <div className="savings-summary">
          <div className="savings-item">
            <span className="label">Potential Savings</span>
            <span className="value highlight">
              ${savings.pending_savings?.toLocaleString() || 0}
            </span>
          </div>
          <div className="savings-item">
            <span className="label">Realized Savings</span>
            <span className="value positive">
              ${savings.realized_savings?.toLocaleString() || 0}
            </span>
          </div>
          <div className="savings-item">
            <span className="label">Pending Actions</span>
            <span className="value">{savings.pending_recommendations || 0}</span>
          </div>
        </div>
      )}

      <div className="filter-tabs">
        <button
          className={filter === 'pending' ? 'active' : ''}
          onClick={() => setFilter('pending')}
        >
          Pending
        </button>
        <button
          className={filter === 'accepted' ? 'active' : ''}
          onClick={() => setFilter('accepted')}
        >
          Accepted
        </button>
        <button
          className={filter === 'all' ? 'active' : ''}
          onClick={() => setFilter('all')}
        >
          All
        </button>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="ai-loading-spinner" />
        </div>
      ) : error ? (
        <div className="error-state">
          <p>{error}</p>
          <button onClick={fetchRecommendations}>Retry</button>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="empty-state">
          <span>✅</span>
          <p>No pending recommendations</p>
        </div>
      ) : (
        <div className="recommendations-list">
          {recommendations.map((rec) => (
            <div key={rec.id} className={`recommendation-card priority-${rec.priority}`}>
              <div className="rec-header">
                <span className="rec-type">
                  {getTypeIcon(rec.recommendation_type)}
                  {getTypeName(rec.recommendation_type)}
                </span>
                <span className={`rec-priority ${rec.priority}`}>
                  {rec.priority}
                </span>
              </div>

              <h4>{rec.title}</h4>
              <p className="rec-description">{rec.description}</p>

              <div className="rec-details">
                {rec.potential_savings > 0 && (
                  <div className="detail">
                    <span className="label">Savings</span>
                    <span className="value positive">
                      ${rec.potential_savings.toLocaleString()}
                    </span>
                  </div>
                )}
                {rec.suggested_payment_date && (
                  <div className="detail">
                    <span className="label">Suggested Date</span>
                    <span className="value">{rec.suggested_payment_date}</span>
                  </div>
                )}
                {rec.deadline && (
                  <div className="detail">
                    <span className="label">Deadline</span>
                    <span className="value urgent">{rec.deadline}</span>
                  </div>
                )}
                {rec.confidence_score && (
                  <div className="detail">
                    <span className="label">Confidence</span>
                    <span className="value">
                      {(rec.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>

              {rec.status === 'pending' && (
                <div className="rec-actions">
                  <button
                    className="btn-reject"
                    onClick={() => rejectRecommendation(rec.id)}
                  >
                    Dismiss
                  </button>
                  <button
                    className="btn-accept"
                    onClick={() => acceptRecommendation(rec.id)}
                  >
                    Accept
                  </button>
                </div>
              )}

              {rec.status !== 'pending' && (
                <div className={`rec-status ${rec.status}`}>
                  {rec.status === 'accepted' ? '✅ Accepted' : '❌ Rejected'}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
