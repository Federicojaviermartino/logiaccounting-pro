# Phase 28: Mobile API & PWA - Part 3: PWA Core

## Overview
This part covers the Progressive Web App core files including manifest, service worker, offline page, and PWA utilities.

---

## File 1: Web App Manifest
**Path:** `frontend/public/manifest.json`

```json
{
  "name": "LogiAccounting Pro",
  "short_name": "LogiAcct",
  "description": "Professional logistics and accounting management platform",
  "start_url": "/portal",
  "display": "standalone",
  "orientation": "portrait-primary",
  "theme_color": "#3b82f6",
  "background_color": "#ffffff",
  "scope": "/",
  "lang": "en",
  "categories": ["business", "finance", "productivity"],
  "icons": [
    {
      "src": "/icons/icon-72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable any"
    }
  ],
  "screenshots": [
    {
      "src": "/screenshots/dashboard-mobile.png",
      "sizes": "390x844",
      "type": "image/png",
      "form_factor": "narrow",
      "label": "Dashboard on mobile"
    },
    {
      "src": "/screenshots/dashboard-desktop.png",
      "sizes": "1920x1080",
      "type": "image/png",
      "form_factor": "wide",
      "label": "Dashboard on desktop"
    }
  ],
  "shortcuts": [
    {
      "name": "Dashboard",
      "short_name": "Dashboard",
      "description": "View your dashboard",
      "url": "/portal",
      "icons": [{ "src": "/icons/shortcut-dashboard.png", "sizes": "192x192" }]
    },
    {
      "name": "Pay Invoice",
      "short_name": "Pay",
      "description": "Pay pending invoices",
      "url": "/portal/payments",
      "icons": [{ "src": "/icons/shortcut-pay.png", "sizes": "192x192" }]
    },
    {
      "name": "New Ticket",
      "short_name": "Support",
      "description": "Create a support ticket",
      "url": "/portal/support/new",
      "icons": [{ "src": "/icons/shortcut-ticket.png", "sizes": "192x192" }]
    },
    {
      "name": "Projects",
      "short_name": "Projects",
      "description": "View your projects",
      "url": "/portal/projects",
      "icons": [{ "src": "/icons/shortcut-projects.png", "sizes": "192x192" }]
    }
  ],
  "related_applications": [],
  "prefer_related_applications": false
}
```

---

## File 2: Service Worker
**Path:** `frontend/public/sw.js`

```javascript
/**
 * Service Worker for LogiAccounting Pro PWA
 * Handles caching, offline support, and push notifications
 */

const CACHE_NAME = 'logiaccounting-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';
const OFFLINE_URL = '/offline.html';

// Static assets to cache immediately
const STATIC_ASSETS = [
  '/',
  '/portal',
  '/portal/login',
  '/offline.html',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

// API routes to cache with network-first strategy
const API_CACHE_ROUTES = [
  '/api/mobile/v1/home',
  '/api/mobile/v1/quick-stats',
  '/api/mobile/v1/offline-data',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== STATIC_CACHE && name !== DYNAMIC_CACHE)
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Skip chrome-extension and other non-http requests
  if (!url.protocol.startsWith('http')) {
    return;
  }
  
  // API requests - Network First with cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }
  
  // Static assets - Cache First
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }
  
  // HTML pages - Network First with offline fallback
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirstWithOffline(request));
    return;
  }
  
  // Default - Stale While Revalidate
  event.respondWith(staleWhileRevalidate(request));
});

// Cache First strategy
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('[SW] Cache first failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

// Network First strategy
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('[SW] Network first falling back to cache');
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return new Response(JSON.stringify({ error: 'Offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

// Network First with offline page fallback
async function networkFirstWithOffline(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('[SW] Network failed, showing offline page');
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return caches.match(OFFLINE_URL);
  }
}

// Stale While Revalidate strategy
async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cached = await cache.match(request);
  
  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cached);
  
  return cached || fetchPromise;
}

// Check if URL is a static asset
function isStaticAsset(pathname) {
  return /\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/.test(pathname);
}

// Push notification event
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  let data = {
    title: 'LogiAccounting Pro',
    body: 'You have a new notification',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.png',
    data: {},
  };
  
  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      data.body = event.data.text();
    }
  }
  
  const options = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    tag: data.tag || 'default',
    data: data.data,
    actions: data.actions || [],
    requireInteraction: data.requireInteraction || false,
    vibrate: [100, 50, 100],
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event.notification.tag);
  
  event.notification.close();
  
  const action = event.action;
  const data = event.notification.data || {};
  let url = data.url || '/portal';
  
  // Handle action buttons
  if (action === 'pay') {
    url = '/portal/payments';
  } else if (action === 'view') {
    url = data.url || '/portal';
  } else if (action === 'reply') {
    url = data.url || '/portal/support';
  }
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if there's already a window open
        for (const client of clientList) {
          if (client.url.includes('/portal') && 'focus' in client) {
            client.navigate(url);
            return client.focus();
          }
        }
        // Open new window if none exists
        if (clients.openWindow) {
          return clients.openWindow(url);
        }
      })
  );
});

// Background sync event
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'sync-offline-actions') {
    event.waitUntil(syncOfflineActions());
  }
});

// Sync offline actions
async function syncOfflineActions() {
  try {
    // Get pending actions from IndexedDB
    const db = await openDB();
    const tx = db.transaction('offline-actions', 'readonly');
    const store = tx.objectStore('offline-actions');
    const actions = await store.getAll();
    
    if (actions.length === 0) {
      return;
    }
    
    // Send to server
    const response = await fetch('/api/mobile/v1/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await getAuthToken()}`,
      },
      body: JSON.stringify({
        pending_actions: actions,
      }),
    });
    
    if (response.ok) {
      // Clear synced actions
      const clearTx = db.transaction('offline-actions', 'readwrite');
      const clearStore = clearTx.objectStore('offline-actions');
      await clearStore.clear();
      
      console.log('[SW] Offline actions synced successfully');
    }
  } catch (error) {
    console.error('[SW] Failed to sync offline actions:', error);
  }
}

// Helper to open IndexedDB
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('logiaccounting-offline', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('offline-actions')) {
        db.createObjectStore('offline-actions', { keyPath: 'id' });
      }
    };
  });
}

// Helper to get auth token
async function getAuthToken() {
  const clients = await self.clients.matchAll();
  for (const client of clients) {
    // Request token from client
    // In production, implement proper token storage
  }
  return null;
}

// Message event - communicate with main app
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);
  
  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data.type === 'CACHE_URLS') {
    caches.open(DYNAMIC_CACHE)
      .then((cache) => cache.addAll(event.data.urls));
  }
});
```

---

## File 3: Offline HTML Page
**Path:** `frontend/public/offline.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#3b82f6">
  <title>Offline - LogiAccounting Pro</title>
  <link rel="manifest" href="/manifest.json">
  <link rel="icon" type="image/png" href="/icons/icon-192.png">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    
    .offline-container {
      background: white;
      border-radius: 20px;
      padding: 40px;
      max-width: 400px;
      width: 100%;
      text-align: center;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }
    
    .offline-icon {
      width: 80px;
      height: 80px;
      margin: 0 auto 24px;
      background: #f3f4f6;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .offline-icon svg {
      width: 40px;
      height: 40px;
      color: #6b7280;
    }
    
    h1 {
      font-size: 24px;
      font-weight: 700;
      color: #111827;
      margin-bottom: 12px;
    }
    
    p {
      font-size: 16px;
      color: #6b7280;
      line-height: 1.6;
      margin-bottom: 24px;
    }
    
    .retry-btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 12px 24px;
      background: #3b82f6;
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 16px;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.2s;
    }
    
    .retry-btn:hover {
      background: #2563eb;
    }
    
    .retry-btn:active {
      transform: scale(0.98);
    }
    
    .status {
      margin-top: 24px;
      padding: 12px;
      background: #fef3c7;
      border-radius: 8px;
      font-size: 14px;
      color: #92400e;
    }
    
    .status.online {
      background: #d1fae5;
      color: #065f46;
    }
    
    .cached-pages {
      margin-top: 24px;
      text-align: left;
    }
    
    .cached-pages h3 {
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 12px;
    }
    
    .cached-pages ul {
      list-style: none;
    }
    
    .cached-pages li {
      margin-bottom: 8px;
    }
    
    .cached-pages a {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      background: #f9fafb;
      border-radius: 8px;
      color: #374151;
      text-decoration: none;
      font-size: 14px;
      transition: background 0.2s;
    }
    
    .cached-pages a:hover {
      background: #f3f4f6;
    }
    
    @media (max-width: 480px) {
      .offline-container {
        padding: 32px 24px;
      }
      
      h1 {
        font-size: 20px;
      }
      
      p {
        font-size: 14px;
      }
    }
  </style>
</head>
<body>
  <div class="offline-container">
    <div class="offline-icon">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
      </svg>
    </div>
    
    <h1>You're Offline</h1>
    <p>It looks like you've lost your internet connection. Don't worry, some features are still available offline.</p>
    
    <button class="retry-btn" onclick="checkConnection()">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      Try Again
    </button>
    
    <div id="status" class="status" style="display: none;"></div>
    
    <div class="cached-pages">
      <h3>Available Offline:</h3>
      <ul>
        <li>
          <a href="/portal">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Dashboard (Cached)
          </a>
        </li>
        <li>
          <a href="/portal/support">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
            </svg>
            Support Tickets
          </a>
        </li>
        <li>
          <a href="/portal/projects">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            Projects
          </a>
        </li>
      </ul>
    </div>
  </div>
  
  <script>
    function checkConnection() {
      const status = document.getElementById('status');
      status.style.display = 'block';
      status.className = 'status';
      status.textContent = 'Checking connection...';
      
      fetch('/api/health', { method: 'HEAD' })
        .then(() => {
          status.className = 'status online';
          status.textContent = 'Connection restored! Redirecting...';
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        })
        .catch(() => {
          status.className = 'status';
          status.textContent = 'Still offline. Please check your internet connection.';
        });
    }
    
    // Auto-check connection periodically
    setInterval(() => {
      if (navigator.onLine) {
        checkConnection();
      }
    }, 5000);
    
    // Listen for online event
    window.addEventListener('online', () => {
      checkConnection();
    });
  </script>
</body>
</html>
```

---

## File 4: Service Worker Registration
**Path:** `frontend/src/pwa/serviceWorker.js`

```javascript
/**
 * Service Worker Registration and Management
 */

const SW_URL = '/sw.js';

class ServiceWorkerManager {
  constructor() {
    this.registration = null;
    this.updateAvailable = false;
    this.onUpdateAvailable = null;
  }

  /**
   * Register the service worker
   */
  async register() {
    if (!('serviceWorker' in navigator)) {
      console.log('[PWA] Service workers not supported');
      return null;
    }

    try {
      this.registration = await navigator.serviceWorker.register(SW_URL, {
        scope: '/',
      });

      console.log('[PWA] Service worker registered:', this.registration.scope);

      // Check for updates
      this.registration.addEventListener('updatefound', () => {
        this.handleUpdateFound();
      });

      // Handle controller change (new SW activated)
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('[PWA] New service worker activated');
      });

      // Check for updates periodically
      setInterval(() => {
        this.checkForUpdates();
      }, 60 * 60 * 1000); // Every hour

      return this.registration;
    } catch (error) {
      console.error('[PWA] Service worker registration failed:', error);
      return null;
    }
  }

  /**
   * Handle when a new service worker is found
   */
  handleUpdateFound() {
    const newWorker = this.registration.installing;

    newWorker.addEventListener('statechange', () => {
      if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
        // New update available
        this.updateAvailable = true;
        console.log('[PWA] New version available');

        if (this.onUpdateAvailable) {
          this.onUpdateAvailable();
        }
      }
    });
  }

  /**
   * Check for service worker updates
   */
  async checkForUpdates() {
    if (this.registration) {
      try {
        await this.registration.update();
        console.log('[PWA] Checked for updates');
      } catch (error) {
        console.error('[PWA] Update check failed:', error);
      }
    }
  }

  /**
   * Apply pending update (reload with new SW)
   */
  applyUpdate() {
    if (this.registration && this.registration.waiting) {
      // Tell waiting SW to skip waiting
      this.registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      
      // Reload page to use new SW
      window.location.reload();
    }
  }

  /**
   * Unregister service worker
   */
  async unregister() {
    if (this.registration) {
      const success = await this.registration.unregister();
      console.log('[PWA] Service worker unregistered:', success);
      return success;
    }
    return false;
  }

  /**
   * Clear all caches
   */
  async clearCaches() {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map((name) => caches.delete(name)));
    console.log('[PWA] All caches cleared');
  }

  /**
   * Pre-cache specific URLs
   */
  async cacheUrls(urls) {
    if (this.registration && this.registration.active) {
      this.registration.active.postMessage({
        type: 'CACHE_URLS',
        urls,
      });
    }
  }

  /**
   * Get cache storage estimate
   */
  async getStorageEstimate() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return {
        usage: estimate.usage,
        quota: estimate.quota,
        usagePercent: ((estimate.usage / estimate.quota) * 100).toFixed(2),
      };
    }
    return null;
  }
}

// Export singleton instance
export const swManager = new ServiceWorkerManager();

// Auto-register on import
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    swManager.register();
  });
}

export default swManager;
```

---

## File 5: Push Notification Manager
**Path:** `frontend/src/pwa/pushManager.js`

```javascript
/**
 * Push Notification Manager
 * Handles push subscription and notification display
 */

import { mobileAPI } from '../services/mobileAPI';

class PushManager {
  constructor() {
    this.subscription = null;
    this.vapidPublicKey = null;
    this.permission = 'default';
  }

  /**
   * Check if push notifications are supported
   */
  isSupported() {
    return 'PushManager' in window && 'serviceWorker' in navigator;
  }

  /**
   * Get current notification permission
   */
  getPermission() {
    if ('Notification' in window) {
      this.permission = Notification.permission;
    }
    return this.permission;
  }

  /**
   * Request notification permission
   */
  async requestPermission() {
    if (!('Notification' in window)) {
      console.log('[Push] Notifications not supported');
      return 'denied';
    }

    const permission = await Notification.requestPermission();
    this.permission = permission;
    console.log('[Push] Permission:', permission);
    return permission;
  }

  /**
   * Get VAPID public key from server
   */
  async getVapidKey() {
    if (this.vapidPublicKey) {
      return this.vapidPublicKey;
    }

    try {
      const response = await mobileAPI.getVapidKey();
      this.vapidPublicKey = response.data.publicKey;
      return this.vapidPublicKey;
    } catch (error) {
      console.error('[Push] Failed to get VAPID key:', error);
      return null;
    }
  }

  /**
   * Subscribe to push notifications
   */
  async subscribe() {
    if (!this.isSupported()) {
      throw new Error('Push notifications not supported');
    }

    // Request permission first
    const permission = await this.requestPermission();
    if (permission !== 'granted') {
      throw new Error('Notification permission denied');
    }

    // Get service worker registration
    const registration = await navigator.serviceWorker.ready;

    // Check for existing subscription
    let subscription = await registration.pushManager.getSubscription();
    
    if (subscription) {
      console.log('[Push] Existing subscription found');
      this.subscription = subscription;
      return subscription;
    }

    // Get VAPID key
    const vapidKey = await this.getVapidKey();
    if (!vapidKey) {
      throw new Error('Failed to get VAPID key');
    }

    // Create new subscription
    try {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(vapidKey),
      });

      console.log('[Push] New subscription created');
      this.subscription = subscription;

      // Send subscription to server
      await this.sendSubscriptionToServer(subscription);

      return subscription;
    } catch (error) {
      console.error('[Push] Subscription failed:', error);
      throw error;
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async unsubscribe() {
    if (!this.subscription) {
      const registration = await navigator.serviceWorker.ready;
      this.subscription = await registration.pushManager.getSubscription();
    }

    if (this.subscription) {
      try {
        await this.subscription.unsubscribe();
        console.log('[Push] Unsubscribed');
        this.subscription = null;
        return true;
      } catch (error) {
        console.error('[Push] Unsubscribe failed:', error);
        return false;
      }
    }

    return true;
  }

  /**
   * Send subscription to server
   */
  async sendSubscriptionToServer(subscription) {
    const data = subscription.toJSON();
    
    try {
      await mobileAPI.subscribePush({
        endpoint: data.endpoint,
        keys: data.keys,
        platform: 'web',
        device_name: this.getDeviceName(),
      });
      console.log('[Push] Subscription sent to server');
    } catch (error) {
      console.error('[Push] Failed to send subscription to server:', error);
      throw error;
    }
  }

  /**
   * Get device name for subscription
   */
  getDeviceName() {
    const ua = navigator.userAgent;
    let browser = 'Unknown Browser';
    let os = 'Unknown OS';

    // Detect browser
    if (ua.includes('Firefox')) browser = 'Firefox';
    else if (ua.includes('Chrome')) browser = 'Chrome';
    else if (ua.includes('Safari')) browser = 'Safari';
    else if (ua.includes('Edge')) browser = 'Edge';

    // Detect OS
    if (ua.includes('Windows')) os = 'Windows';
    else if (ua.includes('Mac')) os = 'MacOS';
    else if (ua.includes('Linux')) os = 'Linux';
    else if (ua.includes('Android')) os = 'Android';
    else if (ua.includes('iOS')) os = 'iOS';

    return `${browser} on ${os}`;
  }

  /**
   * Check if currently subscribed
   */
  async isSubscribed() {
    if (!this.isSupported()) {
      return false;
    }

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return !!subscription;
  }

  /**
   * Show a local notification (not from server)
   */
  async showNotification(title, options = {}) {
    if (this.permission !== 'granted') {
      console.log('[Push] No permission to show notifications');
      return;
    }

    const registration = await navigator.serviceWorker.ready;
    
    await registration.showNotification(title, {
      icon: '/icons/icon-192.png',
      badge: '/icons/badge-72.png',
      vibrate: [100, 50, 100],
      ...options,
    });
  }

  /**
   * Convert VAPID key from base64 to Uint8Array
   */
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray;
  }

  /**
   * Update badge count (if supported)
   */
  async setBadge(count) {
    if ('setAppBadge' in navigator) {
      try {
        if (count > 0) {
          await navigator.setAppBadge(count);
        } else {
          await navigator.clearAppBadge();
        }
      } catch (error) {
        console.error('[Push] Badge update failed:', error);
      }
    }
  }
}

// Export singleton instance
export const pushManager = new PushManager();

export default pushManager;
```

---

## File 6: PWA Index
**Path:** `frontend/src/pwa/index.js`

```javascript
/**
 * PWA Module Index
 */

export { swManager } from './serviceWorker';
export { pushManager } from './pushManager';
export { offlineStorage } from './offlineStorage';

// Initialize PWA features
export const initPWA = async () => {
  // Register service worker
  await import('./serviceWorker');
  
  // Initialize offline storage
  const { offlineStorage } = await import('./offlineStorage');
  await offlineStorage.init();
  
  // Clean up expired cache
  await offlineStorage.clearExpiredCache();
  
  console.log('[PWA] Initialized');
};
```

---

## Summary Part 3

| File | Description | Lines |
|------|-------------|-------|
| `manifest.json` | Web App Manifest | ~90 |
| `sw.js` | Service Worker | ~250 |
| `offline.html` | Offline page | ~200 |
| `serviceWorker.js` | SW registration | ~120 |
| `pushManager.js` | Push client | ~200 |
| `index.js` | PWA index | ~20 |
| **Total** | | **~880 lines** |
