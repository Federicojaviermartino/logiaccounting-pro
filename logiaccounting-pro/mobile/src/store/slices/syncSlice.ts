/**
 * Sync State Slice
 * Manages offline queue and synchronization status
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface QueuedAction {
  id: string;
  type: string;
  payload: any;
  timestamp: number;
  retries: number;
  status: 'pending' | 'processing' | 'failed';
}

interface SyncState {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncTime: number | null;
  syncError: string | null;
  queue: QueuedAction[];
  pendingCount: number;
  conflictsCount: number;
}

const initialState: SyncState = {
  isOnline: true,
  isSyncing: false,
  lastSyncTime: null,
  syncError: null,
  queue: [],
  pendingCount: 0,
  conflictsCount: 0,
};

const syncSlice = createSlice({
  name: 'sync',
  initialState,
  reducers: {
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.isOnline = action.payload;
    },
    startSync: (state) => {
      state.isSyncing = true;
      state.syncError = null;
    },
    syncComplete: (state) => {
      state.isSyncing = false;
      state.lastSyncTime = Date.now();
      state.queue = state.queue.filter((item) => item.status === 'pending');
      state.pendingCount = state.queue.length;
    },
    syncFailed: (state, action: PayloadAction<string>) => {
      state.isSyncing = false;
      state.syncError = action.payload;
    },
    addToQueue: (
      state,
      action: PayloadAction<Omit<QueuedAction, 'id' | 'timestamp' | 'retries' | 'status'>>
    ) => {
      const newAction: QueuedAction = {
        ...action.payload,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
        retries: 0,
        status: 'pending',
      };
      state.queue.push(newAction);
      state.pendingCount = state.queue.filter((i) => i.status === 'pending').length;
    },
    updateQueueItem: (
      state,
      action: PayloadAction<{ id: string; updates: Partial<QueuedAction> }>
    ) => {
      const index = state.queue.findIndex((item) => item.id === action.payload.id);
      if (index !== -1) {
        state.queue[index] = { ...state.queue[index], ...action.payload.updates };
      }
      state.pendingCount = state.queue.filter((i) => i.status === 'pending').length;
    },
    removeFromQueue: (state, action: PayloadAction<string>) => {
      state.queue = state.queue.filter((item) => item.id !== action.payload);
      state.pendingCount = state.queue.filter((i) => i.status === 'pending').length;
    },
    clearQueue: (state) => {
      state.queue = [];
      state.pendingCount = 0;
    },
    setConflictsCount: (state, action: PayloadAction<number>) => {
      state.conflictsCount = action.payload;
    },
  },
});

export const {
  setOnlineStatus,
  startSync,
  syncComplete,
  syncFailed,
  addToQueue,
  updateQueueItem,
  removeFromQueue,
  clearQueue,
  setConflictsCount,
} = syncSlice.actions;

export default syncSlice.reducer;
