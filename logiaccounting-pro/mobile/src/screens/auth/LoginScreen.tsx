/**
 * Login Screen
 * Email/password authentication with remember me and biometric setup
 */

import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Image,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  useTheme,
  Checkbox,
  HelperText,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useDispatch, useSelector } from 'react-redux';

import { spacing, borderRadius } from '@app/theme';
import { login } from '@store/slices/authSlice';
import { AppDispatch, RootState } from '@store/index';
import { LoadingSpinner } from '@components/common';
import type { AuthStackScreenProps } from '@types/navigation';

type Props = AuthStackScreenProps<'Login'>;

export const LoginScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const { isLoading, error } = useSelector((state: RootState) => state.auth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const validateEmail = (text: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!text) {
      setEmailError('Email is required');
      return false;
    }
    if (!emailRegex.test(text)) {
      setEmailError('Please enter a valid email');
      return false;
    }
    setEmailError('');
    return true;
  };

  const validatePassword = (text: string) => {
    if (!text) {
      setPasswordError('Password is required');
      return false;
    }
    if (text.length < 6) {
      setPasswordError('Password must be at least 6 characters');
      return false;
    }
    setPasswordError('');
    return true;
  };

  const handleLogin = async () => {
    const isEmailValid = validateEmail(email);
    const isPasswordValid = validatePassword(password);

    if (!isEmailValid || !isPasswordValid) {
      return;
    }

    try {
      await dispatch(login({ email, password })).unwrap();
    } catch (err) {
      // Error is handled by the slice
    }
  };

  const handleForgotPassword = () => {
    navigation.navigate('ForgotPassword');
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.logoContainer}>
            <View
              style={[
                styles.logoPlaceholder,
                { backgroundColor: theme.colors.primary },
              ]}
            >
              <Text style={[styles.logoText, { color: theme.colors.onPrimary }]}>
                LA
              </Text>
            </View>
            <Text
              variant="headlineMedium"
              style={[styles.appName, { color: theme.colors.onBackground }]}
            >
              LogiAccounting Pro
            </Text>
            <Text
              variant="bodyMedium"
              style={[styles.tagline, { color: theme.colors.onSurfaceVariant }]}
            >
              Manage your business on the go
            </Text>
          </View>

          <View style={styles.form}>
            <TextInput
              label="Email"
              value={email}
              onChangeText={(text) => {
                setEmail(text);
                if (emailError) validateEmail(text);
              }}
              onBlur={() => validateEmail(email)}
              mode="outlined"
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              error={!!emailError}
              left={<TextInput.Icon icon="email-outline" />}
              style={styles.input}
            />
            <HelperText type="error" visible={!!emailError}>
              {emailError}
            </HelperText>

            <TextInput
              label="Password"
              value={password}
              onChangeText={(text) => {
                setPassword(text);
                if (passwordError) validatePassword(text);
              }}
              onBlur={() => validatePassword(password)}
              mode="outlined"
              secureTextEntry={!showPassword}
              autoCapitalize="none"
              error={!!passwordError}
              left={<TextInput.Icon icon="lock-outline" />}
              right={
                <TextInput.Icon
                  icon={showPassword ? 'eye-off' : 'eye'}
                  onPress={() => setShowPassword(!showPassword)}
                />
              }
              style={styles.input}
            />
            <HelperText type="error" visible={!!passwordError}>
              {passwordError}
            </HelperText>

            <View style={styles.options}>
              <View style={styles.rememberMe}>
                <Checkbox
                  status={rememberMe ? 'checked' : 'unchecked'}
                  onPress={() => setRememberMe(!rememberMe)}
                />
                <Text
                  variant="bodyMedium"
                  style={{ color: theme.colors.onSurface }}
                  onPress={() => setRememberMe(!rememberMe)}
                >
                  Remember me
                </Text>
              </View>
              <Button
                mode="text"
                onPress={handleForgotPassword}
                compact
              >
                Forgot password?
              </Button>
            </View>

            {error && (
              <HelperText type="error" visible style={styles.errorText}>
                {error}
              </HelperText>
            )}

            <Button
              mode="contained"
              onPress={handleLogin}
              loading={isLoading}
              disabled={isLoading}
              style={styles.loginButton}
              contentStyle={styles.loginButtonContent}
            >
              Sign In
            </Button>
          </View>

          <View style={styles.footer}>
            <Text
              variant="bodySmall"
              style={{ color: theme.colors.onSurfaceVariant }}
            >
              Secure login protected by industry-standard encryption
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      {isLoading && <LoadingSpinner fullScreen message="Signing in..." />}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: spacing.lg,
    justifyContent: 'center',
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: spacing.xxl,
  },
  logoPlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  logoText: {
    fontSize: 32,
    fontWeight: '700',
  },
  appName: {
    fontWeight: '700',
    marginBottom: spacing.xs,
  },
  tagline: {
    textAlign: 'center',
  },
  form: {
    marginBottom: spacing.xl,
  },
  input: {
    marginBottom: spacing.xs,
  },
  options: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginVertical: spacing.sm,
  },
  rememberMe: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  errorText: {
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  loginButton: {
    marginTop: spacing.md,
    borderRadius: borderRadius.lg,
  },
  loginButtonContent: {
    paddingVertical: spacing.sm,
  },
  footer: {
    alignItems: 'center',
    paddingTop: spacing.lg,
  },
});

export default LoginScreen;
