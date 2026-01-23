/**
 * Service Worker Template
 * Custom service worker with Workbox integration
 */

import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import {
  NetworkFirst,
  CacheFirst,
  StaleWhileRevalidate
} from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';
import { BackgroundSyncPlugin } from 'workbox-background-sync';

// Precache static assets
precacheAndRoute(self.__WB_MANIFEST);

// Clean up old caches
cleanupOutdatedCaches();

// App Shell - Cache First with Network Fallback
const shellStrategy = new CacheFirst({
  cacheName: 'app-shell',
  plugins: [
    new CacheableResponsePlugin({ statuses: [0, 200] }),
    new ExpirationPlugin({ maxEntries: 50 }),
  ],
});

// Navigation requests - Network First
const navigationHandler = new NetworkFirst({
  cacheName: 'pages-cache',
  networkTimeoutSeconds: 3,
  plugins: [
    new CacheableResponsePlugin({ statuses: [0, 200] }),
  ],
});

// Handle navigation requests
registerRoute(
  new NavigationRoute(navigationHandler, {
    denylist: [/^\/_/, /\/api\//],
  })
);

// Background sync for offline mutations
const bgSyncPlugin = new BackgroundSyncPlugin('mutation-queue', {
  maxRetentionTime: 24 * 60, // 24 hours in minutes
  onSync: async ({ queue }) => {
    let entry;
    while ((entry = await queue.shiftRequest())) {
      try {
        await fetch(entry.request.clone());
        console.log('Background sync successful:', entry.request.url);
      } catch (error) {
        console.error('Background sync failed:', error);
        await queue.unshiftRequest(entry);
        throw error;
      }
    }
  },
});

// API mutations - Network Only with Background Sync
registerRoute(
  ({ url, request }) =>
    url.pathname.startsWith('/api/v1/') &&
    ['POST', 'PUT', 'PATCH', 'DELETE'].includes(request.method),
  new NetworkFirst({
    cacheName: 'api-mutations',
    plugins: [bgSyncPlugin],
  }),
  'POST'
);

// Handle push notifications
self.addEventListener('push', (event) => {
  const data = event.data?.json() || {};

  const options = {
    body: data.body || 'New notification',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      url: data.url || '/',
      ...data,
    },
    actions: data.actions || [],
  };

  event.waitUntil(
    self.registration.showNotification(
      data.title || 'LogiAccounting Pro',
      options
    )
  );
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const url = event.notification.data?.url || '/';

  // Handle action buttons
  if (event.action === 'approve') {
    event.waitUntil(
      fetch('/api/v1/approvals/quick-action', {
        method: 'POST',
        body: JSON.stringify({
          action: 'approve',
          id: event.notification.data.id
        }),
      })
    );
    return;
  }

  if (event.action === 'reject') {
    event.waitUntil(
      fetch('/api/v1/approvals/quick-action', {
        method: 'POST',
        body: JSON.stringify({
          action: 'reject',
          id: event.notification.data.id
        }),
      })
    );
    return;
  }

  // Default: open the app
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      // Focus existing window if available
      for (const client of clientList) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      // Open new window
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});

// Handle app updates
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Sync event for background sync
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

async function syncData() {
  // Custom sync logic
  const db = await openDB();
  const pendingItems = await db.getAll('sync-queue');

  for (const item of pendingItems) {
    try {
      await fetch(item.url, {
        method: item.method,
        headers: item.headers,
        body: item.body,
      });
      await db.delete('sync-queue', item.id);
    } catch (error) {
      console.error('Sync failed for item:', item.id);
    }
  }
}

console.log('Service Worker loaded');
