/**
 * Scanner Tab Screen - Entry point for scanning features
 */

import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

const COLORS = {
  primary: '#1E40AF',
  text: '#1F2937',
  textLight: '#6B7280',
  background: '#F3F4F6',
  white: '#FFFFFF',
};

const SCAN_OPTIONS = [
  {
    id: 'barcode',
    title: 'Barcode Scanner',
    description: 'Scan product barcodes for inventory',
    icon: 'barcode-outline' as const,
    color: '#1E40AF',
    route: '/scanner/barcode',
  },
  {
    id: 'document',
    title: 'Document Scanner',
    description: 'Scan receipts and invoices',
    icon: 'document-text-outline' as const,
    color: '#10B981',
    route: '/scanner/document',
  },
  {
    id: 'qr',
    title: 'QR Code Scanner',
    description: 'Scan QR codes for quick actions',
    icon: 'qr-code-outline' as const,
    color: '#8B5CF6',
    route: '/scanner/barcode',
  },
];

export default function ScannerScreen() {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Ionicons name="scan" size={48} color={COLORS.primary} />
        <Text style={styles.title}>Scan & Capture</Text>
        <Text style={styles.subtitle}>
          Use your camera to scan barcodes or capture documents
        </Text>
      </View>

      <View style={styles.options}>
        {SCAN_OPTIONS.map((option) => (
          <TouchableOpacity
            key={option.id}
            style={styles.optionCard}
            onPress={() => router.push(option.route as any)}
            activeOpacity={0.7}
          >
            <View style={[styles.iconContainer, { backgroundColor: option.color + '15' }]}>
              <Ionicons name={option.icon} size={32} color={option.color} />
            </View>
            <View style={styles.optionContent}>
              <Text style={styles.optionTitle}>{option.title}</Text>
              <Text style={styles.optionDescription}>{option.description}</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color={COLORS.textLight} />
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.recentSection}>
        <Text style={styles.sectionTitle}>Recent Scans</Text>
        <View style={styles.emptyRecent}>
          <Ionicons name="time-outline" size={32} color={COLORS.textLight} />
          <Text style={styles.emptyText}>No recent scans</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    padding: 16,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 16,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textLight,
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 32,
  },
  options: {
    gap: 12,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  iconContainer: {
    width: 56,
    height: 56,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  optionContent: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  optionDescription: {
    fontSize: 13,
    color: COLORS.textLight,
    marginTop: 2,
  },
  recentSection: {
    marginTop: 32,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 12,
  },
  emptyRecent: {
    alignItems: 'center',
    paddingVertical: 32,
    backgroundColor: COLORS.white,
    borderRadius: 12,
  },
  emptyText: {
    fontSize: 14,
    color: COLORS.textLight,
    marginTop: 8,
  },
});
