import { useState, useEffect, useRef } from 'react';
import { dashboardAPI } from '../../../services/api';

export default function ChartWidget({ widget, dashboardId, onRemove }) {
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
      console.error('Failed to load chart data:', err);
    }
  };

  const renderChart = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    if (!data?.datasets?.length || !data?.labels?.length) return;

    const dataset = data.datasets[0];
    const values = dataset.data || [];
    const maxValue = Math.max(...values, 1);
    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    // Draw axes
    ctx.strokeStyle = '#e5e7eb';
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.stroke();

    // Draw line chart
    ctx.strokeStyle = '#667eea';
    ctx.lineWidth = 2;
    ctx.beginPath();

    values.forEach((value, i) => {
      const x = padding + (i / (values.length - 1)) * chartWidth;
      const y = height - padding - (value / maxValue) * chartHeight;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw points
    ctx.fillStyle = '#667eea';
    values.forEach((value, i) => {
      const x = padding + (i / (values.length - 1)) * chartWidth;
      const y = height - padding - (value / maxValue) * chartHeight;
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw labels
    ctx.fillStyle = '#6b7280';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    data.labels.forEach((label, i) => {
      const x = padding + (i / (data.labels.length - 1)) * chartWidth;
      ctx.fillText(label.slice(-5), x, height - 10);
    });
  };

  return (
    <div className="widget chart-widget">
      {onRemove && <button className="widget-remove" onClick={onRemove}>x</button>}
      <div className="widget-title">{widget.config?.title || 'Chart'}</div>
      <div className="chart-container">
        <canvas ref={canvasRef} width={400} height={200} style={{ width: '100%', height: 'calc(100% - 30px)' }} />
      </div>
    </div>
  );
}
