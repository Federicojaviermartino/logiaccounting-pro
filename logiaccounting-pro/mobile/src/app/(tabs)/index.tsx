/**
 * Dashboard Screen - Main home screen with KPIs and quick actions
 */

import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@store/authStore';
import { invoicesService, InvoiceStats, Invoice } from '@services/invoices';
import { KPICard } from '@components/ui/KPICard';
import { QuickActions } from '@components/ui/QuickActions';
import { Card } from '@components/ui/Card';

const COLORS = {
  primary: '#1E40AF',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  text: '#1F2937',
  textLight: '#6B7280',
  background: '#F3F4F6',
  white: '#FFFFFF',
};

export default function DashboardScreen() {
  const { user } = useAuthStore();
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<InvoiceStats | null>(null);
  const [recentInvoices, setRecentInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const [statsData, invoicesData] = await Promise.all([
        invoicesService.getStats(),
        invoicesService.getRecent(5),
      ]);
      setStats(statsData);
      setRecentInvoices(invoicesData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  }, [loadData]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return COLORS.success;
      case 'pending':
      case 'sent':
        return COLORS.warning;
      case 'overdue':
        return COLORS.error;
      default:
        return COLORS.textLight;
    }
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
      }
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Welcome back,</Text>
          <Text style={styles.userName}>{user?.name || 'User'}</Text>
        </View>
        <TouchableOpacity style={styles.notificationButton}>
          <Ionicons name="notifications-outline" size={24} color={COLORS.text} />
          <View style={styles.notificationBadge} />
        </TouchableOpacity>
      </View>

      <View style={styles.kpiGrid}>
        <KPICard
          title="Total Revenue"
          value={formatCurrency(stats?.totalRevenue || 0)}
          icon="trending-up"
          color={COLORS.success}
          loading={loading}
        />
        <KPICard
          title="Pending"
          value={formatCurrency(stats?.pendingAmount || 0)}
          icon="time-outline"
          color={COLORS.warning}
          loading={loading}
        />
        <KPICard
          title="Overdue"
          value={formatCurrency(stats?.overdueAmount || 0)}
          icon="alert-circle-outline"
          color={COLORS.error}
          loading={loading}
        />
        <KPICard
          title="Invoices"
          value={stats?.invoiceCount?.toString() || '0'}
          icon="document-text-outline"
          color={COLORS.primary}
          loading={loading}
        />
      </View>

      <QuickActions />

      <Card title="Recent Invoices" style={styles.recentCard}>
        {recentInvoices.length === 0 ? (
          <Text style={styles.emptyText}>No recent invoices</Text>
        ) : (
          recentInvoices.map((invoice) => (
            <TouchableOpacity
              key={invoice.id}
              style={styles.invoiceItem}
              onPress={() => router.push(`/invoices/${invoice.id}`)}
            >
              <View style={styles.invoiceInfo}>
                <Text style={styles.invoiceNumber}>{invoice.invoiceNumber}</Text>
                <Text style={styles.customerName}>{invoice.customerName}</Text>
              </View>
              <View style={styles.invoiceRight}>
                <Text style={styles.invoiceAmount}>{formatCurrency(invoice.total)}</Text>
                <View style={[styles.statusBadge, { backgroundColor: getStatusColor(invoice.status) + '20' }]}>
                  <Text style={[styles.statusText, { color: getStatusColor(invoice.status) }]}>
                    {invoice.status}
                  </Text>
                </View>
              </View>
            </TouchableOpacity>
          ))
        )}
        <TouchableOpacity
          style={styles.viewAllButton}
          onPress={() => router.push('/invoices')}
        >
          <Text style={styles.viewAllText}>View All Invoices</Text>
          <Ionicons name="chevron-forward" size={16} color={COLORS.primary} />
        </TouchableOpacity>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  greeting: {
    fontSize: 14,
    color: COLORS.textLight,
  },
  userName: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  notificationButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.white,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  notificationBadge: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.error,
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  recentCard: {
    marginTop: 16,
  },
  invoiceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  invoiceInfo: {
    flex: 1,
  },
  invoiceNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  customerName: {
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: 2,
  },
  invoiceRight: {
    alignItems: 'flex-end',
  },
  invoiceAmount: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginTop: 4,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  emptyText: {
    textAlign: 'center',
    color: COLORS.textLight,
    paddingVertical: 24,
  },
  viewAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    marginTop: 8,
  },
  viewAllText: {
    color: COLORS.primary,
    fontWeight: '600',
    marginRight: 4,
  },
});
