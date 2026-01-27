/**
 * BarChart - Vertical/Horizontal bar chart
 */

import React, { useRef } from 'react';
import { Bar } from 'react-chartjs-2';
import BaseChart, { CHART_COLORS } from './BaseChart';

export default function BarChart({
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
    horizontal: false,
    stacked: false,
    showGrid: true,
    showLegend: true,
    legendPosition: 'top',
    barThickness: 'flex',
    maxBarThickness: 50,
    borderRadius: 4,
    ...config,
  };

  const chartData = {
    labels: data?.labels || [],
    datasets: (data?.datasets || []).map((dataset, index) => ({
      label: dataset.label,
      data: dataset.data,
      backgroundColor: dataset.color || CHART_COLORS[index % CHART_COLORS.length],
      borderColor: dataset.color || CHART_COLORS[index % CHART_COLORS.length],
      borderWidth: 0,
      borderRadius: defaultConfig.borderRadius,
      barThickness: defaultConfig.barThickness,
      maxBarThickness: defaultConfig.maxBarThickness,
    })),
  };

  const options = {
    indexAxis: defaultConfig.horizontal ? 'y' : 'x',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: defaultConfig.showLegend && chartData.datasets.length > 1,
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
      },
    },
    scales: {
      x: {
        stacked: defaultConfig.stacked,
        grid: {
          display: defaultConfig.horizontal ? defaultConfig.showGrid : false,
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
          display: defaultConfig.horizontal ? false : defaultConfig.showGrid,
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          color: '#64748b',
          font: { size: 11 },
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
      <Bar ref={chartRef} data={chartData} options={options} />
    </BaseChart>
  );
}
