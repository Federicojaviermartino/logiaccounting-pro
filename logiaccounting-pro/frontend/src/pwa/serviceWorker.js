/**
 * Service Worker Registration and Management
 */

const SW_URL = '/sw.js';

class ServiceWorkerManager {
  constructor() {
    this.registration = null;
    this.updateAvailable = false;
    this.onUpdateAvailable = null;
  }

  /**
   * Register the service worker
   */
  async register() {
    if (!('serviceWorker' in navigator)) {
      console.log('[PWA] Service workers not supported');
      return null;
    }

    try {
      this.registration = await navigator.serviceWorker.register(SW_URL, {
        scope: '/',
      });

      console.log('[PWA] Service worker registered:', this.registration.scope);

      // Check for updates
      this.registration.addEventListener('updatefound', () => {
        this.handleUpdateFound();
      });

      // Handle controller change (new SW activated)
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('[PWA] New service worker activated');
      });

      // Check for updates periodically
      setInterval(() => {
        this.checkForUpdates();
      }, 60 * 60 * 1000); // Every hour

      return this.registration;
    } catch (error) {
      console.error('[PWA] Service worker registration failed:', error);
      return null;
    }
  }

  /**
   * Handle when a new service worker is found
   */
  handleUpdateFound() {
    const newWorker = this.registration.installing;

    newWorker.addEventListener('statechange', () => {
      if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
        // New update available
        this.updateAvailable = true;
        console.log('[PWA] New version available');

        if (this.onUpdateAvailable) {
          this.onUpdateAvailable();
        }
      }
    });
  }

  /**
   * Check for service worker updates
   */
  async checkForUpdates() {
    if (this.registration) {
      try {
        await this.registration.update();
        console.log('[PWA] Checked for updates');
      } catch (error) {
        console.error('[PWA] Update check failed:', error);
      }
    }
  }

  /**
   * Apply pending update (reload with new SW)
   */
  applyUpdate() {
    if (this.registration && this.registration.waiting) {
      // Tell waiting SW to skip waiting
      this.registration.waiting.postMessage({ type: 'SKIP_WAITING' });

      // Reload page to use new SW
      window.location.reload();
    }
  }

  /**
   * Unregister service worker
   */
  async unregister() {
    if (this.registration) {
      const success = await this.registration.unregister();
      console.log('[PWA] Service worker unregistered:', success);
      return success;
    }
    return false;
  }

  /**
   * Clear all caches
   */
  async clearCaches() {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map((name) => caches.delete(name)));
    console.log('[PWA] All caches cleared');
  }

  /**
   * Pre-cache specific URLs
   */
  async cacheUrls(urls) {
    if (this.registration && this.registration.active) {
      this.registration.active.postMessage({
        type: 'CACHE_URLS',
        urls,
      });
    }
  }

  /**
   * Get cache storage estimate
   */
  async getStorageEstimate() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return {
        usage: estimate.usage,
        quota: estimate.quota,
        usagePercent: ((estimate.usage / estimate.quota) * 100).toFixed(2),
      };
    }
    return null;
  }
}

// Export singleton instance
export const swManager = new ServiceWorkerManager();

// Auto-register on import
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    swManager.register();
  });
}

export default swManager;
