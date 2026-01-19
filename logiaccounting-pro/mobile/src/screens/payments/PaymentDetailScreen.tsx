/**
 * Payment Detail Screen
 * View payment details and record payment
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
import type { PaymentsStackScreenProps } from '@types/navigation';

type Props = PaymentsStackScreenProps<'PaymentDetail'>;

export const PaymentDetailScreen: React.FC<Props> = ({ route, navigation }) => {
  const theme = useTheme();
  const { paymentId } = route.params;

  const payment = useSelector((state: RootState) =>
    state.payments.payments.find((p) => p.id === paymentId)
  );

  if (!payment) {
    return <LoadingSpinner fullScreen message="Loading payment..." />;
  }

  const isReceivable = payment.type === 'receivable';
  const typeColor = isReceivable ? colors.success : colors.warning;

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return colors.success;
      case 'overdue':
        return colors.error;
      case 'pending':
        return colors.warning;
      case 'cancelled':
        return theme.colors.outline;
      default:
        return theme.colors.outline;
    }
  };

  const statusColor = getStatusColor(payment.status);

  const handleRecordPayment = () => {
    navigation.navigate('RecordPayment', { paymentId: payment.id });
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
            <View style={[styles.typeIcon, { backgroundColor: typeColor + '20' }]}>
              <Icon
                name={isReceivable ? 'arrow-down-bold' : 'arrow-up-bold'}
                size={32}
                color={typeColor}
              />
            </View>
            <View style={[styles.statusBadge, { backgroundColor: statusColor + '20' }]}>
              <Text
                variant="labelMedium"
                style={{ color: statusColor, textTransform: 'uppercase' }}
              >
                {payment.status}
              </Text>
            </View>
          </View>

          <Text
            variant="displaySmall"
            style={[styles.amount, { color: typeColor }]}
          >
            {formatCurrency(payment.amount)}
          </Text>

          <Text
            variant="titleMedium"
            style={[styles.description, { color: theme.colors.onSurface }]}
          >
            {payment.description}
          </Text>

          <Text
            variant="bodyMedium"
            style={{ color: theme.colors.onSurfaceVariant }}
          >
            {isReceivable ? payment.clientName : payment.vendorName}
          </Text>
        </Card>

        {/* Due Date Card */}
        <Card style={styles.dateCard}>
          <View style={styles.dateRow}>
            <View style={styles.dateItem}>
              <Icon name="calendar-clock" size={24} color={theme.colors.primary} />
              <View>
                <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  Due Date
                </Text>
                <Text variant="bodyLarge" style={{ color: theme.colors.onSurface }}>
                  {formatDate(payment.dueDate)}
                </Text>
              </View>
            </View>
            {payment.paidDate && (
              <View style={styles.dateItem}>
                <Icon name="calendar-check" size={24} color={colors.success} />
                <View>
                  <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                    Paid Date
                  </Text>
                  <Text variant="bodyLarge" style={{ color: colors.success }}>
                    {formatDate(payment.paidDate)}
                  </Text>
                </View>
              </View>
            )}
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
            <Icon name="swap-horizontal" size={20} color={theme.colors.onSurfaceVariant} />
            <View style={styles.detailContent}>
              <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                Type
              </Text>
              <Text variant="bodyLarge" style={{ color: theme.colors.onSurface }}>
                {isReceivable ? 'Account Receivable' : 'Account Payable'}
              </Text>
            </View>
          </View>

          <Divider style={styles.divider} />

          <View style={styles.detailRow}>
            <Icon
              name={isReceivable ? 'account' : 'store'}
              size={20}
              color={theme.colors.onSurfaceVariant}
            />
            <View style={styles.detailContent}>
              <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
                {isReceivable ? 'Client' : 'Vendor'}
              </Text>
              <Text variant="bodyLarge" style={{ color: theme.colors.onSurface }}>
                {isReceivable ? payment.clientName : payment.vendorName}
              </Text>
            </View>
          </View>
        </Card>

        {/* Actions */}
        {payment.status !== 'paid' && payment.status !== 'cancelled' && (
          <View style={styles.actions}>
            <Button
              mode="contained"
              icon="check"
              onPress={handleRecordPayment}
              style={[styles.recordButton, { backgroundColor: colors.success }]}
              contentStyle={styles.buttonContent}
            >
              Record Payment
            </Button>
          </View>
        )}

        <View style={styles.secondaryActions}>
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
  statusBadge: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.full,
  },
  amount: {
    fontWeight: '700',
    marginBottom: spacing.sm,
  },
  description: {
    fontWeight: '600',
    marginBottom: spacing.xs,
    textAlign: 'center',
  },
  dateCard: {
    marginBottom: spacing.md,
  },
  dateRow: {
    flexDirection: 'row',
    gap: spacing.xl,
  },
  dateItem: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.md,
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
    marginBottom: spacing.md,
  },
  recordButton: {
    borderRadius: borderRadius.lg,
  },
  buttonContent: {
    paddingVertical: spacing.sm,
  },
  secondaryActions: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  actionButton: {
    flex: 1,
    borderRadius: borderRadius.lg,
  },
});

export default PaymentDetailScreen;
