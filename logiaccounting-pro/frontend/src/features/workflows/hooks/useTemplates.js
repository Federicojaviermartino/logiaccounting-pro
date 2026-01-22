/**
 * useTemplates Hook - Workflow template operations
 */
import { useState, useCallback } from 'react';
import * as templateApi from '../api/templateApi';

export function useTemplates() {
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTemplates = useCallback(async (params = {}) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await templateApi.getTemplates(params);
      setTemplates(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchCategories = useCallback(async () => {
    try {
      const data = await templateApi.getTemplateCategories();
      setCategories(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const fetchTemplate = useCallback(async (templateId) => {
    setIsLoading(true);
    setError(null);

    try {
      const template = await templateApi.getTemplate(templateId);
      setSelectedTemplate(template);
      return template;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createFromTemplate = useCallback(async (templateId, customizations = {}) => {
    setIsLoading(true);
    setError(null);

    try {
      const workflowData = await templateApi.createFromTemplate(templateId, customizations);
      return workflowData;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    templates,
    categories,
    selectedTemplate,
    isLoading,
    error,
    fetchTemplates,
    fetchCategories,
    fetchTemplate,
    createFromTemplate,
    clearSelectedTemplate: () => setSelectedTemplate(null),
  };
}
