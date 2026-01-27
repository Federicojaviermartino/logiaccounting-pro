import { useState, useEffect } from 'react';
import { dashboardAPI } from '../../../services/api';

export default function KPIWidget({ widget, dashboardId, onRemove }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const res = await dashboardAPI.getWidgetData(dashboardId, widget.widget_id);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load KPI data:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value, format) => {
    if (format === 'currency') return `$${value?.toLocaleString() || 0}`;
    if (format === 'percent') return `${value?.toFixed(1) || 0}%`;
    return value?.toLocaleString() || 0;
  };

  if (loading) return <div className="widget-loading">Loading...</div>;

  return (
    <div className="widget kpi-widget">
      {onRemove && (
        <button className="widget-remove" onClick={onRemove}>x</button>
      )}
      <div className="kpi-title">{widget.config?.title || 'KPI'}</div>
      <div className="kpi-value">{formatValue(data?.value, data?.format)}</div>
      {data?.trend !== undefined && (
        <div className={`kpi-trend ${data.trend >= 0 ? 'positive' : 'negative'}`}>
          {data.trend >= 0 ? '+' : ''}{Math.abs(data.trend)}%
        </div>
      )}
      {data?.count !== undefined && (
        <div className="kpi-count">{data.count} items</div>
      )}
    </div>
  );
}
