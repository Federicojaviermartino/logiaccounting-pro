/**
 * Quick Actions Screen
 * Extended list of quick actions
 */

import React from 'react';
import { StyleSheet, View, ScrollView, Pressable } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';
import type { DashboardStackScreenProps } from '@types/navigation';

type Props = DashboardStackScreenProps<'QuickActions'>;

interface ActionGroup {
  title: string;
  actions: {
    icon: string;
    label: string;
    description: string;
    color: string;
    screen: string;
    params?: object;
  }[];
}

const actionGroups: ActionGroup[] = [
  {
    title: 'Inventory',
    actions: [
      {
        icon: 'package-variant-plus',
        label: 'Stock Entry',
        description: 'Add items to inventory',
        color: colors.success,
        screen: 'InventoryTab',
        params: { screen: 'AddMaterial' },
      },
      {
        icon: 'package-variant-minus',
        label: 'Stock Exit',
        description: 'Remove items from inventory',
        color: colors.warning,
        screen: 'InventoryTab',
      },
      {
        icon: 'barcode-scan',
        label: 'Scan Barcode',
        description: 'Quick lookup by barcode',
        color: colors.info,
        screen: 'InventoryTab',
        params: { screen: 'BarcodeScanner' },
      },
    ],
  },
  {
    title: 'Transactions',
    actions: [
      {
        icon: 'cash-plus',
        label: 'Add Income',
        description: 'Record incoming payment',
        color: colors.success,
        screen: 'TransactionsTab',
        params: { screen: 'AddTransaction', params: { type: 'income' } },
      },
      {
        icon: 'cash-minus',
        label: 'Add Expense',
        description: 'Record outgoing payment',
        color: colors.error,
        screen: 'TransactionsTab',
        params: { screen: 'AddTransaction', params: { type: 'expense' } },
      },
      {
        icon: 'camera',
        label: 'Scan Receipt',
        description: 'Capture receipt with camera',
        color: colors.info,
        screen: 'TransactionsTab',
        params: { screen: 'ScanReceipt' },
      },
    ],
  },
  {
    title: 'Payments',
    actions: [
      {
        icon: 'cash-check',
        label: 'Record Payment',
        description: 'Mark payment as received',
        color: colors.success,
        screen: 'PaymentsTab',
      },
      {
        icon: 'file-document-plus',
        label: 'New Receivable',
        description: 'Create new account receivable',
        color: colors.primary,
        screen: 'PaymentsTab',
        params: { screen: 'AddPayment', params: { type: 'receivable' } },
      },
      {
        icon: 'file-document-minus',
        label: 'New Payable',
        description: 'Create new account payable',
        color: colors.warning,
        screen: 'PaymentsTab',
        params: { screen: 'AddPayment', params: { type: 'payable' } },
      },
    ],
  },
];

export const QuickActionsScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();

  const handleAction = (action: ActionGroup['actions'][0]) => {
    navigation.navigate(action.screen as any, action.params);
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
        {actionGroups.map((group, groupIndex) => (
          <View key={groupIndex} style={styles.group}>
            <Text
              variant="titleMedium"
              style={[styles.groupTitle, { color: theme.colors.onSurface }]}
            >
              {group.title}
            </Text>
            <View style={styles.actionsContainer}>
              {group.actions.map((action, actionIndex) => (
                <Pressable
                  key={actionIndex}
                  onPress={() => handleAction(action)}
                  style={({ pressed }) => [
                    styles.actionCard,
                    { backgroundColor: theme.colors.surface },
                    pressed && { opacity: 0.8, transform: [{ scale: 0.98 }] },
                  ]}
                >
                  <View
                    style={[
                      styles.iconContainer,
                      { backgroundColor: action.color + '20' },
                    ]}
                  >
                    <Icon name={action.icon} size={28} color={action.color} />
                  </View>
                  <View style={styles.actionContent}>
                    <Text
                      variant="titleSmall"
                      style={{ color: theme.colors.onSurface }}
                    >
                      {action.label}
                    </Text>
                    <Text
                      variant="bodySmall"
                      style={{ color: theme.colors.onSurfaceVariant }}
                    >
                      {action.description}
                    </Text>
                  </View>
                  <Icon
                    name="chevron-right"
                    size={24}
                    color={theme.colors.onSurfaceVariant}
                  />
                </Pressable>
              ))}
            </View>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: spacing.lg,
  },
  group: {
    marginBottom: spacing.xl,
  },
  groupTitle: {
    fontWeight: '600',
    marginBottom: spacing.md,
  },
  actionsContainer: {
    gap: spacing.sm,
  },
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    gap: spacing.md,
  },
  iconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionContent: {
    flex: 1,
    gap: spacing.xxs,
  },
});

export default QuickActionsScreen;
