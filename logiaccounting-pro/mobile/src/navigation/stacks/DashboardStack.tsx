/**
 * Dashboard Stack Navigator
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from 'react-native-paper';

import { DashboardScreen } from '@screens/dashboard/DashboardScreen';
import { NotificationsScreen } from '@screens/dashboard/NotificationsScreen';
import { QuickActionsScreen } from '@screens/dashboard/QuickActionsScreen';
import type { DashboardStackParamList } from '@types/navigation';

const Stack = createNativeStackNavigator<DashboardStackParamList>();

export const DashboardStack: React.FC = () => {
  const theme = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.colors.surface,
        },
        headerTintColor: theme.colors.onSurface,
        headerTitleStyle: {
          fontWeight: '600',
        },
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          headerShown: false,
        }}
      />
      <Stack.Screen
        name="Notifications"
        component={NotificationsScreen}
        options={{
          title: 'Notifications',
        }}
      />
      <Stack.Screen
        name="QuickActions"
        component={QuickActionsScreen}
        options={{
          title: 'Quick Actions',
        }}
      />
    </Stack.Navigator>
  );
};

export default DashboardStack;
