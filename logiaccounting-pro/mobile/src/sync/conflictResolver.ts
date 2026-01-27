/**
 * Conflict Resolver - Handle data sync conflicts
 */

export enum ConflictResolution {
  UseLocal = 'use_local',
  UseServer = 'use_server',
  Merge = 'merge',
  Manual = 'manual',
}

export interface ConflictInfo {
  entityType: string;
  entityId: string;
  localData: Record<string, unknown>;
  serverData: Record<string, unknown>;
  localModifiedAt: string;
  serverModifiedAt: string;
}

export type ConflictStrategy = 'last_write_wins' | 'local_priority' | 'server_priority' | 'manual';

interface ResolverConfig {
  defaultStrategy: ConflictStrategy;
  entityStrategies: Record<string, ConflictStrategy>;
  fieldMergeRules: Record<string, Record<string, 'local' | 'server' | 'newer'>>;
}

class ConflictResolver {
  private config: ResolverConfig = {
    defaultStrategy: 'last_write_wins',
    entityStrategies: {
      invoices: 'server_priority',
      inventory: 'last_write_wins',
      customers: 'last_write_wins',
      expenses: 'local_priority',
    },
    fieldMergeRules: {
      invoices: {
        status: 'server',
        notes: 'local',
        total: 'server',
      },
      inventory: {
        quantity: 'server',
        name: 'local',
        description: 'local',
      },
    },
  };

  private pendingConflicts: Map<string, ConflictInfo> = new Map();
  private listeners: Set<(conflicts: ConflictInfo[]) => void> = new Set();

  setConfig(config: Partial<ResolverConfig>): void {
    this.config = { ...this.config, ...config };
  }

  addConflictListener(listener: (conflicts: ConflictInfo[]) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners(): void {
    const conflicts = Array.from(this.pendingConflicts.values());
    this.listeners.forEach((listener) => listener(conflicts));
  }

  async resolve(
    entityType: string,
    entityId: string,
    localData: Record<string, unknown>,
    serverData: Record<string, unknown>
  ): Promise<ConflictResolution> {
    const strategy = this.config.entityStrategies[entityType] || this.config.defaultStrategy;

    switch (strategy) {
      case 'local_priority':
        return ConflictResolution.UseLocal;

      case 'server_priority':
        return ConflictResolution.UseServer;

      case 'last_write_wins':
        return this.resolveByTimestamp(localData, serverData);

      case 'manual':
        this.addPendingConflict(entityType, entityId, localData, serverData);
        return ConflictResolution.Manual;

      default:
        return ConflictResolution.UseServer;
    }
  }

  private resolveByTimestamp(
    localData: Record<string, unknown>,
    serverData: Record<string, unknown>
  ): ConflictResolution {
    const localTime = new Date(localData.local_modified_at as string || 0).getTime();
    const serverTime = new Date(serverData.updated_at as string || 0).getTime();

    return localTime > serverTime ? ConflictResolution.UseLocal : ConflictResolution.UseServer;
  }

  merge(
    entityType: string,
    localData: Record<string, unknown>,
    serverData: Record<string, unknown>
  ): Record<string, unknown> {
    const mergeRules = this.config.fieldMergeRules[entityType] || {};
    const merged: Record<string, unknown> = { ...serverData };

    for (const [field, rule] of Object.entries(mergeRules)) {
      switch (rule) {
        case 'local':
          if (field in localData) {
            merged[field] = localData[field];
          }
          break;

        case 'server':
          break;

        case 'newer':
          const localTime = new Date(localData.local_modified_at as string || 0).getTime();
          const serverTime = new Date(serverData.updated_at as string || 0).getTime();
          if (localTime > serverTime && field in localData) {
            merged[field] = localData[field];
          }
          break;
      }
    }

    merged.updated_at = new Date().toISOString();
    merged.synced_at = new Date().toISOString();

    return merged;
  }

  private addPendingConflict(
    entityType: string,
    entityId: string,
    localData: Record<string, unknown>,
    serverData: Record<string, unknown>
  ): void {
    const key = `${entityType}:${entityId}`;
    const conflict: ConflictInfo = {
      entityType,
      entityId,
      localData,
      serverData,
      localModifiedAt: localData.local_modified_at as string,
      serverModifiedAt: serverData.updated_at as string,
    };

    this.pendingConflicts.set(key, conflict);
    this.notifyListeners();
  }

  getPendingConflicts(): ConflictInfo[] {
    return Array.from(this.pendingConflicts.values());
  }

  async resolveManually(
    entityType: string,
    entityId: string,
    resolution: ConflictResolution,
    mergedData?: Record<string, unknown>
  ): Promise<void> {
    const key = `${entityType}:${entityId}`;
    this.pendingConflicts.delete(key);
    this.notifyListeners();
  }

  clearPendingConflicts(): void {
    this.pendingConflicts.clear();
    this.notifyListeners();
  }

  hasPendingConflicts(): boolean {
    return this.pendingConflicts.size > 0;
  }

  getConflictCount(): number {
    return this.pendingConflicts.size;
  }
}

export const conflictResolver = new ConflictResolver();
