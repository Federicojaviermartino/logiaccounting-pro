/**
 * Inventory Screen - Product and stock management
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
  Image,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
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

interface InventoryItem {
  id: string;
  name: string;
  sku: string;
  quantity: number;
  reorderLevel: number;
  price: number;
  category: string;
  imageUrl?: string;
}

const MOCK_INVENTORY: InventoryItem[] = [
  { id: '1', name: 'Widget Pro X', sku: 'WPX-001', quantity: 150, reorderLevel: 50, price: 29.99, category: 'Electronics' },
  { id: '2', name: 'Basic Cable', sku: 'BC-002', quantity: 25, reorderLevel: 100, price: 9.99, category: 'Accessories' },
  { id: '3', name: 'Power Adapter', sku: 'PA-003', quantity: 75, reorderLevel: 30, price: 19.99, category: 'Electronics' },
  { id: '4', name: 'USB Hub', sku: 'UH-004', quantity: 0, reorderLevel: 20, price: 39.99, category: 'Electronics' },
];

export default function InventoryScreen() {
  const [items, setItems] = useState<InventoryItem[]>(MOCK_INVENTORY);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  }, []);

  const getStockStatus = (item: InventoryItem) => {
    if (item.quantity === 0) return { label: 'Out of Stock', variant: 'error' as const };
    if (item.quantity < item.reorderLevel) return { label: 'Low Stock', variant: 'warning' as const };
    return { label: 'In Stock', variant: 'success' as const };
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const filteredItems = items.filter(
    (item) =>
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.sku.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const renderItem = ({ item }: { item: InventoryItem }) => {
    const status = getStockStatus(item);

    return (
      <TouchableOpacity
        style={styles.itemCard}
        onPress={() => router.push(`/inventory/${item.id}`)}
        activeOpacity={0.7}
      >
        <View style={styles.itemImage}>
          {item.imageUrl ? (
            <Image source={{ uri: item.imageUrl }} style={styles.image} />
          ) : (
            <Ionicons name="cube-outline" size={32} color={COLORS.textLight} />
          )}
        </View>
        <View style={styles.itemContent}>
          <View style={styles.itemHeader}>
            <Text style={styles.itemName} numberOfLines={1}>{item.name}</Text>
            <Badge label={status.label} variant={status.variant} size="sm" />
          </View>
          <Text style={styles.itemSku}>SKU: {item.sku}</Text>
          <View style={styles.itemFooter}>
            <Text style={styles.itemQuantity}>Qty: {item.quantity}</Text>
            <Text style={styles.itemPrice}>{formatCurrency(item.price)}</Text>
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.searchInput}>
          <Ionicons name="search" size={20} color={COLORS.textLight} />
          <TextInput
            style={styles.searchText}
            placeholder="Search products..."
            placeholderTextColor={COLORS.textLight}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>
        <TouchableOpacity
          style={styles.scanButton}
          onPress={() => router.push('/scanner/barcode')}
        >
          <Ionicons name="scan" size={24} color={COLORS.white} />
        </TouchableOpacity>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{items.length}</Text>
          <Text style={styles.statLabel}>Products</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, { color: COLORS.warning }]}>
            {items.filter(i => i.quantity < i.reorderLevel && i.quantity > 0).length}
          </Text>
          <Text style={styles.statLabel}>Low Stock</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={[styles.statValue, { color: COLORS.error }]}>
            {items.filter(i => i.quantity === 0).length}
          </Text>
          <Text style={styles.statLabel}>Out of Stock</Text>
        </View>
      </View>

      <FlatList
        data={filteredItems}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="cube-outline" size={48} color={COLORS.textLight} />
            <Text style={styles.emptyText}>No products found</Text>
          </View>
        }
      />

      <TouchableOpacity
        style={styles.fab}
        onPress={() => router.push('/inventory/create')}
      >
        <Ionicons name="add" size={28} color={COLORS.white} />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
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
  scanButton: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 8,
    gap: 8,
  },
  statCard: {
    flex: 1,
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  statLabel: {
    fontSize: 11,
    color: COLORS.textLight,
    marginTop: 2,
  },
  list: {
    padding: 16,
    paddingTop: 8,
  },
  itemCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.white,
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  itemImage: {
    width: 60,
    height: 60,
    borderRadius: 8,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  image: {
    width: 60,
    height: 60,
    borderRadius: 8,
  },
  itemContent: {
    flex: 1,
  },
  itemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  itemName: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
    flex: 1,
    marginRight: 8,
  },
  itemSku: {
    fontSize: 12,
    color: COLORS.textLight,
    marginBottom: 8,
  },
  itemFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  itemQuantity: {
    fontSize: 13,
    color: COLORS.text,
  },
  itemPrice: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
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
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 6,
  },
});
