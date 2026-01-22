/**
 * ExecutionsPage - Workflow execution monitoring page
 */
import React, { useEffect, useState } from 'react';
import { useExecutions } from '../hooks/useExecutions';

const statusColors = {
  pending: 'bg-gray-100 text-gray-800',
  running: 'bg-blue-100 text-blue-800',
  waiting: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-800',
};

export function ExecutionsPage() {
  const {
    executions,
    stats,
    isLoading,
    error,
    filters,
    setFilters,
    fetchExecutions,
    fetchStats,
    cancelExecution,
    retryExecution,
  } = useExecutions();

  const [selectedExecution, setSelectedExecution] = useState(null);

  useEffect(() => {
    fetchExecutions();
    fetchStats();
  }, [fetchExecutions, fetchStats]);

  const handleCancel = async (executionId) => {
    if (window.confirm('Are you sure you want to cancel this execution?')) {
      await cancelExecution(executionId);
      fetchExecutions();
    }
  };

  const handleRetry = async (executionId) => {
    await retryExecution(executionId);
    fetchExecutions();
  };

  const formatDuration = (ms) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
        Workflow Executions
      </h1>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats.total}
            </div>
            <div className="text-sm text-gray-500">Total Executions</div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-green-600">
              {stats.completed}
            </div>
            <div className="text-sm text-gray-500">Completed</div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-red-600">
              {stats.failed}
            </div>
            <div className="text-sm text-gray-500">Failed</div>
          </div>
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <div className="text-2xl font-bold text-blue-600">
              {stats.success_rate?.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">Success Rate</div>
          </div>
        </div>
      )}

      <div className="mb-4 flex gap-4">
        <select
          value={filters.status || ''}
          onChange={(e) => {
            setFilters({ status: e.target.value || null });
            fetchExecutions({ status: e.target.value || null });
          }}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="waiting">Waiting</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Execution ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Workflow
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Trigger
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Started
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Duration
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {executions.map((execution) => (
              <tr
                key={execution.id}
                className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                onClick={() => setSelectedExecution(execution)}
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">
                  {execution.id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {execution.workflow_name}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded-full ${statusColors[execution.status]}`}>
                    {execution.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {execution.trigger_type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(execution.started_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDuration(execution.duration_ms)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  {execution.status === 'running' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCancel(execution.id);
                      }}
                      className="text-red-600 hover:text-red-900 mr-3"
                    >
                      Cancel
                    </button>
                  )}
                  {execution.status === 'failed' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRetry(execution.id);
                      }}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Retry
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {executions.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No executions found.</p>
          </div>
        )}
      </div>

      {selectedExecution && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-4 border-b flex justify-between items-center">
              <h2 className="text-lg font-semibold">Execution Details</h2>
              <button
                onClick={() => setSelectedExecution(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ×
              </button>
            </div>
            <div className="p-4 overflow-y-auto">
              <div className="space-y-4">
                <div>
                  <span className="text-sm text-gray-500">ID:</span>
                  <span className="ml-2 font-mono">{selectedExecution.id}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Workflow:</span>
                  <span className="ml-2">{selectedExecution.workflow_name}</span>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Status:</span>
                  <span className={`ml-2 px-2 py-1 text-xs rounded-full ${statusColors[selectedExecution.status]}`}>
                    {selectedExecution.status}
                  </span>
                </div>
                {selectedExecution.error && (
                  <div>
                    <span className="text-sm text-gray-500">Error:</span>
                    <div className="mt-1 p-2 bg-red-50 text-red-700 rounded text-sm">
                      {selectedExecution.error}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ExecutionsPage;
