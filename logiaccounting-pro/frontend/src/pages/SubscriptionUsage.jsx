import { useState, useEffect } from 'react';
import { subscriptionAPI, quotaAPI, featuresAPI, tenantAPI } from '../services/tenantApi';

const TIER_COLORS = {
  free: '#6B7280',
  standard: '#3B82F6',
  professional: '#8B5CF6',
  business: '#F59E0B',
  enterprise: '#EF4444'
};

export default function SubscriptionUsage() {
  const [tenant, setTenant] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [usage, setUsage] = useState(null);
  const [features, setFeatures] = useState([]);
  const [upgradeSuggestions, setUpgradeSuggestions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [tenantRes, subRes, plansRes, usageRes, featuresRes, suggestionsRes] = await Promise.all([
        tenantAPI.getCurrent(),
        subscriptionAPI.get(),
        subscriptionAPI.getPlans(),
        quotaAPI.getUsage(),
        featuresAPI.list(),
        featuresAPI.getUpgradeSuggestions()
      ]);
      setTenant(tenantRes.data.tenant);
      setSubscription(subRes.data.subscription);
      setPlans(plansRes.data.plans);
      setUsage(usageRes.data);
      setFeatures(featuresRes.data.features);
      setUpgradeSuggestions(suggestionsRes.data);
    } catch (err) {
      setError('Failed to load subscription data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (tier) => {
    try {
      await subscriptionAPI.upgrade({ tier, billing_cycle: 'monthly' });
      setShowUpgradeModal(false);
      setSuccess('Subscription upgraded successfully');
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upgrade subscription');
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel your subscription? Your plan will remain active until the end of the billing period.')) return;
    try {
      await subscriptionAPI.cancel({ cancel_at_period_end: true });
      setSuccess('Subscription will be cancelled at the end of the billing period');
      loadData();
    } catch (err) {
      setError('Failed to cancel subscription');
    }
  };

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return '#EF4444';
    if (percentage >= 75) return '#F59E0B';
    return '#10B981';
  };

  const formatLimit = (limit) => {
    if (limit === -1) return 'Unlimited';
    if (limit >= 1000) return `${(limit / 1000).toFixed(0)}K`;
    return limit.toString();
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">Loading subscription...</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Subscription & Usage</h1>
          <p className="page-subtitle">Manage your plan and monitor resource usage</p>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button className="alert-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
          <button className="alert-close" onClick={() => setSuccess(null)}>×</button>
        </div>
      )}

      {/* Current Plan Card */}
      <div className="card plan-card" style={{ borderTop: `4px solid ${TIER_COLORS[subscription?.tier]}` }}>
        <div className="card-body">
          <div className="plan-header">
            <div>
              <span className="plan-label">Current Plan</span>
              <h2 className="plan-name">{subscription?.tier?.toUpperCase()}</h2>
            </div>
            <div className="plan-price">
              {subscription?.price_cents > 0 ? (
                <>
                  <span className="price-amount">${subscription.price_cents / 100}</span>
                  <span className="price-period">/{subscription.billing_cycle}</span>
                </>
              ) : (
                <span className="price-amount">Free</span>
              )}
            </div>
          </div>
          <div className="plan-details">
            <div className="detail-item">
              <span className="detail-label">Status</span>
              <span className={`badge badge-${subscription?.status === 'active' ? 'success' : 'warning'}`}>
                {subscription?.status}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Billing Cycle</span>
              <span>{subscription?.billing_cycle}</span>
            </div>
            {subscription?.current_period_end && (
              <div className="detail-item">
                <span className="detail-label">Next Billing</span>
                <span>{new Date(subscription.current_period_end).toLocaleDateString()}</span>
              </div>
            )}
          </div>
          <div className="plan-actions">
            {subscription?.tier !== 'enterprise' && (
              <button className="btn btn-primary" onClick={() => setShowUpgradeModal(true)}>
                Upgrade Plan
              </button>
            )}
            {subscription?.tier !== 'free' && !subscription?.cancel_at_period_end && (
              <button className="btn btn-outline" onClick={handleCancel}>
                Cancel Subscription
              </button>
            )}
          </div>
          {subscription?.cancel_at_period_end && (
            <div className="alert alert-warning mt-4">
              Your subscription will be cancelled on {new Date(subscription.current_period_end).toLocaleDateString()}
            </div>
          )}
        </div>
      </div>

      {/* Usage Overview */}
      <div className="card">
        <div className="card-header">
          <h3>Resource Usage</h3>
        </div>
        <div className="card-body">
          <div className="usage-grid">
            {usage?.usage?.map(item => (
              <div key={item.resource} className="usage-item">
                <div className="usage-header">
                  <span className="usage-label">{item.resource.replace('_', ' ')}</span>
                  <span className="usage-value">
                    {item.current} / {item.unlimited ? '∞' : formatLimit(item.limit)}
                  </span>
                </div>
                {!item.unlimited && (
                  <div className="usage-bar">
                    <div
                      className="usage-fill"
                      style={{
                        width: `${Math.min(item.percentage, 100)}%`,
                        backgroundColor: getUsageColor(item.percentage)
                      }}
                    />
                  </div>
                )}
                {item.percentage >= 80 && !item.unlimited && (
                  <span className="usage-warning">
                    {item.percentage >= 100 ? 'Limit reached' : 'Approaching limit'}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="card">
        <div className="card-header">
          <h3>Available Features</h3>
        </div>
        <div className="card-body">
          <div className="features-grid">
            {features.filter(f => f.is_enabled).map(feature => (
              <div key={feature.name} className="feature-item enabled">
                <span className="feature-icon">✓</span>
                <div className="feature-info">
                  <span className="feature-name">{feature.display_name}</span>
                  <span className="feature-description">{feature.description}</span>
                </div>
              </div>
            ))}
          </div>

          {upgradeSuggestions?.new_features?.length > 0 && (
            <>
              <h4 className="mt-4">Unlock with {upgradeSuggestions.suggested_tier?.toUpperCase()}</h4>
              <div className="features-grid">
                {upgradeSuggestions.new_features.map(feature => (
                  <div key={feature.name} className="feature-item locked">
                    <span className="feature-icon">🔒</span>
                    <div className="feature-info">
                      <span className="feature-name">{feature.display_name}</span>
                      <span className="feature-description">{feature.description}</span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Upgrade Modal */}
      {showUpgradeModal && (
        <div className="modal-overlay">
          <div className="modal modal-lg">
            <div className="modal-header">
              <h3>Choose Your Plan</h3>
              <button className="modal-close" onClick={() => setShowUpgradeModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="plans-grid">
                {plans.filter(p => p.tier !== 'free').map(plan => (
                  <div
                    key={plan.tier}
                    className={`plan-option ${plan.is_popular ? 'popular' : ''} ${plan.tier === subscription?.tier ? 'current' : ''}`}
                    onClick={() => setSelectedPlan(plan.tier)}
                  >
                    {plan.is_popular && <span className="popular-badge">Most Popular</span>}
                    <h4>{plan.name}</h4>
                    <p className="plan-description">{plan.description}</p>
                    <div className="plan-price">
                      {plan.price_monthly > 0 ? (
                        <>
                          <span className="price">${plan.price_monthly}</span>
                          <span className="period">/month</span>
                        </>
                      ) : (
                        <span className="price">Contact Sales</span>
                      )}
                    </div>
                    <ul className="plan-features">
                      <li>{formatLimit(plan.limits.max_users)} users</li>
                      <li>{formatLimit(plan.limits.max_storage_mb)}MB storage</li>
                      <li>{formatLimit(plan.limits.max_api_calls_daily)} API calls/day</li>
                      <li>{formatLimit(plan.limits.max_invoices_monthly)} invoices/month</li>
                    </ul>
                    {plan.tier === subscription?.tier ? (
                      <button className="btn btn-outline" disabled>Current Plan</button>
                    ) : plan.tier === 'enterprise' ? (
                      <button className="btn btn-outline">Contact Sales</button>
                    ) : (
                      <button
                        className={`btn ${selectedPlan === plan.tier ? 'btn-primary' : 'btn-outline'}`}
                        onClick={() => handleUpgrade(plan.tier)}
                      >
                        {selectedPlan === plan.tier ? 'Confirm Upgrade' : 'Select'}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowUpgradeModal(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .plan-card {
          margin-bottom: 1.5rem;
        }
        .plan-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 1.5rem;
        }
        .plan-label {
          color: #6B7280;
          font-size: 0.875rem;
        }
        .plan-name {
          font-size: 2rem;
          font-weight: 700;
          margin: 0;
        }
        .plan-price {
          text-align: right;
        }
        .price-amount {
          font-size: 2rem;
          font-weight: 700;
        }
        .price-period {
          color: #6B7280;
        }
        .plan-details {
          display: flex;
          gap: 2rem;
          margin-bottom: 1.5rem;
        }
        .detail-item {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }
        .detail-label {
          color: #6B7280;
          font-size: 0.75rem;
        }
        .plan-actions {
          display: flex;
          gap: 1rem;
        }
        .usage-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 1.5rem;
        }
        .usage-item {
          padding: 1rem;
          background: #F9FAFB;
          border-radius: 8px;
        }
        .usage-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.5rem;
          text-transform: capitalize;
        }
        .usage-label {
          font-weight: 500;
        }
        .usage-value {
          color: #6B7280;
        }
        .usage-bar {
          height: 8px;
          background: #E5E7EB;
          border-radius: 4px;
          overflow: hidden;
        }
        .usage-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s;
        }
        .usage-warning {
          display: block;
          margin-top: 0.5rem;
          font-size: 0.75rem;
          color: #F59E0B;
        }
        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 1rem;
        }
        .feature-item {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          padding: 0.75rem;
          border-radius: 8px;
        }
        .feature-item.enabled {
          background: #F0FDF4;
        }
        .feature-item.locked {
          background: #F3F4F6;
          opacity: 0.7;
        }
        .feature-icon {
          font-size: 1.25rem;
        }
        .feature-name {
          font-weight: 500;
          display: block;
        }
        .feature-description {
          font-size: 0.75rem;
          color: #6B7280;
        }
        .plans-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 1.5rem;
        }
        .plan-option {
          padding: 1.5rem;
          border: 2px solid #E5E7EB;
          border-radius: 12px;
          text-align: center;
          cursor: pointer;
          position: relative;
          transition: border-color 0.2s;
        }
        .plan-option:hover {
          border-color: #3B82F6;
        }
        .plan-option.popular {
          border-color: #8B5CF6;
        }
        .plan-option.current {
          border-color: #10B981;
        }
        .popular-badge {
          position: absolute;
          top: -12px;
          left: 50%;
          transform: translateX(-50%);
          background: #8B5CF6;
          color: white;
          padding: 4px 12px;
          border-radius: 9999px;
          font-size: 0.75rem;
        }
        .plan-option h4 {
          margin: 0 0 0.5rem;
        }
        .plan-description {
          color: #6B7280;
          font-size: 0.875rem;
          margin-bottom: 1rem;
        }
        .plan-option .price {
          font-size: 1.5rem;
          font-weight: 700;
        }
        .plan-option .period {
          color: #6B7280;
        }
        .plan-features {
          list-style: none;
          padding: 0;
          margin: 1rem 0;
          text-align: left;
        }
        .plan-features li {
          padding: 0.25rem 0;
          color: #6B7280;
          font-size: 0.875rem;
        }
        .plan-features li::before {
          content: "✓ ";
          color: #10B981;
        }
      `}</style>
    </div>
  );
}
