# Phase 30: Workflow Automation - Part 5: Frontend Workflow Builder

## Overview
This part covers the frontend workflow builder pages and main canvas component.

---

## File 1: Workflow List Page
**Path:** `frontend/src/features/workflows/pages/WorkflowList.jsx`

```jsx
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
```

---

## File 2: Workflow Builder Page
**Path:** `frontend/src/features/workflows/pages/WorkflowBuilder.jsx`

```jsx
/**
 * Workflow Builder Page
 * Visual workflow editor with drag-and-drop
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Save,
  Play,
  ArrowLeft,
  Settings,
  History,
  Undo,
  Redo,
  ZoomIn,
  ZoomOut,
  Maximize2,
} from 'lucide-react';
import WorkflowCanvas from '../components/WorkflowCanvas';
import NodePalette from '../components/NodePalette';
import NodeConfigPanel from '../components/NodeConfigPanel';
import TriggerConfig from '../components/TriggerConfig';
import { workflowAPI } from '../services/workflowAPI';

const WorkflowBuilder = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const isNew = !id || id === 'new';

  const [workflow, setWorkflow] = useState({
    name: 'Untitled Workflow',
    description: '',
    trigger: { type: 'manual' },
    nodes: [],
    edges: [],
  });
  
  const [selectedNode, setSelectedNode] = useState(null);
  const [showTriggerConfig, setShowTriggerConfig] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  useEffect(() => {
    if (!isNew) {
      loadWorkflow();
    }
  }, [id]);

  const loadWorkflow = async () => {
    try {
      const data = await workflowAPI.getWorkflow(id);
      setWorkflow(data);
      addToHistory(data);
    } catch (error) {
      console.error('Failed to load workflow:', error);
    }
  };

  const addToHistory = (state) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(JSON.stringify(state));
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setWorkflow(JSON.parse(history[historyIndex - 1]));
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setWorkflow(JSON.parse(history[historyIndex + 1]));
    }
  };

  const updateWorkflow = useCallback((updates) => {
    setWorkflow(prev => {
      const newState = { ...prev, ...updates };
      addToHistory(newState);
      setHasChanges(true);
      return newState;
    });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      if (isNew) {
        const created = await workflowAPI.createWorkflow(workflow);
        navigate(`/workflows/${created.id}/edit`, { replace: true });
      } else {
        await workflowAPI.updateWorkflow(id, workflow);
      }
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save workflow:', error);
      alert('Failed to save workflow');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (isNew) {
      alert('Please save the workflow first');
      return;
    }
    
    try {
      const result = await workflowAPI.executeWorkflow(id);
      alert(`Test started! Execution ID: ${result.execution_id}`);
    } catch (error) {
      console.error('Failed to test workflow:', error);
      alert('Failed to test workflow');
    }
  };

  const handleAddNode = (nodeType, nodeConfig) => {
    const newNode = {
      id: `node_${Date.now()}`,
      type: nodeType,
      name: nodeConfig.name || nodeType,
      config: nodeConfig.defaultConfig || {},
      position: { x: 400, y: 200 + workflow.nodes.length * 100 },
      ...nodeConfig,
    };
    
    updateWorkflow({
      nodes: [...workflow.nodes, newNode],
    });
    
    setSelectedNode(newNode.id);
  };

  const handleUpdateNode = (nodeId, updates) => {
    updateWorkflow({
      nodes: workflow.nodes.map(node =>
        node.id === nodeId ? { ...node, ...updates } : node
      ),
    });
  };

  const handleDeleteNode = (nodeId) => {
    updateWorkflow({
      nodes: workflow.nodes.filter(n => n.id !== nodeId),
      edges: workflow.edges.filter(e => e.source !== nodeId && e.target !== nodeId),
    });
    
    if (selectedNode === nodeId) {
      setSelectedNode(null);
    }
  };

  const handleAddEdge = (source, target, condition = null) => {
    const edgeId = `edge_${Date.now()}`;
    updateWorkflow({
      edges: [...workflow.edges, { id: edgeId, source, target, condition }],
    });
  };

  const handleDeleteEdge = (edgeId) => {
    updateWorkflow({
      edges: workflow.edges.filter(e => e.id !== edgeId),
    });
  };

  const handleTriggerUpdate = (triggerConfig) => {
    updateWorkflow({ trigger: triggerConfig });
    setShowTriggerConfig(false);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/workflows')}
            className="p-2 hover:bg-gray-100 rounded"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <input
              type="text"
              value={workflow.name}
              onChange={(e) => updateWorkflow({ name: e.target.value })}
              className="text-lg font-semibold border-none focus:ring-0 p-0"
              placeholder="Workflow Name"
            />
            <input
              type="text"
              value={workflow.description || ''}
              onChange={(e) => updateWorkflow({ description: e.target.value })}
              className="text-sm text-gray-500 border-none focus:ring-0 p-0 w-64"
              placeholder="Add description..."
            />
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={handleUndo}
            disabled={historyIndex <= 0}
            className="p-2 hover:bg-gray-100 rounded disabled:opacity-50"
            title="Undo"
          >
            <Undo size={18} />
          </button>
          <button
            onClick={handleRedo}
            disabled={historyIndex >= history.length - 1}
            className="p-2 hover:bg-gray-100 rounded disabled:opacity-50"
            title="Redo"
          >
            <Redo size={18} />
          </button>
          
          <div className="w-px h-6 bg-gray-300 mx-2" />
          
          <button
            onClick={() => setZoom(z => Math.max(0.5, z - 0.1))}
            className="p-2 hover:bg-gray-100 rounded"
            title="Zoom Out"
          >
            <ZoomOut size={18} />
          </button>
          <span className="text-sm text-gray-600 w-12 text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom(z => Math.min(2, z + 0.1))}
            className="p-2 hover:bg-gray-100 rounded"
            title="Zoom In"
          >
            <ZoomIn size={18} />
          </button>
          
          <div className="w-px h-6 bg-gray-300 mx-2" />
          
          <button
            onClick={() => setShowHistory(true)}
            className="p-2 hover:bg-gray-100 rounded"
            title="Execution History"
          >
            <History size={18} />
          </button>
          
          <button
            onClick={handleTest}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <Play size={18} />
            Test
          </button>
          
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50"
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Node Palette */}
        <NodePalette onAddNode={handleAddNode} />

        {/* Canvas */}
        <div className="flex-1 relative">
          <WorkflowCanvas
            nodes={workflow.nodes}
            edges={workflow.edges}
            trigger={workflow.trigger}
            selectedNode={selectedNode}
            zoom={zoom}
            onSelectNode={setSelectedNode}
            onUpdateNode={handleUpdateNode}
            onDeleteNode={handleDeleteNode}
            onAddEdge={handleAddEdge}
            onDeleteEdge={handleDeleteEdge}
            onTriggerClick={() => setShowTriggerConfig(true)}
          />
        </div>

        {/* Config Panel */}
        {selectedNode && (
          <NodeConfigPanel
            node={workflow.nodes.find(n => n.id === selectedNode)}
            onUpdate={(updates) => handleUpdateNode(selectedNode, updates)}
            onDelete={() => handleDeleteNode(selectedNode)}
            onClose={() => setSelectedNode(null)}
          />
        )}
      </div>

      {/* Trigger Config Modal */}
      {showTriggerConfig && (
        <TriggerConfig
          trigger={workflow.trigger}
          onSave={handleTriggerUpdate}
          onClose={() => setShowTriggerConfig(false)}
        />
      )}

      {/* Unsaved Changes Warning */}
      {hasChanges && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-yellow-100 text-yellow-800 px-4 py-2 rounded-lg shadow">
          You have unsaved changes
        </div>
      )}
    </div>
  );
};

export default WorkflowBuilder;
```

---

## File 3: Workflow Canvas
**Path:** `frontend/src/features/workflows/components/WorkflowCanvas.jsx`

```jsx
/**
 * Workflow Canvas Component
 * Visual canvas for workflow nodes and connections
 */

import React, { useRef, useState, useCallback, useEffect } from 'react';
import { Zap, Calendar, MousePointer, Webhook } from 'lucide-react';
import WorkflowNode from './WorkflowNode';
import EdgeLine from './EdgeLine';

const WorkflowCanvas = ({
  nodes,
  edges,
  trigger,
  selectedNode,
  zoom,
  onSelectNode,
  onUpdateNode,
  onDeleteNode,
  onAddEdge,
  onDeleteEdge,
  onTriggerClick,
}) => {
  const canvasRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragNode, setDragNode] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [connecting, setConnecting] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });

  const getTriggerIcon = () => {
    if (!trigger) return <MousePointer size={20} />;
    switch (trigger.type) {
      case 'event': return <Zap size={20} />;
      case 'schedule': return <Calendar size={20} />;
      case 'webhook': return <Webhook size={20} />;
      default: return <MousePointer size={20} />;
    }
  };

  const getTriggerLabel = () => {
    if (!trigger) return 'Manual Trigger';
    switch (trigger.type) {
      case 'event': return trigger.event || 'Event Trigger';
      case 'schedule': return trigger.cron || 'Schedule Trigger';
      case 'webhook': return 'Webhook Trigger';
      default: return 'Manual Trigger';
    }
  };

  const handleMouseDown = (e, nodeId) => {
    if (e.button !== 0) return;
    
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
    setDragNode(nodeId);
    setIsDragging(true);
    onSelectNode(nodeId);
  };

  const handleMouseMove = useCallback((e) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = (e.clientX - rect.left - panOffset.x) / zoom;
    const y = (e.clientY - rect.top - panOffset.y) / zoom;
    setMousePos({ x, y });
    
    if (isDragging && dragNode) {
      onUpdateNode(dragNode, {
        position: {
          x: Math.max(0, x - dragOffset.x),
          y: Math.max(0, y - dragOffset.y),
        },
      });
    }
  }, [isDragging, dragNode, dragOffset, zoom, panOffset, onUpdateNode]);

  const handleMouseUp = useCallback(() => {
    if (connecting) {
      setConnecting(null);
    }
    setIsDragging(false);
    setDragNode(null);
  }, [connecting]);

  const handleStartConnection = (nodeId, port = 'output') => {
    setConnecting({ nodeId, port });
  };

  const handleEndConnection = (nodeId, port = 'input') => {
    if (connecting && connecting.nodeId !== nodeId) {
      onAddEdge(connecting.nodeId, nodeId);
    }
    setConnecting(null);
  };

  const getNodePosition = (nodeId) => {
    const node = nodes.find(n => n.id === nodeId);
    return node?.position || { x: 0, y: 0 };
  };

  // Trigger node position (fixed at top)
  const triggerPosition = { x: 400, y: 50 };

  return (
    <div
      ref={canvasRef}
      className="w-full h-full bg-gray-50 overflow-hidden relative"
      style={{
        backgroundImage: 'radial-gradient(circle, #ddd 1px, transparent 1px)',
        backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
      }}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div
        style={{
          transform: `scale(${zoom}) translate(${panOffset.x}px, ${panOffset.y}px)`,
          transformOrigin: 'top left',
        }}
      >
        {/* SVG for edges */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ overflow: 'visible' }}>
          {/* Edge from trigger to first node */}
          {nodes.length > 0 && edges.some(e => e.source === 'trigger') && (
            edges.filter(e => e.source === 'trigger').map(edge => {
              const targetPos = getNodePosition(edge.target);
              return (
                <EdgeLine
                  key={edge.id}
                  startX={triggerPosition.x + 100}
                  startY={triggerPosition.y + 40}
                  endX={targetPos.x + 100}
                  endY={targetPos.y}
                  onDelete={() => onDeleteEdge(edge.id)}
                />
              );
            })
          )}
          
          {/* Edges between nodes */}
          {edges.filter(e => e.source !== 'trigger').map(edge => {
            const sourcePos = getNodePosition(edge.source);
            const targetPos = getNodePosition(edge.target);
            return (
              <EdgeLine
                key={edge.id}
                startX={sourcePos.x + 100}
                startY={sourcePos.y + 80}
                endX={targetPos.x + 100}
                endY={targetPos.y}
                label={edge.label}
                condition={edge.condition}
                onDelete={() => onDeleteEdge(edge.id)}
              />
            );
          })}
          
          {/* Connecting line */}
          {connecting && (
            <line
              x1={getNodePosition(connecting.nodeId).x + 100}
              y1={getNodePosition(connecting.nodeId).y + 80}
              x2={mousePos.x}
              y2={mousePos.y}
              stroke="#3b82f6"
              strokeWidth="2"
              strokeDasharray="5,5"
            />
          )}
        </svg>

        {/* Trigger Node */}
        <div
          className="absolute cursor-pointer"
          style={{
            left: triggerPosition.x,
            top: triggerPosition.y,
            width: 200,
          }}
          onClick={onTriggerClick}
        >
          <div className="bg-green-500 text-white rounded-lg p-4 shadow-lg hover:shadow-xl transition-shadow">
            <div className="flex items-center gap-2 mb-1">
              {getTriggerIcon()}
              <span className="font-medium">Trigger</span>
            </div>
            <div className="text-sm text-green-100">{getTriggerLabel()}</div>
            
            {/* Output port */}
            <div
              className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-green-600 rounded-full border-2 border-white cursor-crosshair"
              onMouseDown={(e) => {
                e.stopPropagation();
                handleStartConnection('trigger');
              }}
            />
          </div>
        </div>

        {/* Workflow Nodes */}
        {nodes.map(node => (
          <WorkflowNode
            key={node.id}
            node={node}
            isSelected={selectedNode === node.id}
            onMouseDown={(e) => handleMouseDown(e, node.id)}
            onStartConnection={() => handleStartConnection(node.id)}
            onEndConnection={() => handleEndConnection(node.id)}
            onSelect={() => onSelectNode(node.id)}
            onDelete={() => onDeleteNode(node.id)}
          />
        ))}

        {/* Drop zone indicator */}
        {connecting && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="text-center mt-32 text-gray-400">
              Click on a node to connect
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowCanvas;
```

---

## File 4: Workflow Node Component
**Path:** `frontend/src/features/workflows/components/WorkflowNode.jsx`

```jsx
/**
 * Workflow Node Component
 * Individual node in the workflow canvas
 */

import React from 'react';
import {
  GitBranch,
  Repeat,
  Clock,
  Mail,
  MessageSquare,
  Bell,
  Database,
  Globe,
  Trash2,
  Settings,
  Play,
} from 'lucide-react';

const WorkflowNode = ({
  node,
  isSelected,
  onMouseDown,
  onStartConnection,
  onEndConnection,
  onSelect,
  onDelete,
}) => {
  const getNodeIcon = () => {
    switch (node.type) {
      case 'condition': return <GitBranch size={18} />;
      case 'loop': return <Repeat size={18} />;
      case 'delay': return <Clock size={18} />;
      case 'action':
        switch (node.action) {
          case 'send_email': return <Mail size={18} />;
          case 'send_slack': return <MessageSquare size={18} />;
          case 'send_notification': return <Bell size={18} />;
          case 'query_records':
          case 'create_record':
          case 'update_record': return <Database size={18} />;
          case 'http_request': return <Globe size={18} />;
          default: return <Play size={18} />;
        }
      default: return <Settings size={18} />;
    }
  };

  const getNodeColor = () => {
    switch (node.type) {
      case 'condition': return 'bg-yellow-500';
      case 'loop': return 'bg-purple-500';
      case 'delay': return 'bg-orange-500';
      case 'action': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getNodeTitle = () => {
    if (node.name) return node.name;
    
    switch (node.type) {
      case 'condition': return 'Condition';
      case 'loop': return 'Loop';
      case 'delay': return 'Delay';
      case 'action': return node.action?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Action';
      default: return 'Step';
    }
  };

  const getNodeSubtitle = () => {
    switch (node.type) {
      case 'condition':
        if (node.condition?.field) {
          return `If ${node.condition.field} ${node.condition.operator} ${node.condition.value}`;
        }
        return 'Configure condition';
      case 'loop':
        return node.collection ? `For each in ${node.collection}` : 'Configure loop';
      case 'delay':
        if (node.config?.duration) {
          return `Wait ${node.config.duration} ${node.config.unit || 'seconds'}`;
        }
        return 'Configure delay';
      case 'action':
        if (node.action === 'send_email' && node.config?.to) {
          return `To: ${node.config.to}`;
        }
        if (node.action === 'send_slack' && node.config?.channel) {
          return `Channel: ${node.config.channel}`;
        }
        return node.config?.description || 'Configure action';
      default:
        return '';
    }
  };

  return (
    <div
      className={`absolute cursor-move select-none ${isSelected ? 'z-10' : 'z-0'}`}
      style={{
        left: node.position?.x || 0,
        top: node.position?.y || 0,
        width: 200,
      }}
      onMouseDown={onMouseDown}
    >
      {/* Input port */}
      <div
        className="absolute -top-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-gray-400 rounded-full border-2 border-white cursor-crosshair z-10 hover:bg-blue-500 transition-colors"
        onMouseUp={(e) => {
          e.stopPropagation();
          onEndConnection();
        }}
      />

      {/* Node body */}
      <div
        className={`rounded-lg shadow-lg overflow-hidden transition-all ${
          isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : ''
        }`}
        onClick={(e) => {
          e.stopPropagation();
          onSelect();
        }}
      >
        {/* Header */}
        <div className={`${getNodeColor()} text-white px-3 py-2 flex items-center gap-2`}>
          {getNodeIcon()}
          <span className="font-medium text-sm truncate flex-1">{getNodeTitle()}</span>
          {isSelected && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-1 hover:bg-white/20 rounded"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
        
        {/* Body */}
        <div className="bg-white px-3 py-2">
          <div className="text-xs text-gray-500 truncate">
            {getNodeSubtitle()}
          </div>
        </div>

        {/* Condition branches */}
        {node.type === 'condition' && (
          <div className="bg-gray-50 px-3 py-1 flex justify-between text-xs border-t">
            <span className="text-green-600">True →</span>
            <span className="text-red-600">False →</span>
          </div>
        )}
      </div>

      {/* Output port(s) */}
      {node.type === 'condition' ? (
        <>
          {/* True branch output */}
          <div
            className="absolute -bottom-2 left-1/4 -translate-x-1/2 w-4 h-4 bg-green-500 rounded-full border-2 border-white cursor-crosshair z-10 hover:scale-110 transition-transform"
            onMouseDown={(e) => {
              e.stopPropagation();
              onStartConnection('true');
            }}
          />
          {/* False branch output */}
          <div
            className="absolute -bottom-2 left-3/4 -translate-x-1/2 w-4 h-4 bg-red-500 rounded-full border-2 border-white cursor-crosshair z-10 hover:scale-110 transition-transform"
            onMouseDown={(e) => {
              e.stopPropagation();
              onStartConnection('false');
            }}
          />
        </>
      ) : (
        <div
          className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-gray-400 rounded-full border-2 border-white cursor-crosshair z-10 hover:bg-blue-500 transition-colors"
          onMouseDown={(e) => {
            e.stopPropagation();
            onStartConnection();
          }}
        />
      )}
    </div>
  );
};

export default WorkflowNode;
```

---

## File 5: Edge Line Component
**Path:** `frontend/src/features/workflows/components/EdgeLine.jsx`

```jsx
/**
 * Edge Line Component
 * Connection line between workflow nodes
 */

import React, { useState } from 'react';
import { X } from 'lucide-react';

const EdgeLine = ({
  startX,
  startY,
  endX,
  endY,
  label,
  condition,
  onDelete,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  // Calculate control points for smooth curve
  const midY = (startY + endY) / 2;
  const controlPoint1Y = startY + Math.min(50, (endY - startY) / 2);
  const controlPoint2Y = endY - Math.min(50, (endY - startY) / 2);

  const path = `M ${startX} ${startY} C ${startX} ${controlPoint1Y}, ${endX} ${controlPoint2Y}, ${endX} ${endY}`;

  // Calculate label position
  const labelX = (startX + endX) / 2;
  const labelY = midY;

  const getConditionColor = () => {
    if (condition === 'true') return '#22c55e';
    if (condition === 'false') return '#ef4444';
    return '#6b7280';
  };

  return (
    <g
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{ pointerEvents: 'stroke' }}
    >
      {/* Invisible wider path for easier hover */}
      <path
        d={path}
        fill="none"
        stroke="transparent"
        strokeWidth="20"
        style={{ cursor: 'pointer' }}
      />
      
      {/* Visible path */}
      <path
        d={path}
        fill="none"
        stroke={isHovered ? '#3b82f6' : getConditionColor()}
        strokeWidth={isHovered ? 3 : 2}
        markerEnd="url(#arrowhead)"
      />

      {/* Arrow marker definition */}
      <defs>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon
            points="0 0, 10 3.5, 0 7"
            fill={isHovered ? '#3b82f6' : getConditionColor()}
          />
        </marker>
      </defs>

      {/* Label or condition indicator */}
      {(label || condition) && (
        <g transform={`translate(${labelX}, ${labelY})`}>
          <rect
            x="-20"
            y="-10"
            width="40"
            height="20"
            rx="4"
            fill="white"
            stroke={getConditionColor()}
            strokeWidth="1"
          />
          <text
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize="10"
            fill={getConditionColor()}
            fontWeight="500"
          >
            {label || (condition === 'true' ? 'Yes' : condition === 'false' ? 'No' : '')}
          </text>
        </g>
      )}

      {/* Delete button on hover */}
      {isHovered && onDelete && (
        <g
          transform={`translate(${labelX + 30}, ${labelY})`}
          style={{ cursor: 'pointer', pointerEvents: 'all' }}
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
        >
          <circle r="10" fill="#ef4444" />
          <X
            size={12}
            color="white"
            style={{ transform: 'translate(-6px, -6px)' }}
          />
        </g>
      )}
    </g>
  );
};

export default EdgeLine;
```

---

## File 6: Workflow API Service
**Path:** `frontend/src/features/workflows/services/workflowAPI.js`

```javascript
/**
 * Workflow API Service
 * API calls for workflow management
 */

import api from '../../../services/api';

export const workflowAPI = {
  /**
   * List workflows
   */
  async listWorkflows({ status, limit = 50, offset = 0 } = {}) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit);
    params.append('offset', offset);
    
    const response = await api.get(`/workflows?${params}`);
    return response.data;
  },

  /**
   * Get single workflow
   */
  async getWorkflow(id) {
    const response = await api.get(`/workflows/${id}`);
    return response.data;
  },

  /**
   * Create workflow
   */
  async createWorkflow(data) {
    const response = await api.post('/workflows', data);
    return response.data;
  },

  /**
   * Update workflow
   */
  async updateWorkflow(id, data) {
    const response = await api.put(`/workflows/${id}`, data);
    return response.data;
  },

  /**
   * Delete workflow
   */
  async deleteWorkflow(id) {
    const response = await api.delete(`/workflows/${id}`);
    return response.data;
  },

  /**
   * Duplicate workflow
   */
  async duplicateWorkflow(id) {
    const response = await api.post(`/workflows/${id}/duplicate`);
    return response.data;
  },

  /**
   * Activate workflow
   */
  async activateWorkflow(id) {
    const response = await api.post(`/workflows/${id}/activate`);
    return response.data;
  },

  /**
   * Deactivate workflow
   */
  async deactivateWorkflow(id) {
    const response = await api.post(`/workflows/${id}/deactivate`);
    return response.data;
  },

  /**
   * Execute workflow manually
   */
  async executeWorkflow(id, inputData = {}) {
    const response = await api.post(`/workflows/${id}/execute`, {
      input_data: inputData,
    });
    return response.data;
  },

  /**
   * Get execution history
   */
  async getExecutions(workflowId, limit = 20) {
    const response = await api.get(`/workflows/${workflowId}/executions?limit=${limit}`);
    return response.data;
  },

  /**
   * Get single execution
   */
  async getExecution(workflowId, executionId) {
    const response = await api.get(`/workflows/${workflowId}/executions/${executionId}`);
    return response.data;
  },

  /**
   * Get workflow stats
   */
  async getWorkflowStats(id) {
    const response = await api.get(`/workflows/${id}/stats`);
    return response.data;
  },

  /**
   * Get customer stats
   */
  async getStats() {
    const response = await api.get('/workflows/stats');
    return response.data;
  },

  /**
   * Get templates
   */
  async getTemplates(category) {
    const params = category ? `?category=${category}` : '';
    const response = await api.get(`/workflows/templates${params}`);
    return response.data;
  },

  /**
   * Create from template
   */
  async createFromTemplate(templateId, overrides = {}) {
    const response = await api.post('/workflows/from-template', {
      template_id: templateId,
      ...overrides,
    });
    return response.data;
  },

  /**
   * Get available triggers
   */
  async getTriggers() {
    const response = await api.get('/workflows/metadata/triggers');
    return response.data;
  },

  /**
   * Get available actions
   */
  async getActions() {
    const response = await api.get('/workflows/metadata/actions');
    return response.data;
  },

  /**
   * Get condition metadata
   */
  async getConditions() {
    const response = await api.get('/workflows/metadata/conditions');
    return response.data;
  },

  /**
   * Get available variables
   */
  async getVariables() {
    const response = await api.get('/workflows/metadata/variables');
    return response.data;
  },

  /**
   * Validate cron expression
   */
  async validateCron(cron) {
    const response = await api.post('/workflows/metadata/cron/validate', { cron });
    return response.data;
  },

  /**
   * Preview cron schedule
   */
  async previewCron(cron, count = 10) {
    const response = await api.post('/workflows/metadata/cron/preview', { cron, count });
    return response.data;
  },
};

export default workflowAPI;
```

---

## Summary Part 5

| File | Description | Lines |
|------|-------------|-------|
| `pages/WorkflowList.jsx` | Workflow list page | ~320 |
| `pages/WorkflowBuilder.jsx` | Workflow builder page | ~280 |
| `components/WorkflowCanvas.jsx` | Visual canvas | ~250 |
| `components/WorkflowNode.jsx` | Node component | ~200 |
| `components/EdgeLine.jsx` | Edge line component | ~130 |
| `services/workflowAPI.js` | API service | ~180 |
| **Total** | | **~1,360 lines** |
