import { useState, useEffect } from 'react';
import { dashboardAPI } from '../../../services/api';

export default function GaugeWidget({ widget, dashboardId, onRemove }) {
  const [data, setData] = useState({ value: 0, min: 0, max: 100 });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await dashboardAPI.getWidgetData(dashboardId, widget.widget_id);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load gauge data:', err);
    }
  };

  const percentage = ((data.value - data.min) / (data.max - data.min)) * 100;

  return (
    <div className="widget gauge-widget">
      {onRemove && <button className="widget-remove" onClick={onRemove}>x</button>}
      <div className="widget-title">{widget.config?.title || 'Gauge'}</div>
      <div className="gauge-container">
        <svg viewBox="0 0 100 60" className="gauge-svg">
          <path
            d="M10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="var(--bg-tertiary, #e5e7eb)"
            strokeWidth="8"
            strokeLinecap="round"
          />
          <path
            d="M10 50 A 40 40 0 0 1 90 50"
            fill="none"
            stroke="var(--primary, #667eea)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${percentage * 1.26} 126`}
          />
        </svg>
        <div className="gauge-value">{data.value?.toFixed(1) || 0}%</div>
      </div>
    </div>
  );
}
