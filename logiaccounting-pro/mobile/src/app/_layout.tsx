/**
 * Root Layout - Main app entry point with Expo Router
 */

import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SplashScreen from 'expo-splash-screen';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { useAuthStore } from '@store/authStore';
import { initializeDatabase } from '@storage/database';
import { registerForPushNotifications } from '@notifications/pushService';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    async function initialize() {
      try {
        await initializeDatabase();
        await checkAuth();
        await registerForPushNotifications();
      } catch (error) {
        console.error('Initialization error:', error);
      } finally {
        await SplashScreen.hideAsync();
      }
    }
    initialize();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar style="auto" />
        <Stack screenOptions={{ headerShown: false }}>
          {!isAuthenticated ? (
            <Stack.Screen name="(auth)" options={{ headerShown: false }} />
          ) : (
            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          )}
        </Stack>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
