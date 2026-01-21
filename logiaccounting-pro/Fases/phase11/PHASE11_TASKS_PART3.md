# LogiAccounting Pro - Phase 11 Tasks Part 3

## CORE SCREENS & COMPONENTS

---

## TASK 8: COMMON COMPONENTS

### 8.1 Card Component

**File:** `mobile/src/components/common/Card.tsx`

```typescript
/**
 * Reusable Card Component
 */

import React from 'react';
import { View, StyleSheet, ViewStyle, Pressable } from 'react-native';
import { colors, spacing, borderRadius, shadows } from '@/app/theme';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  onPress?: () => void;
  variant?: 'default' | 'outlined' | 'elevated';
  padding?: keyof typeof spacing;
}

const Card: React.FC<CardProps> = ({
  children,
  style,
  onPress,
  variant = 'default',
  padding = 'md',
}) => {
  const cardStyle = [
    styles.card,
    styles[variant],
    { padding: spacing[padding] },
    style,
  ];

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        style={({ pressed }) => [
          ...cardStyle,
          pressed && styles.pressed,
        ]}
      >
        {children}
      </Pressable>
    );
  }

  return <View style={cardStyle}>{children}</View>;
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.md,
  },
  default: {
    ...shadows.sm,
  },
  outlined: {
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  elevated: {
    ...shadows.md,
  },
  pressed: {
    opacity: 0.9,
    transform: [{ scale: 0.98 }],
  },
});

export default Card;
```

### 8.2 KPI Card Component

**File:** `mobile/src/components/cards/KPICard.tsx`

```typescript
/**
 * KPI Card Component
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import Card from '../common/Card';
import { colors, spacing, borderRadius } from '@/app/theme';

interface KPICardProps {
  title: string;
  value: string;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  icon: string;
  iconColor?: string;
  onPress?: () => void;
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  change,
  trend,
  icon,
  iconColor = colors.primary,
  onPress,
}) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return 'trending-up';
      case 'down':
        return 'trending-down';
      default:
        return 'minus';
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return colors.success;
      case 'down':
        return colors.danger;
      default:
        return colors.onSurfaceVariant;
    }
  };

  return (
    <Card style={styles.card} onPress={onPress}>
      <View style={styles.header}>
        <View style={[styles.iconContainer, { backgroundColor: `${iconColor}20` }]}>
          <Icon name={icon} size={24} color={iconColor} />
        </View>
        {change !== undefined && trend && (
          <View style={[styles.changeBadge, { backgroundColor: `${getTrendColor()}15` }]}>
            <Icon name={getTrendIcon()} size={14} color={getTrendColor()} />
            <Text style={[styles.changeText, { color: getTrendColor() }]}>
              {change >= 0 ? '+' : ''}{change.toFixed(1)}%
            </Text>
          </View>
        )}
      </View>
      <Text style={styles.value}>{value}</Text>
      <Text style={styles.title}>{title}</Text>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minWidth: 150,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.sm,
    justifyContent: 'center',
    alignItems: 'center',
  },
  changeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
  },
  changeText: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 2,
  },
  value: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.onSurface,
    marginBottom: spacing.xs,
  },
  title: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
  },
});

export default KPICard;
```

### 8.3 List Item Components

**File:** `mobile/src/components/lists/InventoryItem.tsx`

```typescript
/**
 * Inventory List Item Component
 */

import React from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { Text, Badge } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors, spacing, borderRadius } from '@/app/theme';

interface InventoryItemProps {
  id: string;
  reference: string;
  name: string;
  category: string;
  currentStock: number;
  minStock: number;
  unitCost: number;
  state: 'active' | 'inactive' | 'depleted';
  onPress: () => void;
}

const InventoryItem: React.FC<InventoryItemProps> = ({
  reference,
  name,
  category,
  currentStock,
  minStock,
  unitCost,
  state,
  onPress,
}) => {
  const isLowStock = currentStock <= minStock;
  const isOutOfStock = currentStock === 0;

  const getStockColor = () => {
    if (isOutOfStock) return colors.danger;
    if (isLowStock) return colors.warning;
    return colors.success;
  };

  const getStockLabel = () => {
    if (isOutOfStock) return 'Out of Stock';
    if (isLowStock) return 'Low Stock';
    return 'In Stock';
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.container, pressed && styles.pressed]}
    >
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.reference}>{reference}</Text>
          <Badge
            style={[styles.stockBadge, { backgroundColor: `${getStockColor()}20` }]}
            size={22}
          >
            <Text style={[styles.stockLabel, { color: getStockColor() }]}>
              {getStockLabel()}
            </Text>
          </Badge>
        </View>
        
        <Text style={styles.name} numberOfLines={1}>
          {name}
        </Text>
        
        <View style={styles.details}>
          <View style={styles.detailItem}>
            <Icon name="tag-outline" size={14} color={colors.onSurfaceVariant} />
            <Text style={styles.detailText}>{category}</Text>
          </View>
          <View style={styles.detailItem}>
            <Icon name="package-variant" size={14} color={colors.onSurfaceVariant} />
            <Text style={styles.detailText}>
              {currentStock} / {minStock} min
            </Text>
          </View>
        </View>
        
        <View style={styles.footer}>
          <Text style={styles.cost}>{formatCurrency(unitCost)}</Text>
          <Text style={styles.totalValue}>
            Total: {formatCurrency(currentStock * unitCost)}
          </Text>
        </View>
      </View>
      
      <Icon name="chevron-right" size={24} color={colors.onSurfaceVariant} />
    </Pressable>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    padding: spacing.md,
    marginHorizontal: spacing.md,
    marginVertical: spacing.xs,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  pressed: {
    backgroundColor: colors.surfaceVariant,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  reference: {
    fontSize: 12,
    color: colors.primary,
    fontWeight: '600',
  },
  stockBadge: {
    paddingHorizontal: spacing.sm,
  },
  stockLabel: {
    fontSize: 10,
    fontWeight: '600',
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.onSurface,
    marginBottom: spacing.sm,
  },
  details: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.sm,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  detailText: {
    fontSize: 12,
    color: colors.onSurfaceVariant,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cost: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.onSurface,
  },
  totalValue: {
    fontSize: 12,
    color: colors.onSurfaceVariant,
  },
});

export default InventoryItem;
```

### 8.4 Empty State Component

**File:** `mobile/src/components/common/EmptyState.tsx`

```typescript
/**
 * Empty State Component
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors, spacing } from '@/app/theme';

interface EmptyStateProps {
  icon: string;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.iconContainer}>
        <Icon name={icon} size={64} color={colors.onSurfaceVariant} />
      </View>
      <Text style={styles.title}>{title}</Text>
      {description && <Text style={styles.description}>{description}</Text>}
      {actionLabel && onAction && (
        <Button
          mode="contained"
          onPress={onAction}
          style={styles.button}
        >
          {actionLabel}
        </Button>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  iconContainer: {
    marginBottom: spacing.lg,
    opacity: 0.5,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.onSurface,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  description: {
    fontSize: 14,
    color: colors.onSurfaceVariant,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  button: {
    marginTop: spacing.md,
  },
});

export default EmptyState;
```

### 8.5 Loading Spinner Component

**File:** `mobile/src/components/common/LoadingSpinner.tsx`

```typescript
/**
 * Loading Spinner Component
 */

import React from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { Text } from 'react-native-paper';
import { colors, spacing } from '@/app/theme';

interface LoadingSpinnerProps {
  size?: 'small' | 'large';
  message?: string;
  fullScreen?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'large',
  message,
  fullScreen = false,
}) => {
  return (
    <View style={[styles.container, fullScreen && styles.fullScreen]}>
      <ActivityIndicator size={size} color={colors.primary} />
      {message && <Text style={styles.message}>{message}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  fullScreen: {
    flex: 1,
    backgroundColor: colors.background,
  },
  message: {
    marginTop: spacing.md,
    fontSize: 14,
    color: colors.onSurfaceVariant,
  },
});

export default LoadingSpinner;
```

---

## TASK 9: DASHBOARD SCREEN

### 9.1 Create Dashboard Screen

**File:** `mobile/src/screens/dashboard/DashboardScreen.tsx`

```typescript
/**
 * Dashboard Screen
 */

import React, { useEffect, useCallback } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Pressable,
} from 'react-native';
import { Text, IconButton, Badge } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useNavigation } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSelector, useDispatch } from 'react-redux';

import { RootState, AppDispatch } from '@store/index';
import { fetchPayments } from '@store/slices/paymentsSlice';
import { fetchMaterials } from '@store/slices/inventorySlice';
import { useGetDashboardQuery } from '@store/api/apiSlice';
import KPICard from '@components/cards/KPICard';
import Card from '@components/common/Card';
import LoadingSpinner from '@components/common/LoadingSpinner';
import { useOffline } from '@hooks/useOffline';
import { colors, spacing, borderRadius } from '@/app/theme';

const DashboardScreen: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const { isOffline, pendingActions } = useOffline();

  const { user } = useSelector((state: RootState) => state.auth);
  const { overdueCount, upcomingCount } = useSelector(
    (state: RootState) => state.payments
  );
  const { materials } = useSelector((state: RootState) => state.inventory);

  const {
    data: dashboard,
    isLoading,
    isFetching,
    refetch,
  } = useGetDashboardQuery(undefined, {
    pollingInterval: isOffline ? 0 : 60000, // Poll every minute when online
  });

  const lowStockCount = materials.filter(
    (m) => m.currentStock <= m.minStock
  ).length;

  useEffect(() => {
    dispatch(fetchPayments());
    dispatch(fetchMaterials());
  }, [dispatch]);

  const onRefresh = useCallback(() => {
    if (!isOffline) {
      refetch();
      dispatch(fetchPayments());
      dispatch(fetchMaterials());
    }
  }, [isOffline, refetch, dispatch]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  if (isLoading && !dashboard) {
    return <LoadingSpinner fullScreen message="Loading dashboard..." />;
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>{getGreeting()},</Text>
          <Text style={styles.userName}>{user?.name || 'User'}</Text>
        </View>
        <View style={styles.headerActions}>
          {isOffline && (
            <View style={styles.offlineBadge}>
              <Icon name="cloud-off-outline" size={16} color={colors.warning} />
              <Text style={styles.offlineText}>Offline</Text>
            </View>
          )}
          <IconButton
            icon="bell-outline"
            size={24}
            onPress={() => navigation.navigate('Notifications' as never)}
          />
          {(overdueCount > 0 || pendingActions > 0) && (
            <Badge style={styles.notificationBadge} size={18}>
              {overdueCount + pendingActions}
            </Badge>
          )}
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={isFetching}
            onRefresh={onRefresh}
            tintColor={colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* KPI Cards */}
        <View style={styles.kpiRow}>
          <KPICard
            title="Revenue"
            value={formatCurrency(dashboard?.revenue?.value || 0)}
            change={dashboard?.revenue?.change}
            trend={dashboard?.revenue?.trend}
            icon="trending-up"
            iconColor={colors.success}
          />
          <KPICard
            title="Expenses"
            value={formatCurrency(dashboard?.expenses?.value || 0)}
            change={dashboard?.expenses?.change}
            trend={dashboard?.expenses?.trend}
            icon="trending-down"
            iconColor={colors.danger}
          />
        </View>

        <View style={styles.kpiRow}>
          <KPICard
            title="Profit"
            value={formatCurrency(dashboard?.profit?.value || 0)}
            change={dashboard?.profit?.change}
            trend={dashboard?.profit?.trend}
            icon="chart-line"
            iconColor={colors.primary}
          />
          <KPICard
            title="Cash Flow"
            value={formatCurrency(dashboard?.cashFlow?.value || 0)}
            change={dashboard?.cashFlow?.change}
            trend={dashboard?.cashFlow?.trend}
            icon="cash-multiple"
            iconColor={colors.info}
          />
        </View>

        {/* Quick Actions */}
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsRow}>
          <Pressable
            style={styles.actionButton}
            onPress={() => navigation.navigate('InventoryTab' as never, {
              screen: 'Scanner',
              params: { mode: 'movement' },
            } as never)}
          >
            <View style={[styles.actionIcon, { backgroundColor: `${colors.primary}15` }]}>
              <Icon name="barcode-scan" size={24} color={colors.primary} />
            </View>
            <Text style={styles.actionLabel}>Scan</Text>
          </Pressable>

          <Pressable
            style={styles.actionButton}
            onPress={() => navigation.navigate('TransactionsTab' as never, {
              screen: 'TransactionForm',
            } as never)}
          >
            <View style={[styles.actionIcon, { backgroundColor: `${colors.success}15` }]}>
              <Icon name="plus-circle" size={24} color={colors.success} />
            </View>
            <Text style={styles.actionLabel}>Transaction</Text>
          </Pressable>

          <Pressable
            style={styles.actionButton}
            onPress={() => navigation.navigate('TransactionsTab' as never, {
              screen: 'DocumentScan',
            } as never)}
          >
            <View style={[styles.actionIcon, { backgroundColor: `${colors.warning}15` }]}>
              <Icon name="camera" size={24} color={colors.warning} />
            </View>
            <Text style={styles.actionLabel}>Scan Doc</Text>
          </Pressable>

          <Pressable
            style={styles.actionButton}
            onPress={() => navigation.navigate('MoreTab' as never, {
              screen: 'Analytics',
            } as never)}
          >
            <View style={[styles.actionIcon, { backgroundColor: `${colors.secondary}15` }]}>
              <Icon name="chart-box" size={24} color={colors.secondary} />
            </View>
            <Text style={styles.actionLabel}>Analytics</Text>
          </Pressable>
        </View>

        {/* Alerts Section */}
        <Text style={styles.sectionTitle}>Alerts</Text>
        <View style={styles.alertsContainer}>
          {overdueCount > 0 && (
            <Card
              style={styles.alertCard}
              variant="outlined"
              onPress={() => navigation.navigate('PaymentsTab' as never)}
            >
              <View style={styles.alertContent}>
                <View style={[styles.alertIcon, { backgroundColor: `${colors.danger}15` }]}>
                  <Icon name="alert-circle" size={24} color={colors.danger} />
                </View>
                <View style={styles.alertText}>
                  <Text style={styles.alertTitle}>Overdue Payments</Text>
                  <Text style={styles.alertDescription}>
                    {overdueCount} payment{overdueCount > 1 ? 's' : ''} overdue
                  </Text>
                </View>
                <Icon name="chevron-right" size={24} color={colors.onSurfaceVariant} />
              </View>
            </Card>
          )}

          {upcomingCount > 0 && (
            <Card
              style={styles.alertCard}
              variant="outlined"
              onPress={() => navigation.navigate('PaymentsTab' as never)}
            >
              <View style={styles.alertContent}>
                <View style={[styles.alertIcon, { backgroundColor: `${colors.warning}15` }]}>
                  <Icon name="clock-alert" size={24} color={colors.warning} />
                </View>
                <View style={styles.alertText}>
                  <Text style={styles.alertTitle}>Upcoming Payments</Text>
                  <Text style={styles.alertDescription}>
                    {upcomingCount} payment{upcomingCount > 1 ? 's' : ''} due soon
                  </Text>
                </View>
                <Icon name="chevron-right" size={24} color={colors.onSurfaceVariant} />
              </View>
            </Card>
          )}

          {lowStockCount > 0 && (
            <Card
              style={styles.alertCard}
              variant="outlined"
              onPress={() => navigation.navigate('InventoryTab' as never)}
            >
              <View style={styles.alertContent}>
                <View style={[styles.alertIcon, { backgroundColor: `${colors.warning}15` }]}>
                  <Icon name="package-variant" size={24} color={colors.warning} />
                </View>
                <View style={styles.alertText}>
                  <Text style={styles.alertTitle}>Low Stock Items</Text>
                  <Text style={styles.alertDescription}>
                    {lowStockCount} item{lowStockCount > 1 ? 's' : ''} need reorder
                  </Text>
                </View>
                <Icon name="chevron-right" size={24} color={colors.onSurfaceVariant} />
              </View>
            </Card>
          )}

          {overdueCount === 0 && upcomingCount === 0 && lowStockCount === 0 && (
            <Card style={styles.alertCard} variant="outlined">
              <View style={styles.alertContent}>
                <View style={[styles.alertIcon, { backgroundColor: `${colors.success}15` }]}>
                  <Icon name="check-circle" size={24} color={colors.success} />
                </View>
                <View style={styles.alertText}>
                  <Text style={styles.alertTitle}>All Clear</Text>
                  <Text style={styles.alertDescription}>
                    No pending alerts at this time
                  </Text>
                </View>
              </View>
            </Card>
          )}
        </View>

        {/* Sync Status */}
        {pendingActions > 0 && (
          <Card style={styles.syncCard} variant="outlined">
            <View style={styles.syncContent}>
              <Icon name="sync" size={20} color={colors.warning} />
              <Text style={styles.syncText}>
                {pendingActions} action{pendingActions > 1 ? 's' : ''} pending sync
              </Text>
            </View>
          </Card>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
  },
  greeting: {
    fontSize: 14,
    color: colors.onSurfaceVariant,
  },
  userName: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.onBackground,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  offlineBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: `${colors.warning}15`,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
    marginRight: spacing.sm,
  },
  offlineText: {
    fontSize: 12,
    color: colors.warning,
    marginLeft: spacing.xs,
    fontWeight: '500',
  },
  notificationBadge: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: colors.danger,
  },
  scrollContent: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xl,
  },
  kpiRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.onBackground,
    marginTop: spacing.lg,
    marginBottom: spacing.md,
  },
  actionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    alignItems: 'center',
    flex: 1,
  },
  actionIcon: {
    width: 56,
    height: 56,
    borderRadius: borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  actionLabel: {
    fontSize: 12,
    color: colors.onSurfaceVariant,
    fontWeight: '500',
  },
  alertsContainer: {
    gap: spacing.sm,
  },
  alertCard: {
    padding: spacing.md,
  },
  alertContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  alertIcon: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.sm,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  alertText: {
    flex: 1,
  },
  alertTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.onSurface,
  },
  alertDescription: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
    marginTop: 2,
  },
  syncCard: {
    marginTop: spacing.lg,
    padding: spacing.md,
    backgroundColor: `${colors.warning}10`,
    borderColor: colors.warning,
  },
  syncContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  syncText: {
    marginLeft: spacing.sm,
    fontSize: 14,
    color: colors.warning,
    fontWeight: '500',
  },
});

export default DashboardScreen;
```

---

## TASK 10: INVENTORY SCREENS

### 10.1 Inventory List Screen

**File:** `mobile/src/screens/inventory/InventoryListScreen.tsx`

```typescript
/**
 * Inventory List Screen
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
} from 'react-native';
import { Searchbar, FAB, Chip, Text } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useSelector, useDispatch } from 'react-redux';

import { RootState, AppDispatch } from '@store/index';
import { fetchMaterials, setFilters, clearFilters } from '@store/slices/inventorySlice';
import InventoryItem from '@components/lists/InventoryItem';
import EmptyState from '@components/common/EmptyState';
import LoadingSpinner from '@components/common/LoadingSpinner';
import { InventoryStackParamList } from '@types/navigation';
import { useOffline } from '@hooks/useOffline';
import { colors, spacing } from '@/app/theme';

type InventoryListNavigationProp = StackNavigationProp<
  InventoryStackParamList,
  'InventoryList'
>;

const InventoryListScreen: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation<InventoryListNavigationProp>();
  const { isOffline } = useOffline();

  const { materials, isLoading, filters, lastUpdated } = useSelector(
    (state: RootState) => state.inventory
  );

  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<string | null>(null);

  useEffect(() => {
    if (!lastUpdated || Date.now() - lastUpdated > 5 * 60 * 1000) {
      dispatch(fetchMaterials());
    }
  }, [dispatch, lastUpdated]);

  const onRefresh = useCallback(() => {
    if (!isOffline) {
      dispatch(fetchMaterials());
    }
  }, [dispatch, isOffline]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    dispatch(setFilters({ search: query }));
  };

  const handleFilterPress = (filter: string) => {
    if (activeFilter === filter) {
      setActiveFilter(null);
      dispatch(clearFilters());
    } else {
      setActiveFilter(filter);
      
      switch (filter) {
        case 'low':
          // Will filter in filteredMaterials
          break;
        case 'active':
          dispatch(setFilters({ state: 'active' }));
          break;
        case 'inactive':
          dispatch(setFilters({ state: 'inactive' }));
          break;
      }
    }
  };

  const filteredMaterials = materials.filter((material) => {
    // Search filter
    if (filters.search) {
      const query = filters.search.toLowerCase();
      const matchesSearch =
        material.name.toLowerCase().includes(query) ||
        material.reference.toLowerCase().includes(query) ||
        material.category.toLowerCase().includes(query);
      if (!matchesSearch) return false;
    }

    // State filter
    if (filters.state && material.state !== filters.state) {
      return false;
    }

    // Low stock filter
    if (activeFilter === 'low' && material.currentStock > material.minStock) {
      return false;
    }

    return true;
  });

  const handleItemPress = (id: string) => {
    navigation.navigate('InventoryDetail', { id });
  };

  const handleScanPress = () => {
    navigation.navigate('Scanner', { mode: 'lookup' });
  };

  const handleAddMovement = () => {
    navigation.navigate('Movement', {});
  };

  if (isLoading && materials.length === 0) {
    return <LoadingSpinner fullScreen message="Loading inventory..." />;
  }

  return (
    <View style={styles.container}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Searchbar
          placeholder="Search materials..."
          onChangeText={handleSearch}
          value={searchQuery}
          style={styles.searchbar}
          inputStyle={styles.searchInput}
          icon="magnify"
          traileringIcon="barcode-scan"
          onTraileringIconPress={handleScanPress}
        />
      </View>

      {/* Filter Chips */}
      <View style={styles.filtersContainer}>
        <Chip
          selected={activeFilter === 'low'}
          onPress={() => handleFilterPress('low')}
          style={styles.filterChip}
          showSelectedOverlay
        >
          Low Stock
        </Chip>
        <Chip
          selected={activeFilter === 'active'}
          onPress={() => handleFilterPress('active')}
          style={styles.filterChip}
          showSelectedOverlay
        >
          Active
        </Chip>
        <Chip
          selected={activeFilter === 'inactive'}
          onPress={() => handleFilterPress('inactive')}
          style={styles.filterChip}
          showSelectedOverlay
        >
          Inactive
        </Chip>
      </View>

      {/* Results Count */}
      <View style={styles.resultsContainer}>
        <Text style={styles.resultsText}>
          {filteredMaterials.length} item{filteredMaterials.length !== 1 ? 's' : ''}
        </Text>
        {isOffline && (
          <Text style={styles.offlineText}>Offline mode</Text>
        )}
      </View>

      {/* List */}
      <FlatList
        data={filteredMaterials}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <InventoryItem
            {...item}
            onPress={() => handleItemPress(item.id)}
          />
        )}
        refreshControl={
          <RefreshControl
            refreshing={isLoading}
            onRefresh={onRefresh}
            tintColor={colors.primary}
          />
        }
        contentContainerStyle={
          filteredMaterials.length === 0 ? styles.emptyContainer : styles.listContent
        }
        ListEmptyComponent={
          <EmptyState
            icon="package-variant"
            title="No materials found"
            description={
              searchQuery || activeFilter
                ? 'Try adjusting your search or filters'
                : 'Add your first material to get started'
            }
            actionLabel={searchQuery || activeFilter ? 'Clear filters' : undefined}
            onAction={
              searchQuery || activeFilter
                ? () => {
                    setSearchQuery('');
                    setActiveFilter(null);
                    dispatch(clearFilters());
                  }
                : undefined
            }
          />
        }
      />

      {/* FAB */}
      <FAB
        icon="plus"
        style={styles.fab}
        onPress={handleAddMovement}
        label="Movement"
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  searchContainer: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
  },
  searchbar: {
    backgroundColor: colors.surface,
    elevation: 0,
    borderWidth: 1,
    borderColor: colors.outlineVariant,
  },
  searchInput: {
    fontSize: 15,
  },
  filtersContainer: {
    flexDirection: 'row',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    gap: spacing.sm,
  },
  filterChip: {
    backgroundColor: colors.surface,
  },
  resultsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
  },
  resultsText: {
    fontSize: 13,
    color: colors.onSurfaceVariant,
  },
  offlineText: {
    fontSize: 12,
    color: colors.warning,
    fontWeight: '500',
  },
  listContent: {
    paddingBottom: 100,
  },
  emptyContainer: {
    flex: 1,
  },
  fab: {
    position: 'absolute',
    right: spacing.lg,
    bottom: spacing.lg,
    backgroundColor: colors.primary,
  },
});

export default InventoryListScreen;
```

---

## TASK 11: API SERVICES

### 11.1 API Client

**File:** `mobile/src/services/api/client.ts`

```typescript
/**
 * API Client Configuration
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import * as Keychain from 'react-native-keychain';
import Config from 'react-native-config';
import NetInfo from '@react-native-community/netinfo';

const API_URL = Config.API_URL || 'http://localhost:5000/api/v1';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // Check network connectivity
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) {
      throw new Error('No network connection');
    }

    // Add auth token
    try {
      const credentials = await Keychain.getGenericPassword({
        service: 'com.logiaccounting.tokens',
      });
      
      if (credentials) {
        const tokens = JSON.parse(credentials.password);
        config.headers.Authorization = `Bearer ${tokens.accessToken}`;
      }
    } catch (error) {
      console.error('Error getting auth token:', error);
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 - Token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const credentials = await Keychain.getGenericPassword({
          service: 'com.logiaccounting.tokens',
        });

        if (credentials) {
          const tokens = JSON.parse(credentials.password);
          
          // Refresh token
          const response = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: tokens.refreshToken,
          });

          const { accessToken, refreshToken } = response.data;

          // Store new tokens
          await Keychain.setGenericPassword(
            'tokens',
            JSON.stringify({ accessToken, refreshToken }),
            { service: 'com.logiaccounting.tokens' }
          );

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens
        await Keychain.resetGenericPassword({ service: 'com.logiaccounting.tokens' });
        // Navigate to login will be handled by auth state
      }
    }

    // Format error message
    const errorMessage =
      (error.response?.data as any)?.message ||
      error.message ||
      'An unexpected error occurred';

    return Promise.reject(new Error(errorMessage));
  }
);

export default api;
```

### 11.2 Inventory API

**File:** `mobile/src/services/api/inventory.ts`

```typescript
/**
 * Inventory API Service
 */

import api from './client';

export interface Material {
  id: string;
  reference: string;
  name: string;
  description?: string;
  category: string;
  location: string;
  currentStock: number;
  minStock: number;
  unitCost: number;
  state: 'active' | 'inactive' | 'depleted';
  updatedAt: string;
}

export interface Movement {
  id: string;
  materialId: string;
  projectId?: string;
  type: 'entry' | 'exit';
  quantity: number;
  date: string;
  notes?: string;
  createdBy: string;
}

export const inventoryApi = {
  /**
   * Get all materials
   */
  getMaterials: () => api.get<Material[]>('/materials'),

  /**
   * Get material by ID
   */
  getMaterial: (id: string) => api.get<Material>(`/materials/${id}`),

  /**
   * Get material by barcode/reference
   */
  getMaterialByBarcode: (barcode: string) =>
    api.get<Material>(`/materials/barcode/${barcode}`),

  /**
   * Create material
   */
  createMaterial: (material: Omit<Material, 'id' | 'updatedAt'>) =>
    api.post<Material>('/materials', material),

  /**
   * Update material
   */
  updateMaterial: (id: string, material: Partial<Material>) =>
    api.put<Material>(`/materials/${id}`, material),

  /**
   * Delete material
   */
  deleteMaterial: (id: string) => api.delete(`/materials/${id}`),

  /**
   * Get movements
   */
  getMovements: (materialId?: string) =>
    api.get<Movement[]>('/movements', {
      params: materialId ? { material_id: materialId } : undefined,
    }),

  /**
   * Create movement
   */
  createMovement: (movement: Omit<Movement, 'id' | 'createdBy'>) =>
    api.post<Movement>('/movements', movement),

  /**
   * Get categories
   */
  getCategories: () => api.get<string[]>('/materials/categories'),

  /**
   * Get locations
   */
  getLocations: () => api.get<string[]>('/materials/locations'),
};
```

---

## TASK 12: INTERNATIONALIZATION

### 12.1 i18n Configuration

**File:** `mobile/src/i18n/index.ts`

```typescript
/**
 * Internationalization Configuration
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as RNLocalize from 'react-native-localize';

import en from './locales/en.json';
import es from './locales/es.json';
import de from './locales/de.json';
import fr from './locales/fr.json';

const resources = {
  en: { translation: en },
  es: { translation: es },
  de: { translation: de },
  fr: { translation: fr },
};

const languageDetector = {
  type: 'languageDetector' as const,
  async: true,
  detect: (callback: (lang: string) => void) => {
    const locales = RNLocalize.getLocales();
    const bestLanguage = locales[0]?.languageCode || 'en';
    callback(bestLanguage);
  },
  init: () => {},
  cacheUserLanguage: () => {},
};

i18n
  .use(languageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    compatibilityJSON: 'v3',
    interpolation: {
      escapeValue: false,
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;
```

### 12.2 English Translations

**File:** `mobile/src/i18n/locales/en.json`

```json
{
  "common": {
    "loading": "Loading...",
    "error": "Error",
    "retry": "Retry",
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "search": "Search",
    "filter": "Filter",
    "all": "All",
    "offline": "Offline",
    "noData": "No data available"
  },
  "auth": {
    "login": "Sign In",
    "logout": "Sign Out",
    "email": "Email",
    "password": "Password",
    "forgotPassword": "Forgot Password?",
    "welcomeBack": "Welcome back",
    "signInContinue": "Sign in to continue",
    "biometric": {
      "faceId": "Face ID",
      "touchId": "Touch ID",
      "fingerprint": "Fingerprint",
      "authenticate": "Authenticate"
    },
    "pin": {
      "create": "Create PIN",
      "enter": "Enter PIN",
      "confirm": "Confirm PIN"
    }
  },
  "dashboard": {
    "title": "Dashboard",
    "greeting": {
      "morning": "Good morning",
      "afternoon": "Good afternoon",
      "evening": "Good evening"
    },
    "kpis": {
      "revenue": "Revenue",
      "expenses": "Expenses",
      "profit": "Profit",
      "cashFlow": "Cash Flow"
    },
    "quickActions": "Quick Actions",
    "alerts": "Alerts",
    "overduePayments": "Overdue Payments",
    "upcomingPayments": "Upcoming Payments",
    "lowStock": "Low Stock Items"
  },
  "inventory": {
    "title": "Inventory",
    "materials": "Materials",
    "movements": "Movements",
    "scan": "Scan",
    "addMovement": "Add Movement",
    "inStock": "In Stock",
    "lowStock": "Low Stock",
    "outOfStock": "Out of Stock",
    "entry": "Entry",
    "exit": "Exit"
  },
  "transactions": {
    "title": "Transactions",
    "income": "Income",
    "expense": "Expense",
    "newTransaction": "New Transaction",
    "scanDocument": "Scan Document"
  },
  "payments": {
    "title": "Payments",
    "pending": "Pending",
    "paid": "Paid",
    "overdue": "Overdue",
    "dueDate": "Due Date",
    "recordPayment": "Record Payment"
  },
  "settings": {
    "title": "Settings",
    "profile": "Profile",
    "security": "Security",
    "notifications": "Notifications",
    "language": "Language",
    "theme": "Theme",
    "sync": "Sync Status",
    "about": "About"
  }
}
```

---

## ✅ PHASE 11 COMPLETE CHECKLIST

| Component | Status |
|-----------|--------|
| Project Setup | ✅ |
| TypeScript Config | ✅ |
| Theme System | ✅ |
| Redux Store | ✅ |
| Auth Slice | ✅ |
| Settings Slice | ✅ |
| Sync Slice | ✅ |
| Inventory Slice | ✅ |
| Payments Slice | ✅ |
| RTK Query API | ✅ |
| Navigation Types | ✅ |
| App Navigator | ✅ |
| Auth Navigator | ✅ |
| Main Tab Navigator | ✅ |
| Stack Navigators | ✅ |
| Login Screen | ✅ |
| Biometric Screen | ✅ |
| PIN Screen | ✅ |
| Auth Service | ✅ |
| Biometric Service | ✅ |
| Common Components | ✅ |
| KPI Card | ✅ |
| Dashboard Screen | ✅ |
| Inventory List Screen | ✅ |
| API Client | ✅ |
| Inventory API | ✅ |
| i18n Setup | ✅ |
| English Translations | ✅ |

---

## 📱 REMAINING TASKS (Future Parts)

- Scanner Screen (Barcode/QR)
- Document Scanner Screen
- Transaction Screens
- Payment Screens
- Analytics Screen
- Settings Screens
- Push Notifications
- Offline Sync Engine
- SQLite Storage
- Testing

---

*Phase 11 Tasks Part 3 - LogiAccounting Pro*
*Core Screens and Components*
