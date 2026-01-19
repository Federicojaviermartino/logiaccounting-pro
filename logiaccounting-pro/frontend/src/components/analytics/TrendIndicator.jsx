/**
 * Trend Indicator Component
 * Visual status indicator for KPIs
 */

import React from 'react';

const TrendIndicator = ({ status, size = 'medium' }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'good':
      case 'excellent':
        return { icon: '\u2713', color: 'green', label: 'Good' };
      case 'warning':
      case 'fair':
        return { icon: '!', color: 'yellow', label: 'Warning' };
      case 'critical':
      case 'poor':
        return { icon: '\u2717', color: 'red', label: 'Critical' };
      default:
        return { icon: '\u2013', color: 'gray', label: 'N/A' };
    }
  };

  const config = getStatusConfig();

  return (
    <span
      className={`trend-indicator ${config.color} ${size}`}
      title={config.label}
    >
      {config.icon}
    </span>
  );
};

export default TrendIndicator;
