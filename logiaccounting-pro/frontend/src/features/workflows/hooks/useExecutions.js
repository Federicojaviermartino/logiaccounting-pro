/**
 * useExecutions Hook - Execution monitoring operations
 */
import { useCallback } from 'react';
import { useExecutionStore } from '../stores/executionStore';
import * as executionApi from '../api/executionApi';

export function useExecutions() {
  const store = useExecutionStore();

  const fetchExecutions = useCallback(async (params = {}) => {
    store.setLoading(true);
    store.setError(null);

    try {
      const executions = await executionApi.getExecutions(params);
      store.setExecutions(executions);
      return executions;
    } catch (error) {
      store.setError(error.message);
      throw error;
    } finally {
      store.setLoading(false);
    }
  }, []);

  const fetchExecution = useCallback(async (executionId) => {
    store.setLoading(true);
    store.setError(null);

    try {
      const [execution, steps, logs] = await Promise.all([
        executionApi.getExecution(executionId),
        executionApi.getExecutionSteps(executionId),
        executionApi.getExecutionLogs(executionId),
      ]);

      store.setCurrentExecution(execution);
      store.setExecutionSteps(steps);
      store.setExecutionLogs(logs);

      return { execution, steps, logs };
    } catch (error) {
      store.setError(error.message);
      throw error;
    } finally {
      store.setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async (params = {}) => {
    try {
      const stats = await executionApi.getExecutionStats(params);
      store.setStats(stats);
      return stats;
    } catch (error) {
      store.setError(error.message);
      throw error;
    }
  }, []);

  const cancelExecution = useCallback(async (executionId) => {
    try {
      const result = await executionApi.cancelExecution(executionId);
      store.updateExecution(executionId, { status: 'cancelled' });
      return result;
    } catch (error) {
      store.setError(error.message);
      throw error;
    }
  }, []);

  const retryExecution = useCallback(async (executionId) => {
    try {
      const result = await executionApi.retryExecution(executionId);
      store.addExecution(result);
      return result;
    } catch (error) {
      store.setError(error.message);
      throw error;
    }
  }, []);

  const refreshLogs = useCallback(async (executionId) => {
    try {
      const logs = await executionApi.getExecutionLogs(executionId);
      store.setExecutionLogs(logs);
      return logs;
    } catch (error) {
      store.setError(error.message);
      throw error;
    }
  }, []);

  return {
    executions: store.executions,
    currentExecution: store.currentExecution,
    executionSteps: store.executionSteps,
    executionLogs: store.executionLogs,
    stats: store.stats,
    isLoading: store.isLoading,
    error: store.error,
    filters: store.filters,
    setFilters: store.setFilters,
    getFilteredExecutions: store.getFilteredExecutions,
    fetchExecutions,
    fetchExecution,
    fetchStats,
    cancelExecution,
    retryExecution,
    refreshLogs,
    clearCurrentExecution: store.clearCurrentExecution,
  };
}
