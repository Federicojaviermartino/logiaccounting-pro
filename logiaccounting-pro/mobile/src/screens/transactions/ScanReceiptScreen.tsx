/**
 * Scan Receipt Screen
 * Camera-based receipt scanning with OCR
 */

import React, { useState } from 'react';
import { StyleSheet, View, Dimensions } from 'react-native';
import { Text, Button, useTheme, IconButton } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';
import type { TransactionsStackScreenProps } from '@types/navigation';

type Props = TransactionsStackScreenProps<'ScanReceipt'>;

const { width, height } = Dimensions.get('window');

export const ScanReceiptScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();
  const [hasPermission, setHasPermission] = useState<boolean>(true);
  const [isCapturing, setIsCapturing] = useState(false);
  const [flashOn, setFlashOn] = useState(false);

  const handleClose = () => {
    navigation.goBack();
  };

  const handleCapture = async () => {
    setIsCapturing(true);
    // Simulate capture
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsCapturing(false);
    // Navigate to add transaction with extracted data
    navigation.replace('AddTransaction', { type: 'expense' });
  };

  const handleSelectFromGallery = () => {
    // Open image picker
    navigation.replace('AddTransaction', { type: 'expense' });
  };

  if (!hasPermission) {
    return (
      <SafeAreaView
        style={[styles.container, { backgroundColor: theme.colors.background }]}
      >
        <View style={styles.permissionContainer}>
          <Icon name="camera-off" size={64} color={theme.colors.error} />
          <Text
            variant="titleLarge"
            style={[styles.permissionTitle, { color: theme.colors.onSurface }]}
          >
            Camera Access Required
          </Text>
          <Text
            variant="bodyMedium"
            style={[styles.permissionText, { color: theme.colors.onSurfaceVariant }]}
          >
            Please grant camera permission to scan receipts
          </Text>
          <Button mode="contained" style={styles.permissionButton}>
            Open Settings
          </Button>
          <Button mode="text" onPress={handleClose}>
            Cancel
          </Button>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <View style={styles.container}>
      {/* Camera Placeholder */}
      <View style={[styles.cameraPlaceholder, { backgroundColor: '#000' }]}>
        {/* Overlay Guide */}
        <View style={styles.overlay}>
          <View style={styles.overlayTop} />
          <View style={styles.overlayMiddle}>
            <View style={styles.overlaySide} />
            <View style={styles.scanArea}>
              <View style={[styles.corner, styles.cornerTL]} />
              <View style={[styles.corner, styles.cornerTR]} />
              <View style={[styles.corner, styles.cornerBL]} />
              <View style={[styles.corner, styles.cornerBR]} />
            </View>
            <View style={styles.overlaySide} />
          </View>
          <View style={styles.overlayBottom} />
        </View>

        {/* Controls */}
        <SafeAreaView style={styles.controls}>
          <View style={styles.topControls}>
            <IconButton
              icon="close"
              iconColor="#fff"
              size={24}
              onPress={handleClose}
              style={styles.controlButton}
            />
            <IconButton
              icon={flashOn ? 'flash' : 'flash-off'}
              iconColor="#fff"
              size={24}
              onPress={() => setFlashOn(!flashOn)}
              style={styles.controlButton}
            />
          </View>

          <View style={styles.instructions}>
            <Icon name="receipt" size={32} color="#fff" />
            <Text variant="titleMedium" style={styles.instructionText}>
              Position receipt within frame
            </Text>
            <Text variant="bodySmall" style={styles.instructionSubtext}>
              Make sure all text is visible and in focus
            </Text>
          </View>

          <View style={styles.bottomControls}>
            <IconButton
              icon="image"
              iconColor="#fff"
              size={28}
              onPress={handleSelectFromGallery}
              style={styles.galleryButton}
            />
            <View style={styles.captureButtonOuter}>
              <Button
                mode="contained"
                onPress={handleCapture}
                loading={isCapturing}
                disabled={isCapturing}
                style={styles.captureButton}
                contentStyle={styles.captureButtonContent}
              >
                {!isCapturing && <Icon name="camera" size={32} color="#fff" />}
              </Button>
            </View>
            <View style={{ width: 56 }} />
          </View>

          <Button
            mode="text"
            onPress={() => navigation.replace('AddTransaction', { type: 'expense' })}
            textColor="#fff"
            style={styles.skipButton}
          >
            Enter Manually
          </Button>
        </SafeAreaView>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  cameraPlaceholder: {
    flex: 1,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
  },
  overlayTop: {
    flex: 0.15,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  overlayMiddle: {
    flex: 0.6,
    flexDirection: 'row',
  },
  overlaySide: {
    flex: 0.05,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  overlayBottom: {
    flex: 0.25,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  scanArea: {
    flex: 0.9,
    borderRadius: borderRadius.lg,
  },
  corner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: colors.primary,
    borderWidth: 4,
  },
  cornerTL: {
    top: 0,
    left: 0,
    borderRightWidth: 0,
    borderBottomWidth: 0,
    borderTopLeftRadius: borderRadius.lg,
  },
  cornerTR: {
    top: 0,
    right: 0,
    borderLeftWidth: 0,
    borderBottomWidth: 0,
    borderTopRightRadius: borderRadius.lg,
  },
  cornerBL: {
    bottom: 0,
    left: 0,
    borderRightWidth: 0,
    borderTopWidth: 0,
    borderBottomLeftRadius: borderRadius.lg,
  },
  cornerBR: {
    bottom: 0,
    right: 0,
    borderLeftWidth: 0,
    borderTopWidth: 0,
    borderBottomRightRadius: borderRadius.lg,
  },
  controls: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'space-between',
  },
  topControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
  },
  controlButton: {
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  instructions: {
    alignItems: 'center',
    marginTop: height * 0.55,
    gap: spacing.sm,
  },
  instructionText: {
    color: '#fff',
    fontWeight: '600',
  },
  instructionSubtext: {
    color: 'rgba(255, 255, 255, 0.7)',
  },
  bottomControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.xl,
  },
  galleryButton: {
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  captureButtonOuter: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  captureButton: {
    width: 64,
    height: 64,
    borderRadius: 32,
  },
  captureButtonContent: {
    width: 64,
    height: 64,
  },
  skipButton: {
    marginBottom: spacing.lg,
  },
  permissionContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  permissionTitle: {
    fontWeight: '600',
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  permissionText: {
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  permissionButton: {
    marginBottom: spacing.md,
    minWidth: 200,
  },
});

export default ScanReceiptScreen;
