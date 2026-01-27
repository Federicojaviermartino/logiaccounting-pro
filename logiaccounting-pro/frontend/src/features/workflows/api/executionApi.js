/**
 * Execution API - Workflow execution monitoring and management
 */

const API_BASE = '/api/v1';

export async function getExecutions(params = {}) {
  const queryString = new URLSearchParams({
    skip: params.skip || 0,
    limit: params.limit || 50,
    ...(params.workflowId && { workflow_id: params.workflowId }),
    ...(params.status && { status: params.status }),
  }).toString();

  const response = await fetch(`${API_BASE}/executions?${queryString}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch executions');
  }

  return response.json();
}

export async function getExecution(executionId) {
  const response = await fetch(`${API_BASE}/executions/${executionId}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch execution');
  }

  return response.json();
}

export async function getExecutionSteps(executionId) {
  const response = await fetch(`${API_BASE}/executions/${executionId}/steps`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch execution steps');
  }

  return response.json();
}

export async function getExecutionLogs(executionId) {
  const response = await fetch(`${API_BASE}/executions/${executionId}/logs`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch execution logs');
  }

  return response.json();
}

export async function cancelExecution(executionId) {
  const response = await fetch(`${API_BASE}/executions/${executionId}/cancel`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to cancel execution');
  }

  return response.json();
}

export async function retryExecution(executionId) {
  const response = await fetch(`${API_BASE}/executions/${executionId}/retry`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to retry execution');
  }

  return response.json();
}

export async function getExecutionStats(params = {}) {
  const queryString = new URLSearchParams({
    ...(params.workflowId && { workflow_id: params.workflowId }),
    ...(params.period && { period: params.period }),
  }).toString();

  const response = await fetch(`${API_BASE}/executions/stats/summary?${queryString}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch statistics');
  }

  return response.json();
}
