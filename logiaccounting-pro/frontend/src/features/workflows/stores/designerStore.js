/**
 * Designer Store - Zustand store for workflow designer state
 */
import { create } from 'zustand';

export const useDesignerStore = create((set, get) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  selectedEdge: null,
  isDirty: false,
  zoom: 1,
  viewport: { x: 0, y: 0 },
  history: [],
  historyIndex: -1,

  setNodes: (nodes) => set({ nodes, isDirty: true }),

  setEdges: (edges) => set({ edges, isDirty: true }),

  addNode: (node) => set((state) => {
    const newNodes = [...state.nodes, node];
    return {
      nodes: newNodes,
      isDirty: true,
    };
  }),

  updateNode: (nodeId, updates) => set((state) => ({
    nodes: state.nodes.map((n) =>
      n.id === nodeId ? { ...n, ...updates, data: { ...n.data, ...updates.data } } : n
    ),
    isDirty: true,
  })),

  removeNode: (nodeId) => set((state) => ({
    nodes: state.nodes.filter((n) => n.id !== nodeId),
    edges: state.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
    selectedNode: state.selectedNode?.id === nodeId ? null : state.selectedNode,
    isDirty: true,
  })),

  addEdge: (edge) => set((state) => ({
    edges: [...state.edges, edge],
    isDirty: true,
  })),

  removeEdge: (edgeId) => set((state) => ({
    edges: state.edges.filter((e) => e.id !== edgeId),
    selectedEdge: state.selectedEdge?.id === edgeId ? null : state.selectedEdge,
    isDirty: true,
  })),

  selectNode: (node) => set({ selectedNode: node, selectedEdge: null }),

  selectEdge: (edge) => set({ selectedEdge: edge, selectedNode: null }),

  clearSelection: () => set({ selectedNode: null, selectedEdge: null }),

  setZoom: (zoom) => set({ zoom }),

  setViewport: (viewport) => set({ viewport }),

  saveToHistory: () => set((state) => {
    const snapshot = {
      nodes: JSON.parse(JSON.stringify(state.nodes)),
      edges: JSON.parse(JSON.stringify(state.edges)),
    };
    const newHistory = state.history.slice(0, state.historyIndex + 1);
    newHistory.push(snapshot);
    return {
      history: newHistory.slice(-50),
      historyIndex: newHistory.length - 1,
    };
  }),

  undo: () => set((state) => {
    if (state.historyIndex <= 0) return state;
    const newIndex = state.historyIndex - 1;
    const snapshot = state.history[newIndex];
    return {
      nodes: snapshot.nodes,
      edges: snapshot.edges,
      historyIndex: newIndex,
      isDirty: true,
    };
  }),

  redo: () => set((state) => {
    if (state.historyIndex >= state.history.length - 1) return state;
    const newIndex = state.historyIndex + 1;
    const snapshot = state.history[newIndex];
    return {
      nodes: snapshot.nodes,
      edges: snapshot.edges,
      historyIndex: newIndex,
      isDirty: true,
    };
  }),

  canUndo: () => get().historyIndex > 0,

  canRedo: () => get().historyIndex < get().history.length - 1,

  loadWorkflow: (workflow) => set({
    nodes: workflow.nodes.map((node) => ({
      id: node.id,
      type: node.type,
      position: node.position,
      data: {
        name: node.name,
        description: node.description,
        config: node.config,
      },
    })),
    edges: workflow.connections.map((conn) => ({
      id: conn.id,
      source: conn.source,
      target: conn.target,
      label: conn.label,
      data: { condition: conn.condition },
    })),
    isDirty: false,
    history: [],
    historyIndex: -1,
  }),

  exportWorkflow: () => {
    const { nodes, edges } = get();
    return {
      nodes: nodes.map((node) => ({
        id: node.id,
        type: node.type,
        name: node.data.name,
        description: node.data.description,
        config: node.data.config || {},
        position: node.position,
        next: edges.find((e) => e.source === node.id)?.target || null,
      })),
      connections: edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        condition: edge.data?.condition,
        label: edge.label,
      })),
    };
  },

  markClean: () => set({ isDirty: false }),

  reset: () => set({
    nodes: [],
    edges: [],
    selectedNode: null,
    selectedEdge: null,
    isDirty: false,
    zoom: 1,
    viewport: { x: 0, y: 0 },
    history: [],
    historyIndex: -1,
  }),
}));
