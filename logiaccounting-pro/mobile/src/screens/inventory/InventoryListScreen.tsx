/**
 * Inventory List Screen
 * Material inventory with search and filters
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  StyleSheet,
  View,
  FlatList,
  RefreshControl,
} from 'react-native';
import { Text, useTheme, FAB, SegmentedButtons } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSelector, useDispatch } from 'react-redux';
import debounce from 'lodash.debounce';

import { spacing, colors } from '@app/theme';
import { RootState, AppDispatch } from '@store/index';
import { fetchMaterials, setFilters } from '@store/slices/inventorySlice';
import {
  SearchBar,
  InventoryItem,
  EmptyState,
  LoadingSpinner,
} from '@components/common';
import type { InventoryStackScreenProps } from '@types/navigation';

type Props = InventoryStackScreenProps<'InventoryList'>;

export const InventoryListScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const { materials, isLoading, filters } = useSelector(
    (state: RootState) => state.inventory
  );

  const [searchQuery, setSearchQuery] = useState(filters.search);
  const [stateFilter, setStateFilter] = useState<string>('all');

  const debouncedSearch = useCallback(
    debounce((query: string) => {
      dispatch(setFilters({ search: query }));
    }, 300),
    []
  );

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    debouncedSearch(query);
  };

  const handleRefresh = () => {
    dispatch(fetchMaterials());
  };

  const handleMaterialPress = (materialId: string) => {
    navigation.navigate('InventoryDetail', { materialId });
  };

  const handleScanPress = () => {
    navigation.navigate('BarcodeScanner', { returnTo: 'InventoryList' });
  };

  const handleAddMaterial = () => {
    navigation.navigate('AddMaterial');
  };

  const filteredMaterials = useMemo(() => {
    let result = [...materials];

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (m) =>
          m.name.toLowerCase().includes(query) ||
          m.reference.toLowerCase().includes(query) ||
          m.category.toLowerCase().includes(query)
      );
    }

    // Filter by state
    if (stateFilter !== 'all') {
      result = result.filter((m) => m.state === stateFilter);
    }

    return result;
  }, [materials, searchQuery, stateFilter]);

  const renderItem = useCallback(
    ({ item }: { item: typeof materials[0] }) => (
      <InventoryItem
        {...item}
        onPress={() => handleMaterialPress(item.id)}
      />
    ),
    []
  );

  const keyExtractor = useCallback((item: typeof materials[0]) => item.id, []);

  const stats = useMemo(() => {
    const lowStock = materials.filter((m) => m.currentStock <= m.minStock).length;
    const outOfStock = materials.filter((m) => m.currentStock <= 0).length;
    return { total: materials.length, lowStock, outOfStock };
  }, [materials]);

  if (isLoading && materials.length === 0) {
    return <LoadingSpinner fullScreen message="Loading inventory..." />;
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      edges={['bottom']}
    >
      {/* Stats Summary */}
      <View style={styles.statsBar}>
        <View style={styles.statItem}>
          <Text variant="titleMedium" style={{ color: theme.colors.onSurface }}>
            {stats.total}
          </Text>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Total
          </Text>
        </View>
        <View style={[styles.statDivider, { backgroundColor: theme.colors.outlineVariant }]} />
        <View style={styles.statItem}>
          <Text variant="titleMedium" style={{ color: colors.warning }}>
            {stats.lowStock}
          </Text>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Low Stock
          </Text>
        </View>
        <View style={[styles.statDivider, { backgroundColor: theme.colors.outlineVariant }]} />
        <View style={styles.statItem}>
          <Text variant="titleMedium" style={{ color: colors.error }}>
            {stats.outOfStock}
          </Text>
          <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>
            Out of Stock
          </Text>
        </View>
      </View>

      {/* Search and Filter */}
      <SearchBar
        value={searchQuery}
        onChangeText={handleSearch}
        placeholder="Search materials..."
        onScanPress={handleScanPress}
        style={styles.searchBar}
      />

      {/* State Filter */}
      <View style={styles.filterContainer}>
        <SegmentedButtons
          value={stateFilter}
          onValueChange={setStateFilter}
          buttons={[
            { value: 'all', label: 'All' },
            { value: 'active', label: 'Active' },
            { value: 'inactive', label: 'Inactive' },
            { value: 'depleted', label: 'Depleted' },
          ]}
          style={styles.segmentedButtons}
        />
      </View>

      {/* Materials List */}
      {filteredMaterials.length > 0 ? (
        <FlatList
          data={filteredMaterials}
          renderItem={renderItem}
          keyExtractor={keyExtractor}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl refreshing={isLoading} onRefresh={handleRefresh} />
          }
        />
      ) : (
        <EmptyState
          icon="package-variant"
          title="No Materials Found"
          description={
            searchQuery
              ? `No materials match "${searchQuery}"`
              : 'Start by adding your first material'
          }
          actionLabel={!searchQuery ? 'Add Material' : undefined}
          onAction={!searchQuery ? handleAddMaterial : undefined}
        />
      )}

      <FAB
        icon="plus"
        onPress={handleAddMaterial}
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        color={theme.colors.onPrimary}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  statsBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    padding: spacing.md,
    marginHorizontal: spacing.md,
    marginBottom: spacing.sm,
  },
  statItem: {
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    height: 32,
  },
  searchBar: {
    marginBottom: spacing.sm,
  },
  filterContainer: {
    paddingHorizontal: spacing.md,
    marginBottom: spacing.md,
  },
  segmentedButtons: {
    // Custom styling if needed
  },
  list: {
    paddingHorizontal: spacing.md,
    paddingBottom: 100,
  },
  fab: {
    position: 'absolute',
    right: spacing.lg,
    bottom: spacing.lg,
  },
});

export default InventoryListScreen;
