import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, X, Clock, CheckCircle, XCircle, AlertCircle, Activity, TrendingUp } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { workflowAPI } from '../../../services/api';

export default function ExecutionMonitor() {
  const { executionId } = useParams();
  const [timeline, setTimeline] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedStep, setSelectedStep] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    loadTimeline();
    connectWebSocket();
    return () => wsRef.current?.close();
  }, [executionId]);

  const loadTimeline = async () => {
    try {
      const res = await workflowAPI.getExecutionTimeline(executionId);
      setTimeline(res.data);
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://${window.location.host}/api/v1/workflows/executions/${executionId}/live`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'step_update' || data.type === 'initial') {
        setTimeline(data.data || data);
      }
    };
    wsRef.current = ws;
  };

  const handleCancel = async () => {
    if (confirm('Cancel this execution?')) {
      await workflowAPI.cancelExecution(executionId);
      loadTimeline();
    }
  };

  const handleRetry = async () => {
    const res = await workflowAPI.retryExecution(executionId);
    window.location.href = `/workflows/executions/${res.data.new_execution_id}`;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed': return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running': return <Activity className="w-5 h-5 text-blue-500 animate-pulse" />;
      case 'pending': return <Clock className="w-5 h-5 text-gray-400" />;
      case 'skipped': return <AlertCircle className="w-5 h-5 text-gray-400" />;
      default: return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-50 border-green-200';
      case 'failed': return 'bg-red-50 border-red-200';
      case 'running': return 'bg-blue-50 border-blue-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  const formatDuration = (ms) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  if (isLoading) return <div className="p-6">Loading...</div>;
  if (!timeline) return <div className="p-6">Execution not found</div>;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            Execution Monitor
            {getStatusIcon(timeline.status)}
          </h1>
          <p className="text-gray-500 mt-1">
            {timeline.workflow_id} • Started {new Date(timeline.started_at).toLocaleString()}
          </p>
        </div>
        <div className="flex gap-2">
          {timeline.status === 'running' && (
            <button onClick={handleCancel} className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50">
              <X className="w-4 h-4" /> Cancel
            </button>
          )}
          {['failed', 'cancelled'].includes(timeline.status) && (
            <button onClick={handleRetry} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg">
              <RotateCcw className="w-4 h-4" /> Retry
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border rounded-xl p-4">
          <div className="text-sm text-gray-500">Status</div>
          <div className={`text-lg font-semibold capitalize ${timeline.status === 'completed' ? 'text-green-600' : timeline.status === 'failed' ? 'text-red-600' : 'text-blue-600'}`}>
            {timeline.status}
          </div>
        </div>
        <div className="bg-white border rounded-xl p-4">
          <div className="text-sm text-gray-500">Duration</div>
          <div className="text-lg font-semibold">{formatDuration(timeline.duration_ms)}</div>
        </div>
        <div className="bg-white border rounded-xl p-4">
          <div className="text-sm text-gray-500">Steps</div>
          <div className="text-lg font-semibold">
            {timeline.steps.filter(s => s.status === 'completed').length} / {timeline.steps.length}
          </div>
        </div>
        <div className="bg-white border rounded-xl p-4">
          <div className="text-sm text-gray-500">Trigger</div>
          <div className="text-lg font-semibold">{timeline.trigger_type || 'manual'}</div>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white border rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Execution Timeline</h2>

        <div className="space-y-4">
          {timeline.steps.map((step, index) => (
            <div
              key={step.id}
              className={`border rounded-lg p-4 cursor-pointer transition ${getStatusColor(step.status)} ${selectedStep?.id === step.id ? 'ring-2 ring-blue-500' : ''}`}
              onClick={() => setSelectedStep(step)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white border">
                    {index + 1}
                  </div>
                  {getStatusIcon(step.status)}
                  <div>
                    <div className="font-medium">{step.name || step.node_id}</div>
                    <div className="text-sm text-gray-500">
                      {step.started_at && new Date(step.started_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium">{formatDuration(step.duration_ms)}</div>
                  {step.error && (
                    <div className="text-sm text-red-600 truncate max-w-xs">{step.error}</div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Error Display */}
        {timeline.error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="font-semibold text-red-800 mb-2">Execution Error</h3>
            <pre className="text-sm text-red-700 whitespace-pre-wrap">{timeline.error}</pre>
          </div>
        )}
      </div>

      {/* Step Detail Modal */}
      {selectedStep && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedStep(null)}>
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[80vh] overflow-auto" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center p-4 border-b">
              <h2 className="text-lg font-semibold">{selectedStep.name || selectedStep.node_id}</h2>
              <button onClick={() => setSelectedStep(null)}><X className="w-5 h-5" /></button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Status</label>
                <div className="flex items-center gap-2 mt-1">
                  {getStatusIcon(selectedStep.status)}
                  <span className="capitalize">{selectedStep.status}</span>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Duration</label>
                <div className="mt-1">{formatDuration(selectedStep.duration_ms)}</div>
              </div>
              {selectedStep.input && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Input</label>
                  <pre className="mt-1 p-3 bg-gray-50 rounded-lg text-sm overflow-auto">
                    {JSON.stringify(selectedStep.input, null, 2)}
                  </pre>
                </div>
              )}
              {selectedStep.output && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Output</label>
                  <pre className="mt-1 p-3 bg-gray-50 rounded-lg text-sm overflow-auto">
                    {JSON.stringify(selectedStep.output, null, 2)}
                  </pre>
                </div>
              )}
              {selectedStep.error && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Error</label>
                  <pre className="mt-1 p-3 bg-red-50 rounded-lg text-sm text-red-700 overflow-auto">
                    {selectedStep.error}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
