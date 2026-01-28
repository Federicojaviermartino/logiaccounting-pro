/**
 * Centralized Token Service
 *
 * This module provides a single source of truth for authentication token access.
 * All API modules should import getAuthToken() from here instead of directly
 * accessing localStorage or sessionStorage.
 *
 * Security: Uses sessionStorage which is cleared when the browser tab closes,
 * reducing the window for XSS-based token exfiltration compared to localStorage.
 */

// Token storage key - must match AuthContext.jsx
const TOKEN_KEY = 'token';
const PORTAL_TOKEN_KEY = 'portal_token';

/**
 * Get the current authentication token.
 * @returns {string|null} The auth token or null if not authenticated
 */
export function getAuthToken() {
  // First try sessionStorage (current standard)
  const sessionToken = sessionStorage.getItem(TOKEN_KEY);
  if (sessionToken) {
    return sessionToken;
  }

  // Fallback to localStorage for migration (legacy support)
  const localToken = localStorage.getItem(TOKEN_KEY);
  if (localToken) {
    // Migrate to sessionStorage
    sessionStorage.setItem(TOKEN_KEY, localToken);
    localStorage.removeItem(TOKEN_KEY);
    return localToken;
  }

  return null;
}

/**
 * Get the portal authentication token (for customer portal).
 * @returns {string|null} The portal token or null if not authenticated
 */
export function getPortalToken() {
  return sessionStorage.getItem(PORTAL_TOKEN_KEY) || localStorage.getItem(PORTAL_TOKEN_KEY);
}

/**
 * Set the authentication token.
 * @param {string|null} token - The token to store, or null to clear
 */
export function setAuthToken(token) {
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(TOKEN_KEY);
  }
  // Also clean up any legacy localStorage token
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Set the portal authentication token.
 * @param {string|null} token - The token to store, or null to clear
 */
export function setPortalToken(token) {
  if (token) {
    sessionStorage.setItem(PORTAL_TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(PORTAL_TOKEN_KEY);
  }
  // Also clean up any legacy localStorage token
  localStorage.removeItem(PORTAL_TOKEN_KEY);
}

/**
 * Clear all authentication tokens.
 */
export function clearAllTokens() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(PORTAL_TOKEN_KEY);
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(PORTAL_TOKEN_KEY);
}

/**
 * Get authorization headers for API requests.
 * @param {boolean} usePortalToken - Whether to use the portal token instead of main token
 * @returns {Object} Headers object with Authorization header if token exists
 */
export function getAuthHeaders(usePortalToken = false) {
  const token = usePortalToken ? getPortalToken() : getAuthToken();
  if (token) {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }
  return {
    'Content-Type': 'application/json',
  };
}

/**
 * Check if user is authenticated (has a valid token).
 * Note: This only checks for token presence, not validity.
 * @returns {boolean}
 */
export function hasAuthToken() {
  return !!getAuthToken();
}

export default {
  getAuthToken,
  getPortalToken,
  setAuthToken,
  setPortalToken,
  clearAllTokens,
  getAuthHeaders,
  hasAuthToken,
};
