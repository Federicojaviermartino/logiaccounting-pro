/**
 * KPICard - Key Performance Indicator display
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function KPICard({
  title,
  value,
  previousValue,
  format = 'number',
  target,
  sparklineData,
  icon,
  color = 'primary',
  size = 'medium',
  onClick,
}) {
  // Calculate change
  const change = previousValue !== undefined && previousValue !== 0
    ? ((value - previousValue) / previousValue) * 100
    : null;

  const isPositive = change > 0;
  const isNegative = change < 0;

  // Format value
  const formattedValue = formatValue(value, format);
  const formattedTarget = target !== undefined ? formatValue(target, format) : null;

  // Progress towards target
  const targetProgress = target !== undefined ? Math.min((value / target) * 100, 100) : null;

  return (
    <div
      className={`kpi-card size-${size} color-${color} ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
    >
      <div className="kpi-header">
        <span className="kpi-title">{title}</span>
        {icon && <span className="kpi-icon">{icon}</span>}
      </div>

      <div className="kpi-value">{formattedValue}</div>

      {/* Change indicator */}
      {change !== null && (
        <div className={`kpi-change ${isPositive ? 'positive' : isNegative ? 'negative' : 'neutral'}`}>
          {isPositive ? <TrendingUp className="w-4 h-4" /> :
           isNegative ? <TrendingDown className="w-4 h-4" /> :
           <Minus className="w-4 h-4" />}
          <span>{Math.abs(change).toFixed(1)}%</span>
          <span className="change-label">vs previous</span>
        </div>
      )}

      {/* Target progress */}
      {targetProgress !== null && (
        <div className="kpi-target">
          <div className="target-bar">
            <div
              className="target-progress"
              style={{ width: `${targetProgress}%` }}
            />
          </div>
          <div className="target-labels">
            <span>{Math.round(targetProgress)}% of target</span>
            <span>{formattedTarget}</span>
          </div>
        </div>
      )}

      {/* Sparkline */}
      {sparklineData && sparklineData.length > 0 && (
        <div className="kpi-sparkline">
          <Sparkline data={sparklineData} color={color} />
        </div>
      )}

      <style jsx>{`
        .kpi-card {
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          padding: 20px;
          display: flex;
          flex-direction: column;
          transition: all 0.2s;
        }

        .kpi-card.clickable {
          cursor: pointer;
        }

        .kpi-card.clickable:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }

        .kpi-card.color-primary {
          border-left: 4px solid var(--primary);
        }

        .kpi-card.color-success {
          border-left: 4px solid #10b981;
        }

        .kpi-card.color-warning {
          border-left: 4px solid #f59e0b;
        }

        .kpi-card.color-error {
          border-left: 4px solid #ef4444;
        }

        .kpi-card.size-small {
          padding: 16px;
        }

        .kpi-card.size-large {
          padding: 24px;
        }

        .kpi-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .kpi-title {
          font-size: 13px;
          color: var(--text-muted);
          font-weight: 500;
        }

        .kpi-icon {
          font-size: 20px;
        }

        .kpi-value {
          font-size: 28px;
          font-weight: 700;
          color: var(--text-primary);
          line-height: 1.2;
        }

        .size-small .kpi-value {
          font-size: 22px;
        }

        .size-large .kpi-value {
          font-size: 36px;
        }

        .kpi-change {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-top: 12px;
          font-size: 13px;
          font-weight: 500;
        }

        .kpi-change.positive {
          color: #10b981;
        }

        .kpi-change.negative {
          color: #ef4444;
        }

        .kpi-change.neutral {
          color: var(--text-muted);
        }

        .change-label {
          color: var(--text-muted);
          font-weight: 400;
        }

        .kpi-target {
          margin-top: 16px;
        }

        .target-bar {
          height: 6px;
          background: var(--bg-tertiary);
          border-radius: 3px;
          overflow: hidden;
        }

        .target-progress {
          height: 100%;
          background: var(--primary);
          border-radius: 3px;
          transition: width 0.5s ease;
        }

        .target-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 6px;
          font-size: 11px;
          color: var(--text-muted);
        }

        .kpi-sparkline {
          margin-top: 16px;
          height: 40px;
        }
      `}</style>
    </div>
  );
}

// Simple Sparkline Component
function Sparkline({ data, color }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 100 - ((value - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke={color === 'primary' ? '#667eea' :
               color === 'success' ? '#10b981' :
               color === 'warning' ? '#f59e0b' : '#ef4444'}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function formatValue(value, format) {
  if (value === null || value === undefined) return '-';

  switch (format) {
    case 'currency':
      if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      }
      if (value >= 1000) {
        return `$${(value / 1000).toFixed(1)}K`;
      }
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
      }).format(value);
    case 'percent':
      return `${value.toFixed(1)}%`;
    case 'integer':
      return Math.round(value).toLocaleString('en-US');
    default:
      return value.toLocaleString('en-US');
  }
}
