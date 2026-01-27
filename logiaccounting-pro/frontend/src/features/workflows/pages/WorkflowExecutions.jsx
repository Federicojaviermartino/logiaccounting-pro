/**
 * Workflow Executions Page
 * View execution history and details
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Play,
} from 'lucide-react';
import { workflowAPI } from '../services/workflowAPI';

const WorkflowExecutions = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [workflow, setWorkflow] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [workflowData, executionsData] = await Promise.all([
        workflowAPI.getWorkflow(id),
        workflowAPI.getExecutions(id, 50),
      ]);
      setWorkflow(workflowData);
      setExecutions(executionsData.executions || []);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadExecutionDetails = async (executionId) => {
    try {
      const data = await workflowAPI.getExecution(id, executionId);
      setSelectedExecution(data);
    } catch (error) {
      console.error('Failed to load execution:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="text-green-500" size={18} />;
      case 'failed': return <XCircle className="text-red-500" size={18} />;
      case 'running': return <RefreshCw className="text-blue-500 animate-spin" size={18} />;
      default: return <Clock className="text-gray-500" size={18} />;
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
      pending: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-yellow-100 text-yellow-800',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || styles.pending}`}>
        {status}
      </span>
    );
  };

  const formatDuration = (ms) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/workflows')}
          className="p-2 hover:bg-gray-100 rounded"
        >
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">
            {workflow?.name} - Executions
          </h1>
          <p className="text-gray-600">View execution history and details</p>
        </div>
        <button
          onClick={loadData}
          className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2"
        >
          <RefreshCw size={18} />
          Refresh
        </button>
      </div>

      <div className="flex gap-6">
        {/* Execution List */}
        <div className="w-1/2">
          <div className="bg-white rounded-lg border">
            <div className="p-4 border-b">
              <h2 className="font-semibold">Recent Executions</h2>
            </div>
            <div className="divide-y max-h-[600px] overflow-auto">
              {executions.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  No executions yet
                </div>
              ) : (
                executions.map(execution => (
                  <div
                    key={execution.id}
                    className={`p-4 hover:bg-gray-50 cursor-pointer ${
                      selectedExecution?.id === execution.id ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => loadExecutionDetails(execution.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(execution.status)}
                        <span className="font-medium">{execution.id.slice(0, 12)}</span>
                      </div>
                      {getStatusBadge(execution.status)}
                    </div>
                    <div className="text-sm text-gray-600">
                      <div>Started: {new Date(execution.started_at).toLocaleString()}</div>
                      <div>Duration: {formatDuration(execution.duration_ms)}</div>
                      <div>Steps: {execution.steps_completed}/{execution.steps_total}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Execution Details */}
        <div className="w-1/2">
          {selectedExecution ? (
            <div className="bg-white rounded-lg border">
              <div className="p-4 border-b">
                <h2 className="font-semibold">Execution Details</h2>
              </div>
              <div className="p-4">
                {/* Status */}
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    {getStatusIcon(selectedExecution.status)}
                    <span className="font-medium text-lg">
                      {selectedExecution.status.charAt(0).toUpperCase() + selectedExecution.status.slice(1)}
                    </span>
                  </div>
                  {selectedExecution.error && (
                    <div className="bg-red-50 text-red-700 p-3 rounded text-sm">
                      {selectedExecution.error}
                    </div>
                  )}
                </div>

                {/* Metadata */}
                <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
                  <div>
                    <div className="text-gray-500">Started</div>
                    <div>{new Date(selectedExecution.started_at).toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Completed</div>
                    <div>
                      {selectedExecution.completed_at
                        ? new Date(selectedExecution.completed_at).toLocaleString()
                        : '-'}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500">Duration</div>
                    <div>{formatDuration(selectedExecution.duration_ms)}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Trigger</div>
                    <div>{selectedExecution.trigger_type || 'Manual'}</div>
                  </div>
                </div>

                {/* Steps */}
                <div>
                  <h3 className="font-medium mb-2">Steps</h3>
                  <div className="space-y-2">
                    {selectedExecution.steps?.map((step, index) => (
                      <div key={step.id} className="border rounded p-3">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(step.status)}
                            <span className="font-medium text-sm">{step.node_id}</span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {formatDuration(step.duration_ms)}
                          </span>
                        </div>
                        {step.error && (
                          <div className="text-xs text-red-600 mt-1">{step.error}</div>
                        )}
                        {step.output_data && Object.keys(step.output_data).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs text-gray-500 cursor-pointer">
                              Output
                            </summary>
                            <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-auto max-h-32">
                              {JSON.stringify(step.output_data, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg border p-8 text-center text-gray-500">
              Select an execution to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkflowExecutions;
