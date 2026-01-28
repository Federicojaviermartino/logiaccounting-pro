/**
 * Sync Queue Manager
 * Manages offline mutations queue
 */

import { getDB } from '../storage/database';
import { getAuthToken } from '../../utils/tokenService';

const SYNC_PRIORITIES = {
  CRITICAL: 1,    // Approvals, payments
  HIGH: 2,        // Invoices, projects
  MEDIUM: 3,      // Inventory
  LOW: 4,         // Settings, preferences
};

class SyncQueue {
  constructor() {
    this.isProcessing = false;
    this.listeners = new Set();
  }

  /**
   * Add item to sync queue
   */
  async enqueue(item) {
    const db = await getDB();

    const queueItem = {
      entity_type: item.entityType,
      entity_id: item.entityId,
      action: item.action, // 'create', 'update', 'delete'
      payload: item.payload,
      timestamp: new Date().toISOString(),
      priority: item.priority || SYNC_PRIORITIES.MEDIUM,
      retries: 0,
      max_retries: item.maxRetries || 3,
      endpoint: item.endpoint,
      method: item.method || 'POST',
    };

    const id = await db.add('sync-queue', queueItem);
    this.notifyListeners({ type: 'enqueued', item: { ...queueItem, id } });

    // Try to sync immediately if online
    if (navigator.onLine) {
      this.processQueue();
    }

    return id;
  }

  /**
   * Get all pending items
   */
  async getPending() {
    const db = await getDB();
    const items = await db.getAllFromIndex('sync-queue', 'by-priority');
    return items.sort((a, b) => a.priority - b.priority);
  }

  /**
   * Get queue count
   */
  async getCount() {
    const db = await getDB();
    return db.count('sync-queue');
  }

  /**
   * Process sync queue
   */
  async processQueue() {
    if (this.isProcessing || !navigator.onLine) {
      return;
    }

    this.isProcessing = true;
    this.notifyListeners({ type: 'sync-started' });

    const db = await getDB();
    const items = await this.getPending();

    const results = {
      success: 0,
      failed: 0,
      skipped: 0,
    };

    for (const item of items) {
      try {
        await this.processItem(item);
        await db.delete('sync-queue', item.id);
        results.success++;
        this.notifyListeners({ type: 'item-synced', item });
      } catch (error) {
        console.error('Sync failed for item:', item.id, error);

        if (item.retries < item.max_retries) {
          // Increment retry count
          await db.put('sync-queue', {
            ...item,
            retries: item.retries + 1,
            last_error: error.message,
            last_retry_at: new Date().toISOString(),
          });
          results.failed++;
        } else {
          // Max retries reached - move to failed items or delete
          await db.delete('sync-queue', item.id);
          results.skipped++;
          this.notifyListeners({ type: 'item-failed', item, error });
        }
      }
    }

    this.isProcessing = false;
    this.notifyListeners({ type: 'sync-completed', results });

    return results;
  }

  /**
   * Process single queue item
   */
  async processItem(item) {
    const token = getAuthToken();

    const response = await fetch(item.endpoint, {
      method: item.method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Offline-Sync': 'true',
        'X-Sync-Timestamp': item.timestamp,
      },
      body: item.method !== 'DELETE' ? JSON.stringify(item.payload) : undefined,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * Clear all pending items
   */
  async clear() {
    const db = await getDB();
    await db.clear('sync-queue');
    this.notifyListeners({ type: 'queue-cleared' });
  }

  /**
   * Add listener for sync events
   */
  addListener(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * Notify all listeners
   */
  notifyListeners(event) {
    this.listeners.forEach(callback => {
      try {
        callback(event);
      } catch (error) {
        console.error('Sync listener error:', error);
      }
    });
  }

  /**
   * Register for background sync
   */
  async registerBackgroundSync() {
    if ('serviceWorker' in navigator && 'SyncManager' in window) {
      const registration = await navigator.serviceWorker.ready;
      await registration.sync.register('sync-data');
    }
  }
}

// Singleton instance
export const syncQueue = new SyncQueue();

// Auto-sync when coming online
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    console.log('Back online - processing sync queue');
    syncQueue.processQueue();
  });
}

export { SYNC_PRIORITIES };
export default syncQueue;
