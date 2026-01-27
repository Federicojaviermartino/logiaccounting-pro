/**
 * Forecast Chart Component
 * Visualizes cash flow predictions with confidence intervals
 */

import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Title,
  Tooltip,
  Legend
);

const ForecastChart = ({ data, scenario }) => {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return null;

    const labels = data.map(d => {
      const date = new Date(d.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    return {
      labels,
      datasets: [
        // Confidence interval (area)
        {
          label: 'Confidence Range',
          data: data.map(d => d.confidence_high),
          fill: '+1',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderColor: 'transparent',
          pointRadius: 0,
        },
        {
          label: 'Lower Bound',
          data: data.map(d => d.confidence_low),
          fill: false,
          backgroundColor: 'transparent',
          borderColor: 'transparent',
          pointRadius: 0,
        },
        // Main prediction line
        {
          label: 'Predicted Balance',
          data: data.map(d => d.predicted_balance),
          fill: false,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgb(59, 130, 246)',
          borderWidth: 2,
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 6,
        },
        // Inflows
        {
          label: 'Inflows',
          data: data.map(d => d.predicted_inflows),
          fill: false,
          borderColor: 'rgb(34, 197, 94)',
          backgroundColor: 'rgb(34, 197, 94)',
          borderWidth: 1,
          borderDash: [5, 5],
          tension: 0.3,
          pointRadius: 0,
          yAxisID: 'y1',
        },
        // Outflows
        {
          label: 'Outflows',
          data: data.map(d => d.predicted_outflows),
          fill: false,
          borderColor: 'rgb(239, 68, 68)',
          backgroundColor: 'rgb(239, 68, 68)',
          borderWidth: 1,
          borderDash: [5, 5],
          tension: 0.3,
          pointRadius: 0,
          yAxisID: 'y1',
        },
      ],
    };
  }, [data]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          filter: (item) => item.text !== 'Lower Bound' && item.text !== 'Confidence Range',
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const value = context.parsed.y;
            return `${context.dataset.label}: $${value.toLocaleString()}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Balance ($)',
        },
        ticks: {
          callback: (value) => `$${(value / 1000).toFixed(0)}K`,
        },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Daily Flow ($)',
        },
        grid: {
          drawOnChartArea: false,
        },
        ticks: {
          callback: (value) => `$${(value / 1000).toFixed(0)}K`,
        },
      },
    },
  };

  if (!chartData) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-500">
        No forecast data available
      </div>
    );
  }

  return (
    <div className="h-80">
      <Line data={chartData} options={options} />
    </div>
  );
};

export default ForecastChart;
