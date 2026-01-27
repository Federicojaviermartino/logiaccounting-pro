/**
 * Settings Screen
 * App settings and preferences
 */

import React from 'react';
import { StyleSheet, View, ScrollView, Pressable } from 'react-native';
import { Text, useTheme, Switch, Divider } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useSelector, useDispatch } from 'react-redux';

import { spacing, borderRadius } from '@app/theme';
import { RootState, AppDispatch } from '@store/index';
import {
  setTheme,
  setNotificationsEnabled,
  toggleBiometric,
} from '@store/slices/settingsSlice';
import { Card } from '@components/common';
import type { MoreStackScreenProps } from '@types/navigation';

type Props = MoreStackScreenProps<'Settings'>;

export const SettingsScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const settings = useSelector((state: RootState) => state.settings);

  const handleThemeChange = () => {
    const themes: ('light' | 'dark' | 'system')[] = ['light', 'dark', 'system'];
    const currentIndex = themes.indexOf(settings.theme);
    const nextTheme = themes[(currentIndex + 1) % themes.length];
    dispatch(setTheme(nextTheme));
  };

  const getThemeLabel = () => {
    switch (settings.theme) {
      case 'light':
        return 'Light';
      case 'dark':
        return 'Dark';
      default:
        return 'System';
    }
  };

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      edges={['bottom']}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Appearance */}
        <View style={styles.section}>
          <Text
            variant="labelLarge"
            style={[styles.sectionTitle, { color: theme.colors.onSurfaceVariant }]}
          >
            Appearance
          </Text>
          <Card style={styles.card}>
            <Pressable
              onPress={handleThemeChange}
              style={({ pressed }) => [
                styles.settingItem,
                pressed && { backgroundColor: theme.colors.surfaceVariant },
              ]}
            >
              <View style={styles.settingLeft}>
                <Icon
                  name="theme-light-dark"
                  size={24}
                  color={theme.colors.onSurfaceVariant}
                />
                <View>
                  <Text variant="bodyLarge" style={{ color: theme.colors.onSurface }}>
                    Theme
                  </Text>
                  <Text
                    variant="bodySmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    {getThemeLabel()}
                  </Text>
                </View>
              </View>
              <Icon
                name="chevron-right"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
            </Pressable>
          </Card>
        </View>

        {/* Security */}
        <View style={styles.section}>
          <Text
            variant="labelLarge"
            style={[styles.sectionTitle, { color: theme.colors.onSurfaceVariant }]}
          >
            Security
          </Text>
          <Card style={styles.card}>
            <Pressable
              onPress={() => navigation.navigate('SecuritySettings')}
              style={({ pressed }) => [
                styles.settingItem,
                pressed && { backgroundColor: theme.colors.surfaceVariant },
              ]}
            >
              <View style={styles.settingLeft}>
                <Icon
                  name="shield-lock-outline"
                  size={24}
                  color={theme.colors.onSurfaceVariant}
                />
                <View>
                  <Text variant="bodyLarge" style={{ color: theme.colors.onSurface }}>
                    Security Settings
                  </Text>
                  <Text
                    variant="bodySmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    PIN, biometrics, auto-lock
                  </Text>
                </View>
              </View>
              <Icon
                name="chevron-right"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
            </Pressable>

            <Divider style={styles.divider} />

            <View style={styles.settingItem}>
              <View style={styles.settingLeft}>
                <Icon
                  name="fingerprint"
                  size={24}
                  color={theme.colors.onSurfaceVariant}
                />
                <View>
                  <Text variant="bodyLarge" style={{ color: theme.colors.onSurface }}>
                    Biometric Unlock
                  </Text>
                  <Text
                    variant="bodySmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    Use fingerprint or face to unlock
                  </Text>
                </View>
              </View>
              <Switch
                value={settings.security.biometricEnabled}
                onValueChange={() => dispatch(toggleBiometric())}
              />
            </View>
          </Card>
        </View>

        {/* Notifications */}
        <View style={styles.section}>
          <Text
            variant="labelLarge"
            style={[styles.sectionTitle, { color: theme.colors.onSurfaceVariant }]}
          >
            Notifications
          </Text>
          <Card style={styles.card}>
            <Pressable
              onPress={() => navigation.navigate('NotificationSettings')}
              style={({ pressed }) => [
                styles.settingItem,
                pressed && { backgroundColor: theme.colors.surfaceVariant },
              ]}
            >
              <View style={styles.settingLeft}>
                <Icon
                  name="bell-outline"
                  size={24}
                  color={theme.colors.onSurfaceVariant}
                />
                <View>
                  <Text variant="bodyLarge" style={{ color: theme.colors.onSurface }}>
                    Notification Preferences
                  </Text>
                  <Text
                    variant="bodySmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    Alerts, reminders, sounds
                  </Text>
                </View>
              </View>
              <Icon
                name="chevron-right"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
            </Pressable>

            <Divider style={styles.divider} />

            <View style={styles.settingItem}>
              <View style={styles.settingLeft}>
                <Icon
                  name="bell-ring-outline"
                  size={24}
                  color={theme.colors.onSurfaceVariant}
                />
                <View>
                  <Text variant="bodyLarge" style={{ color: theme.colors.onSurface }}>
                    Push Notifications
                  </Text>
                  <Text
                    variant="bodySmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    Receive push notifications
                  </Text>
                </View>
              </View>
              <Switch
                value={settings.notifications.enabled}
                onValueChange={(value) => dispatch(setNotificationsEnabled(value))}
              />
            </View>
          </Card>
        </View>

        {/* Sync & Data */}
        <View style={styles.section}>
          <Text
            variant="labelLarge"
            style={[styles.sectionTitle, { color: theme.colors.onSurfaceVariant }]}
          >
            Sync & Data
          </Text>
          <Card style={styles.card}>
            <Pressable
              onPress={() => navigation.navigate('SyncSettings')}
              style={({ pressed }) => [
                styles.settingItem,
                pressed && { backgroundColor: theme.colors.surfaceVariant },
              ]}
            >
              <View style={styles.settingLeft}>
                <Icon
                  name="sync"
                  size={24}
                  color={theme.colors.onSurfaceVariant}
                />
                <View>
                  <Text variant="bodyLarge" style={{ color: theme.colors.onSurface }}>
                    Sync Settings
                  </Text>
                  <Text
                    variant="bodySmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    Auto-sync, offline data
                  </Text>
                </View>
              </View>
              <Icon
                name="chevron-right"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
            </Pressable>
          </Card>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: spacing.md,
    paddingBottom: spacing.xxl,
  },
  section: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    marginBottom: spacing.sm,
    marginLeft: spacing.xs,
    fontWeight: '600',
  },
  card: {
    padding: 0,
    overflow: 'hidden',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.md,
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: spacing.md,
  },
  divider: {
    marginLeft: 56,
  },
});

export default SettingsScreen;
