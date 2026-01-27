/**
 * Transactions List Screen
 * Income and expense transactions list
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  StyleSheet,
  View,
  FlatList,
  RefreshControl,
  Pressable,
} from 'react-native';
import { Text, useTheme, FAB, Chip } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSelector, useDispatch } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';
import { RootState, AppDispatch } from '@store/index';
import { fetchTransactions, setFilters } from '@store/slices/transactionsSlice';
import { Card, SearchBar, EmptyState, LoadingSpinner } from '@components/common';
import type { TransactionsStackScreenProps } from '@types/navigation';

type Props = TransactionsStackScreenProps<'TransactionsList'>;

export const TransactionsListScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const { transactions, isLoading, filters } = useSelector(
    (state: RootState) => state.transactions
  );

  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'income' | 'expense'>('all');

  const handleRefresh = () => {
    dispatch(fetchTransactions());
  };

  const handleTransactionPress = (transactionId: string) => {
    navigation.navigate('TransactionDetail', { transactionId });
  };

  const handleAddTransaction = (type?: 'income' | 'expense') => {
    navigation.navigate('AddTransaction', { type });
  };

  const handleScanReceipt = () => {
    navigation.navigate('ScanReceipt');
  };

  const filteredTransactions = useMemo(() => {
    let result = [...transactions];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (t) =>
          t.description.toLowerCase().includes(query) ||
          t.category.toLowerCase().includes(query) ||
          t.vendorName?.toLowerCase().includes(query)
      );
    }

    if (typeFilter !== 'all') {
      result = result.filter((t) => t.type === typeFilter);
    }

    return result.sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    );
  }, [transactions, searchQuery, typeFilter]);

  const totals = useMemo(() => {
    const income = transactions
      .filter((t) => t.type === 'income')
      .reduce((sum, t) => sum + t.amount, 0);
    const expense = transactions
      .filter((t) => t.type === 'expense')
      .reduce((sum, t) => sum + t.amount, 0);
    return { income, expense, net: income - expense };
  }, [transactions]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  const renderTransaction = ({ item }: { item: typeof transactions[0] }) => {
    const isIncome = item.type === 'income';
    const amountColor = isIncome ? colors.success : colors.error;

    return (
      <Pressable
        onPress={() => handleTransactionPress(item.id)}
        style={({ pressed }) => [
          styles.transactionItem,
          { backgroundColor: theme.colors.surface },
          pressed && { opacity: 0.8 },
        ]}
      >
        <View
          style={[
            styles.transactionIcon,
            { backgroundColor: amountColor + '20' },
          ]}
        >
          <Icon
            name={isIncome ? 'arrow-down' : 'arrow-up'}
            size={20}
            color={amountColor}
          />
        </View>
        <View style={styles.transactionContent}>
          <Text
            variant="bodyLarge"
            style={[styles.transactionDesc, { color: theme.colors.onSurface }]}
            numberOfLines={1}
          >
            {item.description}
          </Text>
          <Text
            variant="bodySmall"
            style={{ color: theme.colors.onSurfaceVariant }}
          >
            {item.category} • {formatDate(item.date)}
          </Text>
        </View>
        <Text
          variant="titleMedium"
          style={[styles.transactionAmount, { color: amountColor }]}
        >
          {isIncome ? '+' : '-'}{formatCurrency(item.amount)}
        </Text>
      </Pressable>
    );
  };

  if (isLoading && transactions.length === 0) {
    return <LoadingSpinner fullScreen message="Loading transactions..." />;
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      edges={['bottom']}
    >
      {/* Summary Cards */}
      <View style={styles.summaryContainer}>
        <View style={[styles.summaryCard, { backgroundColor: colors.success + '15' }]}>
          <Text variant="labelSmall" style={{ color: colors.success }}>
            Income
          </Text>
          <Text variant="titleMedium" style={{ color: colors.success, fontWeight: '600' }}>
            {formatCurrency(totals.income)}
          </Text>
        </View>
        <View style={[styles.summaryCard, { backgroundColor: colors.error + '15' }]}>
          <Text variant="labelSmall" style={{ color: colors.error }}>
            Expenses
          </Text>
          <Text variant="titleMedium" style={{ color: colors.error, fontWeight: '600' }}>
            {formatCurrency(totals.expense)}
          </Text>
        </View>
        <View style={[styles.summaryCard, { backgroundColor: theme.colors.primaryContainer }]}>
          <Text variant="labelSmall" style={{ color: theme.colors.primary }}>
            Net
          </Text>
          <Text
            variant="titleMedium"
            style={{
              color: totals.net >= 0 ? colors.success : colors.error,
              fontWeight: '600',
            }}
          >
            {formatCurrency(totals.net)}
          </Text>
        </View>
      </View>

      {/* Search */}
      <SearchBar
        value={searchQuery}
        onChangeText={setSearchQuery}
        placeholder="Search transactions..."
        onScanPress={handleScanReceipt}
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
          selected={typeFilter === 'income'}
          onPress={() => setTypeFilter('income')}
          style={styles.chip}
          icon="arrow-down"
        >
          Income
        </Chip>
        <Chip
          selected={typeFilter === 'expense'}
          onPress={() => setTypeFilter('expense')}
          style={styles.chip}
          icon="arrow-up"
        >
          Expenses
        </Chip>
      </View>

      {/* Transactions List */}
      {filteredTransactions.length > 0 ? (
        <FlatList
          data={filteredTransactions}
          renderItem={renderTransaction}
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
          icon="receipt"
          title="No Transactions"
          description={
            searchQuery
              ? `No transactions match "${searchQuery}"`
              : 'Start recording your income and expenses'
          }
          actionLabel={!searchQuery ? 'Add Transaction' : undefined}
          onAction={!searchQuery ? () => handleAddTransaction() : undefined}
        />
      )}

      {/* FAB Group */}
      <View style={styles.fabContainer}>
        <FAB
          icon="cash-plus"
          onPress={() => handleAddTransaction('income')}
          style={[styles.fabSmall, { backgroundColor: colors.success }]}
          color="#fff"
          size="small"
        />
        <FAB
          icon="cash-minus"
          onPress={() => handleAddTransaction('expense')}
          style={[styles.fabSmall, { backgroundColor: colors.error }]}
          color="#fff"
          size="small"
        />
        <FAB
          icon="plus"
          onPress={() => handleAddTransaction()}
          style={[styles.fab, { backgroundColor: theme.colors.primary }]}
          color={theme.colors.onPrimary}
        />
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  summaryContainer: {
    flexDirection: 'row',
    padding: spacing.md,
    gap: spacing.sm,
  },
  summaryCard: {
    flex: 1,
    padding: spacing.sm,
    borderRadius: borderRadius.md,
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
  transactionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    gap: spacing.md,
  },
  transactionIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  transactionContent: {
    flex: 1,
  },
  transactionDesc: {
    fontWeight: '500',
    marginBottom: spacing.xxs,
  },
  transactionAmount: {
    fontWeight: '600',
  },
  fabContainer: {
    position: 'absolute',
    right: spacing.lg,
    bottom: spacing.lg,
    alignItems: 'center',
    gap: spacing.sm,
  },
  fabSmall: {
    marginBottom: 0,
  },
  fab: {
    marginTop: spacing.sm,
  },
});

export default TransactionsListScreen;
