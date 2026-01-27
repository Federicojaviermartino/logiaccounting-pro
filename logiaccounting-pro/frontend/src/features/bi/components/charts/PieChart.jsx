/**
 * PieChart - Pie/Donut chart visualization
 */

import React, { useRef } from 'react';
import { Pie, Doughnut } from 'react-chartjs-2';
import BaseChart, { CHART_COLORS } from './BaseChart';

export default function PieChart({
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

  const defaultConfig = {
    donut: false,
    cutout: '60%',
    showLegend: true,
    legendPosition: 'right',
    showLabels: true,
    showValues: true,
    ...config,
  };

  const chartData = {
    labels: data?.labels || [],
    datasets: [{
      data: data?.values || [],
      backgroundColor: data?.colors || CHART_COLORS,
      borderColor: '#ffffff',
      borderWidth: 2,
      hoverOffset: 8,
    }],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: defaultConfig.donut ? defaultConfig.cutout : 0,
    plugins: {
      legend: {
        display: defaultConfig.showLegend,
        position: defaultConfig.legendPosition,
        labels: {
          usePointStyle: true,
          padding: 16,
          generateLabels: (chart) => {
            const datasets = chart.data.datasets;
            return chart.data.labels.map((label, i) => ({
              text: `${label} (${formatValue(datasets[0].data[i], data?.format)})`,
              fillStyle: datasets[0].backgroundColor[i],
              hidden: false,
              index: i,
            }));
          },
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
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const value = context.raw;
            const percentage = ((value / total) * 100).toFixed(1);
            return `${formatValue(value, data?.format)} (${percentage}%)`;
          },
        },
      },
    },
  };

  const ChartComponent = defaultConfig.donut ? Doughnut : Pie;

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
      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <ChartComponent ref={chartRef} data={chartData} options={options} />
      </div>
    </BaseChart>
  );
}

function formatValue(value, format) {
  if (value === null || value === undefined) return '-';

  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
      }).format(value);
    case 'percent':
      return `${value.toFixed(1)}%`;
    default:
      return value.toLocaleString('en-US');
  }
}
