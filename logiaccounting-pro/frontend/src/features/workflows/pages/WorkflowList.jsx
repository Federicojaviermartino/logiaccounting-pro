/**
 * Workflow List Page
 * Displays all workflows with filtering and management
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Plus,
  Search,
  Filter,
  Play,
  Pause,
  Edit2,
  Trash2,
  Copy,
  Clock,
  CheckCircle,
  XCircle,
  MoreVertical,
  Zap,
  Calendar,
  MousePointer,
} from 'lucide-react';
import { workflowAPI } from '../services/workflowAPI';

const WorkflowList = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [stats, setStats] = useState(null);
  const [showTemplates, setShowTemplates] = useState(false);
  const [templates, setTemplates] = useState([]);

  useEffect(() => {
    loadWorkflows();
    loadStats();
    loadTemplates();
  }, [statusFilter]);

  const loadWorkflows = async () => {
    setLoading(true);
    try {
      const status = statusFilter === 'all' ? null : statusFilter;
      const response = await workflowAPI.listWorkflows({ status });
      setWorkflows(response.workflows);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await workflowAPI.getStats();
      setStats(response);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await workflowAPI.getTemplates();
      setTemplates(response.templates);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handleCreateNew = () => {
    navigate('/workflows/new');
  };

  const handleCreateFromTemplate = async (templateId) => {
    try {
      const workflow = await workflowAPI.createFromTemplate(templateId);
      navigate(`/workflows/${workflow.id}/edit`);
    } catch (error) {
      console.error('Failed to create from template:', error);
    }
  };

  const handleActivate = async (workflowId) => {
    try {
      await workflowAPI.activateWorkflow(workflowId);
      loadWorkflows();
    } catch (error) {
      console.error('Failed to activate workflow:', error);
    }
  };

  const handleDeactivate = async (workflowId) => {
    try {
      await workflowAPI.deactivateWorkflow(workflowId);
      loadWorkflows();
    } catch (error) {
      console.error('Failed to deactivate workflow:', error);
    }
  };

  const handleDelete = async (workflowId) => {
    if (!window.confirm('Are you sure you want to delete this workflow?')) return;

    try {
      await workflowAPI.deleteWorkflow(workflowId);
      loadWorkflows();
    } catch (error) {
      console.error('Failed to delete workflow:', error);
    }
  };

  const handleDuplicate = async (workflowId) => {
    try {
      const workflow = await workflowAPI.duplicateWorkflow(workflowId);
      navigate(`/workflows/${workflow.id}/edit`);
    } catch (error) {
      console.error('Failed to duplicate workflow:', error);
    }
  };

  const handleExecute = async (workflowId) => {
    try {
      const result = await workflowAPI.executeWorkflow(workflowId);
      alert(`Workflow started. Execution ID: ${result.execution_id}`);
    } catch (error) {
      console.error('Failed to execute workflow:', error);
    }
  };

  const filteredWorkflows = workflows.filter(wf =>
    wf.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    wf.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getTriggerIcon = (trigger) => {
    if (!trigger) return <MousePointer size={16} />;
    switch (trigger.type) {
      case 'event': return <Zap size={16} />;
      case 'schedule': return <Calendar size={16} />;
      case 'manual': return <MousePointer size={16} />;
      default: return <Zap size={16} />;
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      active: 'bg-green-100 text-green-800',
      draft: 'bg-gray-100 text-gray-800',
      paused: 'bg-yellow-100 text-yellow-800',
      archived: 'bg-red-100 text-red-800',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || styles.draft}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
          <p className="text-gray-600">Automate your business processes</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowTemplates(true)}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <Copy size={18} />
            From Template
          </button>
          <button
            onClick={handleCreateNew}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Plus size={18} />
            New Workflow
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg border p-4">
            <div className="text-sm text-gray-600">Total Workflows</div>
            <div className="text-2xl font-bold">{stats.total_workflows}</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-sm text-gray-600">Active</div>
            <div className="text-2xl font-bold text-green-600">{stats.active_workflows}</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-sm text-gray-600">Total Executions</div>
            <div className="text-2xl font-bold">{stats.total_executions}</div>
          </div>
          <div className="bg-white rounded-lg border p-4">
            <div className="text-sm text-gray-600">Success Rate</div>
            <div className="text-2xl font-bold">{stats.success_rate?.toFixed(1) || 0}%</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Search workflows..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="draft">Draft</option>
          <option value="paused">Paused</option>
        </select>
      </div>

      {/* Workflow List */}
      <div className="bg-white rounded-lg border">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : filteredWorkflows.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-gray-500 mb-4">No workflows found</div>
            <button
              onClick={handleCreateNew}
              className="text-blue-600 hover:underline"
            >
              Create your first workflow
            </button>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Workflow</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trigger</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Executions</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Run</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredWorkflows.map((workflow) => (
                <tr key={workflow.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{workflow.name}</div>
                    <div className="text-sm text-gray-500">{workflow.description}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      {getTriggerIcon(workflow.trigger)}
                      <span>{workflow.trigger?.type || 'Manual'}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(workflow.status)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {workflow.run_count || 0}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {workflow.last_run_at ? new Date(workflow.last_run_at).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex justify-end gap-2">
                      {workflow.status === 'active' ? (
                        <button
                          onClick={() => handleDeactivate(workflow.id)}
                          className="p-2 text-yellow-600 hover:bg-yellow-50 rounded"
                          title="Pause"
                        >
                          <Pause size={16} />
                        </button>
                      ) : (
                        <button
                          onClick={() => handleActivate(workflow.id)}
                          className="p-2 text-green-600 hover:bg-green-50 rounded"
                          title="Activate"
                        >
                          <Play size={16} />
                        </button>
                      )}
                      <button
                        onClick={() => handleExecute(workflow.id)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                        title="Run Now"
                      >
                        <Zap size={16} />
                      </button>
                      <button
                        onClick={() => navigate(`/workflows/${workflow.id}/edit`)}
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                        title="Edit"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDuplicate(workflow.id)}
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                        title="Duplicate"
                      >
                        <Copy size={16} />
                      </button>
                      <button
                        onClick={() => handleDelete(workflow.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Templates Modal */}
      {showTemplates && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Workflow Templates</h2>
              <button onClick={() => setShowTemplates(false)} className="text-gray-500 hover:text-gray-700">
                <XCircle size={24} />
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="border rounded-lg p-4 hover:border-blue-500 cursor-pointer"
                  onClick={() => {
                    handleCreateFromTemplate(template.id);
                    setShowTemplates(false);
                  }}
                >
                  <h3 className="font-medium mb-1">{template.name}</h3>
                  <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">{template.category}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowList;
