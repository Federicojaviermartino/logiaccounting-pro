/**
 * Settings Screen - App preferences and account settings
 */

import { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Switch,
  Alert,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@store/authStore';

const COLORS = {
  primary: '#1E40AF',
  error: '#EF4444',
  text: '#1F2937',
  textLight: '#6B7280',
  background: '#F3F4F6',
  white: '#FFFFFF',
  border: '#E5E7EB',
};

interface SettingItem {
  id: string;
  title: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  type: 'navigate' | 'toggle' | 'action';
  value?: boolean;
  onPress?: () => void;
  route?: string;
  destructive?: boolean;
}

export default function SettingsScreen() {
  const { user, logout, biometricEnabled, enableBiometric, disableBiometric } = useAuthStore();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [autoSync, setAutoSync] = useState(true);

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/(auth)/login');
          },
        },
      ]
    );
  };

  const handleBiometricToggle = async () => {
    if (biometricEnabled) {
      await disableBiometric();
    } else {
      await enableBiometric();
    }
  };

  const sections = [
    {
      title: 'Account',
      items: [
        {
          id: 'profile',
          title: 'Profile',
          icon: 'person-outline',
          type: 'navigate',
          route: '/settings/profile',
        },
        {
          id: 'security',
          title: 'Security',
          icon: 'shield-outline',
          type: 'navigate',
          route: '/settings/security',
        },
        {
          id: 'biometric',
          title: 'Biometric Login',
          icon: 'finger-print',
          type: 'toggle',
          value: biometricEnabled,
          onPress: handleBiometricToggle,
        },
      ] as SettingItem[],
    },
    {
      title: 'Preferences',
      items: [
        {
          id: 'notifications',
          title: 'Push Notifications',
          icon: 'notifications-outline',
          type: 'toggle',
          value: notificationsEnabled,
          onPress: () => setNotificationsEnabled(!notificationsEnabled),
        },
        {
          id: 'darkMode',
          title: 'Dark Mode',
          icon: 'moon-outline',
          type: 'toggle',
          value: darkMode,
          onPress: () => setDarkMode(!darkMode),
        },
        {
          id: 'autoSync',
          title: 'Auto Sync',
          icon: 'sync-outline',
          type: 'toggle',
          value: autoSync,
          onPress: () => setAutoSync(!autoSync),
        },
        {
          id: 'language',
          title: 'Language',
          icon: 'language-outline',
          type: 'navigate',
          route: '/settings/language',
        },
        {
          id: 'currency',
          title: 'Currency',
          icon: 'cash-outline',
          type: 'navigate',
          route: '/settings/currency',
        },
      ] as SettingItem[],
    },
    {
      title: 'Data',
      items: [
        {
          id: 'export',
          title: 'Export Data',
          icon: 'download-outline',
          type: 'navigate',
          route: '/settings/export',
        },
        {
          id: 'sync',
          title: 'Sync Status',
          icon: 'cloud-outline',
          type: 'navigate',
          route: '/settings/sync',
        },
        {
          id: 'cache',
          title: 'Clear Cache',
          icon: 'trash-outline',
          type: 'action',
          onPress: () => Alert.alert('Clear Cache', 'Cache cleared successfully'),
        },
      ] as SettingItem[],
    },
    {
      title: 'Support',
      items: [
        {
          id: 'help',
          title: 'Help Center',
          icon: 'help-circle-outline',
          type: 'navigate',
          route: '/settings/help',
        },
        {
          id: 'feedback',
          title: 'Send Feedback',
          icon: 'chatbubble-outline',
          type: 'navigate',
          route: '/settings/feedback',
        },
        {
          id: 'about',
          title: 'About',
          icon: 'information-circle-outline',
          type: 'navigate',
          route: '/settings/about',
        },
      ] as SettingItem[],
    },
    {
      title: '',
      items: [
        {
          id: 'logout',
          title: 'Sign Out',
          icon: 'log-out-outline',
          type: 'action',
          destructive: true,
          onPress: handleLogout,
        },
      ] as SettingItem[],
    },
  ];

  const renderItem = (item: SettingItem) => (
    <TouchableOpacity
      key={item.id}
      style={styles.settingItem}
      onPress={() => {
        if (item.type === 'navigate' && item.route) {
          router.push(item.route as any);
        } else if (item.onPress) {
          item.onPress();
        }
      }}
      disabled={item.type === 'toggle'}
      activeOpacity={0.7}
    >
      <View style={[styles.iconContainer, item.destructive && styles.iconDestructive]}>
        <Ionicons
          name={item.icon}
          size={20}
          color={item.destructive ? COLORS.error : COLORS.primary}
        />
      </View>
      <Text style={[styles.itemTitle, item.destructive && styles.destructiveText]}>
        {item.title}
      </Text>
      {item.type === 'toggle' ? (
        <Switch
          value={item.value}
          onValueChange={item.onPress}
          trackColor={{ false: '#D1D5DB', true: COLORS.primary + '60' }}
          thumbColor={item.value ? COLORS.primary : '#F3F4F6'}
        />
      ) : item.type === 'navigate' ? (
        <Ionicons name="chevron-forward" size={20} color={COLORS.textLight} />
      ) : null}
    </TouchableOpacity>
  );

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.profileCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </Text>
        </View>
        <View style={styles.profileInfo}>
          <Text style={styles.profileName}>{user?.name || 'User'}</Text>
          <Text style={styles.profileEmail}>{user?.email || 'email@example.com'}</Text>
        </View>
        <TouchableOpacity onPress={() => router.push('/settings/profile')}>
          <Ionicons name="create-outline" size={20} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      {sections.map((section, index) => (
        <View key={index} style={styles.section}>
          {section.title && <Text style={styles.sectionTitle}>{section.title}</Text>}
          <View style={styles.sectionContent}>
            {section.items.map(renderItem)}
          </View>
        </View>
      ))}

      <Text style={styles.version}>Version 1.0.0</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: 16,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.white,
  },
  profileInfo: {
    flex: 1,
    marginLeft: 16,
  },
  profileName: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  profileEmail: {
    fontSize: 14,
    color: COLORS.textLight,
    marginTop: 2,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textLight,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
    marginLeft: 4,
  },
  sectionContent: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  iconContainer: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: COLORS.primary + '15',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  iconDestructive: {
    backgroundColor: COLORS.error + '15',
  },
  itemTitle: {
    flex: 1,
    fontSize: 15,
    color: COLORS.text,
  },
  destructiveText: {
    color: COLORS.error,
  },
  version: {
    textAlign: 'center',
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 8,
    marginBottom: 24,
  },
});
