/**
 * Service Worker Registration
 */

import { Workbox } from 'workbox-window';

let wb = null;
let registration = null;

export async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) {
    console.log('Service Workers not supported');
    return null;
  }

  wb = new Workbox('/sw.js');

  // Handle updates
  wb.addEventListener('waiting', (event) => {
    console.log('New service worker waiting');

    // Dispatch custom event for UI to handle
    window.dispatchEvent(new CustomEvent('sw-update-available', {
      detail: { wb, registration: event.target }
    }));
  });

  // Handle activation
  wb.addEventListener('activated', (event) => {
    if (!event.isUpdate) {
      console.log('Service worker activated for the first time');
    } else {
      console.log('Service worker updated');
      // Reload to get new content
      window.location.reload();
    }
  });

  // Handle controller change
  wb.addEventListener('controlling', () => {
    console.log('Service worker is controlling the page');
  });

  // Register
  try {
    registration = await wb.register();
    console.log('Service Worker registered:', registration);
    return registration;
  } catch (error) {
    console.error('Service Worker registration failed:', error);
    return null;
  }
}

export function skipWaiting() {
  if (wb) {
    wb.messageSkipWaiting();
  }
}

export function getRegistration() {
  return registration;
}

export function getWorkbox() {
  return wb;
}
