/**
 * Execution Store - Zustand store for workflow execution state
 */
import { create } from 'zustand';

export const useExecutionStore = create((set, get) => ({
  executions: [],
  currentExecution: null,
  executionSteps: [],
  executionLogs: [],
  stats: null,
  isLoading: false,
  error: null,
  filters: {
    workflowId: null,
    status: null,
    startDate: null,
    endDate: null,
  },

  setExecutions: (executions) => set({ executions }),

  setCurrentExecution: (execution) => set({ currentExecution: execution }),

  setExecutionSteps: (steps) => set({ executionSteps: steps }),

  setExecutionLogs: (logs) => set({ executionLogs: logs }),

  setStats: (stats) => set({ stats }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters }
  })),

  addExecution: (execution) => set((state) => ({
    executions: [execution, ...state.executions]
  })),

  updateExecution: (executionId, updates) => set((state) => ({
    executions: state.executions.map((e) =>
      e.id === executionId ? { ...e, ...updates } : e
    ),
    currentExecution: state.currentExecution?.id === executionId
      ? { ...state.currentExecution, ...updates }
      : state.currentExecution,
  })),

  addLog: (log) => set((state) => ({
    executionLogs: [...state.executionLogs, log]
  })),

  getFilteredExecutions: () => {
    const { executions, filters } = get();
    let filtered = [...executions];

    if (filters.workflowId) {
      filtered = filtered.filter((e) => e.workflow_id === filters.workflowId);
    }

    if (filters.status) {
      filtered = filtered.filter((e) => e.status === filters.status);
    }

    if (filters.startDate) {
      filtered = filtered.filter((e) =>
        new Date(e.started_at) >= new Date(filters.startDate)
      );
    }

    if (filters.endDate) {
      filtered = filtered.filter((e) =>
        new Date(e.started_at) <= new Date(filters.endDate)
      );
    }

    return filtered;
  },

  getStepsByStatus: (status) => {
    return get().executionSteps.filter((step) => step.status === status);
  },

  clearCurrentExecution: () => set({
    currentExecution: null,
    executionSteps: [],
    executionLogs: [],
  }),

  reset: () => set({
    executions: [],
    currentExecution: null,
    executionSteps: [],
    executionLogs: [],
    stats: null,
    isLoading: false,
    error: null,
    filters: { workflowId: null, status: null, startDate: null, endDate: null },
  }),
}));
