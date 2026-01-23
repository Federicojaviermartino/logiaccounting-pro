/**
 * Badge Component - Status badges and labels
 */

import { View, Text, StyleSheet, ViewStyle } from 'react-native';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info';
type BadgeSize = 'sm' | 'md';

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  size?: BadgeSize;
  style?: ViewStyle;
}

const VARIANTS = {
  default: {
    backgroundColor: '#F3F4F6',
    textColor: '#6B7280',
  },
  success: {
    backgroundColor: '#D1FAE5',
    textColor: '#059669',
  },
  warning: {
    backgroundColor: '#FEF3C7',
    textColor: '#D97706',
  },
  error: {
    backgroundColor: '#FEE2E2',
    textColor: '#DC2626',
  },
  info: {
    backgroundColor: '#DBEAFE',
    textColor: '#2563EB',
  },
};

export function Badge({ label, variant = 'default', size = 'md', style }: BadgeProps) {
  const colors = VARIANTS[variant];

  return (
    <View
      style={[
        styles.container,
        size === 'sm' ? styles.containerSm : styles.containerMd,
        { backgroundColor: colors.backgroundColor },
        style,
      ]}
    >
      <Text
        style={[
          styles.text,
          size === 'sm' ? styles.textSm : styles.textMd,
          { color: colors.textColor },
        ]}
      >
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 100,
    alignSelf: 'flex-start',
  },
  containerSm: {
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  containerMd: {
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  text: {
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  textSm: {
    fontSize: 10,
  },
  textMd: {
    fontSize: 12,
  },
});
