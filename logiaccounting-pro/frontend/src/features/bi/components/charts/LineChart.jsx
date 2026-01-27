/**
 * LineChart - Line/Area chart visualization
 */

import React, { useRef } from 'react';
import { Line } from 'react-chartjs-2';
import BaseChart, { CHART_COLORS } from './BaseChart';

export default function LineChart({
  title,
  subtitle,
  data,
  config = {},
  onRefresh,
  onSettings,
  isLoading,
  error,
}) {
  const chartRef = useRef(null);

  // Default configuration
  const defaultConfig = {
    showArea: false,
    tension: 0.4,
    showPoints: true,
    pointRadius: 4,
    showGrid: true,
    showLegend: true,
    legendPosition: 'top',
    stacked: false,
    ...config,
  };

  // Prepare chart data
  const chartData = {
    labels: data?.labels || [],
    datasets: (data?.datasets || []).map((dataset, index) => ({
      label: dataset.label,
      data: dataset.data,
      borderColor: dataset.color || CHART_COLORS[index % CHART_COLORS.length],
      backgroundColor: defaultConfig.showArea
        ? `${dataset.color || CHART_COLORS[index % CHART_COLORS.length]}20`
        : 'transparent',
      fill: defaultConfig.showArea,
      tension: defaultConfig.tension,
      pointRadius: defaultConfig.showPoints ? defaultConfig.pointRadius : 0,
      pointHoverRadius: defaultConfig.pointRadius + 2,
      borderWidth: 2,
    })),
  };

  // Chart options
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: defaultConfig.showLegend,
        position: defaultConfig.legendPosition,
        labels: {
          usePointStyle: true,
          padding: 20,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: { size: 13 },
        bodyFont: { size: 12 },
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            const format = data?.format || 'number';

            return `${label}: ${formatValue(value, format)}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: defaultConfig.showGrid,
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          color: '#64748b',
          font: { size: 11 },
        },
      },
      y: {
        stacked: defaultConfig.stacked,
        grid: {
          display: defaultConfig.showGrid,
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          color: '#64748b',
          font: { size: 11 },
          callback: (value) => formatValue(value, data?.format || 'number'),
        },
      },
    },
  };

  return (
    <BaseChart
      title={title}
      subtitle={subtitle}
      chartRef={chartRef}
      onRefresh={onRefresh}
      onSettings={onSettings}
      isLoading={isLoading}
      error={error}
    >
      <Line ref={chartRef} data={chartData} options={options} />
    </BaseChart>
  );
}

// Value formatter
function formatValue(value, format) {
  if (value === null || value === undefined) return '-';

  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    case 'percent':
      return `${value.toFixed(1)}%`;
    case 'decimal':
      return value.toLocaleString('en-US', { minimumFractionDigits: 2 });
    default:
      return value.toLocaleString('en-US');
  }
}
