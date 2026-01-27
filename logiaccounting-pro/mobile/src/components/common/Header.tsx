/**
 * Header Component
 * Custom header with actions and optional subtitle
 */

import React from 'react';
import { StyleSheet, View, StatusBar, Platform } from 'react-native';
import { Text, IconButton, useTheme } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { spacing } from '@app/theme';

interface HeaderAction {
  icon: string;
  onPress: () => void;
  accessibilityLabel?: string;
}

interface HeaderProps {
  title: string;
  subtitle?: string;
  showBack?: boolean;
  onBack?: () => void;
  actions?: HeaderAction[];
  transparent?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  showBack = false,
  onBack,
  actions = [],
  transparent = false,
}) => {
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  return (
    <View
      style={[
        styles.container,
        {
          paddingTop: insets.top,
          backgroundColor: transparent ? 'transparent' : theme.colors.surface,
        },
      ]}
    >
      <View style={styles.content}>
        <View style={styles.leftSection}>
          {showBack && (
            <IconButton
              icon="arrow-left"
              onPress={onBack}
              iconColor={theme.colors.onSurface}
              size={24}
              style={styles.backButton}
            />
          )}
        </View>

        <View style={styles.titleSection}>
          <Text
            variant="titleLarge"
            style={[styles.title, { color: theme.colors.onSurface }]}
            numberOfLines={1}
          >
            {title}
          </Text>
          {subtitle && (
            <Text
              variant="bodySmall"
              style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
              numberOfLines={1}
            >
              {subtitle}
            </Text>
          )}
        </View>

        <View style={styles.actionsSection}>
          {actions.map((action, index) => (
            <IconButton
              key={index}
              icon={action.icon}
              onPress={action.onPress}
              iconColor={theme.colors.onSurface}
              size={24}
              accessibilityLabel={action.accessibilityLabel}
            />
          ))}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.sm,
    minHeight: 56,
  },
  leftSection: {
    width: 48,
    alignItems: 'flex-start',
  },
  backButton: {
    margin: 0,
  },
  titleSection: {
    flex: 1,
    alignItems: 'center',
  },
  title: {
    fontWeight: '600',
    textAlign: 'center',
  },
  subtitle: {
    textAlign: 'center',
    marginTop: spacing.xxs,
  },
  actionsSection: {
    flexDirection: 'row',
    minWidth: 48,
    justifyContent: 'flex-end',
  },
});

export default Header;
