/**
 * Barcode Scanner - Scan product barcodes and QR codes
 */

import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Vibration,
  Platform,
} from 'react-native';
import { router } from 'expo-router';
import { Camera, CameraView, BarcodeScanningResult } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';

const COLORS = {
  primary: '#1E40AF',
  text: '#FFFFFF',
  overlay: 'rgba(0, 0, 0, 0.6)',
  scanBox: 'rgba(255, 255, 255, 0.3)',
  success: '#10B981',
};

interface ScanResult {
  type: string;
  data: string;
}

export default function BarcodeScanner() {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanned, setScanned] = useState(false);
  const [flashEnabled, setFlashEnabled] = useState(false);
  const [lastScanned, setLastScanned] = useState<ScanResult | null>(null);

  useEffect(() => {
    const getCameraPermissions = async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
    };

    getCameraPermissions();
  }, []);

  const handleBarCodeScanned = ({ type, data }: BarcodeScanningResult) => {
    if (scanned) return;

    setScanned(true);
    setLastScanned({ type, data });

    if (Platform.OS !== 'web') {
      Vibration.vibrate(100);
    }

    Alert.alert(
      'Barcode Scanned',
      `Type: ${type}\nData: ${data}`,
      [
        {
          text: 'Scan Again',
          onPress: () => setScanned(false),
        },
        {
          text: 'Add to Inventory',
          onPress: () => handleAddToInventory(data),
        },
        {
          text: 'Search Product',
          onPress: () => handleSearchProduct(data),
          style: 'default',
        },
      ]
    );
  };

  const handleAddToInventory = (barcode: string) => {
    router.push({
      pathname: '/inventory/create',
      params: { barcode },
    } as any);
  };

  const handleSearchProduct = (barcode: string) => {
    router.push({
      pathname: '/inventory',
      params: { search: barcode },
    } as any);
  };

  if (hasPermission === null) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.messageText}>Requesting camera permission...</Text>
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="camera-outline" size={64} color={COLORS.primary} />
        <Text style={styles.messageText}>Camera access denied</Text>
        <Text style={styles.subText}>
          Please enable camera permissions in your device settings
        </Text>
        <TouchableOpacity style={styles.button} onPress={() => router.back()}>
          <Text style={styles.buttonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        style={StyleSheet.absoluteFillObject}
        facing="back"
        enableTorch={flashEnabled}
        barcodeScannerSettings={{
          barcodeTypes: [
            'ean13',
            'ean8',
            'upc_a',
            'upc_e',
            'code128',
            'code39',
            'code93',
            'codabar',
            'itf14',
            'qr',
            'pdf417',
            'aztec',
            'datamatrix',
          ],
        }}
        onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
      />

      <View style={styles.overlay}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.headerButton} onPress={() => router.back()}>
            <Ionicons name="close" size={28} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.title}>Scan Barcode</Text>
          <TouchableOpacity
            style={styles.headerButton}
            onPress={() => setFlashEnabled(!flashEnabled)}
          >
            <Ionicons
              name={flashEnabled ? 'flash' : 'flash-off'}
              size={24}
              color={COLORS.text}
            />
          </TouchableOpacity>
        </View>

        <View style={styles.scanArea}>
          <View style={styles.scanBox}>
            <View style={[styles.corner, styles.topLeft]} />
            <View style={[styles.corner, styles.topRight]} />
            <View style={[styles.corner, styles.bottomLeft]} />
            <View style={[styles.corner, styles.bottomRight]} />
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.instructionText}>
            {scanned ? 'Barcode scanned!' : 'Align barcode within the frame'}
          </Text>

          {lastScanned && (
            <View style={styles.lastScannedContainer}>
              <Ionicons name="checkmark-circle" size={20} color={COLORS.success} />
              <Text style={styles.lastScannedText}>
                Last: {lastScanned.data.substring(0, 20)}
                {lastScanned.data.length > 20 ? '...' : ''}
              </Text>
            </View>
          )}

          <View style={styles.actions}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={() => router.push('/scanner/document')}
            >
              <Ionicons name="document-text-outline" size={24} color={COLORS.text} />
              <Text style={styles.actionText}>Document</Text>
            </TouchableOpacity>

            {scanned && (
              <TouchableOpacity
                style={[styles.actionButton, styles.rescanButton]}
                onPress={() => setScanned(false)}
              >
                <Ionicons name="refresh" size={24} color={COLORS.text} />
                <Text style={styles.actionText}>Scan Again</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#F3F4F6',
  },
  messageText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1F2937',
    marginTop: 16,
    textAlign: 'center',
  },
  subText: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  button: {
    marginTop: 24,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
  },
  buttonText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 60,
    backgroundColor: COLORS.overlay,
  },
  headerButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  scanArea: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanBox: {
    width: 280,
    height: 180,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: COLORS.text,
  },
  topLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 4,
    borderLeftWidth: 4,
    borderTopLeftRadius: 12,
  },
  topRight: {
    top: 0,
    right: 0,
    borderTopWidth: 4,
    borderRightWidth: 4,
    borderTopRightRadius: 12,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
    borderBottomLeftRadius: 12,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 4,
    borderRightWidth: 4,
    borderBottomRightRadius: 12,
  },
  footer: {
    padding: 24,
    paddingBottom: 48,
    backgroundColor: COLORS.overlay,
    alignItems: 'center',
  },
  instructionText: {
    fontSize: 16,
    color: COLORS.text,
    marginBottom: 16,
  },
  lastScannedContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  lastScannedText: {
    fontSize: 14,
    color: COLORS.text,
  },
  actions: {
    flexDirection: 'row',
    gap: 16,
  },
  actionButton: {
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    minWidth: 80,
  },
  rescanButton: {
    backgroundColor: COLORS.primary,
  },
  actionText: {
    fontSize: 12,
    color: COLORS.text,
    marginTop: 4,
  },
});
