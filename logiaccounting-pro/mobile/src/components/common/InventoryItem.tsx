/**
 * Inventory Item Component
 * Displays material information in a list
 */

import React from 'react';
import { StyleSheet, View, Pressable } from 'react-native';
import { Text, useTheme, Badge } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';

interface InventoryItemProps {
  id: string;
  name: string;
  reference: string;
  category: string;
  currentStock: number;
  minStock: number;
  unitCost: number;
  location: string;
  state: 'active' | 'inactive' | 'depleted';
  onPress?: () => void;
}

export const InventoryItem: React.FC<InventoryItemProps> = ({
  name,
  reference,
  category,
  currentStock,
  minStock,
  unitCost,
  location,
  state,
  onPress,
}) => {
  const theme = useTheme();

  const getStockStatus = () => {
    if (currentStock <= 0) {
      return { color: colors.error, label: 'Out of Stock', icon: 'alert-circle' };
    }
    if (currentStock <= minStock) {
      return { color: colors.warning, label: 'Low Stock', icon: 'alert' };
    }
    return { color: colors.success, label: 'In Stock', icon: 'check-circle' };
  };

  const getStateColor = () => {
    switch (state) {
      case 'active':
        return colors.success;
      case 'inactive':
        return theme.colors.outline;
      case 'depleted':
        return colors.error;
      default:
        return theme.colors.outline;
    }
  };

  const stockStatus = getStockStatus();

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.container,
        { backgroundColor: theme.colors.surface },
        pressed && styles.pressed,
      ]}
    >
      <View style={styles.content}>
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <Text
              variant="titleMedium"
              style={[styles.name, { color: theme.colors.onSurface }]}
              numberOfLines={1}
            >
              {name}
            </Text>
            <View
              style={[styles.stateBadge, { backgroundColor: getStateColor() + '20' }]}
            >
              <View style={[styles.stateDot, { backgroundColor: getStateColor() }]} />
              <Text
                variant="labelSmall"
                style={{ color: getStateColor(), textTransform: 'capitalize' }}
              >
                {state}
              </Text>
            </View>
          </View>
          <Text
            variant="bodySmall"
            style={[styles.reference, { color: theme.colors.onSurfaceVariant }]}
          >
            {reference} • {category}
          </Text>
        </View>

        <View style={styles.details}>
          <View style={styles.detailItem}>
            <Icon name="package-variant" size={16} color={theme.colors.onSurfaceVariant} />
            <Text variant="bodyMedium" style={{ color: theme.colors.onSurface }}>
              {currentStock} units
            </Text>
          </View>
          <View style={styles.detailItem}>
            <Icon name="map-marker" size={16} color={theme.colors.onSurfaceVariant} />
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {location}
            </Text>
          </View>
          <View style={styles.detailItem}>
            <Icon name="currency-usd" size={16} color={theme.colors.onSurfaceVariant} />
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
              {formatCurrency(unitCost)}
            </Text>
          </View>
        </View>

        <View style={styles.footer}>
          <View style={[styles.stockStatus, { backgroundColor: stockStatus.color + '15' }]}>
            <Icon name={stockStatus.icon} size={14} color={stockStatus.color} />
            <Text variant="labelSmall" style={{ color: stockStatus.color }}>
              {stockStatus.label}
            </Text>
          </View>
          {currentStock <= minStock && (
            <Text
              variant="labelSmall"
              style={{ color: theme.colors.onSurfaceVariant }}
            >
              Min: {minStock}
            </Text>
          )}
        </View>
      </View>

      <Icon
        name="chevron-right"
        size={24}
        color={theme.colors.onSurfaceVariant}
        style={styles.chevron}
      />
    </Pressable>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.sm,
  },
  pressed: {
    opacity: 0.8,
  },
  content: {
    flex: 1,
  },
  header: {
    marginBottom: spacing.sm,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xxs,
  },
  name: {
    fontWeight: '600',
    flex: 1,
    marginRight: spacing.sm,
  },
  stateBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
    borderRadius: borderRadius.full,
    gap: spacing.xxs,
  },
  stateDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  reference: {
    fontWeight: '400',
  },
  details: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
    marginBottom: spacing.sm,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xxs,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  stockStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
    borderRadius: borderRadius.sm,
    gap: spacing.xxs,
  },
  chevron: {
    marginLeft: spacing.sm,
  },
});

export default InventoryItem;
