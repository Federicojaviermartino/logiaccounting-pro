/**
 * Depreciation Run management page.
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Play, CheckCircle, XCircle, RefreshCw,
  Calendar, Calculator, FileText, AlertTriangle
} from 'lucide-react';
import { depreciationAPI, categoriesAPI } from '../services/fixedAssetsAPI';

const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-700',
  calculated: 'bg-yellow-100 text-yellow-700',
  posted: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount || 0);
};

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString();
};

export default function DepreciationRunPage() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [newRun, setNewRun] = useState({
    period_year: new Date().getFullYear(),
    period_month: new Date().getMonth() + 1,
    category_id: '',
  });

  // Fetch categories
  const { data: categories } = useQuery({
    queryKey: ['assetCategories'],
    queryFn: () => categoriesAPI.getAll().then(res => res.data),
  });

  // Fetch depreciation runs
  const { data: runsData, isLoading } = useQuery({
    queryKey: ['depreciationRuns', selectedYear],
    queryFn: () => depreciationAPI.getRuns({ year: selectedYear, limit: 100 }).then(res => res.data),
  });

  // Create run mutation
  const createRunMutation = useMutation({
    mutationFn: (data) => depreciationAPI.createRun(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['depreciationRuns']);
      setShowCreateModal(false);
    },
  });

  // Post run mutation
  const postRunMutation = useMutation({
    mutationFn: (id) => depreciationAPI.postRun(id),
    onSuccess: () => queryClient.invalidateQueries(['depreciationRuns']),
  });

  // Cancel run mutation
  const cancelRunMutation = useMutation({
    mutationFn: (id) => depreciationAPI.cancelRun(id),
    onSuccess: () => queryClient.invalidateQueries(['depreciationRuns']),
  });

  const handleCreateRun = () => {
    createRunMutation.mutate({
      period_year: parseInt(newRun.period_year),
      period_month: parseInt(newRun.period_month),
      category_id: newRun.category_id || null,
    });
  };

  const handlePostRun = (run) => {
    if (confirm(`Post depreciation for ${run.period_month}/${run.period_year}? This will create journal entries.`)) {
      postRunMutation.mutate(run.id);
    }
  };

  const handleCancelRun = (run) => {
    if (confirm(`Cancel depreciation run for ${run.period_month}/${run.period_year}?`)) {
      cancelRunMutation.mutate(run.id);
    }
  };

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Depreciation Runs</h1>
          <p className="text-sm text-gray-500 mt-1">
            Process monthly depreciation for fixed assets
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Calculator size={18} />
          New Depreciation Run
        </button>
      </div>

      {/* Year Filter */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Year:</label>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="input-field w-32"
          >
            {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Runs Grid by Month */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {months.map((month, index) => {
          const monthRun = runsData?.items?.find(
            r => r.period_month === index + 1 && r.period_year === selectedYear
          );

          return (
            <div key={month} className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 border-b">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{month}</span>
                  {monthRun && (
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[monthRun.status]}`}>
                      {monthRun.status}
                    </span>
                  )}
                </div>
              </div>
              <div className="p-4">
                {monthRun ? (
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Assets:</span>
                      <span className="font-medium">{monthRun.assets_processed}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Total:</span>
                      <span className="font-medium">{formatCurrency(monthRun.total_depreciation)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Run Date:</span>
                      <span className="font-medium">{formatDate(monthRun.run_date)}</span>
                    </div>

                    {monthRun.status === 'calculated' && (
                      <div className="flex gap-2 mt-4">
                        <button
                          onClick={() => handlePostRun(monthRun)}
                          className="btn-primary flex-1 text-sm flex items-center justify-center gap-1"
                        >
                          <CheckCircle size={16} />
                          Post
                        </button>
                        <button
                          onClick={() => handleCancelRun(monthRun)}
                          className="btn-secondary flex-1 text-sm flex items-center justify-center gap-1"
                        >
                          <XCircle size={16} />
                          Cancel
                        </button>
                      </div>
                    )}

                    {monthRun.journal_entry_id && (
                      <div className="text-xs text-gray-500 mt-2">
                        <FileText size={14} className="inline mr-1" />
                        Posted to GL
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-400">
                    <Calendar size={32} className="mx-auto mb-2" />
                    <p className="text-sm">No run yet</p>
                    {index + 1 <= new Date().getMonth() + 1 && (
                      <button
                        onClick={() => {
                          setNewRun({ ...newRun, period_month: index + 1 });
                          setShowCreateModal(true);
                        }}
                        className="text-blue-600 text-sm mt-2 hover:underline"
                      >
                        Create Run
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Run Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-bold mb-4">Create Depreciation Run</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                  <select
                    value={newRun.period_year}
                    onChange={(e) => setNewRun({ ...newRun, period_year: e.target.value })}
                    className="input-field"
                  >
                    {Array.from({ length: 3 }, (_, i) => new Date().getFullYear() - i).map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Month</label>
                  <select
                    value={newRun.period_month}
                    onChange={(e) => setNewRun({ ...newRun, period_month: e.target.value })}
                    className="input-field"
                  >
                    {months.map((month, index) => (
                      <option key={month} value={index + 1}>{month}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category (optional)
                </label>
                <select
                  value={newRun.category_id}
                  onChange={(e) => setNewRun({ ...newRun, category_id: e.target.value })}
                  className="input-field"
                >
                  <option value="">All Categories</option>
                  {categories?.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Leave empty to process all active assets
                </p>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <AlertTriangle size={18} className="text-yellow-600 mt-0.5" />
                  <div className="text-sm text-yellow-700">
                    This will calculate depreciation for all eligible assets. Review the results before posting to the general ledger.
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateRun}
                  disabled={createRunMutation.isPending}
                  className="btn-primary flex items-center gap-2"
                >
                  <Play size={18} />
                  {createRunMutation.isPending ? 'Processing...' : 'Run Depreciation'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
