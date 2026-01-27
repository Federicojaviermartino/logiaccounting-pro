/**
 * Search Bar Component
 * Customizable search input with filters
 */

import React, { useState } from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';
import { Searchbar, IconButton, useTheme, Menu } from 'react-native-paper';
import { spacing, borderRadius } from '@app/theme';

interface FilterOption {
  label: string;
  value: string;
}

interface SearchBarProps {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  filterOptions?: FilterOption[];
  selectedFilter?: string;
  onFilterChange?: (value: string) => void;
  onScanPress?: () => void;
  style?: ViewStyle;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChangeText,
  placeholder = 'Search...',
  filterOptions,
  selectedFilter,
  onFilterChange,
  onScanPress,
  style,
}) => {
  const theme = useTheme();
  const [filterMenuVisible, setFilterMenuVisible] = useState(false);

  return (
    <View style={[styles.container, style]}>
      <Searchbar
        placeholder={placeholder}
        onChangeText={onChangeText}
        value={value}
        style={[styles.searchbar, { backgroundColor: theme.colors.surfaceVariant }]}
        inputStyle={styles.input}
        iconColor={theme.colors.onSurfaceVariant}
        placeholderTextColor={theme.colors.onSurfaceVariant}
      />

      {filterOptions && filterOptions.length > 0 && (
        <Menu
          visible={filterMenuVisible}
          onDismiss={() => setFilterMenuVisible(false)}
          anchor={
            <IconButton
              icon="filter-variant"
              onPress={() => setFilterMenuVisible(true)}
              iconColor={selectedFilter ? theme.colors.primary : theme.colors.onSurfaceVariant}
              size={24}
            />
          }
        >
          {filterOptions.map((option) => (
            <Menu.Item
              key={option.value}
              onPress={() => {
                onFilterChange?.(option.value);
                setFilterMenuVisible(false);
              }}
              title={option.label}
              leadingIcon={
                selectedFilter === option.value ? 'check' : undefined
              }
            />
          ))}
        </Menu>
      )}

      {onScanPress && (
        <IconButton
          icon="barcode-scan"
          onPress={onScanPress}
          iconColor={theme.colors.onSurfaceVariant}
          size={24}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    gap: spacing.xs,
  },
  searchbar: {
    flex: 1,
    borderRadius: borderRadius.lg,
    elevation: 0,
  },
  input: {
    minHeight: 0,
  },
});

export default SearchBar;
