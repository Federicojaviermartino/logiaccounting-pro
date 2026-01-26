/**
 * Cash Flow Forecast Page
 * View and manage cash flow forecasts
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { cashflowAPI } from '../services/bankingAPI';
import {
  TrendingUp, TrendingDown, DollarSign, Calendar,
  Plus, RefreshCw, ChevronRight, AlertTriangle
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, Legend
} from 'recharts';

const CashFlowForecast = () => {
  const [selectedForecast, setSelectedForecast] = useState(null);

  // Fetch summary
  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['cashflow-summary'],
    queryFn: () => cashflowAPI.getSummary(),
  });

  // Fetch forecasts
  const { data: forecastsData, isLoading: forecastsLoading } = useQuery({
    queryKey: ['cashflow-forecasts'],
    queryFn: () => cashflowAPI.listForecasts({ status: 'active' }),
  });

  // Fetch forecast details if selected
  const { data: forecastDetail } = useQuery({
    queryKey: ['cashflow-forecast', selectedForecast],
    queryFn: () => cashflowAPI.getForecast(selectedForecast),
    enabled: !!selectedForecast,
  });

  const summary = summaryData?.data;
  const forecasts = forecastsData?.data?.items || [];
  const detail = forecastDetail?.data;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount || 0);
  };

  // Prepare chart data from forecast lines
  const chartData = detail?.lines?.map(line => ({
    name: line.period_label || new Date(line.period_date).toLocaleDateString(),
    opening: parseFloat(line.opening_balance),
    closing: parseFloat(line.closing_balance),
    inflows: parseFloat(line.total_inflows),
    outflows: parseFloat(line.total_outflows),
    net: parseFloat(line.net_cash_flow),
  })) || [];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Cash Flow Forecast</h1>
          <p className="text-gray-600 dark:text-gray-400">Monitor and forecast your cash position</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
          <Plus size={20} />
          New Forecast
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Current Cash</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(summary.current_cash)}
                </p>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900 rounded-full">
                <DollarSign className="text-green-600 dark:text-green-400" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">30-Day Projection</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(summary.projected_cash_30_days)}
                </p>
                <p className={`text-sm ${parseFloat(summary.projected_cash_30_days) >= parseFloat(summary.current_cash) ? 'text-green-600' : 'text-red-600'}`}>
                  {parseFloat(summary.projected_cash_30_days) >= parseFloat(summary.current_cash) ? (
                    <span className="flex items-center gap-1"><TrendingUp size={14} /> Increasing</span>
                  ) : (
                    <span className="flex items-center gap-1"><TrendingDown size={14} /> Decreasing</span>
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Expected AR Collections</p>
                <p className="text-2xl font-bold text-green-600">
                  +{formatCurrency(summary.expected_ar_collections)}
                </p>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900 rounded-full">
                <TrendingUp className="text-green-600 dark:text-green-400" size={24} />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Expected AP Payments</p>
                <p className="text-2xl font-bold text-red-600">
                  -{formatCurrency(summary.expected_ap_payments)}
                </p>
              </div>
              <div className="p-3 bg-red-100 dark:bg-red-900 rounded-full">
                <TrendingDown className="text-red-600 dark:text-red-400" size={24} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Projection Chart */}
      {chartData.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Cash Flow Projection</h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
              <Area type="monotone" dataKey="closing" name="Cash Balance" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.3} />
              <Area type="monotone" dataKey="inflows" name="Inflows" stroke="#10B981" fill="#10B981" fillOpacity={0.3} />
              <Area type="monotone" dataKey="outflows" name="Outflows" stroke="#EF4444" fill="#EF4444" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Forecasts List */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="p-4 border-b dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Forecasts</h2>
            </div>
            {forecastsLoading ? (
              <div className="p-4 text-center text-gray-500">Loading...</div>
            ) : forecasts.length === 0 ? (
              <div className="p-4 text-center text-gray-500">No active forecasts</div>
            ) : (
              <div className="divide-y dark:divide-gray-700">
                {forecasts.map((forecast) => (
                  <button
                    key={forecast.id}
                    onClick={() => setSelectedForecast(forecast.id)}
                    className={`w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700 ${
                      selectedForecast === forecast.id ? 'bg-blue-50 dark:bg-blue-900/30' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">{forecast.forecast_name}</div>
                        <div className="text-sm text-gray-500">
                          {new Date(forecast.period_start).toLocaleDateString()} - {new Date(forecast.period_end).toLocaleDateString()}
                        </div>
                      </div>
                      <ChevronRight className="text-gray-400" size={20} />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="md:col-span-2">
          {detail ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="p-4 border-b dark:border-gray-700 flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{detail.forecast_name}</h2>
                  <p className="text-sm text-gray-500">{detail.description || 'Cash flow forecast'}</p>
                </div>
                <button className="flex items-center gap-2 text-blue-600 hover:text-blue-700">
                  <RefreshCw size={16} />
                  Regenerate
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Period</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Opening</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Inflows</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Outflows</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Closing</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y dark:divide-gray-700">
                    {detail.lines?.map((line) => (
                      <tr key={line.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-4 py-3 text-gray-900 dark:text-white">{line.period_label}</td>
                        <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">
                          {formatCurrency(line.opening_balance)}
                        </td>
                        <td className="px-4 py-3 text-right text-green-600">
                          +{formatCurrency(line.total_inflows)}
                        </td>
                        <td className="px-4 py-3 text-right text-red-600">
                          -{formatCurrency(line.total_outflows)}
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-gray-900 dark:text-white">
                          {formatCurrency(line.closing_balance)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
              <Calendar className="mx-auto text-gray-400 mb-4" size={48} />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Select a Forecast</h3>
              <p className="text-gray-500">Choose a forecast from the list to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CashFlowForecast;
