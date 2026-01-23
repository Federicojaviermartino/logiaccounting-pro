/**
 * Invoices Screen - Invoice list and management
 */

import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  TextInput,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { invoicesService, Invoice } from '@services/invoices';
import { Badge } from '@components/ui/Badge';

const COLORS = {
  primary: '#1E40AF',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  text: '#1F2937',
  textLight: '#6B7280',
  background: '#F3F4F6',
  white: '#FFFFFF',
  border: '#E5E7EB',
};

const STATUS_FILTERS = ['all', 'pending', 'sent', 'paid', 'overdue'];

export default function InvoicesScreen() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const loadInvoices = useCallback(async (reset = false) => {
    try {
      const currentPage = reset ? 1 : page;
      const response = await invoicesService.getAll({
        page: currentPage,
        limit: 20,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        search: searchQuery || undefined,
      });

      if (reset) {
        setInvoices(response.data);
        setPage(1);
      } else {
        setInvoices((prev) => [...prev, ...response.data]);
      }
      setHasMore(currentPage < response.totalPages);
    } catch (error) {
      console.error('Failed to load invoices:', error);
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, searchQuery]);

  useEffect(() => {
    loadInvoices(true);
  }, [statusFilter, searchQuery]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadInvoices(true);
    setRefreshing(false);
  }, [loadInvoices]);

  const loadMore = () => {
    if (hasMore && !loading) {
      setPage((prev) => prev + 1);
      loadInvoices();
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getBadgeVariant = (status: string) => {
    switch (status) {
      case 'paid':
        return 'success';
      case 'pending':
      case 'sent':
        return 'warning';
      case 'overdue':
        return 'error';
      default:
        return 'default';
    }
  };

  const renderInvoice = ({ item }: { item: Invoice }) => (
    <TouchableOpacity
      style={styles.invoiceCard}
      onPress={() => router.push(`/invoices/${item.id}`)}
      activeOpacity={0.7}
    >
      <View style={styles.invoiceHeader}>
        <View>
          <Text style={styles.invoiceNumber}>{item.invoiceNumber}</Text>
          <Text style={styles.customerName}>{item.customerName}</Text>
        </View>
        <Badge label={item.status} variant={getBadgeVariant(item.status)} size="sm" />
      </View>
      <View style={styles.invoiceDetails}>
        <View style={styles.detailItem}>
          <Text style={styles.detailLabel}>Issue Date</Text>
          <Text style={styles.detailValue}>{formatDate(item.issueDate)}</Text>
        </View>
        <View style={styles.detailItem}>
          <Text style={styles.detailLabel}>Due Date</Text>
          <Text style={styles.detailValue}>{formatDate(item.dueDate)}</Text>
        </View>
        <View style={[styles.detailItem, styles.amountItem]}>
          <Text style={styles.detailLabel}>Amount</Text>
          <Text style={styles.amountValue}>{formatCurrency(item.total)}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.searchContainer}>
        <View style={styles.searchInput}>
          <Ionicons name="search" size={20} color={COLORS.textLight} />
          <TextInput
            style={styles.searchText}
            placeholder="Search invoices..."
            placeholderTextColor={COLORS.textLight}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => router.push('/invoices/create')}
        >
          <Ionicons name="add" size={24} color={COLORS.white} />
        </TouchableOpacity>
      </View>

      <View style={styles.filters}>
        {STATUS_FILTERS.map((filter) => (
          <TouchableOpacity
            key={filter}
            style={[
              styles.filterChip,
              statusFilter === filter && styles.filterChipActive,
            ]}
            onPress={() => setStatusFilter(filter)}
          >
            <Text
              style={[
                styles.filterText,
                statusFilter === filter && styles.filterTextActive,
              ]}
            >
              {filter}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={invoices}
        renderItem={renderInvoice}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
        }
        onEndReached={loadMore}
        onEndReachedThreshold={0.5}
        ListEmptyComponent={
          !loading && (
            <View style={styles.emptyContainer}>
              <Ionicons name="document-text-outline" size={48} color={COLORS.textLight} />
              <Text style={styles.emptyText}>No invoices found</Text>
            </View>
          )
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  searchContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  searchInput: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: 12,
    paddingHorizontal: 16,
    height: 48,
    gap: 8,
  },
  searchText: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
  addButton: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  filters: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 8,
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.white,
  },
  filterChipActive: {
    backgroundColor: COLORS.primary,
  },
  filterText: {
    fontSize: 13,
    fontWeight: '500',
    color: COLORS.textLight,
    textTransform: 'capitalize',
  },
  filterTextActive: {
    color: COLORS.white,
  },
  list: {
    padding: 16,
    paddingTop: 8,
  },
  invoiceCard: {
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  invoiceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  invoiceNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  customerName: {
    fontSize: 14,
    color: COLORS.textLight,
    marginTop: 2,
  },
  invoiceDetails: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: 12,
  },
  detailItem: {
    flex: 1,
  },
  amountItem: {
    alignItems: 'flex-end',
  },
  detailLabel: {
    fontSize: 11,
    color: COLORS.textLight,
    marginBottom: 2,
  },
  detailValue: {
    fontSize: 13,
    color: COLORS.text,
    fontWeight: '500',
  },
  amountValue: {
    fontSize: 16,
    color: COLORS.primary,
    fontWeight: '700',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textLight,
    marginTop: 12,
  },
});
