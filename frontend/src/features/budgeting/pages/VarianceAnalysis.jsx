import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import budgetingAPI from '../services/budgetingAPI';

const VarianceAnalysis = () => {
  const { budgetId } = useParams();
  const [periodType, setPeriodType] = useState('ytd');
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);

  const { data, isLoading, error } = useQuery({
    queryKey: ['variance', budgetId, periodType, year, month],
    queryFn: () => budgetingAPI.getBudgetVsActual(budgetId, periodType, year, month),
    enabled: !!budgetId,
  });

  const report = data?.data;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(value || 0);
  };

  const getVarianceColor = (type) => {
    switch (type) {
      case 'favorable': return 'text-green-600';
      case 'unfavorable': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getVarianceBg = (type) => {
    switch (type) {
      case 'favorable': return 'bg-green-50';
      case 'unfavorable': return 'bg-red-50';
      default: return 'bg-gray-50';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading variance data: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Variance Analysis</h1>
          {report && <p className="text-gray-600">{report.budget_name}</p>}
        </div>
        <button
          onClick={() => window.location.href = `/api/v1/budgeting/reports/budgets/${budgetId}/variance?format=xlsx&period_type=${periodType}&year=${year}&month=${month}`}
          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Export Excel
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Period Type</label>
            <select
              value={periodType}
              onChange={(e) => setPeriodType(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="ytd">Year to Date</option>
              <option value="annual">Annual</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
            <select
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2"
            >
              {[2024, 2025, 2026].map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
          {periodType === 'monthly' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Month</label>
              <select
                value={month}
                onChange={(e) => setMonth(parseInt(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2"
              >
                {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((m, i) => (
                  <option key={i} value={i + 1}>{m}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {report && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-2">Revenue</p>
              <div className="flex justify-between">
                <div>
                  <p className="text-xs text-gray-500">Budget</p>
                  <p className="font-semibold">{formatCurrency(report.total_revenue_budget)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Actual</p>
                  <p className="font-semibold">{formatCurrency(report.total_revenue_actual)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Variance</p>
                  <p className={`font-semibold ${report.total_revenue_variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(report.total_revenue_variance)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-2">Expenses</p>
              <div className="flex justify-between">
                <div>
                  <p className="text-xs text-gray-500">Budget</p>
                  <p className="font-semibold">{formatCurrency(report.total_expense_budget)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Actual</p>
                  <p className="font-semibold">{formatCurrency(report.total_expense_actual)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Variance</p>
                  <p className={`font-semibold ${report.total_expense_variance <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(report.total_expense_variance)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg shadow p-4">
              <p className="text-sm text-blue-800 mb-2">Net Income</p>
              <div className="flex justify-between">
                <div>
                  <p className="text-xs text-blue-600">Budget</p>
                  <p className="font-semibold text-blue-900">{formatCurrency(report.net_income_budget)}</p>
                </div>
                <div>
                  <p className="text-xs text-blue-600">Actual</p>
                  <p className="font-semibold text-blue-900">{formatCurrency(report.net_income_actual)}</p>
                </div>
                <div>
                  <p className="text-xs text-blue-600">Variance</p>
                  <p className={`font-semibold ${report.net_income_variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(report.net_income_variance)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Detail Tables */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Budget</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actual</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Variance</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Var %</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {/* Revenue Section */}
                <tr className="bg-green-100">
                  <td colSpan={6} className="px-6 py-2 font-semibold text-green-800">REVENUE</td>
                </tr>
                {report.revenue_lines.map((line) => (
                  <tr key={line.account_id} className={`hover:bg-gray-50 ${getVarianceBg(line.variance_type)}`}>
                    <td className="px-6 py-3">
                      <div className="font-medium">{line.account_code}</div>
                      <div className="text-sm text-gray-500">{line.account_name}</div>
                    </td>
                    <td className="px-6 py-3 text-right">{formatCurrency(line.budgeted)}</td>
                    <td className="px-6 py-3 text-right">{formatCurrency(line.actual)}</td>
                    <td className={`px-6 py-3 text-right font-medium ${getVarianceColor(line.variance_type)}`}>
                      {formatCurrency(line.variance)}
                    </td>
                    <td className={`px-6 py-3 text-right ${getVarianceColor(line.variance_type)}`}>
                      {line.variance_percent.toFixed(1)}%
                    </td>
                    <td className="px-6 py-3 text-center">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        line.variance_type === 'favorable' ? 'bg-green-100 text-green-800' :
                        line.variance_type === 'unfavorable' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {line.variance_type}
                      </span>
                    </td>
                  </tr>
                ))}

                {/* Expense Section */}
                <tr className="bg-red-100">
                  <td colSpan={6} className="px-6 py-2 font-semibold text-red-800">EXPENSES</td>
                </tr>
                {report.expense_lines.map((line) => (
                  <tr key={line.account_id} className={`hover:bg-gray-50 ${getVarianceBg(line.variance_type)}`}>
                    <td className="px-6 py-3">
                      <div className="font-medium">{line.account_code}</div>
                      <div className="text-sm text-gray-500">{line.account_name}</div>
                    </td>
                    <td className="px-6 py-3 text-right">{formatCurrency(line.budgeted)}</td>
                    <td className="px-6 py-3 text-right">{formatCurrency(line.actual)}</td>
                    <td className={`px-6 py-3 text-right font-medium ${getVarianceColor(line.variance_type)}`}>
                      {formatCurrency(line.variance)}
                    </td>
                    <td className={`px-6 py-3 text-right ${getVarianceColor(line.variance_type)}`}>
                      {line.variance_percent.toFixed(1)}%
                    </td>
                    <td className="px-6 py-3 text-center">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        line.variance_type === 'favorable' ? 'bg-green-100 text-green-800' :
                        line.variance_type === 'unfavorable' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {line.variance_type}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};

export default VarianceAnalysis;
