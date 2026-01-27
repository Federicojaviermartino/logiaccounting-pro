/**
 * Sync Service
 * Offline-first data synchronization
 */

import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { store } from '@store/index';
import {
  setOnlineStatus,
  addPendingAction,
  removePendingAction,
  setLastSyncTime,
  setSyncing,
} from '@store/slices/syncSlice';
import storageService from '../storage/storageService';
import apiClient from '../api/client';

export interface PendingAction {
  id: string;
  type: string;
  endpoint: string;
  method: 'POST' | 'PUT' | 'DELETE';
  data?: any;
  timestamp: number;
  retries: number;
}

const PENDING_ACTIONS_KEY = 'pendingActions';
const MAX_RETRIES = 3;

class SyncService {
  private unsubscribeNetInfo: (() => void) | null = null;

  /**
   * Initialize sync service
   */
  async init(): Promise<void> {
    // Start network listener
    this.unsubscribeNetInfo = NetInfo.addEventListener(this.handleConnectivityChange);

    // Load pending actions
    const pendingActions = await storageService.getItem<PendingAction[]>(
      PENDING_ACTIONS_KEY
    );
    if (pendingActions) {
      pendingActions.forEach((action) => {
        store.dispatch(addPendingAction(action));
      });
    }

    // Check initial connectivity
    const state = await NetInfo.fetch();
    this.handleConnectivityChange(state);
  }

  /**
   * Cleanup
   */
  cleanup(): void {
    if (this.unsubscribeNetInfo) {
      this.unsubscribeNetInfo();
    }
  }

  /**
   * Handle connectivity changes
   */
  private handleConnectivityChange = async (state: NetInfoState): Promise<void> => {
    const isConnected = state.isConnected && state.isInternetReachable;
    store.dispatch(setOnlineStatus(!!isConnected));

    if (isConnected) {
      // Sync when coming online
      await this.syncPendingActions();
    }
  };

  /**
   * Queue action for offline sync
   */
  async queueAction(action: Omit<PendingAction, 'id' | 'timestamp' | 'retries'>): Promise<void> {
    const pendingAction: PendingAction = {
      ...action,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      retries: 0,
    };

    store.dispatch(addPendingAction(pendingAction));
    await this.savePendingActions();

    // Try to sync immediately if online
    const state = await NetInfo.fetch();
    if (state.isConnected && state.isInternetReachable) {
      await this.executePendingAction(pendingAction);
    }
  }

  /**
   * Sync all pending actions
   */
  async syncPendingActions(): Promise<void> {
    const state = store.getState();
    const { pendingActions, isSyncing } = state.sync;

    if (isSyncing || pendingActions.length === 0) {
      return;
    }

    store.dispatch(setSyncing(true));

    try {
      // Process actions in order
      for (const action of pendingActions) {
        await this.executePendingAction(action);
      }

      store.dispatch(setLastSyncTime(Date.now()));
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      store.dispatch(setSyncing(false));
    }
  }

  /**
   * Execute a single pending action
   */
  private async executePendingAction(action: PendingAction): Promise<boolean> {
    try {
      switch (action.method) {
        case 'POST':
          await apiClient.post(action.endpoint, action.data);
          break;
        case 'PUT':
          await apiClient.put(action.endpoint, action.data);
          break;
        case 'DELETE':
          await apiClient.delete(action.endpoint);
          break;
      }

      // Remove successful action
      store.dispatch(removePendingAction(action.id));
      await this.savePendingActions();
      return true;
    } catch (error: any) {
      console.error(`Failed to sync action ${action.id}:`, error);

      // Update retry count
      action.retries += 1;

      if (action.retries >= MAX_RETRIES) {
        // Remove after max retries
        store.dispatch(removePendingAction(action.id));
        await this.savePendingActions();
        // TODO: Notify user of failed sync
      }

      return false;
    }
  }

  /**
   * Save pending actions to storage
   */
  private async savePendingActions(): Promise<void> {
    const state = store.getState();
    await storageService.setItem(PENDING_ACTIONS_KEY, state.sync.pendingActions);
  }

  /**
   * Force full sync
   */
  async forceSync(): Promise<void> {
    const state = await NetInfo.fetch();

    if (!state.isConnected || !state.isInternetReachable) {
      throw new Error('No internet connection');
    }

    await this.syncPendingActions();

    // Refresh all data
    // This would dispatch fetch actions for all slices
    store.dispatch(setLastSyncTime(Date.now()));
  }

  /**
   * Clear all pending actions
   */
  async clearPendingActions(): Promise<void> {
    const state = store.getState();
    state.sync.pendingActions.forEach((action) => {
      store.dispatch(removePendingAction(action.id));
    });
    await storageService.removeItem(PENDING_ACTIONS_KEY);
  }

  /**
   * Check if online
   */
  async isOnline(): Promise<boolean> {
    const state = await NetInfo.fetch();
    return !!(state.isConnected && state.isInternetReachable);
  }
}

export const syncService = new SyncService();
export default syncService;
