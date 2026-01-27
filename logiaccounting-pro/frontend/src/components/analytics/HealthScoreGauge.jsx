/**
 * Health Score Gauge Component
 * Visual gauge display for financial health score
 */

import React from 'react';

const HealthScoreGauge = ({ score, grade, category }) => {
  const getScoreColor = () => {
    if (score >= 80) return '#22c55e'; // Green
    if (score >= 60) return '#3b82f6'; // Blue
    if (score >= 40) return '#f59e0b'; // Yellow
    if (score >= 20) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="health-score-gauge">
      <svg viewBox="0 0 100 100" className="gauge-svg">
        {/* Background circle */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="8"
        />
        {/* Score arc */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={getScoreColor()}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          transform="rotate(-90 50 50)"
          style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
        />
        {/* Score text */}
        <text
          x="50"
          y="45"
          textAnchor="middle"
          className="score-value"
          fill={getScoreColor()}
        >
          {score}
        </text>
        <text
          x="50"
          y="58"
          textAnchor="middle"
          className="score-grade"
        >
          Grade: {grade}
        </text>
      </svg>
      <div className="score-category">
        <span className={`category-badge ${category?.toLowerCase()}`}>
          {category}
        </span>
      </div>
    </div>
  );
};

export default HealthScoreGauge;
