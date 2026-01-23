/**
 * Generic Repository for IndexedDB operations
 */

import { getDB } from './database';

export class Repository {
  constructor(storeName) {
    this.storeName = storeName;
  }

  /**
   * Get all items
   */
  async getAll() {
    const db = await getDB();
    return db.getAll(this.storeName);
  }

  /**
   * Get item by ID
   */
  async getById(id) {
    const db = await getDB();
    return db.get(this.storeName, id);
  }

  /**
   * Get items by index
   */
  async getByIndex(indexName, value) {
    const db = await getDB();
    return db.getAllFromIndex(this.storeName, indexName, value);
  }

  /**
   * Get items by index range
   */
  async getByIndexRange(indexName, lowerBound, upperBound) {
    const db = await getDB();
    const range = IDBKeyRange.bound(lowerBound, upperBound);
    return db.getAllFromIndex(this.storeName, indexName, range);
  }

  /**
   * Add or update item
   */
  async put(item) {
    const db = await getDB();
    const itemWithMeta = {
      ...item,
      local_modified_at: new Date().toISOString(),
    };
    await db.put(this.storeName, itemWithMeta);
    return itemWithMeta;
  }

  /**
   * Add multiple items (bulk insert)
   */
  async putMany(items) {
    const db = await getDB();
    const tx = db.transaction(this.storeName, 'readwrite');
    const timestamp = new Date().toISOString();

    await Promise.all([
      ...items.map(item =>
        tx.store.put({ ...item, local_modified_at: timestamp })
      ),
      tx.done,
    ]);
  }

  /**
   * Delete item by ID
   */
  async delete(id) {
    const db = await getDB();
    await db.delete(this.storeName, id);
  }

  /**
   * Delete multiple items
   */
  async deleteMany(ids) {
    const db = await getDB();
    const tx = db.transaction(this.storeName, 'readwrite');
    await Promise.all([
      ...ids.map(id => tx.store.delete(id)),
      tx.done,
    ]);
  }

  /**
   * Clear all items
   */
  async clear() {
    const db = await getDB();
    await db.clear(this.storeName);
  }

  /**
   * Count items
   */
  async count() {
    const db = await getDB();
    return db.count(this.storeName);
  }

  /**
   * Count items by index
   */
  async countByIndex(indexName, value) {
    const db = await getDB();
    return db.countFromIndex(this.storeName, indexName, value);
  }

  /**
   * Get items that need syncing
   */
  async getUnsynced() {
    const db = await getDB();
    const all = await db.getAll(this.storeName);
    return all.filter(item =>
      !item.synced_at ||
      (item.local_modified_at && item.local_modified_at > item.synced_at)
    );
  }

  /**
   * Mark items as synced
   */
  async markSynced(ids, timestamp) {
    const db = await getDB();
    const tx = db.transaction(this.storeName, 'readwrite');
    const syncTime = timestamp || new Date().toISOString();

    for (const id of ids) {
      const item = await tx.store.get(id);
      if (item) {
        await tx.store.put({ ...item, synced_at: syncTime });
      }
    }

    await tx.done;
  }

  /**
   * Get paginated items
   */
  async getPaginated(page = 1, pageSize = 20, indexName = null, direction = 'prev') {
    const db = await getDB();
    const items = [];
    const skip = (page - 1) * pageSize;
    let count = 0;
    let skipped = 0;

    const tx = db.transaction(this.storeName, 'readonly');
    let cursor;

    if (indexName) {
      cursor = await tx.store.index(indexName).openCursor(null, direction);
    } else {
      cursor = await tx.store.openCursor(null, direction);
    }

    while (cursor && count < pageSize) {
      if (skipped < skip) {
        skipped++;
      } else {
        items.push(cursor.value);
        count++;
      }
      cursor = await cursor.continue();
    }

    const total = await this.count();

    return {
      items,
      page,
      pageSize,
      total,
      totalPages: Math.ceil(total / pageSize),
    };
  }
}

// Pre-configured repositories
export const invoicesRepo = new Repository('invoices');
export const projectsRepo = new Repository('projects');
export const inventoryRepo = new Repository('inventory');
export const paymentsRepo = new Repository('payments');
export const approvalsRepo = new Repository('approvals');
