/**
 * KPI Card Component
 * Displays key performance indicators with trend indicators
 */

import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { Card } from './Card';
import { spacing, colors } from '@app/theme';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
  };
  icon?: string;
  iconColor?: string;
  onPress?: () => void;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon,
  iconColor,
  onPress,
}) => {
  const theme = useTheme();

  const getTrendColor = () => {
    if (!trend) return theme.colors.onSurfaceVariant;
    switch (trend.direction) {
      case 'up':
        return colors.success;
      case 'down':
        return colors.error;
      default:
        return theme.colors.onSurfaceVariant;
    }
  };

  const getTrendIcon = () => {
    if (!trend) return null;
    switch (trend.direction) {
      case 'up':
        return 'trending-up';
      case 'down':
        return 'trending-down';
      default:
        return 'trending-neutral';
    }
  };

  return (
    <Card onPress={onPress} style={styles.card}>
      <View style={styles.header}>
        {icon && (
          <View
            style={[
              styles.iconContainer,
              { backgroundColor: (iconColor || theme.colors.primary) + '20' },
            ]}
          >
            <Icon
              name={icon}
              size={24}
              color={iconColor || theme.colors.primary}
            />
          </View>
        )}
        <Text
          variant="labelMedium"
          style={[styles.title, { color: theme.colors.onSurfaceVariant }]}
          numberOfLines={1}
        >
          {title}
        </Text>
      </View>

      <Text variant="headlineMedium" style={[styles.value, { color: theme.colors.onSurface }]}>
        {value}
      </Text>

      <View style={styles.footer}>
        {subtitle && (
          <Text
            variant="bodySmall"
            style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
            numberOfLines={1}
          >
            {subtitle}
          </Text>
        )}
        {trend && (
          <View style={styles.trendContainer}>
            <Icon
              name={getTrendIcon()!}
              size={16}
              color={getTrendColor()}
            />
            <Text
              variant="labelSmall"
              style={[styles.trendText, { color: getTrendColor() }]}
            >
              {trend.value > 0 ? '+' : ''}{trend.value}%
            </Text>
          </View>
        )}
      </View>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    minWidth: 140,
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
  },
  title: {
    flex: 1,
    fontWeight: '500',
  },
  value: {
    fontWeight: '700',
    marginBottom: spacing.xs,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  subtitle: {
    flex: 1,
  },
  trendContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xxs,
  },
  trendText: {
    fontWeight: '600',
  },
});

export default KPICard;
