import { useState, useEffect } from 'react';
import { dashboardAPI } from '../../../services/api';

export default function AlertsWidget({ widget, dashboardId, onRemove }) {
  const [data, setData] = useState({ alerts: [] });

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const res = await dashboardAPI.getWidgetData(dashboardId, widget.widget_id);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    }
  };

  return (
    <div className="widget alerts-widget">
      {onRemove && <button className="widget-remove" onClick={onRemove}>x</button>}
      <div className="widget-title">Alerts</div>
      <div className="alerts-list">
        {data.alerts?.length === 0 ? (
          <div className="no-alerts">No alerts</div>
        ) : (
          data.alerts?.map((alert, i) => (
            <div key={i} className={`alert-item ${alert.type}`}>
              {alert.type === 'error' ? '!' : '!'} {alert.message}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
