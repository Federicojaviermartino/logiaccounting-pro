/**
 * Document Scanner - Capture and process receipts/invoices
 */

import { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
  ScrollView,
} from 'react-native';
import { router } from 'expo-router';
import { Camera, CameraView, CameraCapturedPicture } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';

const COLORS = {
  primary: '#1E40AF',
  text: '#FFFFFF',
  textDark: '#1F2937',
  overlay: 'rgba(0, 0, 0, 0.6)',
  background: '#F3F4F6',
  white: '#FFFFFF',
};

interface ProcessedDocument {
  uri: string;
  extractedData?: {
    vendor?: string;
    date?: string;
    total?: string;
    items?: string[];
  };
}

export default function DocumentScanner() {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [processedDoc, setProcessedDoc] = useState<ProcessedDocument | null>(null);
  const cameraRef = useRef<CameraView>(null);

  useState(() => {
    const getPermissions = async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
    };
    getPermissions();
  });

  const takePicture = async () => {
    if (cameraRef.current) {
      try {
        const photo = await cameraRef.current.takePictureAsync({
          quality: 0.8,
          base64: false,
        });
        if (photo) {
          setCapturedImage(photo.uri);
          processDocument(photo.uri);
        }
      } catch (error) {
        console.error('Error taking picture:', error);
        Alert.alert('Error', 'Failed to capture image');
      }
    }
  };

  const pickImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.8,
        allowsEditing: true,
      });

      if (!result.canceled && result.assets[0]) {
        setCapturedImage(result.assets[0].uri);
        processDocument(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const processDocument = async (uri: string) => {
    setProcessing(true);

    try {
      await new Promise(resolve => setTimeout(resolve, 2000));

      setProcessedDoc({
        uri,
        extractedData: {
          vendor: 'Sample Store',
          date: new Date().toLocaleDateString(),
          total: '$125.99',
          items: ['Product A - $50.00', 'Product B - $75.99'],
        },
      });
    } catch (error) {
      Alert.alert('Processing Error', 'Failed to process document');
    } finally {
      setProcessing(false);
    }
  };

  const retake = () => {
    setCapturedImage(null);
    setProcessedDoc(null);
  };

  const saveDocument = () => {
    Alert.alert(
      'Save Document',
      'Document saved successfully!',
      [
        {
          text: 'Create Invoice',
          onPress: () => router.push('/invoices/create'),
        },
        {
          text: 'Create Expense',
          onPress: () => router.push('/expenses/create'),
        },
        {
          text: 'Done',
          style: 'cancel',
          onPress: () => router.back(),
        },
      ]
    );
  };

  if (hasPermission === null) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.messageText}>Requesting camera permission...</Text>
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="camera-outline" size={64} color={COLORS.primary} />
        <Text style={styles.messageText}>Camera access denied</Text>
        <TouchableOpacity style={styles.button} onPress={() => router.back()}>
          <Text style={styles.buttonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (capturedImage) {
    return (
      <View style={styles.previewContainer}>
        <View style={styles.previewHeader}>
          <TouchableOpacity style={styles.backButton} onPress={retake}>
            <Ionicons name="arrow-back" size={24} color={COLORS.textDark} />
          </TouchableOpacity>
          <Text style={styles.previewTitle}>Document Preview</Text>
          <View style={{ width: 40 }} />
        </View>

        <ScrollView style={styles.previewContent}>
          <Image source={{ uri: capturedImage }} style={styles.previewImage} />

          {processing ? (
            <View style={styles.processingContainer}>
              <ActivityIndicator size="large" color={COLORS.primary} />
              <Text style={styles.processingText}>Processing document...</Text>
            </View>
          ) : processedDoc?.extractedData ? (
            <View style={styles.extractedData}>
              <Text style={styles.sectionTitle}>Extracted Information</Text>

              <View style={styles.dataRow}>
                <Text style={styles.dataLabel}>Vendor:</Text>
                <Text style={styles.dataValue}>{processedDoc.extractedData.vendor}</Text>
              </View>

              <View style={styles.dataRow}>
                <Text style={styles.dataLabel}>Date:</Text>
                <Text style={styles.dataValue}>{processedDoc.extractedData.date}</Text>
              </View>

              <View style={styles.dataRow}>
                <Text style={styles.dataLabel}>Total:</Text>
                <Text style={[styles.dataValue, styles.totalValue]}>
                  {processedDoc.extractedData.total}
                </Text>
              </View>

              {processedDoc.extractedData.items && (
                <View style={styles.itemsSection}>
                  <Text style={styles.dataLabel}>Items:</Text>
                  {processedDoc.extractedData.items.map((item, index) => (
                    <Text key={index} style={styles.itemText}>
                      {item}
                    </Text>
                  ))}
                </View>
              )}
            </View>
          ) : null}
        </ScrollView>

        <View style={styles.previewActions}>
          <TouchableOpacity style={styles.retakeButton} onPress={retake}>
            <Ionicons name="refresh" size={20} color={COLORS.primary} />
            <Text style={styles.retakeText}>Retake</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.saveButton, processing && styles.buttonDisabled]}
            onPress={saveDocument}
            disabled={processing}
          >
            <Ionicons name="checkmark" size={20} color={COLORS.white} />
            <Text style={styles.saveText}>Save</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={StyleSheet.absoluteFillObject}
        facing="back"
      />

      <View style={styles.overlay}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.headerButton} onPress={() => router.back()}>
            <Ionicons name="close" size={28} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.title}>Scan Document</Text>
          <TouchableOpacity style={styles.headerButton} onPress={pickImage}>
            <Ionicons name="images-outline" size={24} color={COLORS.text} />
          </TouchableOpacity>
        </View>

        <View style={styles.scanArea}>
          <View style={styles.documentFrame}>
            <View style={[styles.corner, styles.topLeft]} />
            <View style={[styles.corner, styles.topRight]} />
            <View style={[styles.corner, styles.bottomLeft]} />
            <View style={[styles.corner, styles.bottomRight]} />
          </View>
          <Text style={styles.guideText}>
            Align document within the frame
          </Text>
        </View>

        <View style={styles.footer}>
          <TouchableOpacity style={styles.captureButton} onPress={takePicture}>
            <View style={styles.captureInner} />
          </TouchableOpacity>
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
    backgroundColor: COLORS.background,
  },
  messageText: {
    fontSize: 16,
    color: COLORS.textDark,
    marginTop: 16,
  },
  button: {
    marginTop: 24,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
  },
  buttonText: {
    color: COLORS.white,
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
  documentFrame: {
    width: '85%',
    aspectRatio: 0.707,
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
  },
  topRight: {
    top: 0,
    right: 0,
    borderTopWidth: 4,
    borderRightWidth: 4,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 4,
    borderRightWidth: 4,
  },
  guideText: {
    color: COLORS.text,
    fontSize: 14,
    marginTop: 24,
  },
  footer: {
    padding: 32,
    paddingBottom: 48,
    backgroundColor: COLORS.overlay,
    alignItems: 'center',
  },
  captureButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: COLORS.text,
    justifyContent: 'center',
    alignItems: 'center',
  },
  captureInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: COLORS.text,
    borderWidth: 3,
    borderColor: '#000',
  },
  previewContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  previewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 60,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  previewTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textDark,
  },
  previewContent: {
    flex: 1,
  },
  previewImage: {
    width: '100%',
    height: 300,
    resizeMode: 'contain',
    backgroundColor: '#000',
  },
  processingContainer: {
    padding: 32,
    alignItems: 'center',
  },
  processingText: {
    marginTop: 16,
    fontSize: 16,
    color: COLORS.textDark,
  },
  extractedData: {
    padding: 16,
    backgroundColor: COLORS.white,
    margin: 16,
    borderRadius: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textDark,
    marginBottom: 16,
  },
  dataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  dataLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  dataValue: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.textDark,
  },
  totalValue: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.primary,
  },
  itemsSection: {
    marginTop: 12,
  },
  itemText: {
    fontSize: 13,
    color: COLORS.textDark,
    paddingVertical: 4,
    paddingLeft: 12,
  },
  previewActions: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
    backgroundColor: COLORS.white,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  retakeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.primary,
    gap: 8,
  },
  retakeText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
  saveButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    backgroundColor: COLORS.primary,
    gap: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  saveText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
  },
});
