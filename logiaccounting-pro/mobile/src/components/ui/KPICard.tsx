/**
 * KPI Card Component - Display key performance indicators
 */

import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface KPICardProps {
  title: string;
  value: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  color: string;
  loading?: boolean;
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
}

export function KPICard({ title, value, icon, color, loading, trend }: KPICardProps) {
  return (
    <View style={styles.container}>
      <View style={[styles.iconContainer, { backgroundColor: color + '15' }]}>
        <Ionicons name={icon} size={20} color={color} />
      </View>
      <Text style={styles.title}>{title}</Text>
      {loading ? (
        <ActivityIndicator size="small" color={color} style={styles.loader} />
      ) : (
        <>
          <Text style={styles.value} numberOfLines={1}>
            {value}
          </Text>
          {trend && (
            <View style={styles.trendContainer}>
              <Ionicons
                name={trend.direction === 'up' ? 'trending-up' : 'trending-down'}
                size={14}
                color={trend.direction === 'up' ? '#10B981' : '#EF4444'}
              />
              <Text
                style={[
                  styles.trendText,
                  { color: trend.direction === 'up' ? '#10B981' : '#EF4444' },
                ]}
              >
                {Math.abs(trend.value)}%
              </Text>
            </View>
          )}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  value: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
  },
  loader: {
    marginTop: 8,
  },
  trendContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 2,
  },
  trendText: {
    fontSize: 12,
    fontWeight: '500',
  },
});
