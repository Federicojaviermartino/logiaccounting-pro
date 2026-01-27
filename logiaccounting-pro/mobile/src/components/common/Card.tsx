/**
 * Card Component
 * Reusable card container with consistent styling
 */

import React from 'react';
import { StyleSheet, View, ViewStyle, Pressable } from 'react-native';
import { useTheme, Surface } from 'react-native-paper';
import { spacing, borderRadius, shadows } from '@app/theme';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  onPress?: () => void;
  elevation?: 0 | 1 | 2 | 3 | 4 | 5;
  variant?: 'elevated' | 'outlined' | 'filled';
  padding?: keyof typeof spacing;
}

export const Card: React.FC<CardProps> = ({
  children,
  style,
  onPress,
  elevation = 1,
  variant = 'elevated',
  padding = 'md',
}) => {
  const theme = useTheme();

  const containerStyle: ViewStyle = {
    backgroundColor: variant === 'filled' ? theme.colors.surfaceVariant : theme.colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing[padding],
    ...(variant === 'outlined' && {
      borderWidth: 1,
      borderColor: theme.colors.outline,
    }),
    ...(variant === 'elevated' && shadows.sm),
  };

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        style={({ pressed }) => [
          containerStyle,
          pressed && styles.pressed,
          style,
        ]}
      >
        {children}
      </Pressable>
    );
  }

  return (
    <Surface elevation={elevation} style={[containerStyle, style]}>
      {children}
    </Surface>
  );
};

const styles = StyleSheet.create({
  pressed: {
    opacity: 0.9,
    transform: [{ scale: 0.98 }],
  },
});

export default Card;
