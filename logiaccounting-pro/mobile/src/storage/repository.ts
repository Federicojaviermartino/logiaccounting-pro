/**
 * Generic Repository for SQLite operations
 */

import { getDatabase } from './database';
import { v4 as uuidv4 } from 'uuid';

export interface BaseEntity {
  id: string;
  created_at?: string;
  updated_at?: string;
  synced_at?: string | null;
  local_modified_at?: string;
  is_deleted?: number;
}

export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export class Repository<T extends BaseEntity> {
  constructor(private tableName: string) {}

  async getAll(): Promise<T[]> {
    const db = getDatabase();
    const result = await db.getAllAsync<T>(
      `SELECT * FROM ${this.tableName} WHERE is_deleted = 0 ORDER BY created_at DESC`
    );
    return result;
  }

  async getById(id: string): Promise<T | null> {
    const db = getDatabase();
    const result = await db.getFirstAsync<T>(
      `SELECT * FROM ${this.tableName} WHERE id = ? AND is_deleted = 0`,
      [id]
    );
    return result ?? null;
  }

  async getByField(field: string, value: unknown): Promise<T[]> {
    const db = getDatabase();
    const result = await db.getAllAsync<T>(
      `SELECT * FROM ${this.tableName} WHERE ${field} = ? AND is_deleted = 0`,
      [value]
    );
    return result;
  }

  async getPaginated(page: number = 1, pageSize: number = 20): Promise<PaginatedResult<T>> {
    const db = getDatabase();
    const offset = (page - 1) * pageSize;

    const [data, countResult] = await Promise.all([
      db.getAllAsync<T>(
        `SELECT * FROM ${this.tableName} WHERE is_deleted = 0 ORDER BY created_at DESC LIMIT ? OFFSET ?`,
        [pageSize, offset]
      ),
      db.getFirstAsync<{ count: number }>(
        `SELECT COUNT(*) as count FROM ${this.tableName} WHERE is_deleted = 0`
      ),
    ]);

    const total = countResult?.count ?? 0;

    return {
      data,
      total,
      page,
      pageSize,
      totalPages: Math.ceil(total / pageSize),
    };
  }

  async search(query: string, searchFields: string[]): Promise<T[]> {
    const db = getDatabase();
    const conditions = searchFields.map((f) => `${f} LIKE ?`).join(' OR ');
    const params = searchFields.map(() => `%${query}%`);

    const result = await db.getAllAsync<T>(
      `SELECT * FROM ${this.tableName} WHERE (${conditions}) AND is_deleted = 0 ORDER BY created_at DESC`,
      params
    );
    return result;
  }

  async insert(data: Omit<T, 'id'>): Promise<T> {
    const db = getDatabase();
    const now = new Date().toISOString();
    const id = uuidv4();

    const entity = {
      ...data,
      id,
      created_at: now,
      updated_at: now,
      local_modified_at: now,
      is_deleted: 0,
    } as T;

    const fields = Object.keys(entity);
    const placeholders = fields.map(() => '?').join(', ');
    const values = fields.map((f) => (entity as Record<string, unknown>)[f]);

    await db.runAsync(
      `INSERT INTO ${this.tableName} (${fields.join(', ')}) VALUES (${placeholders})`,
      values
    );

    return entity;
  }

  async update(id: string, data: Partial<T>): Promise<T | null> {
    const db = getDatabase();
    const now = new Date().toISOString();

    const updateData = {
      ...data,
      updated_at: now,
      local_modified_at: now,
    };

    delete (updateData as Partial<BaseEntity>).id;
    delete (updateData as Partial<BaseEntity>).created_at;

    const fields = Object.keys(updateData);
    const setClause = fields.map((f) => `${f} = ?`).join(', ');
    const values = [...fields.map((f) => (updateData as Record<string, unknown>)[f]), id];

    await db.runAsync(
      `UPDATE ${this.tableName} SET ${setClause} WHERE id = ?`,
      values
    );

    return this.getById(id);
  }

  async delete(id: string): Promise<void> {
    const db = getDatabase();
    const now = new Date().toISOString();

    await db.runAsync(
      `UPDATE ${this.tableName} SET is_deleted = 1, updated_at = ?, local_modified_at = ? WHERE id = ?`,
      [now, now, id]
    );
  }

  async hardDelete(id: string): Promise<void> {
    const db = getDatabase();
    await db.runAsync(`DELETE FROM ${this.tableName} WHERE id = ?`, [id]);
  }

  async getUnsynced(): Promise<T[]> {
    const db = getDatabase();
    const result = await db.getAllAsync<T>(
      `SELECT * FROM ${this.tableName} WHERE synced_at IS NULL OR local_modified_at > synced_at`
    );
    return result;
  }

  async markSynced(ids: string[]): Promise<void> {
    if (ids.length === 0) return;

    const db = getDatabase();
    const now = new Date().toISOString();
    const placeholders = ids.map(() => '?').join(', ');

    await db.runAsync(
      `UPDATE ${this.tableName} SET synced_at = ? WHERE id IN (${placeholders})`,
      [now, ...ids]
    );
  }

  async bulkInsert(items: Array<Omit<T, 'id'>>): Promise<void> {
    const db = getDatabase();
    const now = new Date().toISOString();

    for (const item of items) {
      const id = uuidv4();
      const entity = {
        ...item,
        id,
        created_at: now,
        updated_at: now,
        local_modified_at: now,
        is_deleted: 0,
      };

      const fields = Object.keys(entity);
      const placeholders = fields.map(() => '?').join(', ');
      const values = fields.map((f) => (entity as Record<string, unknown>)[f]);

      await db.runAsync(
        `INSERT OR REPLACE INTO ${this.tableName} (${fields.join(', ')}) VALUES (${placeholders})`,
        values
      );
    }
  }

  async count(): Promise<number> {
    const db = getDatabase();
    const result = await db.getFirstAsync<{ count: number }>(
      `SELECT COUNT(*) as count FROM ${this.tableName} WHERE is_deleted = 0`
    );
    return result?.count ?? 0;
  }
}

export const invoicesRepository = new Repository('invoices');
export const inventoryRepository = new Repository('inventory');
export const customersRepository = new Repository('customers');
export const expensesRepository = new Repository('expenses');
