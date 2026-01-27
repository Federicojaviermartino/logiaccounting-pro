/**
 * Inventory Detail Screen
 * Material details with movement history
 */

import React from 'react';
import { StyleSheet, View, ScrollView, Pressable } from 'react-native';
import { Text, useTheme, Button, Divider, Chip } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useSelector } from 'react-redux';

import { spacing, borderRadius, colors } from '@app/theme';
import { RootState } from '@store/index';
import { Card, LoadingSpinner } from '@components/common';
import type { InventoryStackScreenProps } from '@types/navigation';

type Props = InventoryStackScreenProps<'InventoryDetail'>;

export const InventoryDetailScreen: React.FC<Props> = ({ route, navigation }) => {
  const theme = useTheme();
  const { materialId } = route.params;

  const material = useSelector((state: RootState) =>
    state.inventory.materials.find((m) => m.id === materialId)
  );

  const movements = useSelector((state: RootState) =>
    state.inventory.movements.filter((m) => m.materialId === materialId)
  );

  if (!material) {
    return <LoadingSpinner fullScreen message="Loading material..." />;
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getStateColor = () => {
    switch (material.state) {
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

  const getStockStatus = () => {
    if (material.currentStock <= 0) {
      return { color: colors.error, label: 'Out of Stock', icon: 'alert-circle' };
    }
    if (material.currentStock <= material.minStock) {
      return { color: colors.warning, label: 'Low Stock', icon: 'alert' };
    }
    return { color: colors.success, label: 'In Stock', icon: 'check-circle' };
  };

  const stockStatus = getStockStatus();
  const totalValue = material.currentStock * material.unitCost;

  const handleStockEntry = () => {
    navigation.navigate('InventoryMovement', {
      materialId: material.id,
      type: 'entry',
    });
  };

  const handleStockExit = () => {
    navigation.navigate('InventoryMovement', {
      materialId: material.id,
      type: 'exit',
    });
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
        {/* Header Card */}
        <Card style={styles.headerCard}>
          <View style={styles.headerTop}>
            <View style={styles.headerInfo}>
              <Text
                variant="headlineSmall"
                style={[styles.name, { color: theme.colors.onSurface }]}
              >
                {material.name}
              </Text>
              <Text
                variant="bodyMedium"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                {material.reference}
              </Text>
            </View>
            <View
              style={[
                styles.stateBadge,
                { backgroundColor: getStateColor() + '20' },
              ]}
            >
              <View
                style={[styles.stateDot, { backgroundColor: getStateColor() }]}
              />
              <Text
                variant="labelMedium"
                style={{ color: getStateColor(), textTransform: 'capitalize' }}
              >
                {material.state}
              </Text>
            </View>
          </View>

          <View style={styles.stockSection}>
            <View style={styles.stockMain}>
              <Text
                variant="displaySmall"
                style={[styles.stockValue, { color: theme.colors.onSurface }]}
              >
                {material.currentStock}
              </Text>
              <Text
                variant="bodyMedium"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                units in stock
              </Text>
            </View>
            <View
              style={[
                styles.stockBadge,
                { backgroundColor: stockStatus.color + '15' },
              ]}
            >
              <Icon name={stockStatus.icon} size={16} color={stockStatus.color} />
              <Text variant="labelMedium" style={{ color: stockStatus.color }}>
                {stockStatus.label}
              </Text>
            </View>
          </View>

          <View style={styles.actionButtons}>
            <Button
              mode="contained"
              icon="plus"
              onPress={handleStockEntry}
              style={[styles.actionButton, { backgroundColor: colors.success }]}
            >
              Stock Entry
            </Button>
            <Button
              mode="contained"
              icon="minus"
              onPress={handleStockExit}
              style={[styles.actionButton, { backgroundColor: colors.warning }]}
              disabled={material.currentStock <= 0}
            >
              Stock Exit
            </Button>
          </View>
        </Card>

        {/* Details Card */}
        <Card style={styles.detailsCard}>
          <Text
            variant="titleMedium"
            style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
          >
            Details
          </Text>

          <View style={styles.detailRow}>
            <View style={styles.detailItem}>
              <Icon
                name="tag-outline"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
              <View>
                <Text
                  variant="labelSmall"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  Category
                </Text>
                <Text variant="bodyMedium" style={{ color: theme.colors.onSurface }}>
                  {material.category}
                </Text>
              </View>
            </View>
            <View style={styles.detailItem}>
              <Icon
                name="map-marker-outline"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
              <View>
                <Text
                  variant="labelSmall"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  Location
                </Text>
                <Text variant="bodyMedium" style={{ color: theme.colors.onSurface }}>
                  {material.location}
                </Text>
              </View>
            </View>
          </View>

          <Divider style={styles.divider} />

          <View style={styles.detailRow}>
            <View style={styles.detailItem}>
              <Icon
                name="currency-usd"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
              <View>
                <Text
                  variant="labelSmall"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  Unit Cost
                </Text>
                <Text variant="bodyMedium" style={{ color: theme.colors.onSurface }}>
                  {formatCurrency(material.unitCost)}
                </Text>
              </View>
            </View>
            <View style={styles.detailItem}>
              <Icon
                name="calculator"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
              <View>
                <Text
                  variant="labelSmall"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  Total Value
                </Text>
                <Text variant="bodyMedium" style={{ color: theme.colors.onSurface }}>
                  {formatCurrency(totalValue)}
                </Text>
              </View>
            </View>
          </View>

          <Divider style={styles.divider} />

          <View style={styles.detailRow}>
            <View style={styles.detailItem}>
              <Icon
                name="alert-outline"
                size={20}
                color={theme.colors.onSurfaceVariant}
              />
              <View>
                <Text
                  variant="labelSmall"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  Minimum Stock
                </Text>
                <Text variant="bodyMedium" style={{ color: theme.colors.onSurface }}>
                  {material.minStock} units
                </Text>
              </View>
            </View>
          </View>

          {material.description && (
            <>
              <Divider style={styles.divider} />
              <View style={styles.descriptionSection}>
                <Text
                  variant="labelSmall"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  Description
                </Text>
                <Text
                  variant="bodyMedium"
                  style={{ color: theme.colors.onSurface, marginTop: spacing.xs }}
                >
                  {material.description}
                </Text>
              </View>
            </>
          )}
        </Card>

        {/* Recent Movements */}
        <Card style={styles.movementsCard}>
          <View style={styles.movementsHeader}>
            <Text
              variant="titleMedium"
              style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
            >
              Recent Movements
            </Text>
            <Pressable>
              <Text variant="labelMedium" style={{ color: theme.colors.primary }}>
                See all
              </Text>
            </Pressable>
          </View>

          {movements.length > 0 ? (
            movements.slice(0, 5).map((movement, index) => (
              <View
                key={movement.id}
                style={[
                  styles.movementItem,
                  index < Math.min(movements.length - 1, 4) && {
                    borderBottomWidth: 1,
                    borderBottomColor: theme.colors.outlineVariant,
                  },
                ]}
              >
                <View
                  style={[
                    styles.movementIcon,
                    {
                      backgroundColor:
                        movement.type === 'entry'
                          ? colors.success + '20'
                          : colors.warning + '20',
                    },
                  ]}
                >
                  <Icon
                    name={
                      movement.type === 'entry'
                        ? 'arrow-down-bold'
                        : 'arrow-up-bold'
                    }
                    size={16}
                    color={movement.type === 'entry' ? colors.success : colors.warning}
                  />
                </View>
                <View style={styles.movementContent}>
                  <Text
                    variant="bodyMedium"
                    style={{ color: theme.colors.onSurface }}
                  >
                    {movement.type === 'entry' ? '+' : '-'}
                    {movement.quantity} units
                  </Text>
                  <Text
                    variant="bodySmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    {new Date(movement.date).toLocaleDateString()}
                  </Text>
                </View>
                {movement.notes && (
                  <Chip compact style={styles.noteChip}>
                    {movement.notes}
                  </Chip>
                )}
              </View>
            ))
          ) : (
            <Text
              variant="bodyMedium"
              style={{
                color: theme.colors.onSurfaceVariant,
                textAlign: 'center',
                padding: spacing.lg,
              }}
            >
              No movements recorded yet
            </Text>
          )}
        </Card>
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
  headerCard: {
    marginBottom: spacing.md,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.lg,
  },
  headerInfo: {
    flex: 1,
  },
  name: {
    fontWeight: '700',
    marginBottom: spacing.xxs,
  },
  stateBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
    gap: spacing.xxs,
  },
  stateDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  stockSection: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.lg,
  },
  stockMain: {
    alignItems: 'flex-start',
  },
  stockValue: {
    fontWeight: '700',
  },
  stockBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.lg,
    gap: spacing.xs,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  actionButton: {
    flex: 1,
  },
  detailsCard: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontWeight: '600',
    marginBottom: spacing.md,
  },
  detailRow: {
    flexDirection: 'row',
    gap: spacing.xl,
  },
  detailItem: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
  },
  divider: {
    marginVertical: spacing.md,
  },
  descriptionSection: {
    paddingTop: spacing.xs,
  },
  movementsCard: {
    marginBottom: spacing.md,
  },
  movementsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  movementItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    gap: spacing.md,
  },
  movementIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  movementContent: {
    flex: 1,
  },
  noteChip: {
    height: 24,
  },
});

export default InventoryDetailScreen;
