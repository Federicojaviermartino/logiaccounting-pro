/**
 * useDesigner Hook - Workflow designer operations
 */
import { useCallback } from 'react';
import { useDesignerStore } from '../stores/designerStore';

export function useDesigner() {
  const store = useDesignerStore();

  const addNode = useCallback((type, position, data = {}) => {
    const id = `${type}-${Date.now()}`;
    const node = {
      id,
      type,
      position,
      data: {
        name: data.name || `New ${type}`,
        description: data.description || '',
        config: data.config || {},
      },
    };

    store.saveToHistory();
    store.addNode(node);

    return node;
  }, []);

  const connectNodes = useCallback((sourceId, targetId, data = {}) => {
    const edge = {
      id: `edge-${sourceId}-${targetId}`,
      source: sourceId,
      target: targetId,
      label: data.label,
      data: {
        condition: data.condition,
      },
    };

    store.saveToHistory();
    store.addEdge(edge);

    return edge;
  }, []);

  const updateNodeConfig = useCallback((nodeId, config) => {
    store.saveToHistory();
    store.updateNode(nodeId, { data: { config } });
  }, []);

  const deleteSelected = useCallback(() => {
    const { selectedNode, selectedEdge } = store;

    store.saveToHistory();

    if (selectedNode) {
      store.removeNode(selectedNode.id);
    } else if (selectedEdge) {
      store.removeEdge(selectedEdge.id);
    }
  }, []);

  const duplicateNode = useCallback((nodeId) => {
    const node = store.nodes.find((n) => n.id === nodeId);
    if (!node) return null;

    const newNode = {
      ...node,
      id: `${node.type}-${Date.now()}`,
      position: {
        x: node.position.x + 50,
        y: node.position.y + 50,
      },
      data: { ...node.data },
    };

    store.saveToHistory();
    store.addNode(newNode);

    return newNode;
  }, []);

  const validateWorkflow = useCallback(() => {
    const { nodes, edges } = store;
    const errors = [];

    const triggerNodes = nodes.filter((n) => n.type === 'trigger');
    if (triggerNodes.length === 0) {
      errors.push({ type: 'error', message: 'Workflow must have a trigger node' });
    }
    if (triggerNodes.length > 1) {
      errors.push({ type: 'error', message: 'Workflow can only have one trigger node' });
    }

    nodes.forEach((node) => {
      if (node.type !== 'trigger' && node.type !== 'end') {
        const hasIncoming = edges.some((e) => e.target === node.id);
        if (!hasIncoming) {
          errors.push({
            type: 'warning',
            message: `Node "${node.data.name}" has no incoming connections`,
          });
        }
      }

      if (node.type !== 'end') {
        const hasOutgoing = edges.some((e) => e.source === node.id);
        if (!hasOutgoing) {
          errors.push({
            type: 'warning',
            message: `Node "${node.data.name}" has no outgoing connections`,
          });
        }
      }
    });

    return errors;
  }, []);

  const autoLayout = useCallback(() => {
    const { nodes, edges } = store;

    const levels = new Map();
    const triggerNode = nodes.find((n) => n.type === 'trigger');

    if (!triggerNode) return;

    const assignLevel = (nodeId, level) => {
      if (levels.has(nodeId)) return;
      levels.set(nodeId, level);

      const outgoing = edges.filter((e) => e.source === nodeId);
      outgoing.forEach((edge) => assignLevel(edge.target, level + 1));
    };

    assignLevel(triggerNode.id, 0);

    const levelGroups = new Map();
    levels.forEach((level, nodeId) => {
      if (!levelGroups.has(level)) {
        levelGroups.set(level, []);
      }
      levelGroups.get(level).push(nodeId);
    });

    const newNodes = nodes.map((node) => {
      const level = levels.get(node.id) || 0;
      const levelNodes = levelGroups.get(level) || [];
      const indexInLevel = levelNodes.indexOf(node.id);

      return {
        ...node,
        position: {
          x: 150 + level * 250,
          y: 100 + indexInLevel * 150,
        },
      };
    });

    store.saveToHistory();
    store.setNodes(newNodes);
  }, []);

  return {
    nodes: store.nodes,
    edges: store.edges,
    selectedNode: store.selectedNode,
    selectedEdge: store.selectedEdge,
    isDirty: store.isDirty,
    zoom: store.zoom,
    viewport: store.viewport,
    setNodes: store.setNodes,
    setEdges: store.setEdges,
    addNode,
    updateNode: store.updateNode,
    removeNode: store.removeNode,
    connectNodes,
    updateNodeConfig,
    selectNode: store.selectNode,
    selectEdge: store.selectEdge,
    clearSelection: store.clearSelection,
    deleteSelected,
    duplicateNode,
    setZoom: store.setZoom,
    setViewport: store.setViewport,
    undo: store.undo,
    redo: store.redo,
    canUndo: store.canUndo,
    canRedo: store.canRedo,
    loadWorkflow: store.loadWorkflow,
    exportWorkflow: store.exportWorkflow,
    validateWorkflow,
    autoLayout,
    markClean: store.markClean,
    reset: store.reset,
  };
}
