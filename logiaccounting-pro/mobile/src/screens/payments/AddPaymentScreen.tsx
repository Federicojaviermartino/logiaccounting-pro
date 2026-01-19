/**
 * Add Payment Screen
 * Create new receivable or payable
 */

import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  useTheme,
  HelperText,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';
import { Card } from '@components/common';
import type { PaymentsStackScreenProps } from '@types/navigation';

type Props = PaymentsStackScreenProps<'AddPayment'>;

export const AddPaymentScreen: React.FC<Props> = ({ route, navigation }) => {
  const theme = useTheme();
  const { type } = route.params;

  const isReceivable = type === 'receivable';
  const typeColor = isReceivable ? colors.success : colors.warning;

  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [contactName, setContactName] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!amount || isNaN(parseFloat(amount)) || parseFloat(amount) <= 0) {
      newErrors.amount = 'Please enter a valid amount';
    }
    if (!description.trim()) {
      newErrors.description = 'Description is required';
    }
    if (!contactName.trim()) {
      newErrors.contactName = isReceivable
        ? 'Client name is required'
        : 'Vendor name is required';
    }
    if (!dueDate) {
      newErrors.dueDate = 'Due date is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      // API call to create payment
      await new Promise((resolve) => setTimeout(resolve, 1000));
      navigation.goBack();
    } catch (err) {
      setErrors({ submit: 'Failed to create payment' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      edges={['bottom']}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Type Indicator */}
          <Card style={[styles.typeCard, { backgroundColor: typeColor + '15' }]}>
            <View style={styles.typeContent}>
              <View style={[styles.typeIcon, { backgroundColor: typeColor + '30' }]}>
                <Icon
                  name={isReceivable ? 'arrow-down-bold' : 'arrow-up-bold'}
                  size={28}
                  color={typeColor}
                />
              </View>
              <View>
                <Text
                  variant="titleMedium"
                  style={[styles.typeTitle, { color: typeColor }]}
                >
                  New {isReceivable ? 'Account Receivable' : 'Account Payable'}
                </Text>
                <Text
                  variant="bodySmall"
                  style={{ color: typeColor }}
                >
                  {isReceivable
                    ? 'Money to be received from clients'
                    : 'Money to be paid to vendors'}
                </Text>
              </View>
            </View>
          </Card>

          {/* Amount */}
          <Card style={styles.card}>
            <Text
              variant="labelMedium"
              style={{ color: theme.colors.onSurfaceVariant, marginBottom: spacing.sm }}
            >
              Amount
            </Text>
            <View style={styles.amountContainer}>
              <Text
                variant="headlineLarge"
                style={{ color: typeColor, marginRight: spacing.sm }}
              >
                $
              </Text>
              <TextInput
                value={amount}
                onChangeText={(text) => {
                  setAmount(text.replace(/[^0-9.]/g, ''));
                  if (errors.amount) setErrors((e) => ({ ...e, amount: '' }));
                }}
                mode="flat"
                keyboardType="decimal-pad"
                placeholder="0.00"
                style={[styles.amountInput, { color: typeColor }]}
                error={!!errors.amount}
              />
            </View>
            <HelperText type="error" visible={!!errors.amount}>
              {errors.amount}
            </HelperText>
          </Card>

          {/* Details */}
          <Card style={styles.card}>
            <Text
              variant="titleMedium"
              style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
            >
              Details
            </Text>

            <TextInput
              label="Description *"
              value={description}
              onChangeText={(text) => {
                setDescription(text);
                if (errors.description) setErrors((e) => ({ ...e, description: '' }));
              }}
              mode="outlined"
              error={!!errors.description}
              style={styles.input}
              placeholder="e.g., Invoice for construction services"
            />
            <HelperText type="error" visible={!!errors.description}>
              {errors.description}
            </HelperText>

            <TextInput
              label={isReceivable ? 'Client Name *' : 'Vendor Name *'}
              value={contactName}
              onChangeText={(text) => {
                setContactName(text);
                if (errors.contactName) setErrors((e) => ({ ...e, contactName: '' }));
              }}
              mode="outlined"
              error={!!errors.contactName}
              left={<TextInput.Icon icon={isReceivable ? 'account' : 'store'} />}
              style={styles.input}
            />
            <HelperText type="error" visible={!!errors.contactName}>
              {errors.contactName}
            </HelperText>

            <TextInput
              label="Due Date *"
              value={dueDate}
              onChangeText={(text) => {
                setDueDate(text);
                if (errors.dueDate) setErrors((e) => ({ ...e, dueDate: '' }));
              }}
              mode="outlined"
              error={!!errors.dueDate}
              left={<TextInput.Icon icon="calendar" />}
              style={styles.input}
              placeholder="YYYY-MM-DD"
            />
            <HelperText type="error" visible={!!errors.dueDate}>
              {errors.dueDate}
            </HelperText>
          </Card>

          {errors.submit && (
            <HelperText type="error" visible style={styles.submitError}>
              {errors.submit}
            </HelperText>
          )}
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
            icon="plus"
            style={[styles.footerButton, { backgroundColor: typeColor }]}
            contentStyle={styles.buttonContent}
          >
            Create
          </Button>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    padding: spacing.md,
    paddingBottom: spacing.xxl,
  },
  typeCard: {
    marginBottom: spacing.md,
  },
  typeContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  typeIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  typeTitle: {
    fontWeight: '600',
    marginBottom: spacing.xxs,
  },
  card: {
    marginBottom: spacing.md,
  },
  amountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  amountInput: {
    flex: 1,
    backgroundColor: 'transparent',
    fontSize: 48,
  },
  sectionTitle: {
    fontWeight: '600',
    marginBottom: spacing.md,
  },
  input: {
    marginBottom: spacing.xxs,
  },
  submitError: {
    textAlign: 'center',
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

export default AddPaymentScreen;
