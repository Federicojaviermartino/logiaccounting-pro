/**
 * Push Notification Service
 */

const VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY;

class PushService {
  constructor() {
    this.permission = 'default';
    this.subscription = null;
  }

  /**
   * Check if push is supported
   */
  isSupported() {
    return 'serviceWorker' in navigator &&
           'PushManager' in window &&
           'Notification' in window;
  }

  /**
   * Get current permission status
   */
  getPermission() {
    if (!this.isSupported()) return 'unsupported';
    return Notification.permission;
  }

  /**
   * Request notification permission
   */
  async requestPermission() {
    if (!this.isSupported()) {
      console.log('Push notifications not supported');
      return 'unsupported';
    }

    const permission = await Notification.requestPermission();
    this.permission = permission;

    if (permission === 'granted') {
      await this.subscribe();
    }

    return permission;
  }

  /**
   * Subscribe to push notifications
   */
  async subscribe() {
    try {
      const registration = await navigator.serviceWorker.ready;

      // Check existing subscription
      let subscription = await registration.pushManager.getSubscription();

      if (!subscription) {
        // Create new subscription
        subscription = await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: this.urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
        });
      }

      this.subscription = subscription;

      // Send subscription to server
      await this.sendSubscriptionToServer(subscription);

      return subscription;
    } catch (error) {
      console.error('Push subscription failed:', error);
      throw error;
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async unsubscribe() {
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.getSubscription();

      if (subscription) {
        await subscription.unsubscribe();
        await this.removeSubscriptionFromServer(subscription);
      }

      this.subscription = null;
    } catch (error) {
      console.error('Push unsubscribe failed:', error);
      throw error;
    }
  }

  /**
   * Send subscription to backend
   */
  async sendSubscriptionToServer(subscription) {
    const token = localStorage.getItem('token');

    const response = await fetch('/api/v1/notifications/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        subscription: subscription.toJSON(),
        device_type: 'web',
        device_name: navigator.userAgent,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to register subscription');
    }
  }

  /**
   * Remove subscription from backend
   */
  async removeSubscriptionFromServer(subscription) {
    const token = localStorage.getItem('token');

    await fetch('/api/v1/notifications/unsubscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        endpoint: subscription.endpoint,
      }),
    });
  }

  /**
   * Convert VAPID key
   */
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
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
   * Show local notification (for testing)
   */
  async showLocalNotification(title, options = {}) {
    if (Notification.permission !== 'granted') {
      return;
    }

    const registration = await navigator.serviceWorker.ready;
    await registration.showNotification(title, {
      icon: '/icons/icon-192x192.png',
      badge: '/icons/badge-72.png',
      ...options,
    });
  }
}

export const pushService = new PushService();
export default pushService;
