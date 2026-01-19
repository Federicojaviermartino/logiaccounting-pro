/**
 * Payments List Screen
 * Accounts receivable and payable
 */

import React, { useState, useMemo } from 'react';
import {
  StyleSheet,
  View,
  FlatList,
  RefreshControl,
  Pressable,
} from 'react-native';
import { Text, useTheme, FAB, Chip, Badge } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSelector, useDispatch } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';
import { RootState, AppDispatch } from '@store/index';
import { fetchPayments } from '@store/slices/paymentsSlice';
import { Card, SearchBar, EmptyState, LoadingSpinner } from '@components/common';
import type { PaymentsStackScreenProps } from '@types/navigation';

type Props = PaymentsStackScreenProps<'PaymentsList'>;

export const PaymentsListScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const { payments, isLoading, overdueCount, upcomingCount } = useSelector(
    (state: RootState) => state.payments
  );

  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'receivable' | 'payable'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'overdue' | 'paid'>('all');

  const handleRefresh = () => {
    dispatch(fetchPayments());
  };

  const handlePaymentPress = (paymentId: string) => {
    navigation.navigate('PaymentDetail', { paymentId });
  };

  const handleAddPayment = (type: 'receivable' | 'payable') => {
    navigation.navigate('AddPayment', { type });
  };

  const filteredPayments = useMemo(() => {
    let result = [...payments];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (p) =>
          p.description.toLowerCase().includes(query) ||
          p.clientName?.toLowerCase().includes(query) ||
          p.vendorName?.toLowerCase().includes(query)
      );
    }

    if (typeFilter !== 'all') {
      result = result.filter((p) => p.type === typeFilter);
    }

    if (statusFilter !== 'all') {
      result = result.filter((p) => p.status === statusFilter);
    }

    return result.sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime());
  }, [payments, searchQuery, typeFilter, statusFilter]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return colors.success;
      case 'overdue':
        return colors.error;
      case 'pending':
        return colors.warning;
      case 'cancelled':
        return theme.colors.outline;
      default:
        return theme.colors.outline;
    }
  };

  const getDaysUntilDue = (dueDate: string) => {
    const today = new Date();
    const due = new Date(dueDate);
    const diff = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const renderPayment = ({ item }: { item: typeof payments[0] }) => {
    const statusColor = getStatusColor(item.status);
    const daysUntilDue = getDaysUntilDue(item.dueDate);
    const isOverdue = item.status === 'overdue' || (item.status === 'pending' && daysUntilDue < 0);

    return (
      <Pressable
        onPress={() => handlePaymentPress(item.id)}
        style={({ pressed }) => [
          styles.paymentItem,
          { backgroundColor: theme.colors.surface },
          pressed && { opacity: 0.8 },
        ]}
      >
        <View style={styles.paymentHeader}>
          <View
            style={[
              styles.typeIcon,
              {
                backgroundColor:
                  item.type === 'receivable' ? colors.success + '20' : colors.warning + '20',
              },
            ]}
          >
            <Icon
              name={item.type === 'receivable' ? 'arrow-down' : 'arrow-up'}
              size={20}
              color={item.type === 'receivable' ? colors.success : colors.warning}
            />
          </View>
          <View style={styles.paymentInfo}>
            <Text
              variant="bodyLarge"
              style={[styles.paymentDesc, { color: theme.colors.onSurface }]}
              numberOfLines={1}
            >
              {item.description}
            </Text>
            <Text
              variant="bodySmall"
              style={{ color: theme.colors.onSurfaceVariant }}
            >
              {item.type === 'receivable' ? item.clientName : item.vendorName}
            </Text>
          </View>
          <Text
            variant="titleMedium"
            style={[
              styles.paymentAmount,
              { color: item.type === 'receivable' ? colors.success : colors.error },
            ]}
          >
            {formatCurrency(item.amount)}
          </Text>
        </View>

        <View style={styles.paymentFooter}>
          <View style={styles.dueInfo}>
            <Icon
              name="calendar"
              size={14}
              color={isOverdue ? colors.error : theme.colors.onSurfaceVariant}
            />
            <Text
              variant="labelSmall"
              style={{ color: isOverdue ? colors.error : theme.colors.onSurfaceVariant }}
            >
              {item.status === 'paid'
                ? `Paid ${formatDate(item.paidDate!)}`
                : isOverdue
                ? `${Math.abs(daysUntilDue)} days overdue`
                : daysUntilDue === 0
                ? 'Due today'
                : `Due ${formatDate(item.dueDate)}`}
            </Text>
          </View>
          <View
            style={[styles.statusBadge, { backgroundColor: statusColor + '20' }]}
          >
            <Text
              variant="labelSmall"
              style={{ color: statusColor, textTransform: 'capitalize' }}
            >
              {item.status}
            </Text>
          </View>
        </View>
      </Pressable>
    );
  };

  if (isLoading && payments.length === 0) {
    return <LoadingSpinner fullScreen message="Loading payments..." />;
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      edges={['bottom']}
    >
      {/* Summary Stats */}
      <View style={styles.statsContainer}>
        <Pressable
          onPress={() => setStatusFilter(statusFilter === 'overdue' ? 'all' : 'overdue')}
          style={[
            styles.statCard,
            { backgroundColor: colors.error + '15' },
            statusFilter === 'overdue' && { borderWidth: 2, borderColor: colors.error },
          ]}
        >
          <Text variant="headlineSmall" style={{ color: colors.error, fontWeight: '600' }}>
            {overdueCount}
          </Text>
          <Text variant="labelSmall" style={{ color: colors.error }}>
            Overdue
          </Text>
        </Pressable>
        <Pressable
          onPress={() => setStatusFilter(statusFilter === 'pending' ? 'all' : 'pending')}
          style={[
            styles.statCard,
            { backgroundColor: colors.warning + '15' },
            statusFilter === 'pending' && { borderWidth: 2, borderColor: colors.warning },
          ]}
        >
          <Text variant="headlineSmall" style={{ color: colors.warning, fontWeight: '600' }}>
            {upcomingCount}
          </Text>
          <Text variant="labelSmall" style={{ color: colors.warning }}>
            Upcoming
          </Text>
        </Pressable>
      </View>

      {/* Search */}
      <SearchBar
        value={searchQuery}
        onChangeText={setSearchQuery}
        placeholder="Search payments..."
        style={styles.searchBar}
      />

      {/* Type Filter */}
      <View style={styles.filterContainer}>
        <Chip
          selected={typeFilter === 'all'}
          onPress={() => setTypeFilter('all')}
          style={styles.chip}
        >
          All
        </Chip>
        <Chip
          selected={typeFilter === 'receivable'}
          onPress={() => setTypeFilter('receivable')}
          style={styles.chip}
          icon="arrow-down"
        >
          Receivable
        </Chip>
        <Chip
          selected={typeFilter === 'payable'}
          onPress={() => setTypeFilter('payable')}
          style={styles.chip}
          icon="arrow-up"
        >
          Payable
        </Chip>
      </View>

      {/* Payments List */}
      {filteredPayments.length > 0 ? (
        <FlatList
          data={filteredPayments}
          renderItem={renderPayment}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={isLoading} onRefresh={handleRefresh} />
          }
          ItemSeparatorComponent={() => <View style={{ height: spacing.sm }} />}
        />
      ) : (
        <EmptyState
          icon="credit-card-clock"
          title="No Payments"
          description={
            searchQuery
              ? `No payments match "${searchQuery}"`
              : 'Start tracking your receivables and payables'
          }
        />
      )}

      {/* FAB */}
      <View style={styles.fabContainer}>
        <FAB
          icon="cash-plus"
          onPress={() => handleAddPayment('receivable')}
          style={[styles.fabSmall, { backgroundColor: colors.success }]}
          color="#fff"
          size="small"
          label="Receivable"
        />
        <FAB
          icon="cash-minus"
          onPress={() => handleAddPayment('payable')}
          style={[styles.fabSmall, { backgroundColor: colors.warning }]}
          color="#fff"
          size="small"
          label="Payable"
        />
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  statsContainer: {
    flexDirection: 'row',
    padding: spacing.md,
    gap: spacing.md,
  },
  statCard: {
    flex: 1,
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
  },
  searchBar: {
    marginBottom: spacing.sm,
  },
  filterContainer: {
    flexDirection: 'row',
    paddingHorizontal: spacing.md,
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  chip: {
    marginRight: 0,
  },
  list: {
    paddingHorizontal: spacing.md,
    paddingBottom: 120,
  },
  paymentItem: {
    padding: spacing.md,
    borderRadius: borderRadius.lg,
  },
  paymentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
    gap: spacing.md,
  },
  typeIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  paymentInfo: {
    flex: 1,
  },
  paymentDesc: {
    fontWeight: '500',
    marginBottom: spacing.xxs,
  },
  paymentAmount: {
    fontWeight: '600',
  },
  paymentFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginLeft: 52,
  },
  dueInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  statusBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
    borderRadius: borderRadius.sm,
  },
  fabContainer: {
    position: 'absolute',
    right: spacing.lg,
    bottom: spacing.lg,
    gap: spacing.sm,
  },
  fabSmall: {
    marginBottom: 0,
  },
});

export default PaymentsListScreen;
