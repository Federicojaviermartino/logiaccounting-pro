/**
 * Notifications Screen
 * Displays app notifications and alerts
 */

import React, { useState } from 'react';
import { StyleSheet, View, FlatList, Pressable } from 'react-native';
import { Text, useTheme, Chip } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';
import { EmptyState, Card } from '@components/common';
import type { DashboardStackScreenProps } from '@types/navigation';

type Props = DashboardStackScreenProps<'Notifications'>;

interface Notification {
  id: string;
  type: 'alert' | 'info' | 'success' | 'warning';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

const mockNotifications: Notification[] = [
  {
    id: '1',
    type: 'warning',
    title: 'Low Stock Alert',
    message: 'Steel Rods (REF-001) stock is below minimum threshold',
    timestamp: '2 hours ago',
    read: false,
  },
  {
    id: '2',
    type: 'alert',
    title: 'Payment Overdue',
    message: 'Payment from Client ABC is 5 days overdue',
    timestamp: '4 hours ago',
    read: false,
  },
  {
    id: '3',
    type: 'success',
    title: 'Payment Received',
    message: '$3,500 received from Client XYZ',
    timestamp: 'Yesterday',
    read: true,
  },
  {
    id: '4',
    type: 'info',
    title: 'New Feature Available',
    message: 'Try our new barcode scanning feature for faster inventory',
    timestamp: '2 days ago',
    read: true,
  },
];

export const NotificationsScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();
  const [notifications, setNotifications] = useState(mockNotifications);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const filteredNotifications =
    filter === 'all'
      ? notifications
      : notifications.filter((n) => !n.read);

  const getTypeColor = (type: Notification['type']) => {
    switch (type) {
      case 'alert':
        return colors.error;
      case 'warning':
        return colors.warning;
      case 'success':
        return colors.success;
      default:
        return theme.colors.primary;
    }
  };

  const getTypeIcon = (type: Notification['type']) => {
    switch (type) {
      case 'alert':
        return 'alert-circle';
      case 'warning':
        return 'alert';
      case 'success':
        return 'check-circle';
      default:
        return 'information';
    }
  };

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  const renderNotification = ({ item }: { item: Notification }) => {
    const typeColor = getTypeColor(item.type);

    return (
      <Pressable
        onPress={() => markAsRead(item.id)}
        style={({ pressed }) => [
          styles.notificationItem,
          {
            backgroundColor: item.read
              ? theme.colors.surface
              : theme.colors.primaryContainer + '30',
          },
          pressed && { opacity: 0.8 },
        ]}
      >
        <View style={[styles.typeIndicator, { backgroundColor: typeColor }]} />
        <View
          style={[styles.iconContainer, { backgroundColor: typeColor + '20' }]}
        >
          <Icon name={getTypeIcon(item.type)} size={20} color={typeColor} />
        </View>
        <View style={styles.content}>
          <View style={styles.header}>
            <Text
              variant="titleSmall"
              style={[
                styles.title,
                { color: theme.colors.onSurface },
                !item.read && { fontWeight: '700' },
              ]}
            >
              {item.title}
            </Text>
            {!item.read && (
              <View
                style={[styles.unreadDot, { backgroundColor: theme.colors.primary }]}
              />
            )}
          </View>
          <Text
            variant="bodySmall"
            style={{ color: theme.colors.onSurfaceVariant }}
            numberOfLines={2}
          >
            {item.message}
          </Text>
          <Text
            variant="labelSmall"
            style={[styles.timestamp, { color: theme.colors.outline }]}
          >
            {item.timestamp}
          </Text>
        </View>
      </Pressable>
    );
  };

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      edges={['bottom']}
    >
      {/* Filters */}
      <View style={styles.filters}>
        <View style={styles.filterChips}>
          <Chip
            selected={filter === 'all'}
            onPress={() => setFilter('all')}
            style={styles.chip}
          >
            All
          </Chip>
          <Chip
            selected={filter === 'unread'}
            onPress={() => setFilter('unread')}
            style={styles.chip}
          >
            Unread ({unreadCount})
          </Chip>
        </View>
        {unreadCount > 0 && (
          <Pressable onPress={markAllAsRead}>
            <Text variant="labelMedium" style={{ color: theme.colors.primary }}>
              Mark all read
            </Text>
          </Pressable>
        )}
      </View>

      {/* Notifications List */}
      {filteredNotifications.length > 0 ? (
        <FlatList
          data={filteredNotifications}
          renderItem={renderNotification}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          ItemSeparatorComponent={() => <View style={{ height: spacing.sm }} />}
        />
      ) : (
        <EmptyState
          icon="bell-off-outline"
          title="No Notifications"
          description={
            filter === 'unread'
              ? "You're all caught up! No unread notifications."
              : 'You have no notifications yet.'
          }
        />
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  filters: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.md,
    paddingTop: spacing.sm,
  },
  filterChips: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  chip: {
    marginRight: 0,
  },
  list: {
    padding: spacing.md,
    paddingTop: 0,
  },
  notificationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    overflow: 'hidden',
  },
  typeIndicator: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    borderTopLeftRadius: borderRadius.lg,
    borderBottomLeftRadius: borderRadius.lg,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xxs,
  },
  title: {
    flex: 1,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: spacing.sm,
  },
  timestamp: {
    marginTop: spacing.xs,
  },
});

export default NotificationsScreen;
