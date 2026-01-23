/**
 * BaseChart - Base component for all chart types
 */

import React, { useRef, useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Maximize2, Download, Settings, RefreshCw } from 'lucide-react';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Default color palette
export const CHART_COLORS = [
  '#667eea', // Primary
  '#10b981', // Success
  '#f59e0b', // Warning
  '#ef4444', // Error
  '#8b5cf6', // Purple
  '#06b6d4', // Cyan
  '#ec4899', // Pink
  '#84cc16', // Lime
  '#f97316', // Orange
  '#6366f1', // Indigo
];

export default function BaseChart({
  title,
  subtitle,
  chartRef,
  onExport,
  onRefresh,
  onSettings,
  isLoading,
  error,
  children,
  className = '',
}) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);

  const handleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const handleExport = (format) => {
    if (chartRef?.current) {
      const canvas = chartRef.current.canvas;
      const url = canvas.toDataURL(`image/${format}`);

      const link = document.createElement('a');
      link.download = `${title || 'chart'}.${format}`;
      link.href = url;
      link.click();
    }
    onExport?.(format);
  };

  return (
    <div
      ref={containerRef}
      className={`base-chart ${className} ${isFullscreen ? 'fullscreen' : ''}`}
    >
      {/* Header */}
      <div className="chart-header">
        <div className="chart-title-section">
          {title && <h3 className="chart-title">{title}</h3>}
          {subtitle && <p className="chart-subtitle">{subtitle}</p>}
        </div>

        <div className="chart-actions">
          {onRefresh && (
            <button
              className="action-btn"
              onClick={onRefresh}
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          )}
          {onSettings && (
            <button
              className="action-btn"
              onClick={onSettings}
              title="Settings"
            >
              <Settings className="w-4 h-4" />
            </button>
          )}
          <button
            className="action-btn"
            onClick={() => handleExport('png')}
            title="Download PNG"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            className="action-btn"
            onClick={handleFullscreen}
            title="Fullscreen"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="chart-content">
        {isLoading && (
          <div className="chart-loading">
            <div className="spinner" />
            <span>Loading...</span>
          </div>
        )}

        {error && (
          <div className="chart-error">
            <span>{error}</span>
          </div>
        )}

        {!isLoading && !error && children}
      </div>

      <style jsx>{`
        .base-chart {
          background: var(--bg-primary);
          border: 1px solid var(--border-color);
          border-radius: 12px;
          display: flex;
          flex-direction: column;
          height: 100%;
        }

        .base-chart.fullscreen {
          position: fixed;
          inset: 0;
          z-index: 1000;
          border-radius: 0;
        }

        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
        }

        .chart-title {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
        }

        .chart-subtitle {
          margin: 4px 0 0;
          font-size: 13px;
          color: var(--text-muted);
        }

        .chart-actions {
          display: flex;
          gap: 4px;
        }

        .action-btn {
          padding: 6px;
          border-radius: 6px;
          color: var(--text-muted);
          transition: all 0.2s;
        }

        .action-btn:hover {
          background: var(--bg-secondary);
          color: var(--text-primary);
        }

        .chart-content {
          flex: 1;
          padding: 20px;
          position: relative;
          min-height: 200px;
        }

        .chart-loading,
        .chart-error {
          position: absolute;
          inset: 0;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 12px;
          background: var(--bg-primary);
        }

        .spinner {
          width: 32px;
          height: 32px;
          border: 3px solid var(--border-color);
          border-top-color: var(--primary);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        .chart-error {
          color: var(--error);
          background: rgba(239, 68, 68, 0.05);
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
