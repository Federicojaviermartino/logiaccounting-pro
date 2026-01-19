/**
 * Biometric Screen
 * Face ID / Touch ID / Fingerprint authentication
 */

import React, { useEffect, useState } from 'react';
import { StyleSheet, View, Platform } from 'react-native';
import { Text, Button, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';
import { useDispatch } from 'react-redux';

import { spacing } from '@app/theme';
import { setAuthenticated } from '@store/slices/authSlice';
import { AppDispatch } from '@store/index';
import type { AuthStackScreenProps } from '@types/navigation';

type Props = AuthStackScreenProps<'Biometric'>;

const rnBiometrics = new ReactNativeBiometrics();

export const BiometricScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const [biometryType, setBiometryType] = useState<BiometryTypes | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  useEffect(() => {
    checkBiometrics();
  }, []);

  const checkBiometrics = async () => {
    try {
      const { available, biometryType } = await rnBiometrics.isSensorAvailable();
      if (available && biometryType) {
        setBiometryType(biometryType);
        // Auto-prompt on mount
        setTimeout(() => {
          authenticate();
        }, 500);
      } else {
        // Biometrics not available, fallback to login
        navigation.replace('Login');
      }
    } catch (err) {
      navigation.replace('Login');
    }
  };

  const authenticate = async () => {
    if (isAuthenticating) return;

    setIsAuthenticating(true);
    setError(null);

    try {
      const promptMessage = getBiometricPromptMessage();
      const { success } = await rnBiometrics.simplePrompt({
        promptMessage,
        cancelButtonText: 'Use Password',
      });

      if (success) {
        dispatch(setAuthenticated(true));
      } else {
        setError('Authentication cancelled');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setIsAuthenticating(false);
    }
  };

  const getBiometricIcon = () => {
    switch (biometryType) {
      case BiometryTypes.FaceID:
        return 'face-recognition';
      case BiometryTypes.TouchID:
        return 'fingerprint';
      case BiometryTypes.Biometrics:
        return Platform.OS === 'ios' ? 'face-recognition' : 'fingerprint';
      default:
        return 'shield-lock';
    }
  };

  const getBiometricLabel = () => {
    switch (biometryType) {
      case BiometryTypes.FaceID:
        return 'Face ID';
      case BiometryTypes.TouchID:
        return 'Touch ID';
      case BiometryTypes.Biometrics:
        return Platform.OS === 'ios' ? 'Face ID' : 'Fingerprint';
      default:
        return 'Biometric';
    }
  };

  const getBiometricPromptMessage = () => {
    return `Authenticate with ${getBiometricLabel()} to access LogiAccounting Pro`;
  };

  const handleUsePassword = () => {
    navigation.replace('Login');
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.content}>
        <View style={styles.iconContainer}>
          <View
            style={[
              styles.iconBackground,
              { backgroundColor: theme.colors.primaryContainer },
            ]}
          >
            <Icon
              name={getBiometricIcon()}
              size={80}
              color={theme.colors.primary}
            />
          </View>
        </View>

        <Text
          variant="headlineMedium"
          style={[styles.title, { color: theme.colors.onBackground }]}
        >
          Welcome Back
        </Text>

        <Text
          variant="bodyLarge"
          style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
        >
          Use {getBiometricLabel()} to unlock
        </Text>

        {error && (
          <View style={[styles.errorContainer, { backgroundColor: theme.colors.errorContainer }]}>
            <Icon name="alert-circle" size={20} color={theme.colors.error} />
            <Text
              variant="bodyMedium"
              style={[styles.errorText, { color: theme.colors.error }]}
            >
              {error}
            </Text>
          </View>
        )}

        <Button
          mode="contained"
          onPress={authenticate}
          loading={isAuthenticating}
          disabled={isAuthenticating}
          icon={getBiometricIcon()}
          style={styles.primaryButton}
          contentStyle={styles.buttonContent}
        >
          {isAuthenticating ? 'Authenticating...' : `Use ${getBiometricLabel()}`}
        </Button>

        <Button
          mode="outlined"
          onPress={handleUsePassword}
          style={styles.secondaryButton}
          contentStyle={styles.buttonContent}
        >
          Use Password Instead
        </Button>
      </View>

      <View style={styles.footer}>
        <Text
          variant="bodySmall"
          style={{ color: theme.colors.onSurfaceVariant, textAlign: 'center' }}
        >
          Your biometric data never leaves your device
        </Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  iconContainer: {
    marginBottom: spacing.xl,
  },
  iconBackground: {
    width: 160,
    height: 160,
    borderRadius: 80,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontWeight: '700',
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  subtitle: {
    textAlign: 'center',
    marginBottom: spacing.xl,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: 12,
    marginBottom: spacing.lg,
    gap: spacing.sm,
  },
  errorText: {
    flex: 1,
  },
  primaryButton: {
    width: '100%',
    marginBottom: spacing.md,
    borderRadius: 12,
  },
  secondaryButton: {
    width: '100%',
    borderRadius: 12,
  },
  buttonContent: {
    paddingVertical: spacing.sm,
  },
  footer: {
    padding: spacing.lg,
  },
});

export default BiometricScreen;
