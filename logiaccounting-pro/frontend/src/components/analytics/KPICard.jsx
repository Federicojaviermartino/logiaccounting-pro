/**
 * KPI Card Component
 * Displays a single KPI with trend indicator
 */

import React from 'react';
import TrendIndicator from './TrendIndicator';

const KPICard = ({
  title,
  value,
  change,
  trend,
  target,
  status,
  icon,
  color = 'blue',
  invertTrend = false
}) => {
  const getTrendClass = () => {
    if (!trend) return '';
    if (invertTrend) {
      return trend === 'up' ? 'negative' : (trend === 'down' ? 'positive' : '');
    }
    return trend === 'up' ? 'positive' : (trend === 'down' ? 'negative' : '');
  };

  const formatChange = (val) => {
    if (val === undefined || val === null) return null;
    const sign = val >= 0 ? '+' : '';
    return `${sign}${val.toFixed(1)}%`;
  };

  return (
    <div className={`kpi-card color-${color}`}>
      <div className="kpi-header">
        <span className="kpi-icon">{icon}</span>
        <span className="kpi-title">{title}</span>
      </div>
      <div className="kpi-body">
        <span className="kpi-value">{value}</span>
        {change !== undefined && change !== null && (
          <span className={`kpi-change ${getTrendClass()}`}>
            {trend === 'up' && '\u2191'}
            {trend === 'down' && '\u2193'}
            {trend === 'stable' && '\u2192'}
            {formatChange(change)}
          </span>
        )}
      </div>
      {target && (
        <div className="kpi-footer">
          <span className="kpi-target">{target}</span>
          {status && <TrendIndicator status={status} size="small" />}
        </div>
      )}
    </div>
  );
};

export default KPICard;
