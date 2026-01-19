/**
 * Forgot Password Screen
 * Password recovery flow
 */

import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  useTheme,
  HelperText,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { spacing, borderRadius } from '@app/theme';
import type { AuthStackScreenProps } from '@types/navigation';

type Props = AuthStackScreenProps<'ForgotPassword'>;

export const ForgotPasswordScreen: React.FC<Props> = ({ navigation }) => {
  const theme = useTheme();

  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

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

  const handleSubmit = async () => {
    if (!validateEmail(email)) {
      return;
    }

    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500));
      setIsSuccess(true);
    } catch (err) {
      setEmailError('Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    navigation.goBack();
  };

  if (isSuccess) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={styles.successContent}>
          <View
            style={[
              styles.successIcon,
              { backgroundColor: theme.colors.primaryContainer },
            ]}
          >
            <Icon
              name="email-check-outline"
              size={64}
              color={theme.colors.primary}
            />
          </View>

          <Text
            variant="headlineMedium"
            style={[styles.successTitle, { color: theme.colors.onBackground }]}
          >
            Check Your Email
          </Text>

          <Text
            variant="bodyLarge"
            style={[styles.successText, { color: theme.colors.onSurfaceVariant }]}
          >
            We've sent password reset instructions to{' '}
            <Text style={{ fontWeight: '600' }}>{email}</Text>
          </Text>

          <Text
            variant="bodyMedium"
            style={[styles.successHint, { color: theme.colors.onSurfaceVariant }]}
          >
            Didn't receive the email? Check your spam folder or try again.
          </Text>

          <Button
            mode="contained"
            onPress={handleBackToLogin}
            style={styles.successButton}
            contentStyle={styles.buttonContent}
          >
            Back to Login
          </Button>

          <Button
            mode="text"
            onPress={() => {
              setIsSuccess(false);
              setEmail('');
            }}
          >
            Try different email
          </Button>
        </View>
      </SafeAreaView>
    );
  }

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
          <View style={styles.header}>
            <View
              style={[
                styles.iconContainer,
                { backgroundColor: theme.colors.primaryContainer },
              ]}
            >
              <Icon
                name="lock-reset"
                size={48}
                color={theme.colors.primary}
              />
            </View>

            <Text
              variant="headlineMedium"
              style={[styles.title, { color: theme.colors.onBackground }]}
            >
              Forgot Password?
            </Text>

            <Text
              variant="bodyLarge"
              style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}
            >
              Enter your email address and we'll send you instructions to reset
              your password.
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
              autoFocus
              error={!!emailError}
              left={<TextInput.Icon icon="email-outline" />}
              style={styles.input}
            />
            <HelperText type="error" visible={!!emailError}>
              {emailError}
            </HelperText>

            <Button
              mode="contained"
              onPress={handleSubmit}
              loading={isLoading}
              disabled={isLoading}
              style={styles.submitButton}
              contentStyle={styles.buttonContent}
            >
              Send Reset Link
            </Button>

            <Button
              mode="text"
              onPress={handleBackToLogin}
              style={styles.backButton}
            >
              Back to Login
            </Button>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
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
  header: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  iconContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  title: {
    fontWeight: '700',
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  subtitle: {
    textAlign: 'center',
    lineHeight: 24,
    paddingHorizontal: spacing.md,
  },
  form: {
    alignItems: 'stretch',
  },
  input: {
    marginBottom: spacing.xs,
  },
  submitButton: {
    marginTop: spacing.md,
    borderRadius: borderRadius.lg,
  },
  buttonContent: {
    paddingVertical: spacing.sm,
  },
  backButton: {
    marginTop: spacing.md,
  },
  // Success state styles
  successContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  successIcon: {
    width: 120,
    height: 120,
    borderRadius: 60,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xl,
  },
  successTitle: {
    fontWeight: '700',
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  successText: {
    textAlign: 'center',
    marginBottom: spacing.md,
    lineHeight: 24,
  },
  successHint: {
    textAlign: 'center',
    marginBottom: spacing.xl,
    paddingHorizontal: spacing.lg,
  },
  successButton: {
    width: '100%',
    borderRadius: borderRadius.lg,
    marginBottom: spacing.md,
  },
});

export default ForgotPasswordScreen;
