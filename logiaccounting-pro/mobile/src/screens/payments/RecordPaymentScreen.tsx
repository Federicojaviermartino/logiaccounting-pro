/**
 * Record Payment Screen
 * Mark payment as received/paid
 */

import React, { useState } from 'react';
import { StyleSheet, View, ScrollView, Pressable } from 'react-native';
import { Text, TextInput, Button, useTheme, HelperText } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSelector, useDispatch } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';
import { RootState, AppDispatch } from '@store/index';
import { recordPayment } from '@store/slices/paymentsSlice';
import { Card, LoadingSpinner } from '@components/common';
import type { PaymentsStackScreenProps } from '@types/navigation';

type Props = PaymentsStackScreenProps<'RecordPayment'>;

export const RecordPaymentScreen: React.FC<Props> = ({ route, navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const { paymentId } = route.params;

  const payment = useSelector((state: RootState) =>
    state.payments.payments.find((p) => p.id === paymentId)
  );

  const [paidDate, setPaidDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleSubmit = async () => {
    if (!paidDate) {
      setError('Please select a payment date');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await dispatch(
        recordPayment({
          id: payment.id,
          paidDate: new Date(paidDate).toISOString(),
        })
      ).unwrap();
      navigation.goBack();
    } catch (err: any) {
      setError(err.message || 'Failed to record payment');
    } finally {
      setIsSubmitting(false);
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
        {/* Payment Summary */}
        <Card style={styles.summaryCard}>
          <View style={styles.summaryHeader}>
            <View style={[styles.typeIcon, { backgroundColor: typeColor + '20' }]}>
              <Icon
                name={isReceivable ? 'arrow-down' : 'arrow-up'}
                size={24}
                color={typeColor}
              />
            </View>
            <View style={styles.summaryInfo}>
              <Text
                variant="titleMedium"
                style={[styles.summaryTitle, { color: theme.colors.onSurface }]}
              >
                {payment.description}
              </Text>
              <Text
                variant="bodySmall"
                style={{ color: theme.colors.onSurfaceVariant }}
              >
                {isReceivable ? payment.clientName : payment.vendorName}
              </Text>
            </View>
          </View>

          <View style={styles.amountContainer}>
            <Text variant="labelMedium" style={{ color: theme.colors.onSurfaceVariant }}>
              Amount to {isReceivable ? 'Receive' : 'Pay'}
            </Text>
            <Text
              variant="displaySmall"
              style={[styles.amount, { color: typeColor }]}
            >
              {formatCurrency(payment.amount)}
            </Text>
          </View>
        </Card>

        {/* Payment Details Form */}
        <Card style={styles.formCard}>
          <Text
            variant="titleMedium"
            style={[styles.formTitle, { color: theme.colors.onSurface }]}
          >
            Payment Details
          </Text>

          <TextInput
            label="Payment Date"
            value={paidDate}
            onChangeText={setPaidDate}
            mode="outlined"
            left={<TextInput.Icon icon="calendar" />}
            style={styles.input}
          />
          <HelperText type="info" visible>
            Date when the payment was received/made
          </HelperText>

          <TextInput
            label="Notes (optional)"
            value={notes}
            onChangeText={setNotes}
            mode="outlined"
            multiline
            numberOfLines={3}
            left={<TextInput.Icon icon="note-text-outline" />}
            style={styles.input}
            placeholder="Add any additional notes..."
          />

          {error && (
            <HelperText type="error" visible style={styles.errorText}>
              {error}
            </HelperText>
          )}
        </Card>

        {/* Confirmation */}
        <Card style={styles.confirmCard}>
          <View style={styles.confirmRow}>
            <Icon
              name="information-outline"
              size={20}
              color={theme.colors.primary}
            />
            <Text
              variant="bodyMedium"
              style={{ color: theme.colors.onSurfaceVariant, flex: 1 }}
            >
              This will mark the payment as{' '}
              <Text style={{ fontWeight: '600', color: colors.success }}>Paid</Text>{' '}
              and update your records accordingly.
            </Text>
          </View>
        </Card>
      </ScrollView>

      {/* Submit Button */}
      <View style={[styles.footer, { backgroundColor: theme.colors.surface }]}>
        <Button
          mode="outlined"
          onPress={() => navigation.goBack()}
          style={styles.footerButton}
          contentStyle={styles.buttonContent}
        >
          Cancel
        </Button>
        <Button
          mode="contained"
          onPress={handleSubmit}
          loading={isSubmitting}
          disabled={isSubmitting}
          icon="check"
          style={[styles.footerButton, { backgroundColor: colors.success }]}
          contentStyle={styles.buttonContent}
        >
          Confirm Payment
        </Button>
      </View>
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
  summaryCard: {
    marginBottom: spacing.md,
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
    gap: spacing.md,
  },
  typeIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  summaryInfo: {
    flex: 1,
  },
  summaryTitle: {
    fontWeight: '600',
    marginBottom: spacing.xxs,
  },
  amountContainer: {
    alignItems: 'center',
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  amount: {
    fontWeight: '700',
    marginTop: spacing.xs,
  },
  formCard: {
    marginBottom: spacing.md,
  },
  formTitle: {
    fontWeight: '600',
    marginBottom: spacing.lg,
  },
  input: {
    marginBottom: spacing.xs,
  },
  errorText: {
    marginTop: spacing.sm,
  },
  confirmCard: {
    backgroundColor: 'rgba(0, 122, 255, 0.1)',
  },
  confirmRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
  },
  footer: {
    flexDirection: 'row',
    padding: spacing.md,
    gap: spacing.md,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  footerButton: {
    flex: 1,
    borderRadius: borderRadius.lg,
  },
  buttonContent: {
    paddingVertical: spacing.xs,
  },
});

export default RecordPaymentScreen;
