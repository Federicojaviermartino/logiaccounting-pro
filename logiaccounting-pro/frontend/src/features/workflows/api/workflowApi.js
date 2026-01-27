/**
 * Workflow API - CRUD operations for workflow management
 */

const API_BASE = '/api/v1';

export async function getWorkflows(params = {}) {
  const queryString = new URLSearchParams({
    skip: params.skip || 0,
    limit: params.limit || 20,
    ...(params.status && { status: params.status }),
    ...(params.category && { category: params.category }),
  }).toString();

  const response = await fetch(`${API_BASE}/workflows?${queryString}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch workflows');
  }

  return response.json();
}

export async function getWorkflow(workflowId) {
  const response = await fetch(`${API_BASE}/workflows/${workflowId}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch workflow');
  }

  return response.json();
}

export async function createWorkflow(workflowData) {
  const response = await fetch(`${API_BASE}/workflows`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(workflowData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create workflow');
  }

  return response.json();
}

export async function updateWorkflow(workflowId, workflowData) {
  const response = await fetch(`${API_BASE}/workflows/${workflowId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(workflowData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update workflow');
  }

  return response.json();
}

export async function deleteWorkflow(workflowId) {
  const response = await fetch(`${API_BASE}/workflows/${workflowId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete workflow');
  }
}

export async function activateWorkflow(workflowId) {
  const response = await fetch(`${API_BASE}/workflows/${workflowId}/activate`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to activate workflow');
  }

  return response.json();
}

export async function pauseWorkflow(workflowId) {
  const response = await fetch(`${API_BASE}/workflows/${workflowId}/pause`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to pause workflow');
  }

  return response.json();
}

export async function triggerWorkflow(workflowId, triggerData = {}) {
  const response = await fetch(`${API_BASE}/workflows/${workflowId}/trigger`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(triggerData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to trigger workflow');
  }

  return response.json();
}

export async function testWorkflow(workflowId, testData) {
  const response = await fetch(`${API_BASE}/workflows/${workflowId}/test`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(testData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to test workflow');
  }

  return response.json();
}

export async function getWorkflowVersions(workflowId) {
  const response = await fetch(`${API_BASE}/workflows/${workflowId}/versions`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch versions');
  }

  return response.json();
}

export async function rollbackWorkflow(workflowId, version) {
  const response = await fetch(`${API_BASE}/workflows/${workflowId}/rollback/${version}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to rollback workflow');
  }

  return response.json();
}
