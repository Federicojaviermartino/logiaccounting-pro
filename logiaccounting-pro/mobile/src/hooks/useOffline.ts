/**
 * useOffline Hook
 * Offline status and sync utilities
 */

import { useCallback, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '@store/index';
import { syncService, PendingAction } from '@services/index';
import { setOnlineStatus, clearPendingActions } from '@store/slices/syncSlice';

export const useOffline = () => {
  const dispatch = useDispatch<AppDispatch>();
  const syncState = useSelector((state: RootState) => state.sync);

  useEffect(() => {
    // Initialize sync service
    syncService.init();

    return () => {
      syncService.cleanup();
    };
  }, []);

  const queueAction = useCallback(
    async (action: Omit<PendingAction, 'id' | 'timestamp' | 'retries'>) => {
      await syncService.queueAction(action);
    },
    []
  );

  const sync = useCallback(async () => {
    try {
      await syncService.forceSync();
      return true;
    } catch (error) {
      console.error('Sync failed:', error);
      return false;
    }
  }, []);

  const clearQueue = useCallback(async () => {
    await syncService.clearPendingActions();
    dispatch(clearPendingActions());
  }, [dispatch]);

  const checkConnection = useCallback(async () => {
    const isOnline = await syncService.isOnline();
    dispatch(setOnlineStatus(isOnline));
    return isOnline;
  }, [dispatch]);

  return {
    // State
    isOnline: syncState.isOnline,
    isSyncing: syncState.isSyncing,
    pendingCount: syncState.pendingActions.length,
    pendingActions: syncState.pendingActions,
    lastSyncTime: syncState.lastSyncTime,

    // Actions
    queueAction,
    sync,
    clearQueue,
    checkConnection,
  };
};

export default useOffline;
