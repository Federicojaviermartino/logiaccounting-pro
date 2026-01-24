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
