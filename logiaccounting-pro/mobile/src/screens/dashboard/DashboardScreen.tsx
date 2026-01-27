/**
 * Dashboard Screen
 * Main home screen with KPIs and quick actions
 */

import React, { useCallback } from 'react';
import {
  StyleSheet,
  View,
  ScrollView,
  RefreshControl,
  Pressable,
} from 'react-native';
import { Text, useTheme, FAB, Badge } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useSelector } from 'react-redux';

import { spacing, borderRadius, colors } from '@app/theme';
import { RootState } from '@store/index';
import { useGetDashboardQuery } from '@store/api/apiSlice';
import { Card, KPICard, LoadingSpinner, Header } from '@components/common';
import type { DashboardStackScreenProps } from '@types/navigation';

type Props = DashboardStackScreenProps<'Dashboard'>;

interface QuickAction {
  icon: string;
  label: string;
  color: string;
  screen: string;
  params?: object;
}

const quickActions: QuickAction[] = [
  {
    icon: 'package-variant-plus',
    label: 'Stock Entry',
    color: colors.success,
    screen: 'InventoryTab',
    params: { screen: 'InventoryMovement', params: { type: 'entry' } },
  },
  {
    icon: 'package-variant-minus',
    label: 'Stock Exit',
    color: colors.warning,
    screen: 'InventoryTab',
    params: { screen: 'InventoryMovement', params: { type: 'exit' } },
  },
  {
    icon: 'cash-plus',
    label: 'Add Income',
    color: colors.success,
    screen: 'TransactionsTab',
    params: { screen: 'AddTransaction', params: { type: 'income' } },
  },
  {
    icon: 'cash-minus',
    label: 'Add Expense',
    color: colors.error,
    screen: 'TransactionsTab',
    params: { screen: 'AddTransaction', params: { type: 'expense' } },
  },
];

export const DashboardScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();
  const { user } = useSelector((state: RootState) => state.auth);
  const { data, isLoading, isFetching, refetch } = useGetDashboardQuery(undefined);

  const handleNotifications = () => {
    navigation.navigate('Notifications');
  };

  const handleQuickAction = (action: QuickAction) => {
    navigation.navigate(action.screen as any, action.params);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const renderGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Loading dashboard..." />;
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      edges={['top']}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text
            variant="titleSmall"
            style={{ color: theme.colors.onSurfaceVariant }}
          >
            {renderGreeting()}
          </Text>
          <Text
            variant="headlineSmall"
            style={[styles.userName, { color: theme.colors.onSurface }]}
          >
            {user?.name || 'User'}
          </Text>
        </View>
        <Pressable
          onPress={handleNotifications}
          style={({ pressed }) => [
            styles.notificationButton,
            { backgroundColor: theme.colors.surfaceVariant },
            pressed && { opacity: 0.8 },
          ]}
        >
          <Icon
            name="bell-outline"
            size={24}
            color={theme.colors.onSurfaceVariant}
          />
          <Badge style={styles.badge} size={8} />
        </Pressable>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={isFetching} onRefresh={refetch} />
        }
      >
        {/* KPI Cards */}
        <View style={styles.section}>
          <Text
            variant="titleMedium"
            style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
          >
            Overview
          </Text>
          <View style={styles.kpiGrid}>
            <KPICard
              title="Revenue"
              value={formatCurrency(data?.revenue || 125000)}
              subtitle="This month"
              icon="trending-up"
              iconColor={colors.success}
              trend={{ value: 12.5, direction: 'up' }}
            />
            <KPICard
              title="Expenses"
              value={formatCurrency(data?.expenses || 45000)}
              subtitle="This month"
              icon="trending-down"
              iconColor={colors.error}
              trend={{ value: -3.2, direction: 'down' }}
            />
          </View>
          <View style={styles.kpiGrid}>
            <KPICard
              title="Pending Payments"
              value={data?.pendingPayments || 8}
              subtitle="To collect"
              icon="clock-outline"
              iconColor={colors.warning}
            />
            <KPICard
              title="Low Stock Items"
              value={data?.lowStockItems || 5}
              subtitle="Need attention"
              icon="alert-circle-outline"
              iconColor={colors.error}
            />
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text
            variant="titleMedium"
            style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
          >
            Quick Actions
          </Text>
          <View style={styles.actionsGrid}>
            {quickActions.map((action, index) => (
              <Pressable
                key={index}
                onPress={() => handleQuickAction(action)}
                style={({ pressed }) => [
                  styles.actionCard,
                  { backgroundColor: theme.colors.surface },
                  pressed && { opacity: 0.8, transform: [{ scale: 0.98 }] },
                ]}
              >
                <View
                  style={[
                    styles.actionIcon,
                    { backgroundColor: action.color + '20' },
                  ]}
                >
                  <Icon name={action.icon} size={24} color={action.color} />
                </View>
                <Text
                  variant="labelMedium"
                  style={{ color: theme.colors.onSurface, textAlign: 'center' }}
                  numberOfLines={2}
                >
                  {action.label}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>

        {/* Recent Activity */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text
              variant="titleMedium"
              style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
            >
              Recent Activity
            </Text>
            <Pressable>
              <Text variant="labelMedium" style={{ color: theme.colors.primary }}>
                See all
              </Text>
            </Pressable>
          </View>
          <Card>
            {[
              {
                icon: 'package-variant',
                title: 'Stock updated',
                description: '50 units of Steel Rods added',
                time: '2 hours ago',
              },
              {
                icon: 'cash-plus',
                title: 'Payment received',
                description: '$2,500 from Client ABC',
                time: '4 hours ago',
              },
              {
                icon: 'file-document',
                title: 'Invoice created',
                description: 'INV-2024-0125 for Project X',
                time: 'Yesterday',
              },
            ].map((activity, index) => (
              <View
                key={index}
                style={[
                  styles.activityItem,
                  index < 2 && {
                    borderBottomWidth: 1,
                    borderBottomColor: theme.colors.outlineVariant,
                  },
                ]}
              >
                <View
                  style={[
                    styles.activityIcon,
                    { backgroundColor: theme.colors.primaryContainer },
                  ]}
                >
                  <Icon
                    name={activity.icon}
                    size={20}
                    color={theme.colors.primary}
                  />
                </View>
                <View style={styles.activityContent}>
                  <Text
                    variant="bodyMedium"
                    style={{ color: theme.colors.onSurface, fontWeight: '500' }}
                  >
                    {activity.title}
                  </Text>
                  <Text
                    variant="bodySmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    {activity.description}
                  </Text>
                </View>
                <Text
                  variant="labelSmall"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  {activity.time}
                </Text>
              </View>
            ))}
          </Card>
        </View>
      </ScrollView>

      <FAB
        icon="barcode-scan"
        onPress={() =>
          navigation.navigate('InventoryTab', {
            screen: 'BarcodeScanner',
            params: { returnTo: 'InventoryList' },
          })
        }
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        color={theme.colors.onPrimary}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.lg,
    paddingBottom: spacing.md,
  },
  headerLeft: {
    flex: 1,
  },
  userName: {
    fontWeight: '700',
  },
  notificationButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: colors.error,
  },
  scrollContent: {
    padding: spacing.lg,
    paddingTop: 0,
    paddingBottom: 100,
  },
  section: {
    marginBottom: spacing.xl,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontWeight: '600',
    marginBottom: spacing.md,
  },
  kpiGrid: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  actionCard: {
    width: '47%',
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
    gap: spacing.sm,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    gap: spacing.md,
  },
  activityIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activityContent: {
    flex: 1,
  },
  fab: {
    position: 'absolute',
    right: spacing.lg,
    bottom: spacing.lg,
  },
});

export default DashboardScreen;
