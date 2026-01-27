/**
 * Executive Dashboard - Financial KPIs and Summary
 */
import { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, Percent, 
  BarChart2, PieChart, Activity, RefreshCw 
} from 'lucide-react';
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
  Filler
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import reportingAPI from '../services/reportingAPI';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler
);

export default function ExecutiveDashboard() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await reportingAPI.getDashboardSummary();
      setSummary(response.data);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) return '-';
    return `${Number(value).toFixed(1)}%`;
  };

  const formatRatio = (value) => {
    if (value === null || value === undefined) return '-';
    return `${Number(value).toFixed(2)}x`;
  };

  const getKPIStatusColor = (status) => {
    switch (status) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'warning': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-green-600 bg-green-50';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-600 p-4 rounded-lg">
        {error}
        <button onClick={loadDashboard} className="ml-4 underline">Retry</button>
      </div>
    );
  }

  // Chart data
  const revenueChartData = {
    labels: summary?.revenue_trend?.map(t => t.period) || [],
    datasets: [{
      label: 'Revenue',
      data: summary?.revenue_trend?.map(t => t.value) || [],
      borderColor: 'rgb(59, 130, 246)',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true,
      tension: 0.4
    }]
  };

  const expenseChartData = {
    labels: summary?.expense_trend?.map(t => t.period) || [],
    datasets: [{
      label: 'Expenses',
      data: summary?.expense_trend?.map(t => t.value) || [],
      backgroundColor: 'rgba(239, 68, 68, 0.8)',
      borderRadius: 4
    }]
  };

  const cashPositionData = {
    labels: ['Cash', 'Receivables', 'Payables'],
    datasets: [{
      data: [
        Number(summary?.cash_balance || 0),
        Number(summary?.ar_balance || 0),
        Number(summary?.ap_balance || 0)
      ],
      backgroundColor: [
        'rgba(34, 197, 94, 0.8)',
        'rgba(59, 130, 246, 0.8)',
        'rgba(239, 68, 68, 0.8)'
      ]
    }]
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Executive Dashboard</h1>
          <p className="text-gray-500">Financial overview and key metrics</p>
        </div>
        <button
          onClick={loadDashboard}
          className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Revenue (YTD)</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(summary?.total_revenue)}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Expenses (YTD)</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(summary?.total_expenses)}
              </p>
            </div>
            <div className="p-3 bg-red-100 rounded-full">
              <TrendingDown className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Net Income (YTD)</p>
              <p className={`text-2xl font-bold ${Number(summary?.net_income) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(summary?.net_income)}
              </p>
            </div>
            <div className={`p-3 rounded-full ${Number(summary?.net_income) >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
              {Number(summary?.net_income) >= 0 ? (
                <TrendingUp className="w-6 h-6 text-green-600" />
              ) : (
                <TrendingDown className="w-6 h-6 text-red-600" />
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Cash Balance</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(summary?.cash_balance)}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <Activity className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Margins */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-500">Gross Margin</p>
            <Percent size={16} className="text-gray-400" />
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {formatPercent(summary?.gross_margin)}
          </p>
          <div className="mt-2 h-2 bg-gray-200 rounded-full">
            <div 
              className="h-2 bg-blue-600 rounded-full"
              style={{ width: `${Math.min(Number(summary?.gross_margin || 0), 100)}%` }}
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-500">Net Margin</p>
            <Percent size={16} className="text-gray-400" />
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {formatPercent(summary?.net_margin)}
          </p>
          <div className="mt-2 h-2 bg-gray-200 rounded-full">
            <div 
              className="h-2 bg-green-600 rounded-full"
              style={{ width: `${Math.min(Math.max(Number(summary?.net_margin || 0), 0), 100)}%` }}
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-500">Current Ratio</p>
            <BarChart2 size={16} className="text-gray-400" />
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {formatRatio(summary?.current_ratio)}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            {Number(summary?.current_ratio) >= 2 ? 'Healthy' : 
             Number(summary?.current_ratio) >= 1 ? 'Adequate' : 'Low'}
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue Trend</h3>
          <Line 
            data={revenueChartData}
            options={{
              responsive: true,
              plugins: { legend: { display: false } },
              scales: {
                y: { beginAtZero: true }
              }
            }}
          />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Expense Trend</h3>
          <Bar 
            data={expenseChartData}
            options={{
              responsive: true,
              plugins: { legend: { display: false } },
              scales: {
                y: { beginAtZero: true }
              }
            }}
          />
        </div>
      </div>

      {/* KPIs */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Key Performance Indicators</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {summary?.kpis?.map((kpi) => (
              <div key={kpi.code} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-500">{kpi.name}</p>
                  <span className={`px-2 py-1 rounded-full text-xs ${getKPIStatusColor(kpi.status)}`}>
                    {kpi.status}
                  </span>
                </div>
                <p className="text-2xl font-bold text-gray-900">{kpi.formatted_value}</p>
                {kpi.target && (
                  <p className="text-sm text-gray-500 mt-1">Target: {kpi.target}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Cash Position */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cash Position</h3>
          <Doughnut 
            data={cashPositionData}
            options={{
              responsive: true,
              plugins: {
                legend: { position: 'bottom' }
              }
            }}
          />
        </div>

        <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Working Capital</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
              <span className="text-gray-700">Cash</span>
              <span className="text-lg font-semibold text-green-600">
                {formatCurrency(summary?.cash_balance)}
              </span>
            </div>
            <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
              <span className="text-gray-700">Accounts Receivable</span>
              <span className="text-lg font-semibold text-blue-600">
                {formatCurrency(summary?.ar_balance)}
              </span>
            </div>
            <div className="flex justify-between items-center p-4 bg-red-50 rounded-lg">
              <span className="text-gray-700">Accounts Payable</span>
              <span className="text-lg font-semibold text-red-600">
                {formatCurrency(summary?.ap_balance)}
              </span>
            </div>
            <div className="flex justify-between items-center p-4 bg-gray-100 rounded-lg border-t-2">
              <span className="text-gray-900 font-semibold">Net Working Capital</span>
              <span className="text-lg font-bold text-gray-900">
                {formatCurrency(
                  (Number(summary?.cash_balance) || 0) + 
                  (Number(summary?.ar_balance) || 0) - 
                  (Number(summary?.ap_balance) || 0)
                )}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
