/**
 * PWA Module Index
 */

export { swManager } from './serviceWorker';
export { pushManager } from './pushManager';
export { offlineStorage } from './offlineStorage';

// Initialize PWA features
export const initPWA = async () => {
  // Register service worker
  await import('./serviceWorker');

  // Initialize offline storage
  const { offlineStorage } = await import('./offlineStorage');
  await offlineStorage.init();

  // Clean up expired cache
  await offlineStorage.clearExpiredCache();

  console.log('[PWA] Initialized');
};
