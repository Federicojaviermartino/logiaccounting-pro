/**
 * Offline Storage Manager
 * IndexedDB wrapper for offline data persistence
 */

const DB_NAME = 'logiaccounting-offline';
const DB_VERSION = 1;

// Store names
const STORES = {
  OFFLINE_ACTIONS: 'offline-actions',
  CACHED_DATA: 'cached-data',
  USER_PREFERENCES: 'user-preferences',
  SYNC_STATE: 'sync-state',
};

class OfflineStorage {
  constructor() {
    this.db = null;
    this.isReady = false;
  }

  /**
   * Initialize the database
   */
  async init() {
    if (this.db) {
      return this.db;
    }

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.error('[Offline] Database failed to open');
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        this.isReady = true;
        console.log('[Offline] Database ready');
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        // Offline actions store
        if (!db.objectStoreNames.contains(STORES.OFFLINE_ACTIONS)) {
          const actionStore = db.createObjectStore(STORES.OFFLINE_ACTIONS, {
            keyPath: 'id',
          });
          actionStore.createIndex('type', 'type', { unique: false });
          actionStore.createIndex('created_at', 'created_at', { unique: false });
        }

        // Cached data store
        if (!db.objectStoreNames.contains(STORES.CACHED_DATA)) {
          const dataStore = db.createObjectStore(STORES.CACHED_DATA, {
            keyPath: 'key',
          });
          dataStore.createIndex('type', 'type', { unique: false });
          dataStore.createIndex('expires_at', 'expires_at', { unique: false });
        }

        // User preferences store
        if (!db.objectStoreNames.contains(STORES.USER_PREFERENCES)) {
          db.createObjectStore(STORES.USER_PREFERENCES, { keyPath: 'key' });
        }

        // Sync state store
        if (!db.objectStoreNames.contains(STORES.SYNC_STATE)) {
          db.createObjectStore(STORES.SYNC_STATE, { keyPath: 'key' });
        }

        console.log('[Offline] Database schema created');
      };
    });
  }

  /**
   * Ensure database is ready
   */
  async ensureReady() {
    if (!this.db) {
      await this.init();
    }
  }

  // ==================== Offline Actions ====================

  /**
   * Queue an offline action
   */
  async queueAction(type, data) {
    await this.ensureReady();

    const action = {
      id: `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      data,
      created_at: new Date().toISOString(),
      status: 'pending',
    };

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.OFFLINE_ACTIONS, 'readwrite');
      const store = tx.objectStore(STORES.OFFLINE_ACTIONS);
      const request = store.add(action);

      request.onsuccess = () => {
        console.log('[Offline] Action queued:', action.id);
        resolve(action);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Get all pending actions
   */
  async getPendingActions() {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.OFFLINE_ACTIONS, 'readonly');
      const store = tx.objectStore(STORES.OFFLINE_ACTIONS);
      const request = store.getAll();

      request.onsuccess = () => {
        const actions = request.result.filter((a) => a.status === 'pending');
        resolve(actions);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Mark action as synced
   */
  async markActionSynced(actionId, serverId) {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.OFFLINE_ACTIONS, 'readwrite');
      const store = tx.objectStore(STORES.OFFLINE_ACTIONS);
      const getRequest = store.get(actionId);

      getRequest.onsuccess = () => {
        const action = getRequest.result;
        if (action) {
          action.status = 'synced';
          action.server_id = serverId;
          action.synced_at = new Date().toISOString();
          store.put(action);
        }
        resolve();
      };

      getRequest.onerror = () => {
        reject(getRequest.error);
      };
    });
  }

  /**
   * Clear synced actions
   */
  async clearSyncedActions() {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.OFFLINE_ACTIONS, 'readwrite');
      const store = tx.objectStore(STORES.OFFLINE_ACTIONS);
      const request = store.getAll();

      request.onsuccess = () => {
        const actions = request.result;
        actions.forEach((action) => {
          if (action.status === 'synced') {
            store.delete(action.id);
          }
        });
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  // ==================== Cached Data ====================

  /**
   * Cache data with optional TTL
   */
  async cacheData(key, type, data, ttlMinutes = 60) {
    await this.ensureReady();

    const item = {
      key,
      type,
      data,
      cached_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + ttlMinutes * 60 * 1000).toISOString(),
    };

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.CACHED_DATA, 'readwrite');
      const store = tx.objectStore(STORES.CACHED_DATA);
      const request = store.put(item);

      request.onsuccess = () => {
        resolve(item);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Get cached data
   */
  async getCachedData(key) {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.CACHED_DATA, 'readonly');
      const store = tx.objectStore(STORES.CACHED_DATA);
      const request = store.get(key);

      request.onsuccess = () => {
        const item = request.result;
        if (item && new Date(item.expires_at) > new Date()) {
          resolve(item.data);
        } else {
          resolve(null);
        }
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  /**
   * Clear expired cache
   */
  async clearExpiredCache() {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.CACHED_DATA, 'readwrite');
      const store = tx.objectStore(STORES.CACHED_DATA);
      const request = store.getAll();

      request.onsuccess = () => {
        const now = new Date();
        request.result.forEach((item) => {
          if (new Date(item.expires_at) <= now) {
            store.delete(item.key);
          }
        });
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  // ==================== Sync State ====================

  /**
   * Save sync state
   */
  async setSyncState(key, value) {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.SYNC_STATE, 'readwrite');
      const store = tx.objectStore(STORES.SYNC_STATE);
      const request = store.put({ key, value, updated_at: new Date().toISOString() });

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get sync state
   */
  async getSyncState(key) {
    await this.ensureReady();

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(STORES.SYNC_STATE, 'readonly');
      const store = tx.objectStore(STORES.SYNC_STATE);
      const request = store.get(key);

      request.onsuccess = () => {
        resolve(request.result?.value || null);
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  // ==================== Utilities ====================

  /**
   * Clear all offline data
   */
  async clearAll() {
    await this.ensureReady();

    const stores = Object.values(STORES);
    const tx = this.db.transaction(stores, 'readwrite');

    stores.forEach((storeName) => {
      tx.objectStore(storeName).clear();
    });

    return new Promise((resolve, reject) => {
      tx.oncomplete = () => {
        console.log('[Offline] All data cleared');
        resolve();
      };
      tx.onerror = () => reject(tx.error);
    });
  }

  /**
   * Get storage info
   */
  async getStorageInfo() {
    const pendingActions = await this.getPendingActions();

    return {
      pendingActionsCount: pendingActions.length,
      isReady: this.isReady,
    };
  }
}

// Export singleton instance
export const offlineStorage = new OfflineStorage();

// Initialize on import
offlineStorage.init().catch(console.error);

export default offlineStorage;
