/**
 * Quick Actions Component - Fast access to common actions
 */

import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

interface Action {
  id: string;
  label: string;
  icon: React.ComponentProps<typeof Ionicons>['name'];
  color: string;
  route: string;
}

const ACTIONS: Action[] = [
  {
    id: 'new-invoice',
    label: 'New Invoice',
    icon: 'add-circle',
    color: '#1E40AF',
    route: '/invoices/create',
  },
  {
    id: 'scan-barcode',
    label: 'Scan',
    icon: 'scan',
    color: '#10B981',
    route: '/scanner',
  },
  {
    id: 'add-expense',
    label: 'Add Expense',
    icon: 'receipt',
    color: '#F59E0B',
    route: '/expenses/create',
  },
  {
    id: 'reports',
    label: 'Reports',
    icon: 'bar-chart',
    color: '#8B5CF6',
    route: '/reports',
  },
];

export function QuickActions() {
  const handlePress = (route: string) => {
    router.push(route as any);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Quick Actions</Text>
      <View style={styles.grid}>
        {ACTIONS.map((action) => (
          <TouchableOpacity
            key={action.id}
            style={styles.actionButton}
            onPress={() => handlePress(action.route)}
            activeOpacity={0.7}
          >
            <View style={[styles.iconContainer, { backgroundColor: action.color + '15' }]}>
              <Ionicons name={action.icon} size={24} color={action.color} />
            </View>
            <Text style={styles.actionLabel}>{action.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 12,
  },
  grid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    alignItems: 'center',
    width: '23%',
  },
  iconContainer: {
    width: 56,
    height: 56,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  actionLabel: {
    fontSize: 11,
    color: '#6B7280',
    textAlign: 'center',
  },
});
