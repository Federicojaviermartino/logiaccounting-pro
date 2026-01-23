/**
 * IndexedDB Database Manager
 */

import { openDB, deleteDB } from 'idb';

const DB_NAME = 'logiaccounting-db';
const DB_VERSION = 1;

let dbPromise = null;

/**
 * Initialize the database
 */
export async function initDatabase() {
  if (dbPromise) return dbPromise;

  dbPromise = openDB(DB_NAME, DB_VERSION, {
    upgrade(db, oldVersion, newVersion, transaction) {
      console.log(`Upgrading database from v${oldVersion} to v${newVersion}`);

      // Invoices store
      if (!db.objectStoreNames.contains('invoices')) {
        const invoicesStore = db.createObjectStore('invoices', { keyPath: 'id' });
        invoicesStore.createIndex('by-status', 'status');
        invoicesStore.createIndex('by-client', 'client_id');
        invoicesStore.createIndex('by-date', 'date');
        invoicesStore.createIndex('by-synced', 'synced_at');
      }

      // Projects store
      if (!db.objectStoreNames.contains('projects')) {
        const projectsStore = db.createObjectStore('projects', { keyPath: 'id' });
        projectsStore.createIndex('by-status', 'status');
        projectsStore.createIndex('by-client', 'client_id');
        projectsStore.createIndex('by-synced', 'synced_at');
      }

      // Inventory store
      if (!db.objectStoreNames.contains('inventory')) {
        const inventoryStore = db.createObjectStore('inventory', { keyPath: 'id' });
        inventoryStore.createIndex('by-sku', 'sku');
        inventoryStore.createIndex('by-category', 'category');
        inventoryStore.createIndex('by-low-stock', 'is_low_stock');
        inventoryStore.createIndex('by-synced', 'synced_at');
      }

      // Payments store
      if (!db.objectStoreNames.contains('payments')) {
        const paymentsStore = db.createObjectStore('payments', { keyPath: 'id' });
        paymentsStore.createIndex('by-status', 'status');
        paymentsStore.createIndex('by-invoice', 'invoice_id');
        paymentsStore.createIndex('by-synced', 'synced_at');
      }

      // Approvals store
      if (!db.objectStoreNames.contains('approvals')) {
        const approvalsStore = db.createObjectStore('approvals', { keyPath: 'id' });
        approvalsStore.createIndex('by-status', 'status');
        approvalsStore.createIndex('by-type', 'type');
        approvalsStore.createIndex('by-synced', 'synced_at');
      }

      // Sync queue store
      if (!db.objectStoreNames.contains('sync-queue')) {
        const syncStore = db.createObjectStore('sync-queue', {
          keyPath: 'id',
          autoIncrement: true
        });
        syncStore.createIndex('by-timestamp', 'timestamp');
        syncStore.createIndex('by-entity', 'entity_type');
        syncStore.createIndex('by-priority', 'priority');
      }

      // Settings store
      if (!db.objectStoreNames.contains('settings')) {
        db.createObjectStore('settings', { keyPath: 'key' });
      }

      // Cache metadata store
      if (!db.objectStoreNames.contains('cache-meta')) {
        const cacheStore = db.createObjectStore('cache-meta', { keyPath: 'key' });
        cacheStore.createIndex('by-expires', 'expires_at');
      }
    },
    blocked() {
      console.warn('Database upgrade blocked. Please close other tabs.');
    },
    blocking() {
      console.warn('This tab is blocking database upgrade.');
    },
    terminated() {
      console.error('Database connection terminated unexpectedly.');
      dbPromise = null;
    },
  });

  return dbPromise;
}

/**
 * Get database instance
 */
export async function getDB() {
  if (!dbPromise) {
    await initDatabase();
  }
  return dbPromise;
}

/**
 * Clear all data (for logout)
 */
export async function clearAllData() {
  const db = await getDB();
  const stores = ['invoices', 'projects', 'inventory', 'payments', 'approvals', 'sync-queue'];

  const tx = db.transaction(stores, 'readwrite');
  await Promise.all([
    ...stores.map(store => tx.objectStore(store).clear()),
    tx.done,
  ]);
}

/**
 * Delete database completely
 */
export async function deleteDatabase() {
  dbPromise = null;
  await deleteDB(DB_NAME);
}

/**
 * Get database stats
 */
export async function getDatabaseStats() {
  const db = await getDB();
  const stores = ['invoices', 'projects', 'inventory', 'payments', 'approvals', 'sync-queue'];

  const stats = {};
  for (const storeName of stores) {
    const count = await db.count(storeName);
    stats[storeName] = count;
  }

  return stats;
}
