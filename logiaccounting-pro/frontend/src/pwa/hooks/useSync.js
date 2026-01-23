/**
 * useSync - Hook for sync queue management
 */

import { useState, useEffect, useCallback } from 'react';
import { syncQueue, SYNC_PRIORITIES } from '../sync/syncQueue';

export function useSync() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isSyncing, setIsSyncing] = useState(false);
  const [pendingCount, setPendingCount] = useState(0);
  const [lastSyncResult, setLastSyncResult] = useState(null);

  useEffect(() => {
    // Network status
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Sync queue listener
    const unsubscribe = syncQueue.addListener((event) => {
      switch (event.type) {
        case 'sync-started':
          setIsSyncing(true);
          break;
        case 'sync-completed':
          setIsSyncing(false);
          setLastSyncResult(event.results);
          updatePendingCount();
          break;
        case 'enqueued':
        case 'item-synced':
        case 'item-failed':
        case 'queue-cleared':
          updatePendingCount();
          break;
      }
    });

    // Initial count
    updatePendingCount();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      unsubscribe();
    };
  }, []);

  const updatePendingCount = async () => {
    const count = await syncQueue.getCount();
    setPendingCount(count);
  };

  const enqueue = useCallback(async (item) => {
    return syncQueue.enqueue(item);
  }, []);

  const syncNow = useCallback(async () => {
    if (!isOnline) {
      console.log('Cannot sync while offline');
      return null;
    }
    return syncQueue.processQueue();
  }, [isOnline]);

  const clearQueue = useCallback(async () => {
    return syncQueue.clear();
  }, []);

  const getPending = useCallback(async () => {
    return syncQueue.getPending();
  }, []);

  return {
    isOnline,
    isSyncing,
    pendingCount,
    lastSyncResult,
    enqueue,
    syncNow,
    clearQueue,
    getPending,
    SYNC_PRIORITIES,
  };
}

export default useSync;
