/**
 * Transaction Detail Screen
 * View transaction details
 */

import React from 'react';
import { StyleSheet, View, ScrollView } from 'react-native';
import { Text, useTheme, Button, Divider } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useSelector } from 'react-redux';

import { spacing, borderRadius, colors } from '@app/theme';
import { RootState } from '@store/index';
import { Card, LoadingSpinner } from '@components/common';
import type { TransactionsStackScreenProps } from '@types/navigation';

type Props = TransactionsStackScreenProps<'TransactionDetail'>;

export const TransactionDetailScreen: React.FC<Props> = ({ route }) => {
  const theme = useTheme();
  const { transactionId } = route.params;

  const transaction = useSelector((state: RootState) =>
    state.transactions.transactions.find((t) => t.id === transactionId)
  );

  if (!transaction) {
    return <LoadingSpinner fullScreen message="Loading transaction..." />;
  }

  const isIncome = transaction.type === 'income';
  const typeColor = isIncome ? colors.success : colors.error;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
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
            <View
              style={[styles.typeIcon, { backgroundColor: typeColor + '20' }]}
            >
              <Icon
                name={isIncome ? 'arrow-down-bold' : 'arrow-up-bold'}
                size={32}
                color={typeColor}
              />
            </View>
            <View
              style={[styles.typeBadge, { backgroundColor: typeColor + '20' }]}
            >
              <Text
                variant="labelMedium"
                style={{ color: typeColor, textTransform: 'uppercase' }}
              >
                {transaction.type}
              </Text>
            </View>
          </View>

          <Text
            variant="displaySmall"
            style={[styles.amount, { color: typeColor }]}
          >
            {isIncome ? '+' : '-'}{formatCurrency(transaction.amount)}
          </Text>

          {transaction.taxAmount > 0 && (
            <Text
              variant="bodyMedium"
              style={{ color: theme.colors.onSurfaceVariant }}
            >
              Tax: {formatCurrency(transaction.taxAmount)}
            </Text>
          )}
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
            <Icon
              name="text"
              size={20}
              color={theme.colors.onSurfaceVariant}
            />
            <View style={styles.detailContent}>
              <Text
                variant="labelSmall"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                Description
              </Text>
              <Text
                variant="bodyLarge"
                style={{ color: theme.colors.onSurface }}
              >
                {transaction.description}
              </Text>
            </View>
          </View>

          <Divider style={styles.divider} />

          <View style={styles.detailRow}>
            <Icon
              name="tag-outline"
              size={20}
              color={theme.colors.onSurfaceVariant}
            />
            <View style={styles.detailContent}>
              <Text
                variant="labelSmall"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                Category
              </Text>
              <Text
                variant="bodyLarge"
                style={{ color: theme.colors.onSurface }}
              >
                {transaction.category}
              </Text>
            </View>
          </View>

          <Divider style={styles.divider} />

          <View style={styles.detailRow}>
            <Icon
              name="calendar"
              size={20}
              color={theme.colors.onSurfaceVariant}
            />
            <View style={styles.detailContent}>
              <Text
                variant="labelSmall"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                Date
              </Text>
              <Text
                variant="bodyLarge"
                style={{ color: theme.colors.onSurface }}
              >
                {formatDate(transaction.date)}
              </Text>
            </View>
          </View>

          {transaction.vendorName && (
            <>
              <Divider style={styles.divider} />
              <View style={styles.detailRow}>
                <Icon
                  name="store"
                  size={20}
                  color={theme.colors.onSurfaceVariant}
                />
                <View style={styles.detailContent}>
                  <Text
                    variant="labelSmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    Vendor
                  </Text>
                  <Text
                    variant="bodyLarge"
                    style={{ color: theme.colors.onSurface }}
                  >
                    {transaction.vendorName}
                  </Text>
                </View>
              </View>
            </>
          )}

          {transaction.invoiceNumber && (
            <>
              <Divider style={styles.divider} />
              <View style={styles.detailRow}>
                <Icon
                  name="file-document-outline"
                  size={20}
                  color={theme.colors.onSurfaceVariant}
                />
                <View style={styles.detailContent}>
                  <Text
                    variant="labelSmall"
                    style={{ color: theme.colors.onSurfaceVariant }}
                  >
                    Invoice Number
                  </Text>
                  <Text
                    variant="bodyLarge"
                    style={{ color: theme.colors.onSurface }}
                  >
                    {transaction.invoiceNumber}
                  </Text>
                </View>
              </View>
            </>
          )}
        </Card>

        {/* Actions */}
        <View style={styles.actions}>
          <Button
            mode="outlined"
            icon="pencil"
            onPress={() => {}}
            style={styles.actionButton}
          >
            Edit
          </Button>
          <Button
            mode="outlined"
            icon="delete"
            onPress={() => {}}
            style={styles.actionButton}
            textColor={colors.error}
          >
            Delete
          </Button>
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
  headerCard: {
    marginBottom: spacing.md,
    alignItems: 'center',
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: spacing.lg,
  },
  typeIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  typeBadge: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  amount: {
    fontWeight: '700',
    marginBottom: spacing.xs,
  },
  detailsCard: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontWeight: '600',
    marginBottom: spacing.lg,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
  },
  detailContent: {
    flex: 1,
  },
  divider: {
    marginVertical: spacing.md,
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  actionButton: {
    flex: 1,
    borderRadius: borderRadius.lg,
  },
});

export default TransactionDetailScreen;
