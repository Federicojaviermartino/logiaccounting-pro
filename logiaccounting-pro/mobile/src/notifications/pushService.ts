/**
 * Push Notification Service - Expo Notifications integration
 */

import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import { apiClient } from '@services/client';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export interface NotificationPayload {
  title: string;
  body: string;
  data?: Record<string, unknown>;
}

export interface PushToken {
  token: string;
  type: 'expo' | 'fcm' | 'apns';
  deviceId: string;
  platform: 'ios' | 'android' | 'web';
}

class PushNotificationService {
  private expoPushToken: string | null = null;
  private notificationListener: Notifications.Subscription | null = null;
  private responseListener: Notifications.Subscription | null = null;

  async registerForPushNotifications(): Promise<string | null> {
    if (!Device.isDevice) {
      console.log('Push notifications require a physical device');
      return null;
    }

    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Push notification permission denied');
      return null;
    }

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'Default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#1E40AF',
      });

      await Notifications.setNotificationChannelAsync('invoices', {
        name: 'Invoices',
        description: 'Invoice notifications',
        importance: Notifications.AndroidImportance.HIGH,
      });

      await Notifications.setNotificationChannelAsync('reminders', {
        name: 'Reminders',
        description: 'Payment reminders',
        importance: Notifications.AndroidImportance.HIGH,
      });
    }

    try {
      const token = await Notifications.getExpoPushTokenAsync({
        projectId: 'logiaccounting-pro',
      });

      this.expoPushToken = token.data;
      await this.registerTokenWithServer(token.data);

      return token.data;
    } catch (error) {
      console.error('Failed to get push token:', error);
      return null;
    }
  }

  private async registerTokenWithServer(token: string): Promise<void> {
    try {
      const deviceId = Device.modelId || 'unknown';

      await apiClient.post('/push/register', {
        token,
        type: 'expo',
        deviceId,
        platform: Platform.OS,
      });
    } catch (error) {
      console.error('Failed to register push token with server:', error);
    }
  }

  async unregisterFromServer(): Promise<void> {
    if (this.expoPushToken) {
      try {
        await apiClient.post('/push/unregister', {
          token: this.expoPushToken,
        });
      } catch (error) {
        console.error('Failed to unregister push token:', error);
      }
    }
  }

  setupNotificationListeners(
    onNotificationReceived?: (notification: Notifications.Notification) => void,
    onNotificationResponse?: (response: Notifications.NotificationResponse) => void
  ): void {
    this.notificationListener = Notifications.addNotificationReceivedListener((notification) => {
      console.log('Notification received:', notification);
      onNotificationReceived?.(notification);
    });

    this.responseListener = Notifications.addNotificationResponseReceivedListener((response) => {
      console.log('Notification response:', response);
      const data = response.notification.request.content.data;
      this.handleNotificationAction(data);
      onNotificationResponse?.(response);
    });
  }

  private handleNotificationAction(data: Record<string, unknown>): void {
    const action = data.action as string;
    const entityId = data.id as string;

    switch (action) {
      case 'view_invoice':
        break;
      case 'approve':
        break;
      case 'reject':
        break;
      default:
        break;
    }
  }

  removeListeners(): void {
    if (this.notificationListener) {
      Notifications.removeNotificationSubscription(this.notificationListener);
    }
    if (this.responseListener) {
      Notifications.removeNotificationSubscription(this.responseListener);
    }
  }

  async scheduleLocalNotification(
    payload: NotificationPayload,
    trigger?: Notifications.NotificationTriggerInput
  ): Promise<string> {
    const identifier = await Notifications.scheduleNotificationAsync({
      content: {
        title: payload.title,
        body: payload.body,
        data: payload.data,
        sound: true,
      },
      trigger: trigger || null,
    });

    return identifier;
  }

  async schedulePaymentReminder(
    invoiceId: string,
    customerName: string,
    amount: string,
    dueDate: Date
  ): Promise<string> {
    const reminderDate = new Date(dueDate);
    reminderDate.setDate(reminderDate.getDate() - 3);

    return this.scheduleLocalNotification(
      {
        title: 'Payment Reminder',
        body: `Invoice for ${customerName} (${amount}) is due in 3 days`,
        data: { action: 'view_invoice', id: invoiceId },
      },
      { date: reminderDate }
    );
  }

  async cancelNotification(identifier: string): Promise<void> {
    await Notifications.cancelScheduledNotificationAsync(identifier);
  }

  async cancelAllNotifications(): Promise<void> {
    await Notifications.cancelAllScheduledNotificationsAsync();
  }

  async getBadgeCount(): Promise<number> {
    return Notifications.getBadgeCountAsync();
  }

  async setBadgeCount(count: number): Promise<void> {
    await Notifications.setBadgeCountAsync(count);
  }

  async clearBadge(): Promise<void> {
    await Notifications.setBadgeCountAsync(0);
  }

  getExpoPushToken(): string | null {
    return this.expoPushToken;
  }
}

export const pushService = new PushNotificationService();

export async function registerForPushNotifications(): Promise<string | null> {
  return pushService.registerForPushNotifications();
}
