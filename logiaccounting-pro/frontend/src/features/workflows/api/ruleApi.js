/**
 * Rules API - Business rules management
 */
import { getAuthHeaders } from '../../../utils/tokenService';

const API_BASE = '/api/v1';

export async function getRules(params = {}) {
  const queryString = new URLSearchParams({
    skip: params.skip || 0,
    limit: params.limit || 50,
    ...(params.status && { status: params.status }),
  }).toString();

  const response = await fetch(`${API_BASE}/rules?${queryString}`, {
    headers: {
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch rules');
  }

  return response.json();
}

export async function getRule(ruleId) {
  const response = await fetch(`${API_BASE}/rules/${ruleId}`, {
    headers: {
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch rule');
  }

  return response.json();
}

export async function createRule(ruleData) {
  const response = await fetch(`${API_BASE}/rules`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
    body: JSON.stringify(ruleData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create rule');
  }

  return response.json();
}

export async function updateRule(ruleId, ruleData) {
  const response = await fetch(`${API_BASE}/rules/${ruleId}`, {
    method: 'PUT',
    headers: {
      ...getAuthHeaders(),
    },
    body: JSON.stringify(ruleData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update rule');
  }

  return response.json();
}

export async function deleteRule(ruleId) {
  const response = await fetch(`${API_BASE}/rules/${ruleId}`, {
    method: 'DELETE',
    headers: {
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete rule');
  }
}

export async function activateRule(ruleId) {
  const response = await fetch(`${API_BASE}/rules/${ruleId}/activate`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to activate rule');
  }

  return response.json();
}

export async function pauseRule(ruleId) {
  const response = await fetch(`${API_BASE}/rules/${ruleId}/pause`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to pause rule');
  }

  return response.json();
}

export async function testRule(ruleId, testData) {
  const response = await fetch(`${API_BASE}/rules/${ruleId}/test`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
    body: JSON.stringify(testData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to test rule');
  }

  return response.json();
}

export async function evaluateExpression(expression, variables) {
  const response = await fetch(`${API_BASE}/rules/evaluate`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ expression, variables }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to evaluate expression');
  }

  return response.json();
}
