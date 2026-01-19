/**
 * Inventory Movement Screen
 * Record stock entry or exit
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
import { useSelector, useDispatch } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';
import { RootState, AppDispatch } from '@store/index';
import { createMovement } from '@store/slices/inventorySlice';
import { Card, LoadingSpinner } from '@components/common';
import type { InventoryStackScreenProps } from '@types/navigation';

type Props = InventoryStackScreenProps<'InventoryMovement'>;

export const InventoryMovementScreen: React.FC<Props> = ({ route, navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const { materialId, type } = route.params;

  const material = useSelector((state: RootState) =>
    state.inventory.materials.find((m) => m.id === materialId)
  );

  const [quantity, setQuantity] = useState('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!material) {
    return <LoadingSpinner fullScreen message="Loading..." />;
  }

  const isEntry = type === 'entry';
  const themeColor = isEntry ? colors.success : colors.warning;

  const validateQuantity = () => {
    const qty = parseInt(quantity, 10);
    if (!quantity || isNaN(qty) || qty <= 0) {
      setError('Please enter a valid quantity');
      return false;
    }
    if (!isEntry && qty > material.currentStock) {
      setError(`Cannot remove more than ${material.currentStock} units`);
      return false;
    }
    setError(null);
    return true;
  };

  const handleSubmit = async () => {
    if (!validateQuantity()) return;

    setIsSubmitting(true);
    try {
      await dispatch(
        createMovement({
          materialId: material.id,
          type,
          quantity: parseInt(quantity, 10),
          date: new Date().toISOString(),
          notes: notes.trim() || undefined,
        })
      ).unwrap();
      navigation.goBack();
    } catch (err: any) {
      setError(err.message || 'Failed to record movement');
    } finally {
      setIsSubmitting(false);
    }
  };

  const newStock = isEntry
    ? material.currentStock + (parseInt(quantity, 10) || 0)
    : material.currentStock - (parseInt(quantity, 10) || 0);

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
          {/* Material Info */}
          <Card style={styles.materialCard}>
            <View style={styles.materialHeader}>
              <View
                style={[
                  styles.typeIcon,
                  { backgroundColor: themeColor + '20' },
                ]}
              >
                <Icon
                  name={isEntry ? 'arrow-down-bold' : 'arrow-up-bold'}
                  size={28}
                  color={themeColor}
                />
              </View>
              <View style={styles.materialInfo}>
                <Text
                  variant="titleMedium"
                  style={[styles.materialName, { color: theme.colors.onSurface }]}
                >
                  {material.name}
                </Text>
                <Text
                  variant="bodySmall"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  {material.reference} • {material.category}
                </Text>
              </View>
            </View>

            <View style={styles.stockInfo}>
              <View style={styles.stockItem}>
                <Text
                  variant="labelSmall"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  Current Stock
                </Text>
                <Text
                  variant="titleLarge"
                  style={{ color: theme.colors.onSurface, fontWeight: '600' }}
                >
                  {material.currentStock}
                </Text>
              </View>
              <Icon
                name="arrow-right"
                size={24}
                color={theme.colors.onSurfaceVariant}
              />
              <View style={styles.stockItem}>
                <Text
                  variant="labelSmall"
                  style={{ color: theme.colors.onSurfaceVariant }}
                >
                  New Stock
                </Text>
                <Text
                  variant="titleLarge"
                  style={{
                    color: newStock < material.minStock ? colors.warning : colors.success,
                    fontWeight: '600',
                  }}
                >
                  {Math.max(0, newStock)}
                </Text>
              </View>
            </View>
          </Card>

          {/* Movement Form */}
          <Card style={styles.formCard}>
            <Text
              variant="titleMedium"
              style={[styles.formTitle, { color: theme.colors.onSurface }]}
            >
              {isEntry ? 'Stock Entry' : 'Stock Exit'} Details
            </Text>

            <TextInput
              label="Quantity"
              value={quantity}
              onChangeText={(text) => {
                setQuantity(text.replace(/[^0-9]/g, ''));
                if (error) setError(null);
              }}
              mode="outlined"
              keyboardType="numeric"
              error={!!error}
              left={<TextInput.Icon icon="package-variant" />}
              right={<TextInput.Affix text="units" />}
              style={styles.input}
            />
            <HelperText type="error" visible={!!error}>
              {error}
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
            />

            {!isEntry && material.currentStock <= material.minStock && (
              <View
                style={[
                  styles.warningBox,
                  { backgroundColor: colors.warning + '20' },
                ]}
              >
                <Icon name="alert" size={20} color={colors.warning} />
                <Text
                  variant="bodySmall"
                  style={{ color: colors.warning, flex: 1 }}
                >
                  Stock is already at or below minimum level ({material.minStock}{' '}
                  units)
                </Text>
              </View>
            )}
          </Card>
        </ScrollView>

        {/* Submit Button */}
        <View style={[styles.footer, { backgroundColor: theme.colors.surface }]}>
          <Button
            mode="contained"
            onPress={handleSubmit}
            loading={isSubmitting}
            disabled={isSubmitting || !quantity}
            icon={isEntry ? 'plus' : 'minus'}
            style={[styles.submitButton, { backgroundColor: themeColor }]}
            contentStyle={styles.submitButtonContent}
          >
            {isEntry ? 'Add to Stock' : 'Remove from Stock'}
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
  materialCard: {
    marginBottom: spacing.md,
  },
  materialHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
    gap: spacing.md,
  },
  typeIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  materialInfo: {
    flex: 1,
  },
  materialName: {
    fontWeight: '600',
    marginBottom: spacing.xxs,
  },
  stockInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  stockItem: {
    alignItems: 'center',
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
  warningBox: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: borderRadius.md,
    gap: spacing.sm,
    marginTop: spacing.md,
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

export default InventoryMovementScreen;
