/**
 * PIN Screen
 * Setup and verify PIN code
 */

import React, { useState, useRef, useEffect } from 'react';
import { StyleSheet, View, Pressable, Vibration, Animated } from 'react-native';
import { Text, useTheme, IconButton } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useDispatch, useSelector } from 'react-redux';

import { spacing, borderRadius } from '@app/theme';
import { setPin, verifyPin } from '@store/slices/authSlice';
import { AppDispatch, RootState } from '@store/index';
import type { AuthStackScreenProps } from '@types/navigation';

type Props = AuthStackScreenProps<'Pin'>;

const PIN_LENGTH = 6;

export const PinScreen: React.FC<Props> = ({ route, navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const { isLoading, error } = useSelector((state: RootState) => state.auth);

  const mode = route.params?.mode || 'verify';
  const [pin, setLocalPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [step, setStep] = useState<'enter' | 'confirm'>('enter');
  const [localError, setLocalError] = useState<string | null>(null);

  const shakeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (pin.length === PIN_LENGTH) {
      handlePinComplete();
    }
  }, [pin]);

  useEffect(() => {
    if (confirmPin.length === PIN_LENGTH) {
      handleConfirmComplete();
    }
  }, [confirmPin]);

  const shake = () => {
    Vibration.vibrate(100);
    Animated.sequence([
      Animated.timing(shakeAnim, {
        toValue: 10,
        duration: 50,
        useNativeDriver: true,
      }),
      Animated.timing(shakeAnim, {
        toValue: -10,
        duration: 50,
        useNativeDriver: true,
      }),
      Animated.timing(shakeAnim, {
        toValue: 10,
        duration: 50,
        useNativeDriver: true,
      }),
      Animated.timing(shakeAnim, {
        toValue: 0,
        duration: 50,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const handlePinComplete = async () => {
    if (mode === 'verify') {
      try {
        await dispatch(verifyPin(pin)).unwrap();
      } catch (err) {
        shake();
        setLocalPin('');
        setLocalError('Incorrect PIN. Please try again.');
      }
    } else {
      // Setup mode - move to confirm step
      setStep('confirm');
    }
  };

  const handleConfirmComplete = async () => {
    if (pin === confirmPin) {
      try {
        await dispatch(setPin(pin)).unwrap();
        // PIN set successfully, auth state will update
      } catch (err) {
        setLocalError('Failed to set PIN. Please try again.');
        resetSetup();
      }
    } else {
      shake();
      setLocalError('PINs do not match. Please try again.');
      resetSetup();
    }
  };

  const resetSetup = () => {
    setLocalPin('');
    setConfirmPin('');
    setStep('enter');
  };

  const handleKeyPress = (key: string) => {
    setLocalError(null);
    const currentPin = step === 'confirm' ? confirmPin : pin;
    const setCurrentPin = step === 'confirm' ? setConfirmPin : setLocalPin;

    if (currentPin.length < PIN_LENGTH) {
      setCurrentPin(currentPin + key);
    }
  };

  const handleDelete = () => {
    const currentPin = step === 'confirm' ? confirmPin : pin;
    const setCurrentPin = step === 'confirm' ? setConfirmPin : setLocalPin;

    if (currentPin.length > 0) {
      setCurrentPin(currentPin.slice(0, -1));
    }
  };

  const handleUsePassword = () => {
    navigation.replace('Login');
  };

  const currentPin = step === 'confirm' ? confirmPin : pin;

  const getTitle = () => {
    if (mode === 'setup') {
      return step === 'confirm' ? 'Confirm PIN' : 'Create PIN';
    }
    return 'Enter PIN';
  };

  const getSubtitle = () => {
    if (mode === 'setup') {
      return step === 'confirm'
        ? 'Re-enter your PIN to confirm'
        : 'Create a 6-digit PIN for quick access';
    }
    return 'Enter your 6-digit PIN to unlock';
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text
          variant="headlineMedium"
          style={[styles.title, { color: theme.colors.onBackground }]}
        >
          {getTitle()}
        </Text>
        <Text
          variant="bodyLarge"
          style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
        >
          {getSubtitle()}
        </Text>
      </View>

      <Animated.View
        style={[
          styles.dotsContainer,
          { transform: [{ translateX: shakeAnim }] },
        ]}
      >
        {Array.from({ length: PIN_LENGTH }).map((_, index) => (
          <View
            key={index}
            style={[
              styles.dot,
              {
                backgroundColor:
                  index < currentPin.length
                    ? theme.colors.primary
                    : theme.colors.surfaceVariant,
                borderColor:
                  index < currentPin.length
                    ? theme.colors.primary
                    : theme.colors.outline,
              },
            ]}
          />
        ))}
      </Animated.View>

      {(localError || error) && (
        <View style={styles.errorContainer}>
          <Text
            variant="bodyMedium"
            style={[styles.errorText, { color: theme.colors.error }]}
          >
            {localError || error}
          </Text>
        </View>
      )}

      <View style={styles.keypad}>
        {[
          ['1', '2', '3'],
          ['4', '5', '6'],
          ['7', '8', '9'],
          ['', '0', 'delete'],
        ].map((row, rowIndex) => (
          <View key={rowIndex} style={styles.keypadRow}>
            {row.map((key, keyIndex) => {
              if (key === '') {
                return <View key={keyIndex} style={styles.keyPlaceholder} />;
              }
              if (key === 'delete') {
                return (
                  <Pressable
                    key={keyIndex}
                    onPress={handleDelete}
                    style={({ pressed }) => [
                      styles.key,
                      pressed && { opacity: 0.6 },
                    ]}
                  >
                    <Icon
                      name="backspace-outline"
                      size={28}
                      color={theme.colors.onSurface}
                    />
                  </Pressable>
                );
              }
              return (
                <Pressable
                  key={keyIndex}
                  onPress={() => handleKeyPress(key)}
                  style={({ pressed }) => [
                    styles.key,
                    { backgroundColor: theme.colors.surfaceVariant },
                    pressed && { backgroundColor: theme.colors.primary + '30' },
                  ]}
                >
                  <Text
                    variant="headlineMedium"
                    style={{ color: theme.colors.onSurface }}
                  >
                    {key}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        ))}
      </View>

      {mode === 'verify' && (
        <View style={styles.footer}>
          <Pressable onPress={handleUsePassword}>
            <Text
              variant="bodyMedium"
              style={{ color: theme.colors.primary }}
            >
              Use password instead
            </Text>
          </Pressable>
        </View>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    alignItems: 'center',
    paddingTop: spacing.xxl,
    paddingHorizontal: spacing.lg,
  },
  title: {
    fontWeight: '700',
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  subtitle: {
    textAlign: 'center',
  },
  dotsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: spacing.xxl,
    gap: spacing.md,
  },
  dot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 2,
  },
  errorContainer: {
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    marginBottom: spacing.md,
  },
  errorText: {
    textAlign: 'center',
  },
  keypad: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing.xl,
    gap: spacing.md,
  },
  keypadRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: spacing.lg,
  },
  key: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  keyPlaceholder: {
    width: 80,
    height: 80,
  },
  footer: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
});

export default PinScreen;
