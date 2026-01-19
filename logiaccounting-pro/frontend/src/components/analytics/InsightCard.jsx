/**
 * Insight Card Component
 * Displays AI-generated business insights
 */

import React from 'react';

const InsightCard = ({ icon, title, detail, type }) => {
  return (
    <div className={`insight-card type-${type}`}>
      <span className="insight-icon">{icon}</span>
      <div className="insight-content">
        <h4 className="insight-title">{title}</h4>
        <p className="insight-detail">{detail}</p>
      </div>
    </div>
  );
};

export default InsightCard;
