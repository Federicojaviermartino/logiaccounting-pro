/**
 * More Menu Screen
 * Settings and navigation hub
 */

import React from 'react';
import { StyleSheet, View, ScrollView, Pressable } from 'react-native';
import { Text, useTheme, Avatar, Divider, Badge } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useSelector } from 'react-redux';

import { spacing, borderRadius, colors } from '@app/theme';
import { RootState } from '@store/index';
import { Card } from '@components/common';
import type { MoreStackScreenProps } from '@types/navigation';

type Props = MoreStackScreenProps<'MoreMenu'>;

interface MenuItem {
  icon: string;
  label: string;
  screen: keyof Props['navigation'] extends { navigate: (screen: infer S) => void } ? S : never;
  badge?: number;
  color?: string;
}

const menuSections: { title: string; items: MenuItem[] }[] = [
  {
    title: 'Business',
    items: [
      { icon: 'folder-outline', label: 'Projects', screen: 'Projects' },
      { icon: 'chart-bar', label: 'Reports', screen: 'Reports' },
      { icon: 'chart-line', label: 'Analytics', screen: 'Analytics' },
    ],
  },
  {
    title: 'Account',
    items: [
      { icon: 'account-outline', label: 'Profile', screen: 'Profile' },
      { icon: 'cog-outline', label: 'Settings', screen: 'Settings' },
    ],
  },
  {
    title: 'Support',
    items: [
      { icon: 'help-circle-outline', label: 'Help & Support', screen: 'Help' },
      { icon: 'information-outline', label: 'About', screen: 'About' },
    ],
  },
];

export const MoreMenuScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();
  const { user } = useSelector((state: RootState) => state.auth);
  const { isOnline, pendingActions } = useSelector((state: RootState) => state.sync);

  const handleMenuPress = (screen: string) => {
    navigation.navigate(screen as any);
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
        {/* Profile Card */}
        <Pressable
          onPress={() => handleMenuPress('Profile')}
          style={({ pressed }) => [pressed && { opacity: 0.8 }]}
        >
          <Card style={styles.profileCard}>
            <View style={styles.profileContent}>
              <Avatar.Text
                size={64}
                label={user?.name?.substring(0, 2).toUpperCase() || 'U'}
                style={{ backgroundColor: theme.colors.primary }}
              />
              <View style={styles.profileInfo}>
                <Text
                  variant="titleLarge"
                  style={[styles.profileName, { color: theme.colors.onSurface }]}
                >
                  {user?.name || 'User'}
                </Text>
                <Text
                  variant="bodyMedium"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  {user?.email || 'user@example.com'}
                </Text>
                <View style={styles.syncStatus}>
                  <View
                    style={[
                      styles.statusDot,
                      { backgroundColor: isOnline ? colors.success : colors.warning },
                    ]}
                  />
                  <Text
                    variant="labelSmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    {isOnline ? 'Online' : `Offline (${pendingActions.length} pending)`}
                  </Text>
                </View>
              </View>
              <Icon
                name="chevron-right"
                size={24}
                color={theme.colors.onSurfaceVariant}
              />
            </View>
          </Card>
        </Pressable>

        {/* Menu Sections */}
        {menuSections.map((section, sectionIndex) => (
          <View key={sectionIndex} style={styles.section}>
            <Text
              variant="labelLarge"
              style={[styles.sectionTitle, { color: theme.colors.onSurfaceVariant }]}
            >
              {section.title}
            </Text>
            <Card style={styles.menuCard}>
              {section.items.map((item, itemIndex) => (
                <React.Fragment key={item.screen}>
                  <Pressable
                    onPress={() => handleMenuPress(item.screen)}
                    style={({ pressed }) => [
                      styles.menuItem,
                      pressed && { backgroundColor: theme.colors.surfaceVariant },
                    ]}
                  >
                    <View style={styles.menuItemLeft}>
                      <View
                        style={[
                          styles.menuIcon,
                          { backgroundColor: (item.color || theme.colors.primary) + '15' },
                        ]}
                      >
                        <Icon
                          name={item.icon}
                          size={22}
                          color={item.color || theme.colors.primary}
                        />
                      </View>
                      <Text
                        variant="bodyLarge"
                        style={{ color: theme.colors.onSurface }}
                      >
                        {item.label}
                      </Text>
                    </View>
                    <View style={styles.menuItemRight}>
                      {item.badge && item.badge > 0 && (
                        <Badge style={styles.badge}>{item.badge}</Badge>
                      )}
                      <Icon
                        name="chevron-right"
                        size={20}
                        color={theme.colors.onSurfaceVariant}
                      />
                    </View>
                  </Pressable>
                  {itemIndex < section.items.length - 1 && (
                    <Divider style={styles.divider} />
                  )}
                </React.Fragment>
              ))}
            </Card>
          </View>
        ))}

        {/* App Version */}
        <View style={styles.versionContainer}>
          <Text
            variant="labelSmall"
            style={{ color: theme.colors.onSurfaceVariant }}
          >
            LogiAccounting Pro v1.0.0
          </Text>
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
  profileCard: {
    marginBottom: spacing.lg,
  },
  profileContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  profileInfo: {
    flex: 1,
    marginLeft: spacing.md,
  },
  profileName: {
    fontWeight: '600',
    marginBottom: spacing.xxs,
  },
  syncStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.xs,
    gap: spacing.xs,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  section: {
    marginBottom: spacing.lg,
  },
  sectionTitle: {
    marginBottom: spacing.sm,
    marginLeft: spacing.xs,
    fontWeight: '600',
  },
  menuCard: {
    padding: 0,
    overflow: 'hidden',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.md,
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  menuIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuItemRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  badge: {
    backgroundColor: colors.error,
  },
  divider: {
    marginLeft: 68,
  },
  versionContainer: {
    alignItems: 'center',
    paddingTop: spacing.lg,
  },
});

export default MoreMenuScreen;
