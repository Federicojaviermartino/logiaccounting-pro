/**
 * Cash Flow Forecast Page
 * AI-powered cash flow predictions and analysis
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  DollarSign,
  Calendar,
  RefreshCw,
  Download,
  ChevronDown,
} from 'lucide-react';
import ForecastChart from '../components/ForecastChart';
import { aiAPI } from '../services/aiAPI';

const CashFlowForecast = () => {
  const { t } = useTranslation();

  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [horizonDays, setHorizonDays] = useState(30);
  const [scenario, setScenario] = useState('expected');
  const [modelStatus, setModelStatus] = useState(null);

  useEffect(() => {
    loadForecast();
    loadModelStatus();
  }, [horizonDays, scenario]);

  const loadForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await aiAPI.getCashFlowForecast({
        horizon_days: horizonDays,
        scenario,
        include_pending: true,
        include_recurring: true,
      });
      setForecast(data);
    } catch (err) {
      setError('Failed to load forecast');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadModelStatus = async () => {
    try {
      const status = await aiAPI.getCashFlowStatus();
      setModelStatus(status);
    } catch (err) {
      console.error('Failed to load model status:', err);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getTrendIcon = (trend) => {
    if (trend === 'increasing') return <TrendingUp className="text-green-500" size={20} />;
    if (trend === 'decreasing') return <TrendingDown className="text-red-500" size={20} />;
    return <span className="text-gray-500">→</span>;
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      info: 'bg-blue-100 text-blue-800 border-blue-200',
    };
    return colors[severity] || colors.info;
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cash Flow Forecast</h1>
          <p className="text-gray-600">AI-powered predictions for your cash position</p>
        </div>
        <div className="flex gap-3">
          <select
            value={horizonDays}
            onChange={(e) => setHorizonDays(Number(e.target.value))}
            className="px-3 py-2 border rounded-lg"
          >
            <option value={7}>7 Days</option>
            <option value={14}>14 Days</option>
            <option value={30}>30 Days</option>
            <option value={60}>60 Days</option>
            <option value={90}>90 Days</option>
          </select>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="expected">Expected</option>
            <option value="optimistic">Optimistic</option>
            <option value="pessimistic">Pessimistic</option>
          </select>
          <button
            onClick={loadForecast}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Model Status */}
      {modelStatus && !modelStatus.trained && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-yellow-600" size={20} />
            <span className="text-yellow-800">
              Cash flow model is not trained yet. Predictions may be less accurate.
            </span>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="animate-spin text-gray-400" size={32} />
        </div>
      ) : forecast ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg border p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Current Balance</span>
                <DollarSign className="text-gray-400" size={18} />
              </div>
              <div className="text-2xl font-bold">
                {formatCurrency(forecast.summary?.starting_balance || 0)}
              </div>
            </div>

            <div className="bg-white rounded-lg border p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Forecast ({horizonDays}d)</span>
                {getTrendIcon(forecast.summary?.trend)}
              </div>
              <div className="text-2xl font-bold">
                {formatCurrency(forecast.summary?.ending_balance || 0)}
              </div>
              <div className={`text-sm ${forecast.summary?.net_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {forecast.summary?.net_change >= 0 ? '+' : ''}
                {formatCurrency(forecast.summary?.net_change || 0)}
              </div>
            </div>

            <div className="bg-white rounded-lg border p-4">
              <div className="text-sm text-gray-600 mb-2">Lowest Point</div>
              <div className="text-2xl font-bold text-red-600">
                {formatCurrency(forecast.summary?.lowest_point?.balance || 0)}
              </div>
              <div className="text-sm text-gray-500">
                {forecast.summary?.lowest_point?.date}
              </div>
            </div>

            <div className="bg-white rounded-lg border p-4">
              <div className="text-sm text-gray-600 mb-2">Total Inflows</div>
              <div className="text-2xl font-bold text-green-600">
                {formatCurrency(forecast.summary?.total_inflows || 0)}
              </div>
              <div className="text-sm text-gray-500">
                Outflows: {formatCurrency(forecast.summary?.total_outflows || 0)}
              </div>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-white rounded-lg border p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Forecast Timeline</h2>
            <ForecastChart
              data={forecast.forecast}
              scenario={scenario}
            />
          </div>

          {/* Alerts */}
          {forecast.alerts && forecast.alerts.length > 0 && (
            <div className="bg-white rounded-lg border p-6 mb-6">
              <h2 className="text-lg font-semibold mb-4">Alerts & Warnings</h2>
              <div className="space-y-3">
                {forecast.alerts.map((alert, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle size={16} />
                      <span className="font-medium">{alert.type.replace(/_/g, ' ').toUpperCase()}</span>
                      <span className="text-sm opacity-75">• {alert.date}</span>
                    </div>
                    <div className="text-sm">{alert.message}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Forecast Table */}
          <div className="bg-white rounded-lg border overflow-hidden">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold">Daily Forecast</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Inflows</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Outflows</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Balance</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {forecast.forecast?.slice(0, 14).map((day, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm">{day.date}</td>
                      <td className="px-4 py-3 text-sm text-right text-green-600">
                        +{formatCurrency(day.predicted_inflows)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right text-red-600">
                        -{formatCurrency(day.predicted_outflows)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-medium">
                        {formatCurrency(day.predicted_balance)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          day.confidence_level === 'high' ? 'bg-green-100 text-green-800' :
                          day.confidence_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {day.confidence_level}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};

export default CashFlowForecast;
