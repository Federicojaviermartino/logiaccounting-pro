/**
 * Mobile API Service
 * Handles all mobile-specific API calls
 */

import axios from 'axios';
import { offlineStorage } from '../pwa/offlineStorage';
import { getPortalToken, clearPortalToken } from '../utils/tokenService';

const API_BASE = '/api/mobile/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = getPortalToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors and offline fallback
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!navigator.onLine && error.config.method === 'get') {
      const cachedData = await offlineStorage.getCachedData(error.config.url);
      if (cachedData) {
        return { data: cachedData, cached: true };
      }
    }

    if (error.response?.status === 401) {
      clearPortalToken();
      window.location.href = '/portal/login';
    }

    return Promise.reject(error);
  }
);

// Cache successful GET responses
api.interceptors.response.use(
  async (response) => {
    if (response.config.method === 'get' && response.data) {
      await offlineStorage.cacheData(response.config.url, 'api', response.data, 30);
    }
    return response;
  }
);

export const mobileAPI = {
  // Home
  getHome: () => api.get('/home'),
  getQuickStats: () => api.get('/quick-stats'),
  getActivity: (limit = 10) => api.get('/activity', { params: { limit } }),
  getQuickActions: () => api.get('/quick-actions'),
  getOfflineData: () => api.get('/offline-data'),
  getAlerts: () => api.get('/alerts'),

  // Notifications
  getVapidKey: () => api.get('/notifications/vapid-key'),
  getNotifications: (params) => api.get('/notifications', { params }),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markRead: (notificationId) => api.post(`/notifications/${notificationId}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
  getSubscriptions: () => api.get('/notifications/subscriptions'),
  subscribePush: (data) => api.post('/notifications/subscribe', data),
  unsubscribePush: (subscriptionId) => api.delete(`/notifications/subscriptions/${subscriptionId}`),
  updateNotificationPreferences: (subscriptionId, preferences) =>
    api.put(`/notifications/subscriptions/${subscriptionId}/preferences`, preferences),

  // Devices
  getDevices: () => api.get('/devices'),
  registerDevice: (data) => api.post('/devices', data),
  updateDevice: (deviceId, data) => api.put(`/devices/${deviceId}`, data),
  unregisterDevice: (deviceId) => api.delete(`/devices/${deviceId}`),
  pingDevice: (deviceId) => api.post(`/devices/${deviceId}/ping`),

  // Sync
  sync: async (data) => {
    const pendingActions = await offlineStorage.getPendingActions();

    const response = await api.post('/sync', {
      last_sync: data?.last_sync,
      pending_actions: pendingActions,
    });

    if (response.data.processed) {
      for (const result of response.data.processed) {
        if (result.status === 'success') {
          await offlineStorage.markActionSynced(result.offline_id, result.server_id);
        }
      }
    }

    await offlineStorage.setSyncState('last_sync', response.data.server_time);
    await offlineStorage.clearSyncedActions();

    return response;
  },
  getSyncStatus: () => api.get('/sync/status'),
  fullSync: () => api.post('/sync/full'),

  // Offline Actions
  queueOfflineAction: async (type, data) => {
    const action = await offlineStorage.queueAction(type, data);

    if (navigator.onLine) {
      try {
        await mobileAPI.sync();
      } catch (error) {
        console.log('[Mobile API] Will sync later');
      }
    } else {
      if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register('sync-offline-actions');
      }
    }

    return action;
  },

  getPendingActionsCount: async () => {
    const actions = await offlineStorage.getPendingActions();
    return actions.length;
  },
};

export default mobileAPI;
