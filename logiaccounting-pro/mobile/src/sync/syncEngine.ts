/**
 * Sync Engine - Bidirectional data synchronization
 */

import { getDatabase } from '@storage/database';
import { apiClient } from '@services/client';
import { conflictResolver, ConflictResolution } from './conflictResolver';
import NetInfo from '@react-native-community/netinfo';

export type SyncStatus = 'idle' | 'syncing' | 'error' | 'offline';
export type EntityType = 'invoices' | 'inventory' | 'customers' | 'expenses';

interface SyncQueueItem {
  id: string;
  entity_type: EntityType;
  entity_id: string;
  operation: 'create' | 'update' | 'delete';
  payload: string;
  priority: number;
  retry_count: number;
  last_error: string | null;
  created_at: string;
  processed_at: string | null;
}

interface SyncResult {
  success: boolean;
  synced: number;
  failed: number;
  conflicts: number;
  errors: string[];
}

interface ServerChange {
  id: string;
  entity_type: EntityType;
  data: Record<string, unknown>;
  updated_at: string;
  deleted: boolean;
}

class SyncEngine {
  private status: SyncStatus = 'idle';
  private lastSyncTime: string | null = null;
  private listeners: Set<(status: SyncStatus) => void> = new Set();

  getStatus(): SyncStatus {
    return this.status;
  }

  getLastSyncTime(): string | null {
    return this.lastSyncTime;
  }

  addStatusListener(listener: (status: SyncStatus) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private setStatus(status: SyncStatus): void {
    this.status = status;
    this.listeners.forEach((listener) => listener(status));
  }

  async sync(): Promise<SyncResult> {
    const networkState = await NetInfo.fetch();

    if (!networkState.isConnected) {
      this.setStatus('offline');
      return { success: false, synced: 0, failed: 0, conflicts: 0, errors: ['No network connection'] };
    }

    this.setStatus('syncing');

    const result: SyncResult = {
      success: true,
      synced: 0,
      failed: 0,
      conflicts: 0,
      errors: [],
    };

    try {
      await this.pushLocalChanges(result);
      await this.pullServerChanges(result);

      this.lastSyncTime = new Date().toISOString();
      this.setStatus('idle');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Sync failed';
      result.success = false;
      result.errors.push(message);
      this.setStatus('error');
    }

    return result;
  }

  private async pushLocalChanges(result: SyncResult): Promise<void> {
    const db = getDatabase();
    const queue = await db.getAllAsync<SyncQueueItem>(
      'SELECT * FROM sync_queue WHERE processed_at IS NULL ORDER BY priority DESC, created_at ASC'
    );

    for (const item of queue) {
      try {
        const payload = JSON.parse(item.payload);

        switch (item.operation) {
          case 'create':
            await apiClient.post(`/${item.entity_type}`, payload);
            break;
          case 'update':
            await apiClient.patch(`/${item.entity_type}/${item.entity_id}`, payload);
            break;
          case 'delete':
            await apiClient.delete(`/${item.entity_type}/${item.entity_id}`);
            break;
        }

        await db.runAsync(
          'UPDATE sync_queue SET processed_at = ? WHERE id = ?',
          [new Date().toISOString(), item.id]
        );

        await db.runAsync(
          `UPDATE ${item.entity_type} SET synced_at = ? WHERE id = ?`,
          [new Date().toISOString(), item.entity_id]
        );

        result.synced++;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';

        if (this.isConflictError(error)) {
          result.conflicts++;
          await this.handleConflict(item, error);
        } else {
          result.failed++;
          result.errors.push(`Failed to sync ${item.entity_type}/${item.entity_id}: ${errorMessage}`);

          await db.runAsync(
            'UPDATE sync_queue SET retry_count = retry_count + 1, last_error = ? WHERE id = ?',
            [errorMessage, item.id]
          );
        }
      }
    }
  }

  private async pullServerChanges(result: SyncResult): Promise<void> {
    const db = getDatabase();
    const entityTypes: EntityType[] = ['invoices', 'inventory', 'customers', 'expenses'];

    for (const entityType of entityTypes) {
      try {
        const lastSync = this.lastSyncTime || '1970-01-01T00:00:00.000Z';
        const response = await apiClient.get<{ changes: ServerChange[] }>(
          `/sync/${entityType}`,
          { params: { since: lastSync } }
        );

        for (const change of response.data.changes) {
          if (change.deleted) {
            await db.runAsync(
              `UPDATE ${entityType} SET is_deleted = 1, synced_at = ? WHERE id = ?`,
              [new Date().toISOString(), change.id]
            );
          } else {
            const localItem = await db.getFirstAsync<{ local_modified_at: string; synced_at: string }>(
              `SELECT local_modified_at, synced_at FROM ${entityType} WHERE id = ?`,
              [change.id]
            );

            if (localItem && localItem.local_modified_at > (localItem.synced_at || '')) {
              const resolution = await conflictResolver.resolve(
                entityType,
                change.id,
                localItem,
                change.data
              );

              if (resolution === ConflictResolution.UseServer) {
                await this.upsertEntity(entityType, change.data);
              }
              result.conflicts++;
            } else {
              await this.upsertEntity(entityType, change.data);
            }
          }
          result.synced++;
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown error';
        result.errors.push(`Failed to pull ${entityType}: ${message}`);
      }
    }
  }

  private async upsertEntity(entityType: EntityType, data: Record<string, unknown>): Promise<void> {
    const db = getDatabase();
    const fields = Object.keys(data);
    const placeholders = fields.map(() => '?').join(', ');
    const values = fields.map((f) => data[f]);

    const updateClause = fields.map((f) => `${f} = excluded.${f}`).join(', ');

    await db.runAsync(
      `INSERT INTO ${entityType} (${fields.join(', ')}) VALUES (${placeholders})
       ON CONFLICT(id) DO UPDATE SET ${updateClause}, synced_at = ?`,
      [...values, new Date().toISOString()]
    );
  }

  private isConflictError(error: unknown): boolean {
    if (error && typeof error === 'object' && 'response' in error) {
      const response = (error as { response?: { status?: number } }).response;
      return response?.status === 409;
    }
    return false;
  }

  private async handleConflict(item: SyncQueueItem, error: unknown): Promise<void> {
    console.log('Handling conflict for:', item.entity_type, item.entity_id);
  }

  async addToQueue(
    entityType: EntityType,
    entityId: string,
    operation: 'create' | 'update' | 'delete',
    payload: Record<string, unknown>,
    priority: number = 0
  ): Promise<void> {
    const db = getDatabase();
    const id = `${entityType}-${entityId}-${Date.now()}`;

    await db.runAsync(
      `INSERT INTO sync_queue (id, entity_type, entity_id, operation, payload, priority, retry_count, created_at)
       VALUES (?, ?, ?, ?, ?, ?, 0, ?)`,
      [id, entityType, entityId, operation, JSON.stringify(payload), priority, new Date().toISOString()]
    );
  }

  async clearQueue(): Promise<void> {
    const db = getDatabase();
    await db.runAsync('DELETE FROM sync_queue WHERE processed_at IS NOT NULL');
  }

  async getQueueCount(): Promise<number> {
    const db = getDatabase();
    const result = await db.getFirstAsync<{ count: number }>(
      'SELECT COUNT(*) as count FROM sync_queue WHERE processed_at IS NULL'
    );
    return result?.count ?? 0;
  }
}

export const syncEngine = new SyncEngine();
