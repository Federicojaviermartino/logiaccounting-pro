/**
 * Workflow Store - Zustand store for workflow state management
 */
import { create } from 'zustand';

export const useWorkflowStore = create((set, get) => ({
  workflows: [],
  currentWorkflow: null,
  isLoading: false,
  error: null,
  filters: {
    status: null,
    category: null,
    search: '',
  },

  setWorkflows: (workflows) => set({ workflows }),

  setCurrentWorkflow: (workflow) => set({ currentWorkflow: workflow }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters }
  })),

  addWorkflow: (workflow) => set((state) => ({
    workflows: [workflow, ...state.workflows]
  })),

  updateWorkflowInList: (workflowId, updates) => set((state) => ({
    workflows: state.workflows.map((w) =>
      w.id === workflowId ? { ...w, ...updates } : w
    )
  })),

  removeWorkflow: (workflowId) => set((state) => ({
    workflows: state.workflows.filter((w) => w.id !== workflowId)
  })),

  getFilteredWorkflows: () => {
    const { workflows, filters } = get();
    let filtered = [...workflows];

    if (filters.status) {
      filtered = filtered.filter((w) => w.status === filters.status);
    }

    if (filters.category) {
      filtered = filtered.filter((w) => w.category === filters.category);
    }

    if (filters.search) {
      const search = filters.search.toLowerCase();
      filtered = filtered.filter((w) =>
        w.name.toLowerCase().includes(search) ||
        (w.description && w.description.toLowerCase().includes(search))
      );
    }

    return filtered;
  },

  clearCurrentWorkflow: () => set({ currentWorkflow: null }),

  reset: () => set({
    workflows: [],
    currentWorkflow: null,
    isLoading: false,
    error: null,
    filters: { status: null, category: null, search: '' },
  }),
}));
