/**
 * Add Material Screen
 * Form to add new material to inventory
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
  SegmentedButtons,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';

import { spacing, borderRadius } from '@app/theme';
import { Card } from '@components/common';
import type { InventoryStackScreenProps } from '@types/navigation';

type Props = InventoryStackScreenProps<'AddMaterial'>;

interface FormData {
  reference: string;
  name: string;
  description: string;
  category: string;
  location: string;
  initialStock: string;
  minStock: string;
  unitCost: string;
}

interface FormErrors {
  reference?: string;
  name?: string;
  category?: string;
  location?: string;
  initialStock?: string;
  minStock?: string;
  unitCost?: string;
}

export const AddMaterialScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();

  const [formData, setFormData] = useState<FormData>({
    reference: '',
    name: '',
    description: '',
    category: '',
    location: '',
    initialStock: '0',
    minStock: '10',
    unitCost: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('raw_materials');

  const categories = [
    { value: 'raw_materials', label: 'Raw Materials' },
    { value: 'components', label: 'Components' },
    { value: 'finished', label: 'Finished' },
    { value: 'tools', label: 'Tools' },
  ];

  const updateField = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.reference.trim()) {
      newErrors.reference = 'Reference is required';
    }
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.location.trim()) {
      newErrors.location = 'Location is required';
    }
    if (!formData.unitCost || isNaN(parseFloat(formData.unitCost))) {
      newErrors.unitCost = 'Valid unit cost is required';
    }
    if (formData.initialStock && isNaN(parseInt(formData.initialStock, 10))) {
      newErrors.initialStock = 'Must be a valid number';
    }
    if (formData.minStock && isNaN(parseInt(formData.minStock, 10))) {
      newErrors.minStock = 'Must be a valid number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      // API call to create material
      await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulated
      navigation.goBack();
    } catch (err) {
      // Handle error
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
          {/* Basic Info */}
          <Card style={styles.card}>
            <Text
              variant="titleMedium"
              style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
            >
              Basic Information
            </Text>

            <TextInput
              label="Reference Code *"
              value={formData.reference}
              onChangeText={(text) => updateField('reference', text)}
              mode="outlined"
              error={!!errors.reference}
              left={<TextInput.Icon icon="tag-outline" />}
              style={styles.input}
              placeholder="e.g., REF-001"
            />
            <HelperText type="error" visible={!!errors.reference}>
              {errors.reference}
            </HelperText>

            <TextInput
              label="Name *"
              value={formData.name}
              onChangeText={(text) => updateField('name', text)}
              mode="outlined"
              error={!!errors.name}
              left={<TextInput.Icon icon="package-variant" />}
              style={styles.input}
              placeholder="e.g., Steel Rods"
            />
            <HelperText type="error" visible={!!errors.name}>
              {errors.name}
            </HelperText>

            <TextInput
              label="Description"
              value={formData.description}
              onChangeText={(text) => updateField('description', text)}
              mode="outlined"
              multiline
              numberOfLines={3}
              left={<TextInput.Icon icon="text" />}
              style={styles.input}
              placeholder="Optional description..."
            />
          </Card>

          {/* Category */}
          <Card style={styles.card}>
            <Text
              variant="titleMedium"
              style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
            >
              Category
            </Text>
            <SegmentedButtons
              value={selectedCategory}
              onValueChange={setSelectedCategory}
              buttons={categories}
              style={styles.segmentedButtons}
            />
          </Card>

          {/* Location & Stock */}
          <Card style={styles.card}>
            <Text
              variant="titleMedium"
              style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
            >
              Stock Details
            </Text>

            <TextInput
              label="Storage Location *"
              value={formData.location}
              onChangeText={(text) => updateField('location', text)}
              mode="outlined"
              error={!!errors.location}
              left={<TextInput.Icon icon="map-marker-outline" />}
              style={styles.input}
              placeholder="e.g., Warehouse A, Shelf B3"
            />
            <HelperText type="error" visible={!!errors.location}>
              {errors.location}
            </HelperText>

            <View style={styles.row}>
              <View style={styles.halfInput}>
                <TextInput
                  label="Initial Stock"
                  value={formData.initialStock}
                  onChangeText={(text) =>
                    updateField('initialStock', text.replace(/[^0-9]/g, ''))
                  }
                  mode="outlined"
                  keyboardType="numeric"
                  error={!!errors.initialStock}
                  right={<TextInput.Affix text="units" />}
                  style={styles.input}
                />
                <HelperText type="error" visible={!!errors.initialStock}>
                  {errors.initialStock}
                </HelperText>
              </View>
              <View style={styles.halfInput}>
                <TextInput
                  label="Minimum Stock"
                  value={formData.minStock}
                  onChangeText={(text) =>
                    updateField('minStock', text.replace(/[^0-9]/g, ''))
                  }
                  mode="outlined"
                  keyboardType="numeric"
                  error={!!errors.minStock}
                  right={<TextInput.Affix text="units" />}
                  style={styles.input}
                />
                <HelperText type="error" visible={!!errors.minStock}>
                  {errors.minStock}
                </HelperText>
              </View>
            </View>
          </Card>

          {/* Pricing */}
          <Card style={styles.card}>
            <Text
              variant="titleMedium"
              style={[styles.sectionTitle, { color: theme.colors.onSurface }]}
            >
              Pricing
            </Text>

            <TextInput
              label="Unit Cost *"
              value={formData.unitCost}
              onChangeText={(text) =>
                updateField('unitCost', text.replace(/[^0-9.]/g, ''))
              }
              mode="outlined"
              keyboardType="decimal-pad"
              error={!!errors.unitCost}
              left={<TextInput.Icon icon="currency-usd" />}
              style={styles.input}
              placeholder="0.00"
            />
            <HelperText type="error" visible={!!errors.unitCost}>
              {errors.unitCost}
            </HelperText>
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
            style={styles.footerButton}
            contentStyle={styles.buttonContent}
          >
            Add Material
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
  card: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontWeight: '600',
    marginBottom: spacing.md,
  },
  input: {
    marginBottom: spacing.xxs,
  },
  segmentedButtons: {
    // Styling
  },
  row: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  halfInput: {
    flex: 1,
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

export default AddMaterialScreen;
