/**
 * Barcode Scanner Screen
 * Camera-based barcode/QR scanning
 */

import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Animated, Dimensions } from 'react-native';
import { Text, Button, useTheme, IconButton } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius, colors } from '@app/theme';
import type { InventoryStackScreenProps } from '@types/navigation';

type Props = InventoryStackScreenProps<'BarcodeScanner'>;

const { width } = Dimensions.get('window');
const SCAN_AREA_SIZE = width * 0.7;

export const BarcodeScannerScreen: React.FC<Props> = ({ route, navigation }) => {
  const theme = useTheme();
  const { returnTo } = route.params;
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanned, setScanned] = useState(false);
  const [flashOn, setFlashOn] = useState(false);

  // Animation for scanning line
  const scanLineAnim = React.useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Simulate permission check
    // In real implementation, use react-native-camera or expo-camera
    const checkPermission = async () => {
      // const { status } = await Camera.requestCameraPermissionsAsync();
      // setHasPermission(status === 'granted');
      setHasPermission(true); // Simulated
    };
    checkPermission();

    // Start scanning animation
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(scanLineAnim, {
          toValue: SCAN_AREA_SIZE - 4,
          duration: 2000,
          useNativeDriver: true,
        }),
        Animated.timing(scanLineAnim, {
          toValue: 0,
          duration: 2000,
          useNativeDriver: true,
        }),
      ])
    );
    animation.start();

    return () => animation.stop();
  }, []);

  const handleBarCodeScanned = (data: string) => {
    if (scanned) return;

    setScanned(true);
    // Navigate to inventory detail or search with the scanned code
    // For now, just go back
    navigation.goBack();
  };

  const handleClose = () => {
    navigation.goBack();
  };

  const handleManualEntry = () => {
    navigation.goBack();
    // Could navigate to a manual entry screen
  };

  if (hasPermission === null) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <Text>Requesting camera permission...</Text>
      </View>
    );
  }

  if (hasPermission === false) {
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
            Please grant camera permission to scan barcodes
          </Text>
          <Button
            mode="contained"
            onPress={() => {
              // Open app settings
            }}
            style={styles.permissionButton}
          >
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
      {/* Camera View Placeholder */}
      <View style={[styles.cameraPlaceholder, { backgroundColor: '#000' }]}>
        {/* In production, replace with actual Camera component */}
        <View style={styles.overlay}>
          {/* Top overlay */}
          <View style={[styles.overlaySection, styles.overlayTop]} />

          {/* Middle section with scan area */}
          <View style={styles.overlayMiddle}>
            <View style={styles.overlaySide} />
            <View style={styles.scanArea}>
              {/* Corner markers */}
              <View style={[styles.corner, styles.cornerTL]} />
              <View style={[styles.corner, styles.cornerTR]} />
              <View style={[styles.corner, styles.cornerBL]} />
              <View style={[styles.corner, styles.cornerBR]} />

              {/* Scanning line */}
              <Animated.View
                style={[
                  styles.scanLine,
                  { transform: [{ translateY: scanLineAnim }] },
                ]}
              />
            </View>
            <View style={styles.overlaySide} />
          </View>

          {/* Bottom overlay */}
          <View style={[styles.overlaySection, styles.overlayBottom]} />
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
            <Text variant="titleMedium" style={styles.instructionText}>
              Position barcode within frame
            </Text>
            <Text variant="bodySmall" style={styles.instructionSubtext}>
              Scanning will happen automatically
            </Text>
          </View>

          <View style={styles.bottomControls}>
            <Button
              mode="contained-tonal"
              onPress={handleManualEntry}
              style={styles.manualButton}
            >
              Enter Code Manually
            </Button>
          </View>
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
  overlaySection: {
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  overlayTop: {
    flex: 1,
  },
  overlayMiddle: {
    flexDirection: 'row',
  },
  overlaySide: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  overlayBottom: {
    flex: 1,
  },
  scanArea: {
    width: SCAN_AREA_SIZE,
    height: SCAN_AREA_SIZE,
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
  },
  corner: {
    position: 'absolute',
    width: 32,
    height: 32,
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
  scanLine: {
    position: 'absolute',
    left: 4,
    right: 4,
    height: 2,
    backgroundColor: colors.primary,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 8,
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
    marginTop: SCAN_AREA_SIZE + 40,
  },
  instructionText: {
    color: '#fff',
    fontWeight: '600',
    marginBottom: spacing.xs,
  },
  instructionSubtext: {
    color: 'rgba(255, 255, 255, 0.7)',
  },
  bottomControls: {
    padding: spacing.lg,
    alignItems: 'center',
  },
  manualButton: {
    minWidth: 200,
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

export default BarcodeScannerScreen;
