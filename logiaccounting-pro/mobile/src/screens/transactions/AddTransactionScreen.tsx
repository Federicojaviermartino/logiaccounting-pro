/**
 * Add Transaction Screen
 * Form to add new income or expense
 */

import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Pressable,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  useTheme,
  HelperText,
  SegmentedButtons,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useDispatch } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';
import { AppDispatch } from '@store/index';
import { createTransaction } from '@store/slices/transactionsSlice';
import { Card } from '@components/common';
import type { TransactionsStackScreenProps } from '@types/navigation';

type Props = TransactionsStackScreenProps<'AddTransaction'>;

const categories = {
  income: [
    { value: 'sales', label: 'Sales', icon: 'cart' },
    { value: 'services', label: 'Services', icon: 'tools' },
    { value: 'refunds', label: 'Refunds', icon: 'cash-refund' },
    { value: 'other_income', label: 'Other', icon: 'dots-horizontal' },
  ],
  expense: [
    { value: 'materials', label: 'Materials', icon: 'package-variant' },
    { value: 'labor', label: 'Labor', icon: 'account-hard-hat' },
    { value: 'utilities', label: 'Utilities', icon: 'flash' },
    { value: 'rent', label: 'Rent', icon: 'home' },
    { value: 'equipment', label: 'Equipment', icon: 'hammer-wrench' },
    { value: 'other_expense', label: 'Other', icon: 'dots-horizontal' },
  ],
};

export const AddTransactionScreen: React.FC<Props> = ({ route, navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();

  const initialType = route.params?.type || 'expense';

  const [type, setType] = useState<'income' | 'expense'>(initialType);
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [vendorName, setVendorName] = useState('');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const typeColor = type === 'income' ? colors.success : colors.error;
  const currentCategories = categories[type];

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!amount || isNaN(parseFloat(amount)) || parseFloat(amount) <= 0) {
      newErrors.amount = 'Please enter a valid amount';
    }
    if (!description.trim()) {
      newErrors.description = 'Description is required';
    }
    if (!category) {
      newErrors.category = 'Please select a category';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await dispatch(
        createTransaction({
          type,
          amount: parseFloat(amount),
          taxAmount: 0,
          description: description.trim(),
          category,
          date: new Date().toISOString(),
          vendorName: vendorName.trim() || undefined,
          invoiceNumber: invoiceNumber.trim() || undefined,
        })
      ).unwrap();
      navigation.goBack();
    } catch (err) {
      setErrors({ submit: 'Failed to create transaction' });
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
          {/* Type Selector */}
          <SegmentedButtons
            value={type}
            onValueChange={(value) => {
              setType(value as 'income' | 'expense');
              setCategory('');
            }}
            buttons={[
              {
                value: 'income',
                label: 'Income',
                icon: 'arrow-down',
              },
              {
                value: 'expense',
                label: 'Expense',
                icon: 'arrow-up',
              },
            ]}
            style={styles.typeSelector}
          />

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
                contentStyle={styles.amountInputContent}
                error={!!errors.amount}
              />
            </View>
            <HelperText type="error" visible={!!errors.amount}>
              {errors.amount}
            </HelperText>
          </Card>

          {/* Category */}
          <Card style={styles.card}>
            <Text
              variant="titleMedium"
              style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
            >
              Category
            </Text>
            <View style={styles.categoryGrid}>
              {currentCategories.map((cat) => (
                <Pressable
                  key={cat.value}
                  onPress={() => {
                    setCategory(cat.value);
                    if (errors.category) setErrors((e) => ({ ...e, category: '' }));
                  }}
                  style={({ pressed }) => [
                    styles.categoryItem,
                    {
                      backgroundColor:
                        category === cat.value
                          ? typeColor + '20'
                          : theme.colors.surfaceVariant,
                      borderColor:
                        category === cat.value ? typeColor : 'transparent',
                    },
                    pressed && { opacity: 0.8 },
                  ]}
                >
                  <Icon
                    name={cat.icon}
                    size={24}
                    color={category === cat.value ? typeColor : theme.colors.onSurfaceVariant}
                  />
                  <Text
                    variant="labelMedium"
                    style={{
                      color:
                        category === cat.value
                          ? typeColor
                          : theme.colors.onSurface,
                    }}
                  >
                    {cat.label}
                  </Text>
                </Pressable>
              ))}
            </View>
            <HelperText type="error" visible={!!errors.category}>
              {errors.category}
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
            />
            <HelperText type="error" visible={!!errors.description}>
              {errors.description}
            </HelperText>

            <TextInput
              label="Vendor/Client Name"
              value={vendorName}
              onChangeText={setVendorName}
              mode="outlined"
              style={styles.input}
            />

            <TextInput
              label="Invoice/Receipt Number"
              value={invoiceNumber}
              onChangeText={setInvoiceNumber}
              mode="outlined"
              style={styles.input}
            />
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
            mode="contained"
            onPress={handleSubmit}
            loading={isSubmitting}
            disabled={isSubmitting}
            style={[styles.submitButton, { backgroundColor: typeColor }]}
            contentStyle={styles.submitButtonContent}
            icon={type === 'income' ? 'plus' : 'minus'}
          >
            Add {type === 'income' ? 'Income' : 'Expense'}
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
  typeSelector: {
    marginBottom: spacing.md,
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
  amountInputContent: {
    paddingLeft: 0,
  },
  sectionTitle: {
    fontWeight: '600',
    marginBottom: spacing.md,
  },
  categoryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  categoryItem: {
    width: '31%',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 2,
    gap: spacing.xs,
  },
  input: {
    marginBottom: spacing.xs,
  },
  submitError: {
    textAlign: 'center',
  },
  footer: {
    padding: spacing.md,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  submitButton: {
    borderRadius: borderRadius.lg,
  },
  submitButtonContent: {
    paddingVertical: spacing.sm,
  },
});

export default AddTransactionScreen;
