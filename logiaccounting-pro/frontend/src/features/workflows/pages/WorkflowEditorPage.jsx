/**
 * WorkflowEditorPage - Visual workflow designer page
 */
import React, { useEffect, useCallback, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { useWorkflows } from '../hooks/useWorkflows';
import { useDesigner } from '../hooks/useDesigner';
import {
  TriggerNode,
  ActionNode,
  ConditionNode,
  ParallelNode,
  DelayNode,
  EndNode,
} from '../components/nodes';

const nodeTypes = {
  trigger: TriggerNode,
  action: ActionNode,
  condition: ConditionNode,
  parallel: ParallelNode,
  delay: DelayNode,
  end: EndNode,
};

export function WorkflowEditorPage() {
  const { workflowId } = useParams();
  const navigate = useNavigate();
  const { fetchWorkflow, createWorkflow, updateWorkflow, currentWorkflow } = useWorkflows();
  const {
    nodes,
    edges,
    setNodes,
    setEdges,
    selectedNode,
    selectNode,
    addNode,
    exportWorkflow,
    loadWorkflow,
    validateWorkflow,
    autoLayout,
    isDirty,
    markClean,
  } = useDesigner();

  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [showNodePalette, setShowNodePalette] = useState(true);

  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState([]);
  const [flowEdges, setFlowEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (workflowId && workflowId !== 'new') {
      fetchWorkflow(workflowId);
    }
  }, [workflowId, fetchWorkflow]);

  useEffect(() => {
    if (currentWorkflow) {
      setWorkflowName(currentWorkflow.name);
      setWorkflowDescription(currentWorkflow.description || '');
      loadWorkflow(currentWorkflow);
    }
  }, [currentWorkflow, loadWorkflow]);

  useEffect(() => {
    setFlowNodes(nodes);
    setFlowEdges(edges);
  }, [nodes, edges, setFlowNodes, setFlowEdges]);

  const onConnect = useCallback(
    (params) => setFlowEdges((eds) => addEdge(params, eds)),
    [setFlowEdges]
  );

  const onNodeClick = useCallback(
    (event, node) => {
      selectNode(node);
    },
    [selectNode]
  );

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow');

      if (!type) return;

      const position = {
        x: event.clientX - 250,
        y: event.clientY - 100,
      };

      addNode(type, position);
    },
    [addNode]
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const handleSave = async () => {
    const errors = validateWorkflow();
    const criticalErrors = errors.filter(e => e.type === 'error');

    if (criticalErrors.length > 0) {
      alert('Please fix the following errors:\n' + criticalErrors.map(e => e.message).join('\n'));
      return;
    }

    setIsSaving(true);
    try {
      const workflowData = exportWorkflow();
      const data = {
        name: workflowName,
        description: workflowDescription,
        trigger: currentWorkflow?.trigger || { type: 'manual' },
        ...workflowData,
      };

      if (workflowId && workflowId !== 'new') {
        await updateWorkflow(workflowId, data);
      } else {
        const result = await createWorkflow(data);
        navigate(`/workflows/${result.id}/edit`);
      }
      markClean();
    } catch (error) {
      alert('Failed to save workflow: ' + error.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAutoLayout = () => {
    autoLayout();
    setFlowNodes([...nodes]);
  };

  const NodePaletteItem = ({ type, label, color }) => (
    <div
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('application/reactflow', type);
        e.dataTransfer.effectAllowed = 'move';
      }}
      className="p-3 mb-2 bg-white dark:bg-gray-700 rounded-lg shadow cursor-move hover:shadow-md transition-shadow border-l-4"
      style={{ borderLeftColor: color }}
    >
      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </span>
    </div>
  );

  return (
    <div className="h-screen flex flex-col">
      <div className="bg-white dark:bg-gray-800 border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/workflows')}
            className="text-gray-600 hover:text-gray-900"
          >
            ← Back
          </button>
          <input
            type="text"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="text-xl font-bold bg-transparent border-none focus:ring-0 focus:outline-none"
            placeholder="Workflow Name"
          />
          {isDirty && <span className="text-xs text-yellow-600">Unsaved changes</span>}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleAutoLayout}
            className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 border rounded"
          >
            Auto Layout
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      <div className="flex-1 flex">
        {showNodePalette && (
          <div className="w-64 bg-gray-100 dark:bg-gray-900 p-4 border-r overflow-y-auto">
            <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3">
              Node Palette
            </h3>
            <NodePaletteItem type="trigger" label="Trigger" color="#10b981" />
            <NodePaletteItem type="action" label="Action" color="#3b82f6" />
            <NodePaletteItem type="condition" label="Condition" color="#f59e0b" />
            <NodePaletteItem type="parallel" label="Parallel" color="#8b5cf6" />
            <NodePaletteItem type="delay" label="Delay" color="#6b7280" />
            <NodePaletteItem type="end" label="End" color="#ef4444" />
          </div>
        )}

        <div className="flex-1">
          <ReactFlow
            nodes={flowNodes}
            edges={flowEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
            fitView
          >
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />
          </ReactFlow>
        </div>

        {selectedNode && (
          <div className="w-80 bg-white dark:bg-gray-800 border-l p-4 overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Node Properties</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={selectedNode.data?.name || ''}
                  onChange={(e) => {/* Update node name */}}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={selectedNode.data?.description || ''}
                  onChange={(e) => {/* Update node description */}}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Type: {selectedNode.type}
                </label>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default WorkflowEditorPage;
