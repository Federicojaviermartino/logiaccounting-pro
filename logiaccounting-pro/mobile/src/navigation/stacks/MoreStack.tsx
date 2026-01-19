/**
 * More Stack Navigator
 * Settings, Profile, Projects, Reports, etc.
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from 'react-native-paper';

import { MoreMenuScreen } from '@screens/more/MoreMenuScreen';
import { ProfileScreen } from '@screens/more/ProfileScreen';
import { SettingsScreen } from '@screens/more/SettingsScreen';
import { SecuritySettingsScreen } from '@screens/more/SecuritySettingsScreen';
import { NotificationSettingsScreen } from '@screens/more/NotificationSettingsScreen';
import { SyncSettingsScreen } from '@screens/more/SyncSettingsScreen';
import { ProjectsScreen } from '@screens/more/ProjectsScreen';
import { ProjectDetailScreen } from '@screens/more/ProjectDetailScreen';
import { ReportsScreen } from '@screens/more/ReportsScreen';
import { ReportDetailScreen } from '@screens/more/ReportDetailScreen';
import { AnalyticsScreen } from '@screens/more/AnalyticsScreen';
import { HelpScreen } from '@screens/more/HelpScreen';
import { AboutScreen } from '@screens/more/AboutScreen';
import type { MoreStackParamList } from '@types/navigation';

const Stack = createNativeStackNavigator<MoreStackParamList>();

export const MoreStack: React.FC = () => {
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
        name="MoreMenu"
        component={MoreMenuScreen}
        options={{
          title: 'More',
        }}
      />
      <Stack.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          title: 'Profile',
        }}
      />
      <Stack.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: 'Settings',
        }}
      />
      <Stack.Screen
        name="SecuritySettings"
        component={SecuritySettingsScreen}
        options={{
          title: 'Security',
        }}
      />
      <Stack.Screen
        name="NotificationSettings"
        component={NotificationSettingsScreen}
        options={{
          title: 'Notifications',
        }}
      />
      <Stack.Screen
        name="SyncSettings"
        component={SyncSettingsScreen}
        options={{
          title: 'Sync & Offline',
        }}
      />
      <Stack.Screen
        name="Projects"
        component={ProjectsScreen}
        options={{
          title: 'Projects',
        }}
      />
      <Stack.Screen
        name="ProjectDetail"
        component={ProjectDetailScreen}
        options={{
          title: 'Project Details',
        }}
      />
      <Stack.Screen
        name="Reports"
        component={ReportsScreen}
        options={{
          title: 'Reports',
        }}
      />
      <Stack.Screen
        name="ReportDetail"
        component={ReportDetailScreen}
        options={{
          title: 'Report',
        }}
      />
      <Stack.Screen
        name="Analytics"
        component={AnalyticsScreen}
        options={{
          title: 'Analytics',
        }}
      />
      <Stack.Screen
        name="Help"
        component={HelpScreen}
        options={{
          title: 'Help & Support',
        }}
      />
      <Stack.Screen
        name="About"
        component={AboutScreen}
        options={{
          title: 'About',
        }}
      />
    </Stack.Navigator>
  );
};

export default MoreStack;
