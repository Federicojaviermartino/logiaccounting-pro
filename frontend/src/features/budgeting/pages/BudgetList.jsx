import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import budgetingAPI from '../services/budgetingAPI';

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-blue-100 text-blue-800',
  active: 'bg-green-100 text-green-800',
  closed: 'bg-red-100 text-red-800',
};

const BudgetList = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    fiscal_year: new Date().getFullYear(),
    status: '',
    skip: 0,
    limit: 20,
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['budgets', filters],
    queryFn: () => budgetingAPI.getBudgets(filters),
  });

  const budgets = data?.data?.items || [];
  const total = data?.data?.total || 0;

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, skip: 0 }));
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
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
        <p className="text-red-800">Error loading budgets: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Budgets</h1>
          <p className="text-gray-600">Manage your financial budgets and planning</p>
        </div>
        <button
          onClick={() => navigate('/budgeting/new')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + New Budget
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Total Budgets</p>
          <p className="text-2xl font-bold text-gray-900">{total}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Total Revenue</p>
          <p className="text-2xl font-bold text-green-600">
            {formatCurrency(budgets.reduce((sum, b) => sum + parseFloat(b.total_revenue || 0), 0))}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Total Expenses</p>
          <p className="text-2xl font-bold text-red-600">
            {formatCurrency(budgets.reduce((sum, b) => sum + parseFloat(b.total_expenses || 0), 0))}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600">Net Income</p>
          <p className="text-2xl font-bold text-blue-600">
            {formatCurrency(budgets.reduce((sum, b) => sum + parseFloat(b.total_net_income || 0), 0))}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fiscal Year</label>
            <select
              value={filters.fiscal_year}
              onChange={(e) => handleFilterChange('fiscal_year', e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2"
            >
              {[2024, 2025, 2026, 2027].map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="pending_approval">Pending Approval</option>
              <option value="approved">Approved</option>
              <option value="active">Active</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Budget Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Budget
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Revenue
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Expenses
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Net Income
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {budgets.map((budget) => (
              <tr key={budget.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="font-medium text-gray-900">{budget.name}</div>
                    <div className="text-sm text-gray-500">{budget.budget_code}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="capitalize">{budget.budget_type}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[budget.status]}`}>
                    {budget.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-green-600">
                  {formatCurrency(budget.total_revenue)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-red-600">
                  {formatCurrency(budget.total_expenses)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                  {formatCurrency(budget.total_net_income)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <Link
                    to={`/budgeting/${budget.id}`}
                    className="text-blue-600 hover:text-blue-800 mr-3"
                  >
                    View
                  </Link>
                  {budget.status === 'draft' && (
                    <Link
                      to={`/budgeting/${budget.id}/edit`}
                      className="text-gray-600 hover:text-gray-800"
                    >
                      Edit
                    </Link>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {budgets.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No budgets found</p>
            <button
              onClick={() => navigate('/budgeting/new')}
              className="mt-4 text-blue-600 hover:text-blue-800"
            >
              Create your first budget
            </button>
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > filters.limit && (
        <div className="flex justify-between items-center">
          <p className="text-sm text-gray-600">
            Showing {filters.skip + 1} to {Math.min(filters.skip + filters.limit, total)} of {total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setFilters(prev => ({ ...prev, skip: Math.max(0, prev.skip - prev.limit) }))}
              disabled={filters.skip === 0}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setFilters(prev => ({ ...prev, skip: prev.skip + prev.limit }))}
              disabled={filters.skip + filters.limit >= total}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BudgetList;
