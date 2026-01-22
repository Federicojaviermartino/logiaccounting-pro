/**
 * useRules Hook - Business rules operations
 */
import { useState, useCallback } from 'react';
import * as ruleApi from '../api/ruleApi';

export function useRules() {
  const [rules, setRules] = useState([]);
  const [currentRule, setCurrentRule] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchRules = useCallback(async (params = {}) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await ruleApi.getRules(params);
      setRules(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchRule = useCallback(async (ruleId) => {
    setIsLoading(true);
    setError(null);

    try {
      const rule = await ruleApi.getRule(ruleId);
      setCurrentRule(rule);
      return rule;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createRule = useCallback(async (ruleData) => {
    setIsLoading(true);
    setError(null);

    try {
      const rule = await ruleApi.createRule(ruleData);
      setRules((prev) => [rule, ...prev]);
      return rule;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateRule = useCallback(async (ruleId, ruleData) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await ruleApi.updateRule(ruleId, ruleData);
      setRules((prev) =>
        prev.map((r) => (r.id === ruleId ? { ...r, ...ruleData } : r))
      );
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteRule = useCallback(async (ruleId) => {
    setIsLoading(true);
    setError(null);

    try {
      await ruleApi.deleteRule(ruleId);
      setRules((prev) => prev.filter((r) => r.id !== ruleId));
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const activateRule = useCallback(async (ruleId) => {
    try {
      const result = await ruleApi.activateRule(ruleId);
      setRules((prev) =>
        prev.map((r) => (r.id === ruleId ? { ...r, status: 'active' } : r))
      );
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const pauseRule = useCallback(async (ruleId) => {
    try {
      const result = await ruleApi.pauseRule(ruleId);
      setRules((prev) =>
        prev.map((r) => (r.id === ruleId ? { ...r, status: 'paused' } : r))
      );
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const testRule = useCallback(async (ruleId, testData) => {
    try {
      return await ruleApi.testRule(ruleId, testData);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const evaluateExpression = useCallback(async (expression, variables) => {
    try {
      return await ruleApi.evaluateExpression(expression, variables);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  return {
    rules,
    currentRule,
    isLoading,
    error,
    fetchRules,
    fetchRule,
    createRule,
    updateRule,
    deleteRule,
    activateRule,
    pauseRule,
    testRule,
    evaluateExpression,
    clearCurrentRule: () => setCurrentRule(null),
  };
}
