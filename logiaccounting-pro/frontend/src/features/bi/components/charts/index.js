/**
 * Charts Module - Export all chart components
 */

export { default as BaseChart, CHART_COLORS } from './BaseChart';
export { default as LineChart } from './LineChart';
export { default as BarChart } from './BarChart';
export { default as PieChart } from './PieChart';
export { default as KPICard } from './KPICard';
export { default as DataTable } from './DataTable';
export { default as PivotTable } from './PivotTable';

// Chart type registry for dynamic rendering
export const CHART_TYPES = {
  line: {
    component: 'LineChart',
    label: 'Line Chart',
    icon: '📈',
    supportedDataTypes: ['time_series', 'trend'],
  },
  bar: {
    component: 'BarChart',
    label: 'Bar Chart',
    icon: '📊',
    supportedDataTypes: ['categorical', 'comparison'],
  },
  pie: {
    component: 'PieChart',
    label: 'Pie Chart',
    icon: '🥧',
    supportedDataTypes: ['part_of_whole'],
  },
  donut: {
    component: 'PieChart',
    label: 'Donut Chart',
    icon: '🍩',
    config: { donut: true },
    supportedDataTypes: ['part_of_whole'],
  },
  kpi: {
    component: 'KPICard',
    label: 'KPI Card',
    icon: '🎯',
    supportedDataTypes: ['single_value', 'metric'],
  },
  table: {
    component: 'DataTable',
    label: 'Data Table',
    icon: '📋',
    supportedDataTypes: ['tabular', 'detail'],
  },
  pivot: {
    component: 'PivotTable',
    label: 'Pivot Table',
    icon: '📑',
    supportedDataTypes: ['aggregated', 'summary'],
  },
};
