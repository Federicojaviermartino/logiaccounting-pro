import { useState, useEffect, useRef } from 'react';
import { dashboardAPI } from '../../../services/api';

export default function DonutWidget({ widget, dashboardId, onRemove }) {
  const [data, setData] = useState(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (data && canvasRef.current) {
      renderChart();
    }
  }, [data]);

  const loadData = async () => {
    try {
      const res = await dashboardAPI.getWidgetData(dashboardId, widget.widget_id);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load donut data:', err);
    }
  };

  const renderChart = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 20;
    const innerRadius = radius * 0.6;

    ctx.clearRect(0, 0, width, height);

    if (!data?.data?.length) return;

    const total = data.data.reduce((sum, val) => sum + val, 0);
    const colors = ['#667eea', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

    let startAngle = -Math.PI / 2;

    data.data.forEach((value, i) => {
      const sliceAngle = (value / total) * Math.PI * 2;

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
      ctx.closePath();
      ctx.fillStyle = colors[i % colors.length];
      ctx.fill();

      startAngle += sliceAngle;
    });

    // Draw inner circle (donut hole)
    ctx.beginPath();
    ctx.arc(centerX, centerY, innerRadius, 0, Math.PI * 2);
    ctx.fillStyle = 'var(--card-bg, #fff)';
    ctx.fill();

    // Draw total in center
    ctx.fillStyle = 'var(--text-primary, #000)';
    ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`$${(total / 1000).toFixed(0)}k`, centerX, centerY);
  };

  return (
    <div className="widget donut-widget">
      {onRemove && <button className="widget-remove" onClick={onRemove}>x</button>}
      <div className="widget-title">{widget.config?.title || 'Chart'}</div>
      <div className="chart-container">
        <canvas ref={canvasRef} width={200} height={200} style={{ width: '100%', height: 'calc(100% - 30px)' }} />
      </div>
    </div>
  );
}
