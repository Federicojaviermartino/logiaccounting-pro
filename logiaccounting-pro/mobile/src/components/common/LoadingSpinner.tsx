/**
 * Loading Spinner Component
 * Displays loading states with optional message
 */

import React from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';
import { ActivityIndicator, Text, useTheme } from 'react-native-paper';
import { spacing } from '@app/theme';

interface LoadingSpinnerProps {
  size?: 'small' | 'large';
  message?: string;
  color?: string;
  fullScreen?: boolean;
  style?: ViewStyle;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'large',
  message,
  color,
  fullScreen = false,
  style,
}) => {
  const theme = useTheme();

  const containerStyle: ViewStyle[] = [
    styles.container,
    fullScreen && styles.fullScreen,
    fullScreen && { backgroundColor: theme.colors.background },
    style,
  ].filter(Boolean) as ViewStyle[];

  return (
    <View style={containerStyle}>
      <ActivityIndicator
        size={size}
        color={color || theme.colors.primary}
        animating
      />
      {message && (
        <Text
          variant="bodyMedium"
          style={[styles.message, { color: theme.colors.onSurfaceVariant }]}
        >
          {message}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  fullScreen: {
    flex: 1,
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 999,
  },
  message: {
    marginTop: spacing.md,
    textAlign: 'center',
  },
});

export default LoadingSpinner;
