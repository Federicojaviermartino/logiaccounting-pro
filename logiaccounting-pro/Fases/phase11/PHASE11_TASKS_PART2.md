# LogiAccounting Pro - Phase 11 Tasks Part 2

## NAVIGATION & AUTHENTICATION SCREENS

---

## TASK 4: NAVIGATION SYSTEM

### 4.1 Create Type Definitions

**File:** `mobile/src/types/navigation.ts`

```typescript
/**
 * Navigation Type Definitions
 */

import { NavigatorScreenParams } from '@react-navigation/native';

// Auth Stack
export type AuthStackParamList = {
  Login: undefined;
  Biometric: undefined;
  Pin: { mode: 'verify' | 'setup' };
  ForgotPassword: undefined;
};

// Main Tab Navigator
export type MainTabParamList = {
  DashboardTab: undefined;
  InventoryTab: NavigatorScreenParams<InventoryStackParamList>;
  TransactionsTab: NavigatorScreenParams<TransactionsStackParamList>;
  PaymentsTab: NavigatorScreenParams<PaymentsStackParamList>;
  MoreTab: NavigatorScreenParams<MoreStackParamList>;
};

// Inventory Stack
export type InventoryStackParamList = {
  InventoryList: undefined;
  InventoryDetail: { id: string };
  Scanner: { mode: 'lookup' | 'movement' };
  Movement: { materialId?: string };
};

// Transactions Stack
export type TransactionsStackParamList = {
  TransactionList: undefined;
  TransactionForm: { id?: string };
  DocumentScan: undefined;
};

// Payments Stack
export type PaymentsStackParamList = {
  PaymentList: undefined;
  PaymentDetail: { id: string };
  RecordPayment: { id: string };
};

// Projects Stack
export type ProjectsStackParamList = {
  ProjectList: undefined;
  ProjectDetail: { id: string };
};

// More Stack (Settings, Profile, etc.)
export type MoreStackParamList = {
  MoreMenu: undefined;
  Projects: NavigatorScreenParams<ProjectsStackParamList>;
  Analytics: undefined;
  Settings: undefined;
  Profile: undefined;
  Sync: undefined;
  About: undefined;
};

// Root Navigator
export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
  Notifications: undefined;
};

// Declaration merging for useNavigation hook
declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
```

### 4.2 Create App Navigator

**File:** `mobile/src/navigation/AppNavigator.tsx`

```typescript
/**
 * Root App Navigator
 */

import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { useSelector, useDispatch } from 'react-redux';

import { RootState, AppDispatch } from '@store/index';
import { refreshSession } from '@store/slices/authSlice';
import AuthNavigator from './AuthNavigator';
import MainNavigator from './MainNavigator';
import NotificationsScreen from '@screens/NotificationsScreen';
import LoadingScreen from '@screens/LoadingScreen';
import { RootStackParamList } from '@types/navigation';

const Stack = createStackNavigator<RootStackParamList>();

const AppNavigator: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const [isInitializing, setIsInitializing] = useState(true);
  
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);
  const { theme } = useSelector((state: RootState) => state.settings);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Try to restore session
        await dispatch(refreshSession()).unwrap();
      } catch (error) {
        // Session expired or no stored credentials
        console.log('No valid session found');
      } finally {
        setIsInitializing(false);
      }
    };

    initializeAuth();
  }, [dispatch]);

  if (isInitializing) {
    return <LoadingScreen />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
        }}
      >
        {isAuthenticated ? (
          <>
            <Stack.Screen name="Main" component={MainNavigator} />
            <Stack.Screen
              name="Notifications"
              component={NotificationsScreen}
              options={{
                presentation: 'modal',
              }}
            />
          </>
        ) : (
          <Stack.Screen name="Auth" component={AuthNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;
```

### 4.3 Create Auth Navigator

**File:** `mobile/src/navigation/AuthNavigator.tsx`

```typescript
/**
 * Authentication Navigator
 */

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { useSelector } from 'react-redux';

import LoginScreen from '@screens/auth/LoginScreen';
import BiometricScreen from '@screens/auth/BiometricScreen';
import PinScreen from '@screens/auth/PinScreen';
import ForgotPasswordScreen from '@screens/auth/ForgotPasswordScreen';
import { AuthStackParamList } from '@types/navigation';
import { RootState } from '@store/index';

const Stack = createStackNavigator<AuthStackParamList>();

const AuthNavigator: React.FC = () => {
  const { biometricsEnabled, pinEnabled } = useSelector(
    (state: RootState) => state.auth
  );

  // Determine initial route based on auth settings
  const getInitialRoute = (): keyof AuthStackParamList => {
    if (biometricsEnabled) return 'Biometric';
    if (pinEnabled) return 'Pin';
    return 'Login';
  };

  return (
    <Stack.Navigator
      initialRouteName={getInitialRoute()}
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: 'transparent' },
        animationEnabled: true,
      }}
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Biometric" component={BiometricScreen} />
      <Stack.Screen
        name="Pin"
        component={PinScreen}
        initialParams={{ mode: 'verify' }}
      />
      <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
    </Stack.Navigator>
  );
};

export default AuthNavigator;
```

### 4.4 Create Main Tab Navigator

**File:** `mobile/src/navigation/MainNavigator.tsx`

```typescript
/**
 * Main Tab Navigator
 */

import React from 'react';
import { Platform, StyleSheet, View } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useTheme, Badge } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useSelector } from 'react-redux';

import DashboardScreen from '@screens/dashboard/DashboardScreen';
import InventoryNavigator from './stacks/InventoryNavigator';
import TransactionsNavigator from './stacks/TransactionsNavigator';
import PaymentsNavigator from './stacks/PaymentsNavigator';
import MoreNavigator from './stacks/MoreNavigator';
import { MainTabParamList } from '@types/navigation';
import { RootState } from '@store/index';
import { colors } from '@/app/theme';

const Tab = createBottomTabNavigator<MainTabParamList>();

const MainNavigator: React.FC = () => {
  const theme = useTheme();
  const { overdueCount, upcomingCount } = useSelector(
    (state: RootState) => state.payments
  );
  const { pendingCount } = useSelector((state: RootState) => state.sync);

  const getTabBarIcon = (
    routeName: string,
    focused: boolean,
    color: string,
    size: number
  ) => {
    let iconName: string;

    switch (routeName) {
      case 'DashboardTab':
        iconName = focused ? 'view-dashboard' : 'view-dashboard-outline';
        break;
      case 'InventoryTab':
        iconName = focused ? 'package-variant-closed' : 'package-variant';
        break;
      case 'TransactionsTab':
        iconName = focused ? 'receipt' : 'receipt';
        break;
      case 'PaymentsTab':
        iconName = focused ? 'credit-card' : 'credit-card-outline';
        break;
      case 'MoreTab':
        iconName = focused ? 'dots-horizontal-circle' : 'dots-horizontal-circle-outline';
        break;
      default:
        iconName = 'circle';
    }

    return <Icon name={iconName} size={size} color={color} />;
  };

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused, color, size }) =>
          getTabBarIcon(route.name, focused, color, size),
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.onSurfaceVariant,
        tabBarStyle: styles.tabBar,
        tabBarLabelStyle: styles.tabBarLabel,
        tabBarHideOnKeyboard: true,
      })}
    >
      <Tab.Screen
        name="DashboardTab"
        component={DashboardScreen}
        options={{
          tabBarLabel: 'Dashboard',
        }}
      />
      <Tab.Screen
        name="InventoryTab"
        component={InventoryNavigator}
        options={{
          tabBarLabel: 'Inventory',
        }}
      />
      <Tab.Screen
        name="TransactionsTab"
        component={TransactionsNavigator}
        options={{
          tabBarLabel: 'Transactions',
        }}
      />
      <Tab.Screen
        name="PaymentsTab"
        component={PaymentsNavigator}
        options={{
          tabBarLabel: 'Payments',
          tabBarBadge: overdueCount > 0 ? overdueCount : undefined,
          tabBarBadgeStyle: styles.badge,
        }}
      />
      <Tab.Screen
        name="MoreTab"
        component={MoreNavigator}
        options={{
          tabBarLabel: 'More',
          tabBarBadge: pendingCount > 0 ? pendingCount : undefined,
          tabBarBadgeStyle: [styles.badge, { backgroundColor: colors.warning }],
        }}
      />
    </Tab.Navigator>
  );
};

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: colors.surface,
    borderTopColor: colors.outlineVariant,
    borderTopWidth: 1,
    height: Platform.OS === 'ios' ? 88 : 64,
    paddingTop: 8,
    paddingBottom: Platform.OS === 'ios' ? 28 : 8,
  },
  tabBarLabel: {
    fontSize: 11,
    fontWeight: '500',
  },
  badge: {
    backgroundColor: colors.danger,
    fontSize: 10,
    minWidth: 18,
    height: 18,
  },
});

export default MainNavigator;
```

### 4.5 Create Stack Navigators

**File:** `mobile/src/navigation/stacks/InventoryNavigator.tsx`

```typescript
/**
 * Inventory Stack Navigator
 */

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';

import InventoryListScreen from '@screens/inventory/InventoryListScreen';
import InventoryDetailScreen from '@screens/inventory/InventoryDetailScreen';
import ScannerScreen from '@screens/inventory/ScannerScreen';
import MovementScreen from '@screens/inventory/MovementScreen';
import { InventoryStackParamList } from '@types/navigation';
import { colors } from '@/app/theme';

const Stack = createStackNavigator<InventoryStackParamList>();

const InventoryNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: colors.surface,
          elevation: 0,
          shadowOpacity: 0,
          borderBottomWidth: 1,
          borderBottomColor: colors.outlineVariant,
        },
        headerTintColor: colors.onSurface,
        headerTitleStyle: {
          fontWeight: '600',
          fontSize: 18,
        },
      }}
    >
      <Stack.Screen
        name="InventoryList"
        component={InventoryListScreen}
        options={{ title: 'Inventory' }}
      />
      <Stack.Screen
        name="InventoryDetail"
        component={InventoryDetailScreen}
        options={{ title: 'Material Details' }}
      />
      <Stack.Screen
        name="Scanner"
        component={ScannerScreen}
        options={{
          title: 'Scan',
          presentation: 'modal',
          headerShown: false,
        }}
      />
      <Stack.Screen
        name="Movement"
        component={MovementScreen}
        options={{ title: 'Record Movement' }}
      />
    </Stack.Navigator>
  );
};

export default InventoryNavigator;
```

**File:** `mobile/src/navigation/stacks/TransactionsNavigator.tsx`

```typescript
/**
 * Transactions Stack Navigator
 */

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';

import TransactionListScreen from '@screens/transactions/TransactionListScreen';
import TransactionFormScreen from '@screens/transactions/TransactionFormScreen';
import DocumentScanScreen from '@screens/transactions/DocumentScanScreen';
import { TransactionsStackParamList } from '@types/navigation';
import { colors } from '@/app/theme';

const Stack = createStackNavigator<TransactionsStackParamList>();

const TransactionsNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: colors.surface,
          elevation: 0,
          shadowOpacity: 0,
          borderBottomWidth: 1,
          borderBottomColor: colors.outlineVariant,
        },
        headerTintColor: colors.onSurface,
        headerTitleStyle: {
          fontWeight: '600',
          fontSize: 18,
        },
      }}
    >
      <Stack.Screen
        name="TransactionList"
        component={TransactionListScreen}
        options={{ title: 'Transactions' }}
      />
      <Stack.Screen
        name="TransactionForm"
        component={TransactionFormScreen}
        options={({ route }) => ({
          title: route.params?.id ? 'Edit Transaction' : 'New Transaction',
        })}
      />
      <Stack.Screen
        name="DocumentScan"
        component={DocumentScanScreen}
        options={{
          title: 'Scan Document',
          presentation: 'modal',
          headerShown: false,
        }}
      />
    </Stack.Navigator>
  );
};

export default TransactionsNavigator;
```

**File:** `mobile/src/navigation/stacks/PaymentsNavigator.tsx`

```typescript
/**
 * Payments Stack Navigator
 */

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';

import PaymentListScreen from '@screens/payments/PaymentListScreen';
import PaymentDetailScreen from '@screens/payments/PaymentDetailScreen';
import RecordPaymentScreen from '@screens/payments/RecordPaymentScreen';
import { PaymentsStackParamList } from '@types/navigation';
import { colors } from '@/app/theme';

const Stack = createStackNavigator<PaymentsStackParamList>();

const PaymentsNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: colors.surface,
          elevation: 0,
          shadowOpacity: 0,
          borderBottomWidth: 1,
          borderBottomColor: colors.outlineVariant,
        },
        headerTintColor: colors.onSurface,
        headerTitleStyle: {
          fontWeight: '600',
          fontSize: 18,
        },
      }}
    >
      <Stack.Screen
        name="PaymentList"
        component={PaymentListScreen}
        options={{ title: 'Payments' }}
      />
      <Stack.Screen
        name="PaymentDetail"
        component={PaymentDetailScreen}
        options={{ title: 'Payment Details' }}
      />
      <Stack.Screen
        name="RecordPayment"
        component={RecordPaymentScreen}
        options={{ title: 'Record Payment' }}
      />
    </Stack.Navigator>
  );
};

export default PaymentsNavigator;
```

**File:** `mobile/src/navigation/stacks/MoreNavigator.tsx`

```typescript
/**
 * More Stack Navigator
 */

import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';

import MoreMenuScreen from '@screens/more/MoreMenuScreen';
import ProjectsNavigator from './ProjectsNavigator';
import AnalyticsScreen from '@screens/analytics/AnalyticsScreen';
import SettingsScreen from '@screens/settings/SettingsScreen';
import ProfileScreen from '@screens/settings/ProfileScreen';
import SyncScreen from '@screens/settings/SyncScreen';
import AboutScreen from '@screens/settings/AboutScreen';
import { MoreStackParamList } from '@types/navigation';
import { colors } from '@/app/theme';

const Stack = createStackNavigator<MoreStackParamList>();

const MoreNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: colors.surface,
          elevation: 0,
          shadowOpacity: 0,
          borderBottomWidth: 1,
          borderBottomColor: colors.outlineVariant,
        },
        headerTintColor: colors.onSurface,
        headerTitleStyle: {
          fontWeight: '600',
          fontSize: 18,
        },
      }}
    >
      <Stack.Screen
        name="MoreMenu"
        component={MoreMenuScreen}
        options={{ title: 'More' }}
      />
      <Stack.Screen
        name="Projects"
        component={ProjectsNavigator}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="Analytics"
        component={AnalyticsScreen}
        options={{ title: 'Analytics' }}
      />
      <Stack.Screen
        name="Settings"
        component={SettingsScreen}
        options={{ title: 'Settings' }}
      />
      <Stack.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ title: 'Profile' }}
      />
      <Stack.Screen
        name="Sync"
        component={SyncScreen}
        options={{ title: 'Sync Status' }}
      />
      <Stack.Screen
        name="About"
        component={AboutScreen}
        options={{ title: 'About' }}
      />
    </Stack.Navigator>
  );
};

export default MoreNavigator;
```

---

## TASK 5: AUTHENTICATION SCREENS

### 5.1 Login Screen

**File:** `mobile/src/screens/auth/LoginScreen.tsx`

```typescript
/**
 * Login Screen
 */

import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Image,
} from 'react-native';
import {
  TextInput,
  Button,
  Text,
  HelperText,
  ActivityIndicator,
} from 'react-native-paper';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

import { AppDispatch, RootState } from '@store/index';
import { login, clearError } from '@store/slices/authSlice';
import { AuthStackParamList } from '@types/navigation';
import { colors, spacing, borderRadius } from '@/app/theme';

type LoginNavigationProp = StackNavigationProp<AuthStackParamList, 'Login'>;

const LoginScreen: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation<LoginNavigationProp>();
  
  const { isLoading, error } = useSelector((state: RootState) => state.auth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const validateEmail = (value: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!value) {
      setEmailError('Email is required');
      return false;
    }
    if (!emailRegex.test(value)) {
      setEmailError('Please enter a valid email');
      return false;
    }
    setEmailError('');
    return true;
  };

  const validatePassword = (value: string): boolean => {
    if (!value) {
      setPasswordError('Password is required');
      return false;
    }
    if (value.length < 6) {
      setPasswordError('Password must be at least 6 characters');
      return false;
    }
    setPasswordError('');
    return true;
  };

  const handleLogin = async () => {
    dispatch(clearError());
    
    const isEmailValid = validateEmail(email);
    const isPasswordValid = validatePassword(password);

    if (!isEmailValid || !isPasswordValid) {
      return;
    }

    try {
      await dispatch(login({ email, password })).unwrap();
    } catch (err) {
      // Error handled in reducer
    }
  };

  const handleForgotPassword = () => {
    navigation.navigate('ForgotPassword');
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* Logo */}
        <View style={styles.logoContainer}>
          <View style={styles.logoPlaceholder}>
            <Text style={styles.logoText}>LA</Text>
          </View>
          <Text style={styles.appName}>LogiAccounting Pro</Text>
          <Text style={styles.tagline}>Enterprise Logistics & Accounting</Text>
        </View>

        {/* Form */}
        <View style={styles.formContainer}>
          <Text style={styles.welcomeText}>Welcome back</Text>
          <Text style={styles.subtitleText}>Sign in to continue</Text>

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
            autoComplete="password"
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

          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          <Button
            mode="contained"
            onPress={handleLogin}
            loading={isLoading}
            disabled={isLoading}
            style={styles.loginButton}
            contentStyle={styles.loginButtonContent}
            labelStyle={styles.loginButtonLabel}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </Button>

          <Button
            mode="text"
            onPress={handleForgotPassword}
            style={styles.forgotButton}
          >
            Forgot Password?
          </Button>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            © 2026 LogiAccounting Pro. All rights reserved.
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxl,
    paddingBottom: spacing.lg,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  logoPlaceholder: {
    width: 80,
    height: 80,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  logoText: {
    fontSize: 32,
    fontWeight: '700',
    color: colors.onPrimary,
  },
  appName: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.onBackground,
  },
  tagline: {
    fontSize: 14,
    color: colors.onSurfaceVariant,
    marginTop: spacing.xs,
  },
  formContainer: {
    flex: 1,
  },
  welcomeText: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.onBackground,
    marginBottom: spacing.xs,
  },
  subtitleText: {
    fontSize: 16,
    color: colors.onSurfaceVariant,
    marginBottom: spacing.lg,
  },
  input: {
    marginBottom: 0,
    backgroundColor: colors.surface,
  },
  errorContainer: {
    backgroundColor: colors.dangerContainer,
    padding: spacing.md,
    borderRadius: borderRadius.sm,
    marginBottom: spacing.md,
  },
  errorText: {
    color: colors.onDangerContainer,
    fontSize: 14,
  },
  loginButton: {
    marginTop: spacing.md,
    borderRadius: borderRadius.sm,
  },
  loginButtonContent: {
    height: 52,
  },
  loginButtonLabel: {
    fontSize: 16,
    fontWeight: '600',
  },
  forgotButton: {
    marginTop: spacing.sm,
  },
  footer: {
    alignItems: 'center',
    marginTop: spacing.xl,
  },
  footerText: {
    fontSize: 12,
    color: colors.onSurfaceVariant,
  },
});

export default LoginScreen;
```

### 5.2 Biometric Screen

**File:** `mobile/src/screens/auth/BiometricScreen.tsx`

```typescript
/**
 * Biometric Authentication Screen
 */

import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Alert, Platform } from 'react-native';
import { Text, Button, ActivityIndicator } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

import { AppDispatch, RootState } from '@store/index';
import { refreshSession, updateLastActivity } from '@store/slices/authSlice';
import { AuthStackParamList } from '@types/navigation';
import { colors, spacing, borderRadius } from '@/app/theme';

type BiometricNavigationProp = StackNavigationProp<AuthStackParamList, 'Biometric'>;

const rnBiometrics = new ReactNativeBiometrics();

const BiometricScreen: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation<BiometricNavigationProp>();
  
  const { pinEnabled } = useSelector((state: RootState) => state.auth);

  const [biometryType, setBiometryType] = useState<BiometryTypes | null>(null);
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [attempts, setAttempts] = useState(0);

  useEffect(() => {
    checkBiometrics();
  }, []);

  const checkBiometrics = async () => {
    try {
      const { available, biometryType } = await rnBiometrics.isSensorAvailable();
      
      if (available) {
        setBiometryType(biometryType);
        // Auto-prompt on mount
        setTimeout(promptBiometric, 500);
      } else {
        // Biometrics not available, fall back
        handleFallback();
      }
    } catch (error) {
      console.error('Biometrics check failed:', error);
      handleFallback();
    }
  };

  const promptBiometric = async () => {
    setIsAuthenticating(true);
    
    try {
      const promptMessage = getBiometricPromptMessage();
      
      const { success } = await rnBiometrics.simplePrompt({
        promptMessage,
        cancelButtonText: 'Cancel',
      });

      if (success) {
        // Biometric verified, restore session
        await dispatch(refreshSession()).unwrap();
        dispatch(updateLastActivity());
      } else {
        handleAuthFailure();
      }
    } catch (error: any) {
      console.error('Biometric auth failed:', error);
      
      if (error.message?.includes('cancel')) {
        // User cancelled, don't count as attempt
      } else {
        handleAuthFailure();
      }
    } finally {
      setIsAuthenticating(false);
    }
  };

  const handleAuthFailure = () => {
    const newAttempts = attempts + 1;
    setAttempts(newAttempts);

    if (newAttempts >= 3) {
      // Max attempts reached, require alternative
      Alert.alert(
        'Too Many Attempts',
        'Please use an alternative authentication method.',
        [{ text: 'OK', onPress: handleFallback }]
      );
    }
  };

  const handleFallback = () => {
    if (pinEnabled) {
      navigation.replace('Pin', { mode: 'verify' });
    } else {
      navigation.replace('Login');
    }
  };

  const getBiometricPromptMessage = (): string => {
    switch (biometryType) {
      case BiometryTypes.FaceID:
        return 'Authenticate with Face ID';
      case BiometryTypes.TouchID:
        return 'Authenticate with Touch ID';
      case BiometryTypes.Biometrics:
        return 'Authenticate with fingerprint';
      default:
        return 'Authenticate';
    }
  };

  const getBiometricIcon = (): string => {
    switch (biometryType) {
      case BiometryTypes.FaceID:
        return 'face-recognition';
      case BiometryTypes.TouchID:
      case BiometryTypes.Biometrics:
        return 'fingerprint';
      default:
        return 'shield-lock';
    }
  };

  const getBiometricLabel = (): string => {
    switch (biometryType) {
      case BiometryTypes.FaceID:
        return 'Face ID';
      case BiometryTypes.TouchID:
        return 'Touch ID';
      case BiometryTypes.Biometrics:
        return 'Fingerprint';
      default:
        return 'Biometrics';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <View style={styles.logoPlaceholder}>
            <Text style={styles.logoText}>LA</Text>
          </View>
        </View>

        {/* Biometric Icon */}
        <View style={styles.iconContainer}>
          <View style={styles.iconCircle}>
            <Icon
              name={getBiometricIcon()}
              size={64}
              color={colors.primary}
            />
          </View>
        </View>

        {/* Text */}
        <Text style={styles.title}>
          {isAuthenticating ? 'Authenticating...' : `Use ${getBiometricLabel()}`}
        </Text>
        <Text style={styles.subtitle}>
          {isAuthenticating
            ? 'Please verify your identity'
            : 'Tap the button below to authenticate'}
        </Text>

        {/* Loading or Button */}
        {isAuthenticating ? (
          <ActivityIndicator
            size="large"
            color={colors.primary}
            style={styles.loader}
          />
        ) : (
          <Button
            mode="contained"
            onPress={promptBiometric}
            style={styles.authButton}
            contentStyle={styles.authButtonContent}
            icon={getBiometricIcon()}
          >
            Authenticate
          </Button>
        )}

        {/* Fallback Options */}
        <View style={styles.fallbackContainer}>
          {pinEnabled && (
            <Button
              mode="text"
              onPress={() => navigation.replace('Pin', { mode: 'verify' })}
            >
              Use PIN instead
            </Button>
          )}
          <Button
            mode="text"
            onPress={() => navigation.replace('Login')}
          >
            Use password
          </Button>
        </View>

        {/* Attempts indicator */}
        {attempts > 0 && (
          <Text style={styles.attemptsText}>
            {3 - attempts} attempt{3 - attempts !== 1 ? 's' : ''} remaining
          </Text>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.lg,
  },
  logoContainer: {
    marginBottom: spacing.xl,
  },
  logoPlaceholder: {
    width: 64,
    height: 64,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoText: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.onPrimary,
  },
  iconContainer: {
    marginBottom: spacing.xl,
  },
  iconCircle: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: colors.primaryContainer,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.onBackground,
    marginBottom: spacing.sm,
  },
  subtitle: {
    fontSize: 16,
    color: colors.onSurfaceVariant,
    textAlign: 'center',
    marginBottom: spacing.xl,
    paddingHorizontal: spacing.lg,
  },
  loader: {
    marginVertical: spacing.lg,
  },
  authButton: {
    minWidth: 200,
    borderRadius: borderRadius.sm,
  },
  authButtonContent: {
    height: 52,
  },
  fallbackContainer: {
    marginTop: spacing.xl,
    alignItems: 'center',
  },
  attemptsText: {
    marginTop: spacing.lg,
    fontSize: 14,
    color: colors.danger,
  },
});

export default BiometricScreen;
```

### 5.3 PIN Screen

**File:** `mobile/src/screens/auth/PinScreen.tsx`

```typescript
/**
 * PIN Authentication Screen
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Vibration,
} from 'react-native';
import { Text, Button } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

import { AppDispatch, RootState } from '@store/index';
import {
  verifyPin,
  setPin,
  refreshSession,
  updateLastActivity,
} from '@store/slices/authSlice';
import { AuthStackParamList } from '@types/navigation';
import { colors, spacing, borderRadius } from '@/app/theme';

type PinNavigationProp = StackNavigationProp<AuthStackParamList, 'Pin'>;
type PinRouteProp = RouteProp<AuthStackParamList, 'Pin'>;

const PIN_LENGTH = 4;

const PinScreen: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation<PinNavigationProp>();
  const route = useRoute<PinRouteProp>();

  const mode = route.params?.mode || 'verify';
  const isSetup = mode === 'setup';

  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [step, setStep] = useState<'enter' | 'confirm'>('enter');
  const [error, setError] = useState('');
  const [attempts, setAttempts] = useState(0);

  const shakeAnimation = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (pin.length === PIN_LENGTH) {
      handlePinComplete();
    }
  }, [pin]);

  useEffect(() => {
    if (confirmPin.length === PIN_LENGTH && isSetup) {
      handleConfirmComplete();
    }
  }, [confirmPin]);

  const handlePinComplete = async () => {
    if (isSetup) {
      // Move to confirm step
      setStep('confirm');
      setPin('');
    } else {
      // Verify PIN
      try {
        await dispatch(verifyPin(pin)).unwrap();
        await dispatch(refreshSession()).unwrap();
        dispatch(updateLastActivity());
      } catch (error) {
        handleError();
      }
    }
  };

  const handleConfirmComplete = async () => {
    if (pin === confirmPin) {
      // PINs match, save it
      try {
        await dispatch(setPin(pin)).unwrap();
        navigation.goBack();
      } catch (error) {
        setError('Failed to save PIN');
      }
    } else {
      // PINs don't match
      setError('PINs do not match');
      shake();
      setConfirmPin('');
    }
  };

  const handleError = () => {
    const newAttempts = attempts + 1;
    setAttempts(newAttempts);
    setError('Incorrect PIN');
    shake();
    setPin('');

    if (newAttempts >= 3) {
      // Force password login
      navigation.replace('Login');
    }
  };

  const shake = () => {
    Vibration.vibrate(200);
    Animated.sequence([
      Animated.timing(shakeAnimation, {
        toValue: 10,
        duration: 50,
        useNativeDriver: true,
      }),
      Animated.timing(shakeAnimation, {
        toValue: -10,
        duration: 50,
        useNativeDriver: true,
      }),
      Animated.timing(shakeAnimation, {
        toValue: 10,
        duration: 50,
        useNativeDriver: true,
      }),
      Animated.timing(shakeAnimation, {
        toValue: 0,
        duration: 50,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const handleKeyPress = (key: string) => {
    setError('');
    
    const currentValue = step === 'confirm' ? confirmPin : pin;
    const setValue = step === 'confirm' ? setConfirmPin : setPin;

    if (key === 'delete') {
      setValue(currentValue.slice(0, -1));
    } else if (currentValue.length < PIN_LENGTH) {
      setValue(currentValue + key);
    }
  };

  const currentPin = step === 'confirm' ? confirmPin : pin;

  const getTitle = () => {
    if (isSetup) {
      return step === 'enter' ? 'Create PIN' : 'Confirm PIN';
    }
    return 'Enter PIN';
  };

  const getSubtitle = () => {
    if (isSetup) {
      return step === 'enter'
        ? 'Create a 4-digit PIN for quick access'
        : 'Re-enter your PIN to confirm';
    }
    return 'Enter your PIN to unlock';
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.logoPlaceholder}>
          <Text style={styles.logoText}>LA</Text>
        </View>
        <Text style={styles.title}>{getTitle()}</Text>
        <Text style={styles.subtitle}>{getSubtitle()}</Text>
      </View>

      {/* PIN Dots */}
      <Animated.View
        style={[
          styles.dotsContainer,
          { transform: [{ translateX: shakeAnimation }] },
        ]}
      >
        {Array.from({ length: PIN_LENGTH }).map((_, index) => (
          <View
            key={index}
            style={[
              styles.dot,
              index < currentPin.length && styles.dotFilled,
              error && styles.dotError,
            ]}
          />
        ))}
      </Animated.View>

      {/* Error */}
      {error && <Text style={styles.errorText}>{error}</Text>}
      {!isSetup && attempts > 0 && (
        <Text style={styles.attemptsText}>
          {3 - attempts} attempt{3 - attempts !== 1 ? 's' : ''} remaining
        </Text>
      )}

      {/* Keypad */}
      <View style={styles.keypad}>
        {['1', '2', '3', '4', '5', '6', '7', '8', '9', '', '0', 'delete'].map(
          (key, index) => (
            <TouchableOpacity
              key={index}
              style={[styles.key, !key && styles.keyEmpty]}
              onPress={() => key && handleKeyPress(key)}
              disabled={!key}
              activeOpacity={0.7}
            >
              {key === 'delete' ? (
                <Icon name="backspace-outline" size={28} color={colors.onSurface} />
              ) : (
                <Text style={styles.keyText}>{key}</Text>
              )}
            </TouchableOpacity>
          )
        )}
      </View>

      {/* Footer Options */}
      <View style={styles.footer}>
        {!isSetup && (
          <Button
            mode="text"
            onPress={() => navigation.replace('Login')}
          >
            Use password instead
          </Button>
        )}
        {isSetup && step === 'confirm' && (
          <Button
            mode="text"
            onPress={() => {
              setStep('enter');
              setPin('');
              setConfirmPin('');
              setError('');
            }}
          >
            Start over
          </Button>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    padding: spacing.lg,
  },
  header: {
    alignItems: 'center',
    marginTop: spacing.xxl,
    marginBottom: spacing.xl,
  },
  logoPlaceholder: {
    width: 56,
    height: 56,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  logoText: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.onPrimary,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.onBackground,
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontSize: 14,
    color: colors.onSurfaceVariant,
    textAlign: 'center',
  },
  dotsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  dot: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: colors.outline,
    marginHorizontal: spacing.sm,
  },
  dotFilled: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  dotError: {
    borderColor: colors.danger,
    backgroundColor: 'transparent',
  },
  errorText: {
    color: colors.danger,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  attemptsText: {
    color: colors.onSurfaceVariant,
    textAlign: 'center',
    fontSize: 12,
    marginBottom: spacing.md,
  },
  keypad: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    maxWidth: 300,
    alignSelf: 'center',
    marginTop: spacing.lg,
  },
  key: {
    width: 80,
    height: 80,
    justifyContent: 'center',
    alignItems: 'center',
    margin: spacing.xs,
    borderRadius: 40,
    backgroundColor: colors.surfaceVariant,
  },
  keyEmpty: {
    backgroundColor: 'transparent',
  },
  keyText: {
    fontSize: 28,
    fontWeight: '500',
    color: colors.onSurface,
  },
  footer: {
    flex: 1,
    justifyContent: 'flex-end',
    alignItems: 'center',
    paddingBottom: spacing.lg,
  },
});

export default PinScreen;
```

---

## TASK 6: AUTHENTICATION SERVICE

### 6.1 Create Auth Service

**File:** `mobile/src/services/auth/authService.ts`

```typescript
/**
 * Authentication Service
 */

import api from '../api/client';

interface LoginCredentials {
  email: string;
  password: string;
}

interface AuthResponse {
  user: {
    id: string;
    email: string;
    name: string;
    role: 'admin' | 'client' | 'supplier';
    avatar?: string;
  };
  accessToken: string;
  refreshToken: string;
}

interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  user: AuthResponse['user'];
}

export const authService = {
  /**
   * Login with email and password
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },

  /**
   * Logout current session
   */
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // Ignore logout errors
    }
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  /**
   * Get current user profile
   */
  async getProfile(): Promise<AuthResponse['user']> {
    const response = await api.get<AuthResponse['user']>('/auth/profile');
    return response.data;
  },

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<void> {
    await api.post('/auth/forgot-password', { email });
  },

  /**
   * Reset password with token
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await api.post('/auth/reset-password', {
      token,
      password: newPassword,
    });
  },

  /**
   * Change password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },
};
```

### 6.2 Create Biometric Service

**File:** `mobile/src/services/auth/biometricService.ts`

```typescript
/**
 * Biometric Authentication Service
 */

import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';
import * as Keychain from 'react-native-keychain';

const rnBiometrics = new ReactNativeBiometrics();

export interface BiometricStatus {
  available: boolean;
  biometryType: BiometryTypes | null;
  enrolled: boolean;
}

export const biometricService = {
  /**
   * Check if biometrics is available
   */
  async checkBiometrics(): Promise<BiometricStatus> {
    try {
      const { available, biometryType } = await rnBiometrics.isSensorAvailable();
      
      return {
        available,
        biometryType: available ? biometryType : null,
        enrolled: available,
      };
    } catch (error) {
      console.error('Biometric check failed:', error);
      return {
        available: false,
        biometryType: null,
        enrolled: false,
      };
    }
  },

  /**
   * Prompt for biometric authentication
   */
  async authenticate(promptMessage?: string): Promise<boolean> {
    try {
      const { success } = await rnBiometrics.simplePrompt({
        promptMessage: promptMessage || 'Authenticate',
        cancelButtonText: 'Cancel',
      });
      
      return success;
    } catch (error) {
      console.error('Biometric authentication failed:', error);
      return false;
    }
  },

  /**
   * Create biometric keys for secure storage
   */
  async createKeys(): Promise<boolean> {
    try {
      const { keysExist } = await rnBiometrics.biometricKeysExist();
      
      if (!keysExist) {
        const { publicKey } = await rnBiometrics.createKeys();
        return !!publicKey;
      }
      
      return true;
    } catch (error) {
      console.error('Failed to create biometric keys:', error);
      return false;
    }
  },

  /**
   * Delete biometric keys
   */
  async deleteKeys(): Promise<boolean> {
    try {
      const { keysDeleted } = await rnBiometrics.deleteKeys();
      return keysDeleted;
    } catch (error) {
      console.error('Failed to delete biometric keys:', error);
      return false;
    }
  },

  /**
   * Sign data with biometric
   */
  async signWithBiometric(
    payload: string,
    promptMessage?: string
  ): Promise<string | null> {
    try {
      const { success, signature } = await rnBiometrics.createSignature({
        promptMessage: promptMessage || 'Sign in',
        payload,
      });
      
      return success ? signature : null;
    } catch (error) {
      console.error('Biometric signing failed:', error);
      return null;
    }
  },

  /**
   * Get biometry type label
   */
  getBiometryLabel(biometryType: BiometryTypes | null): string {
    switch (biometryType) {
      case BiometryTypes.FaceID:
        return 'Face ID';
      case BiometryTypes.TouchID:
        return 'Touch ID';
      case BiometryTypes.Biometrics:
        return 'Fingerprint';
      default:
        return 'Biometrics';
    }
  },

  /**
   * Get biometry icon name
   */
  getBiometryIcon(biometryType: BiometryTypes | null): string {
    switch (biometryType) {
      case BiometryTypes.FaceID:
        return 'face-recognition';
      case BiometryTypes.TouchID:
      case BiometryTypes.Biometrics:
        return 'fingerprint';
      default:
        return 'shield-lock';
    }
  },
};
```

---

## TASK 7: CUSTOM HOOKS

### 7.1 Create useAuth Hook

**File:** `mobile/src/hooks/useAuth.ts`

```typescript
/**
 * Authentication Hook
 */

import { useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '@store/index';
import {
  login as loginAction,
  logout as logoutAction,
  refreshSession,
  setBiometricsEnabled,
  setPinEnabled,
  updateLastActivity,
} from '@store/slices/authSlice';

export const useAuth = () => {
  const dispatch = useDispatch<AppDispatch>();
  const auth = useSelector((state: RootState) => state.auth);

  const login = useCallback(
    async (email: string, password: string) => {
      return dispatch(loginAction({ email, password })).unwrap();
    },
    [dispatch]
  );

  const logout = useCallback(async () => {
    return dispatch(logoutAction()).unwrap();
  }, [dispatch]);

  const refresh = useCallback(async () => {
    return dispatch(refreshSession()).unwrap();
  }, [dispatch]);

  const enableBiometrics = useCallback(
    (enabled: boolean) => {
      dispatch(setBiometricsEnabled(enabled));
    },
    [dispatch]
  );

  const enablePin = useCallback(
    (enabled: boolean) => {
      dispatch(setPinEnabled(enabled));
    },
    [dispatch]
  );

  const recordActivity = useCallback(() => {
    dispatch(updateLastActivity());
  }, [dispatch]);

  return {
    ...auth,
    login,
    logout,
    refresh,
    enableBiometrics,
    enablePin,
    recordActivity,
  };
};
```

### 7.2 Create useBiometrics Hook

**File:** `mobile/src/hooks/useBiometrics.ts`

```typescript
/**
 * Biometrics Hook
 */

import { useState, useEffect, useCallback } from 'react';
import { BiometryTypes } from 'react-native-biometrics';
import { biometricService, BiometricStatus } from '@services/auth/biometricService';

export const useBiometrics = () => {
  const [status, setStatus] = useState<BiometricStatus>({
    available: false,
    biometryType: null,
    enrolled: false,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = useCallback(async () => {
    setIsLoading(true);
    const result = await biometricService.checkBiometrics();
    setStatus(result);
    setIsLoading(false);
  }, []);

  const authenticate = useCallback(async (prompt?: string) => {
    return biometricService.authenticate(prompt);
  }, []);

  const getLabel = useCallback(() => {
    return biometricService.getBiometryLabel(status.biometryType);
  }, [status.biometryType]);

  const getIcon = useCallback(() => {
    return biometricService.getBiometryIcon(status.biometryType);
  }, [status.biometryType]);

  return {
    ...status,
    isLoading,
    checkStatus,
    authenticate,
    getLabel,
    getIcon,
  };
};
```

### 7.3 Create useOffline Hook

**File:** `mobile/src/hooks/useOffline.ts`

```typescript
/**
 * Offline Status Hook
 */

import { useState, useEffect, useCallback } from 'react';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { useDispatch, useSelector } from 'react-redux';
import { setOnlineStatus } from '@store/slices/syncSlice';
import { RootState } from '@store/index';

export const useOffline = () => {
  const dispatch = useDispatch();
  const { isOnline, pendingCount } = useSelector((state: RootState) => state.sync);
  const [connectionType, setConnectionType] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      const online = state.isConnected ?? false;
      dispatch(setOnlineStatus(online));
      setConnectionType(state.type);
    });

    // Check initial status
    NetInfo.fetch().then((state) => {
      dispatch(setOnlineStatus(state.isConnected ?? false));
      setConnectionType(state.type);
    });

    return () => unsubscribe();
  }, [dispatch]);

  const checkConnection = useCallback(async () => {
    const state = await NetInfo.fetch();
    dispatch(setOnlineStatus(state.isConnected ?? false));
    return state.isConnected ?? false;
  }, [dispatch]);

  return {
    isOnline,
    isOffline: !isOnline,
    connectionType,
    pendingActions: pendingCount,
    checkConnection,
  };
};
```

---

## Continue to Part 3 for Core Screens and Components

---

*Phase 11 Tasks Part 2 - LogiAccounting Pro*
*Navigation and Authentication*
