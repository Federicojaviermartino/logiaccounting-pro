/**
 * Card Component - Container with shadow and styling
 */

import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { ReactNode } from 'react';

interface CardProps {
  title?: string;
  children: ReactNode;
  style?: ViewStyle;
  headerRight?: ReactNode;
}

export function Card({ title, children, style, headerRight }: CardProps) {
  return (
    <View style={[styles.container, style]}>
      {title && (
        <View style={styles.header}>
          <Text style={styles.title}>{title}</Text>
          {headerRight}
        </View>
      )}
      <View style={styles.content}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 3,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
});
