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
import toast from '../../../utils/toast';

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
      toast.error('Failed to save workflow');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (isNew) {
      toast.info('Please save the workflow first');
      return;
    }

    try {
      const result = await workflowAPI.executeWorkflow(id);
      toast.info(`Test started! Execution ID: ${result.execution_id}`);
    } catch (error) {
      console.error('Failed to test workflow:', error);
      toast.error('Failed to test workflow');
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
