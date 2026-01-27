/**
 * useWorkflows Hook - Workflow operations with state management
 */
import { useCallback } from 'react';
import { useWorkflowStore } from '../stores/workflowStore';
import * as workflowApi from '../api/workflowApi';

export function useWorkflows() {
  const store = useWorkflowStore();

  const fetchWorkflows = useCallback(async (params = {}) => {
    store.setLoading(true);
    store.setError(null);

    try {
      const workflows = await workflowApi.getWorkflows(params);
      store.setWorkflows(workflows);
      return workflows;
    } catch (error) {
      store.setError(error.message);
      throw error;
    } finally {
      store.setLoading(false);
    }
  }, []);

  const fetchWorkflow = useCallback(async (workflowId) => {
    store.setLoading(true);
    store.setError(null);

    try {
      const workflow = await workflowApi.getWorkflow(workflowId);
      store.setCurrentWorkflow(workflow);
      return workflow;
    } catch (error) {
      store.setError(error.message);
      throw error;
    } finally {
      store.setLoading(false);
    }
  }, []);

  const createWorkflow = useCallback(async (workflowData) => {
    store.setLoading(true);
    store.setError(null);

    try {
      const workflow = await workflowApi.createWorkflow(workflowData);
      store.addWorkflow(workflow);
      return workflow;
    } catch (error) {
      store.setError(error.message);
      throw error;
    } finally {
      store.setLoading(false);
    }
  }, []);

  const updateWorkflow = useCallback(async (workflowId, workflowData) => {
    store.setLoading(true);
    store.setError(null);

    try {
      const result = await workflowApi.updateWorkflow(workflowId, workflowData);
      store.updateWorkflowInList(workflowId, workflowData);
      return result;
    } catch (error) {
      store.setError(error.message);
      throw error;
    } finally {
      store.setLoading(false);
    }
  }, []);

  const deleteWorkflow = useCallback(async (workflowId) => {
    store.setLoading(true);
    store.setError(null);

    try {
      await workflowApi.deleteWorkflow(workflowId);
      store.removeWorkflow(workflowId);
    } catch (error) {
      store.setError(error.message);
      throw error;
    } finally {
      store.setLoading(false);
    }
  }, []);

  const activateWorkflow = useCallback(async (workflowId) => {
    try {
      const result = await workflowApi.activateWorkflow(workflowId);
      store.updateWorkflowInList(workflowId, { status: 'active' });
      return result;
    } catch (error) {
      store.setError(error.message);
      throw error;
    }
  }, []);

  const pauseWorkflow = useCallback(async (workflowId) => {
    try {
      const result = await workflowApi.pauseWorkflow(workflowId);
      store.updateWorkflowInList(workflowId, { status: 'paused' });
      return result;
    } catch (error) {
      store.setError(error.message);
      throw error;
    }
  }, []);

  const triggerWorkflow = useCallback(async (workflowId, triggerData) => {
    try {
      return await workflowApi.triggerWorkflow(workflowId, triggerData);
    } catch (error) {
      store.setError(error.message);
      throw error;
    }
  }, []);

  const testWorkflow = useCallback(async (workflowId, testData) => {
    try {
      return await workflowApi.testWorkflow(workflowId, testData);
    } catch (error) {
      store.setError(error.message);
      throw error;
    }
  }, []);

  return {
    workflows: store.workflows,
    currentWorkflow: store.currentWorkflow,
    isLoading: store.isLoading,
    error: store.error,
    filters: store.filters,
    setFilters: store.setFilters,
    getFilteredWorkflows: store.getFilteredWorkflows,
    fetchWorkflows,
    fetchWorkflow,
    createWorkflow,
    updateWorkflow,
    deleteWorkflow,
    activateWorkflow,
    pauseWorkflow,
    triggerWorkflow,
    testWorkflow,
    clearCurrentWorkflow: store.clearCurrentWorkflow,
  };
}
