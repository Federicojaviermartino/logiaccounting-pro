# LogiAccounting Pro - Phase 11 Tasks Part 1

## PROJECT SETUP, NAVIGATION & CORE COMPONENTS

---

## TASK 1: PROJECT INITIALIZATION

### 1.1 Create React Native Project

```bash
# Create new React Native project with TypeScript
npx react-native init LogiAccountingPro --template react-native-template-typescript

# Navigate to project
cd LogiAccountingPro

# Install core dependencies
npm install @react-navigation/native @react-navigation/bottom-tabs @react-navigation/stack
npm install react-native-screens react-native-safe-area-context
npm install @reduxjs/toolkit react-redux redux-persist
npm install react-native-paper react-native-vector-icons
npm install react-native-reanimated react-native-gesture-handler
npm install @react-native-async-storage/async-storage
npm install react-native-keychain
npm install axios
npm install i18next react-i18next
npm install date-fns

# Dev dependencies
npm install -D @types/react-native-vector-icons
npm install -D jest @testing-library/react-native
```

### 1.2 Package.json Configuration

**File:** `mobile/package.json`

```json
{
  "name": "LogiAccountingPro",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "android": "react-native run-android",
    "ios": "react-native run-ios",
    "start": "react-native start",
    "test": "jest",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx",
    "clean": "cd android && ./gradlew clean && cd .. && cd ios && xcodebuild clean && cd ..",
    "pod-install": "cd ios && pod install && cd ..",
    "build:android": "cd android && ./gradlew assembleRelease",
    "build:ios": "cd ios && xcodebuild -workspace LogiAccountingPro.xcworkspace -scheme LogiAccountingPro -configuration Release"
  },
  "dependencies": {
    "@react-native-async-storage/async-storage": "^1.21.0",
    "@react-navigation/bottom-tabs": "^6.5.11",
    "@react-navigation/native": "^6.1.9",
    "@react-navigation/stack": "^6.3.20",
    "@reduxjs/toolkit": "^2.0.1",
    "axios": "^1.6.2",
    "date-fns": "^3.0.6",
    "i18next": "^23.7.11",
    "react": "18.2.0",
    "react-i18next": "^14.0.0",
    "react-native": "0.73.1",
    "react-native-gesture-handler": "^2.14.0",
    "react-native-keychain": "^8.1.2",
    "react-native-paper": "^5.11.3",
    "react-native-reanimated": "^3.6.1",
    "react-native-safe-area-context": "^4.8.2",
    "react-native-screens": "^3.29.0",
    "react-native-vector-icons": "^10.0.3",
    "react-redux": "^9.0.4",
    "redux-persist": "^6.0.0"
  },
  "devDependencies": {
    "@babel/core": "^7.23.6",
    "@babel/preset-env": "^7.23.6",
    "@babel/runtime": "^7.23.6",
    "@testing-library/react-native": "^12.4.3",
    "@types/jest": "^29.5.11",
    "@types/react": "^18.2.45",
    "@types/react-native-vector-icons": "^6.4.18",
    "@types/react-test-renderer": "^18.0.7",
    "babel-jest": "^29.7.0",
    "eslint": "^8.56.0",
    "jest": "^29.7.0",
    "react-test-renderer": "18.2.0",
    "typescript": "^5.3.3"
  }
}
```

### 1.3 TypeScript Configuration

**File:** `mobile/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "esnext",
    "module": "commonjs",
    "lib": ["es2019"],
    "allowJs": true,
    "jsx": "react-native",
    "noEmit": true,
    "isolatedModules": true,
    "strict": true,
    "moduleResolution": "node",
    "baseUrl": "./",
    "paths": {
      "@/*": ["src/*"],
      "@screens/*": ["src/screens/*"],
      "@components/*": ["src/components/*"],
      "@services/*": ["src/services/*"],
      "@store/*": ["src/store/*"],
      "@hooks/*": ["src/hooks/*"],
      "@utils/*": ["src/utils/*"],
      "@types/*": ["src/types/*"],
      "@i18n/*": ["src/i18n/*"]
    },
    "allowSyntheticDefaultImports": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "babel.config.js", "metro.config.js", "jest.config.js"]
}
```

### 1.4 Babel Configuration

**File:** `mobile/babel.config.js`

```javascript
module.exports = {
  presets: ['module:@react-native/babel-preset'],
  plugins: [
    'react-native-reanimated/plugin',
    [
      'module-resolver',
      {
        root: ['./src'],
        extensions: ['.ios.js', '.android.js', '.js', '.ts', '.tsx', '.json'],
        alias: {
          '@': './src',
          '@screens': './src/screens',
          '@components': './src/components',
          '@services': './src/services',
          '@store': './src/store',
          '@hooks': './src/hooks',
          '@utils': './src/utils',
          '@types': './src/types',
          '@i18n': './src/i18n',
        },
      },
    ],
  ],
};
```

### 1.5 Environment Configuration

**File:** `mobile/.env.development`

```
API_URL=http://localhost:5000/api/v1
WS_URL=ws://localhost:5000
ENVIRONMENT=development
ENABLE_FLIPPER=true
```

**File:** `mobile/.env.production`

```
API_URL=https://logiaccounting-pro.onrender.com/api/v1
WS_URL=wss://logiaccounting-pro.onrender.com
ENVIRONMENT=production
ENABLE_FLIPPER=false
```

---

## TASK 2: THEME SYSTEM

### 2.1 Create Theme Configuration

**File:** `mobile/src/app/theme.ts`

```typescript
/**
 * Theme Configuration
 * Design system for LogiAccounting Pro mobile app
 */

import { MD3LightTheme, MD3DarkTheme, configureFonts } from 'react-native-paper';
import { Platform } from 'react-native';

// Font configuration
const fontConfig = {
  displayLarge: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif' }),
    fontWeight: '700' as const,
    fontSize: 57,
    lineHeight: 64,
    letterSpacing: -0.25,
  },
  displayMedium: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif' }),
    fontWeight: '700' as const,
    fontSize: 45,
    lineHeight: 52,
    letterSpacing: 0,
  },
  displaySmall: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif' }),
    fontWeight: '600' as const,
    fontSize: 36,
    lineHeight: 44,
    letterSpacing: 0,
  },
  headlineLarge: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif' }),
    fontWeight: '600' as const,
    fontSize: 32,
    lineHeight: 40,
    letterSpacing: 0,
  },
  headlineMedium: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif' }),
    fontWeight: '600' as const,
    fontSize: 28,
    lineHeight: 36,
    letterSpacing: 0,
  },
  headlineSmall: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif' }),
    fontWeight: '600' as const,
    fontSize: 24,
    lineHeight: 32,
    letterSpacing: 0,
  },
  titleLarge: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif-medium' }),
    fontWeight: '500' as const,
    fontSize: 22,
    lineHeight: 28,
    letterSpacing: 0,
  },
  titleMedium: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif-medium' }),
    fontWeight: '500' as const,
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0.15,
  },
  titleSmall: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif-medium' }),
    fontWeight: '500' as const,
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.1,
  },
  bodyLarge: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif' }),
    fontWeight: '400' as const,
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0.5,
  },
  bodyMedium: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif' }),
    fontWeight: '400' as const,
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.25,
  },
  bodySmall: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif' }),
    fontWeight: '400' as const,
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.4,
  },
  labelLarge: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif-medium' }),
    fontWeight: '500' as const,
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0.1,
  },
  labelMedium: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif-medium' }),
    fontWeight: '500' as const,
    fontSize: 12,
    lineHeight: 16,
    letterSpacing: 0.5,
  },
  labelSmall: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif-medium' }),
    fontWeight: '500' as const,
    fontSize: 11,
    lineHeight: 16,
    letterSpacing: 0.5,
  },
};

// Custom colors
export const colors = {
  // Primary
  primary: '#3B82F6',
  primaryContainer: '#DBEAFE',
  onPrimary: '#FFFFFF',
  onPrimaryContainer: '#1E40AF',
  
  // Secondary
  secondary: '#6366F1',
  secondaryContainer: '#E0E7FF',
  onSecondary: '#FFFFFF',
  onSecondaryContainer: '#3730A3',
  
  // Semantic
  success: '#22C55E',
  successContainer: '#DCFCE7',
  onSuccess: '#FFFFFF',
  onSuccessContainer: '#166534',
  
  warning: '#F59E0B',
  warningContainer: '#FEF3C7',
  onWarning: '#FFFFFF',
  onWarningContainer: '#92400E',
  
  danger: '#EF4444',
  dangerContainer: '#FEE2E2',
  onDanger: '#FFFFFF',
  onDangerContainer: '#991B1B',
  
  info: '#06B6D4',
  infoContainer: '#CFFAFE',
  onInfo: '#FFFFFF',
  onInfoContainer: '#155E75',
  
  // Neutral
  background: '#F8FAFC',
  surface: '#FFFFFF',
  surfaceVariant: '#F1F5F9',
  onBackground: '#1E293B',
  onSurface: '#1E293B',
  onSurfaceVariant: '#64748B',
  outline: '#CBD5E1',
  outlineVariant: '#E2E8F0',
  
  // Dark mode
  darkBackground: '#0F172A',
  darkSurface: '#1E293B',
  darkSurfaceVariant: '#334155',
  darkOnBackground: '#F1F5F9',
  darkOnSurface: '#F1F5F9',
  darkOnSurfaceVariant: '#94A3B8',
  darkOutline: '#475569',
  darkOutlineVariant: '#334155',
};

// Spacing scale
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

// Border radius
export const borderRadius = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  full: 9999,
};

// Shadows
export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
  },
};

// Light theme
export const lightTheme = {
  ...MD3LightTheme,
  fonts: configureFonts({ config: fontConfig }),
  colors: {
    ...MD3LightTheme.colors,
    primary: colors.primary,
    primaryContainer: colors.primaryContainer,
    onPrimary: colors.onPrimary,
    onPrimaryContainer: colors.onPrimaryContainer,
    secondary: colors.secondary,
    secondaryContainer: colors.secondaryContainer,
    onSecondary: colors.onSecondary,
    onSecondaryContainer: colors.onSecondaryContainer,
    background: colors.background,
    surface: colors.surface,
    surfaceVariant: colors.surfaceVariant,
    onBackground: colors.onBackground,
    onSurface: colors.onSurface,
    onSurfaceVariant: colors.onSurfaceVariant,
    outline: colors.outline,
    outlineVariant: colors.outlineVariant,
    error: colors.danger,
    errorContainer: colors.dangerContainer,
    onError: colors.onDanger,
    onErrorContainer: colors.onDangerContainer,
  },
  custom: {
    success: colors.success,
    successContainer: colors.successContainer,
    warning: colors.warning,
    warningContainer: colors.warningContainer,
    info: colors.info,
    infoContainer: colors.infoContainer,
  },
};

// Dark theme
export const darkTheme = {
  ...MD3DarkTheme,
  fonts: configureFonts({ config: fontConfig }),
  colors: {
    ...MD3DarkTheme.colors,
    primary: colors.primary,
    primaryContainer: '#1E3A5F',
    onPrimary: colors.onPrimary,
    onPrimaryContainer: '#93C5FD',
    secondary: colors.secondary,
    secondaryContainer: '#312E81',
    onSecondary: colors.onSecondary,
    onSecondaryContainer: '#A5B4FC',
    background: colors.darkBackground,
    surface: colors.darkSurface,
    surfaceVariant: colors.darkSurfaceVariant,
    onBackground: colors.darkOnBackground,
    onSurface: colors.darkOnSurface,
    onSurfaceVariant: colors.darkOnSurfaceVariant,
    outline: colors.darkOutline,
    outlineVariant: colors.darkOutlineVariant,
    error: colors.danger,
    errorContainer: '#7F1D1D',
    onError: colors.onDanger,
    onErrorContainer: '#FCA5A5',
  },
  custom: {
    success: colors.success,
    successContainer: '#14532D',
    warning: colors.warning,
    warningContainer: '#78350F',
    info: colors.info,
    infoContainer: '#164E63',
  },
};

export type AppTheme = typeof lightTheme;
```

---

## TASK 3: REDUX STORE CONFIGURATION

### 3.1 Create Store Configuration

**File:** `mobile/src/store/index.ts`

```typescript
/**
 * Redux Store Configuration
 * Centralized state management with persistence
 */

import { configureStore, combineReducers } from '@reduxjs/toolkit';
import {
  persistStore,
  persistReducer,
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER,
} from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';

import authReducer from './slices/authSlice';
import inventoryReducer from './slices/inventorySlice';
import projectsReducer from './slices/projectsSlice';
import transactionsReducer from './slices/transactionsSlice';
import paymentsReducer from './slices/paymentsSlice';
import syncReducer from './slices/syncSlice';
import settingsReducer from './slices/settingsSlice';
import { apiSlice } from './api/apiSlice';

// Persist configuration
const persistConfig = {
  key: 'root',
  version: 1,
  storage: AsyncStorage,
  whitelist: ['auth', 'settings', 'inventory', 'projects', 'transactions', 'payments'],
  blacklist: ['sync', 'api'],
};

// Root reducer
const rootReducer = combineReducers({
  auth: authReducer,
  inventory: inventoryReducer,
  projects: projectsReducer,
  transactions: transactionsReducer,
  payments: paymentsReducer,
  sync: syncReducer,
  settings: settingsReducer,
  [apiSlice.reducerPath]: apiSlice.reducer,
});

// Persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configure store
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    }).concat(apiSlice.middleware),
  devTools: __DEV__,
});

// Persistor
export const persistor = persistStore(store);

// Types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### 3.2 Create Auth Slice

**File:** `mobile/src/store/slices/authSlice.ts`

```typescript
/**
 * Authentication State Slice
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import * as Keychain from 'react-native-keychain';
import { authService } from '@services/auth/authService';

interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'client' | 'supplier';
  avatar?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  biometricsEnabled: boolean;
  pinEnabled: boolean;
  lastActivity: number | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  biometricsEnabled: false,
  pinEnabled: false,
  lastActivity: null,
};

// Async thunks
export const login = createAsyncThunk(
  'auth/login',
  async (
    credentials: { email: string; password: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await authService.login(credentials);
      
      // Store tokens securely
      await Keychain.setGenericPassword(
        'tokens',
        JSON.stringify({
          accessToken: response.accessToken,
          refreshToken: response.refreshToken,
        }),
        { service: 'com.logiaccounting.tokens' }
      );
      
      return response.user;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Login failed');
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authService.logout();
      await Keychain.resetGenericPassword({ service: 'com.logiaccounting.tokens' });
      await Keychain.resetGenericPassword({ service: 'com.logiaccounting.pin' });
    } catch (error: any) {
      return rejectWithValue(error.message || 'Logout failed');
    }
  }
);

export const refreshSession = createAsyncThunk(
  'auth/refresh',
  async (_, { rejectWithValue }) => {
    try {
      const credentials = await Keychain.getGenericPassword({
        service: 'com.logiaccounting.tokens',
      });
      
      if (!credentials) {
        throw new Error('No stored credentials');
      }
      
      const tokens = JSON.parse(credentials.password);
      const response = await authService.refreshToken(tokens.refreshToken);
      
      // Update stored tokens
      await Keychain.setGenericPassword(
        'tokens',
        JSON.stringify({
          accessToken: response.accessToken,
          refreshToken: response.refreshToken,
        }),
        { service: 'com.logiaccounting.tokens' }
      );
      
      return response.user;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Session refresh failed');
    }
  }
);

export const setPin = createAsyncThunk(
  'auth/setPin',
  async (pin: string, { rejectWithValue }) => {
    try {
      await Keychain.setGenericPassword('pin', pin, {
        service: 'com.logiaccounting.pin',
        accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
      });
      return true;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to set PIN');
    }
  }
);

export const verifyPin = createAsyncThunk(
  'auth/verifyPin',
  async (pin: string, { rejectWithValue }) => {
    try {
      const credentials = await Keychain.getGenericPassword({
        service: 'com.logiaccounting.pin',
      });
      
      if (!credentials || credentials.password !== pin) {
        throw new Error('Invalid PIN');
      }
      
      return true;
    } catch (error: any) {
      return rejectWithValue(error.message || 'PIN verification failed');
    }
  }
);

// Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User | null>) => {
      state.user = action.payload;
      state.isAuthenticated = !!action.payload;
    },
    setBiometricsEnabled: (state, action: PayloadAction<boolean>) => {
      state.biometricsEnabled = action.payload;
    },
    setPinEnabled: (state, action: PayloadAction<boolean>) => {
      state.pinEnabled = action.payload;
    },
    updateLastActivity: (state) => {
      state.lastActivity = Date.now();
    },
    clearError: (state) => {
      state.error = null;
    },
    resetAuth: () => initialState,
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
        state.lastActivity = Date.now();
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Logout
      .addCase(logout.fulfilled, () => initialState)
      // Refresh
      .addCase(refreshSession.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthenticated = true;
        state.lastActivity = Date.now();
      })
      .addCase(refreshSession.rejected, () => initialState)
      // PIN
      .addCase(setPin.fulfilled, (state) => {
        state.pinEnabled = true;
      })
      .addCase(verifyPin.fulfilled, (state) => {
        state.lastActivity = Date.now();
      });
  },
});

export const {
  setUser,
  setBiometricsEnabled,
  setPinEnabled,
  updateLastActivity,
  clearError,
  resetAuth,
} = authSlice.actions;

export default authSlice.reducer;
```

### 3.3 Create Settings Slice

**File:** `mobile/src/store/slices/settingsSlice.ts`

```typescript
/**
 * Settings State Slice
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type ThemeMode = 'light' | 'dark' | 'system';
type Language = 'en' | 'es' | 'de' | 'fr';
type Currency = 'USD' | 'EUR' | 'GBP';
type DateFormat = 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD';

interface SettingsState {
  theme: ThemeMode;
  language: Language;
  currency: Currency;
  dateFormat: DateFormat;
  notifications: {
    push: boolean;
    payments: boolean;
    inventory: boolean;
    approvals: boolean;
    weeklySummary: boolean;
  };
  security: {
    biometricEnabled: boolean;
    pinEnabled: boolean;
    autoLockMinutes: number;
  };
  sync: {
    autoSync: boolean;
    syncOnWifiOnly: boolean;
    syncIntervalMinutes: number;
  };
  display: {
    compactMode: boolean;
    showAnimations: boolean;
  };
}

const initialState: SettingsState = {
  theme: 'system',
  language: 'en',
  currency: 'USD',
  dateFormat: 'MM/DD/YYYY',
  notifications: {
    push: true,
    payments: true,
    inventory: true,
    approvals: true,
    weeklySummary: true,
  },
  security: {
    biometricEnabled: false,
    pinEnabled: false,
    autoLockMinutes: 5,
  },
  sync: {
    autoSync: true,
    syncOnWifiOnly: false,
    syncIntervalMinutes: 15,
  },
  display: {
    compactMode: false,
    showAnimations: true,
  },
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<ThemeMode>) => {
      state.theme = action.payload;
    },
    setLanguage: (state, action: PayloadAction<Language>) => {
      state.language = action.payload;
    },
    setCurrency: (state, action: PayloadAction<Currency>) => {
      state.currency = action.payload;
    },
    setDateFormat: (state, action: PayloadAction<DateFormat>) => {
      state.dateFormat = action.payload;
    },
    updateNotificationSettings: (
      state,
      action: PayloadAction<Partial<SettingsState['notifications']>>
    ) => {
      state.notifications = { ...state.notifications, ...action.payload };
    },
    updateSecuritySettings: (
      state,
      action: PayloadAction<Partial<SettingsState['security']>>
    ) => {
      state.security = { ...state.security, ...action.payload };
    },
    updateSyncSettings: (
      state,
      action: PayloadAction<Partial<SettingsState['sync']>>
    ) => {
      state.sync = { ...state.sync, ...action.payload };
    },
    updateDisplaySettings: (
      state,
      action: PayloadAction<Partial<SettingsState['display']>>
    ) => {
      state.display = { ...state.display, ...action.payload };
    },
    resetSettings: () => initialState,
  },
});

export const {
  setTheme,
  setLanguage,
  setCurrency,
  setDateFormat,
  updateNotificationSettings,
  updateSecuritySettings,
  updateSyncSettings,
  updateDisplaySettings,
  resetSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;
```

### 3.4 Create Sync Slice

**File:** `mobile/src/store/slices/syncSlice.ts`

```typescript
/**
 * Sync State Slice
 * Manages offline queue and synchronization status
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface QueuedAction {
  id: string;
  type: string;
  payload: any;
  timestamp: number;
  retries: number;
  status: 'pending' | 'processing' | 'failed';
}

interface SyncState {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncTime: number | null;
  syncError: string | null;
  queue: QueuedAction[];
  pendingCount: number;
  conflictsCount: number;
}

const initialState: SyncState = {
  isOnline: true,
  isSyncing: false,
  lastSyncTime: null,
  syncError: null,
  queue: [],
  pendingCount: 0,
  conflictsCount: 0,
};

const syncSlice = createSlice({
  name: 'sync',
  initialState,
  reducers: {
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.isOnline = action.payload;
    },
    startSync: (state) => {
      state.isSyncing = true;
      state.syncError = null;
    },
    syncComplete: (state) => {
      state.isSyncing = false;
      state.lastSyncTime = Date.now();
      state.queue = state.queue.filter((item) => item.status === 'pending');
      state.pendingCount = state.queue.length;
    },
    syncFailed: (state, action: PayloadAction<string>) => {
      state.isSyncing = false;
      state.syncError = action.payload;
    },
    addToQueue: (state, action: PayloadAction<Omit<QueuedAction, 'id' | 'timestamp' | 'retries' | 'status'>>) => {
      const newAction: QueuedAction = {
        ...action.payload,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
        retries: 0,
        status: 'pending',
      };
      state.queue.push(newAction);
      state.pendingCount = state.queue.filter((i) => i.status === 'pending').length;
    },
    updateQueueItem: (
      state,
      action: PayloadAction<{ id: string; updates: Partial<QueuedAction> }>
    ) => {
      const index = state.queue.findIndex((item) => item.id === action.payload.id);
      if (index !== -1) {
        state.queue[index] = { ...state.queue[index], ...action.payload.updates };
      }
      state.pendingCount = state.queue.filter((i) => i.status === 'pending').length;
    },
    removeFromQueue: (state, action: PayloadAction<string>) => {
      state.queue = state.queue.filter((item) => item.id !== action.payload);
      state.pendingCount = state.queue.filter((i) => i.status === 'pending').length;
    },
    clearQueue: (state) => {
      state.queue = [];
      state.pendingCount = 0;
    },
    setConflictsCount: (state, action: PayloadAction<number>) => {
      state.conflictsCount = action.payload;
    },
  },
});

export const {
  setOnlineStatus,
  startSync,
  syncComplete,
  syncFailed,
  addToQueue,
  updateQueueItem,
  removeFromQueue,
  clearQueue,
  setConflictsCount,
} = syncSlice.actions;

export default syncSlice.reducer;
```

### 3.5 Create Inventory Slice

**File:** `mobile/src/store/slices/inventorySlice.ts`

```typescript
/**
 * Inventory State Slice
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { inventoryApi } from '@services/api/inventory';

interface Material {
  id: string;
  reference: string;
  name: string;
  description?: string;
  category: string;
  location: string;
  currentStock: number;
  minStock: number;
  unitCost: number;
  state: 'active' | 'inactive' | 'depleted';
  updatedAt: string;
}

interface Movement {
  id: string;
  materialId: string;
  projectId?: string;
  type: 'entry' | 'exit';
  quantity: number;
  date: string;
  notes?: string;
  createdBy: string;
}

interface InventoryState {
  materials: Material[];
  movements: Movement[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;
  filters: {
    search: string;
    category: string | null;
    location: string | null;
    state: string | null;
  };
}

const initialState: InventoryState = {
  materials: [],
  movements: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  filters: {
    search: '',
    category: null,
    location: null,
    state: null,
  },
};

// Async thunks
export const fetchMaterials = createAsyncThunk(
  'inventory/fetchMaterials',
  async (_, { rejectWithValue }) => {
    try {
      const response = await inventoryApi.getMaterials();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch materials');
    }
  }
);

export const fetchMovements = createAsyncThunk(
  'inventory/fetchMovements',
  async (materialId: string | undefined, { rejectWithValue }) => {
    try {
      const response = await inventoryApi.getMovements(materialId);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch movements');
    }
  }
);

export const createMovement = createAsyncThunk(
  'inventory/createMovement',
  async (movement: Omit<Movement, 'id' | 'createdBy'>, { rejectWithValue }) => {
    try {
      const response = await inventoryApi.createMovement(movement);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to create movement');
    }
  }
);

// Slice
const inventorySlice = createSlice({
  name: 'inventory',
  initialState,
  reducers: {
    setMaterials: (state, action: PayloadAction<Material[]>) => {
      state.materials = action.payload;
      state.lastUpdated = Date.now();
    },
    updateMaterial: (state, action: PayloadAction<Material>) => {
      const index = state.materials.findIndex((m) => m.id === action.payload.id);
      if (index !== -1) {
        state.materials[index] = action.payload;
      }
    },
    setFilters: (state, action: PayloadAction<Partial<InventoryState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = initialState.filters;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch materials
      .addCase(fetchMaterials.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchMaterials.fulfilled, (state, action) => {
        state.isLoading = false;
        state.materials = action.payload;
        state.lastUpdated = Date.now();
      })
      .addCase(fetchMaterials.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Fetch movements
      .addCase(fetchMovements.fulfilled, (state, action) => {
        state.movements = action.payload;
      })
      // Create movement
      .addCase(createMovement.fulfilled, (state, action) => {
        state.movements.unshift(action.payload);
        // Update material stock
        const material = state.materials.find(
          (m) => m.id === action.payload.materialId
        );
        if (material) {
          const delta =
            action.payload.type === 'entry'
              ? action.payload.quantity
              : -action.payload.quantity;
          material.currentStock += delta;
        }
      });
  },
});

export const {
  setMaterials,
  updateMaterial,
  setFilters,
  clearFilters,
  clearError,
} = inventorySlice.actions;

export default inventorySlice.reducer;
```

### 3.6 Create Remaining Slices Stubs

**File:** `mobile/src/store/slices/projectsSlice.ts`

```typescript
/**
 * Projects State Slice
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { projectsApi } from '@services/api/projects';

interface Project {
  id: string;
  code: string;
  name: string;
  clientId: string;
  clientName: string;
  status: 'planning' | 'active' | 'completed' | 'cancelled';
  startDate: string;
  endDate?: string;
  budget: number;
  spent: number;
  description?: string;
}

interface ProjectsState {
  projects: Project[];
  selectedProject: Project | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;
}

const initialState: ProjectsState = {
  projects: [],
  selectedProject: null,
  isLoading: false,
  error: null,
  lastUpdated: null,
};

export const fetchProjects = createAsyncThunk(
  'projects/fetchProjects',
  async (_, { rejectWithValue }) => {
    try {
      const response = await projectsApi.getProjects();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch projects');
    }
  }
);

const projectsSlice = createSlice({
  name: 'projects',
  initialState,
  reducers: {
    setProjects: (state, action: PayloadAction<Project[]>) => {
      state.projects = action.payload;
      state.lastUpdated = Date.now();
    },
    setSelectedProject: (state, action: PayloadAction<Project | null>) => {
      state.selectedProject = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchProjects.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchProjects.fulfilled, (state, action) => {
        state.isLoading = false;
        state.projects = action.payload;
        state.lastUpdated = Date.now();
      })
      .addCase(fetchProjects.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { setProjects, setSelectedProject, clearError } = projectsSlice.actions;
export default projectsSlice.reducer;
```

**File:** `mobile/src/store/slices/transactionsSlice.ts`

```typescript
/**
 * Transactions State Slice
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { transactionsApi } from '@services/api/transactions';

interface Transaction {
  id: string;
  type: 'income' | 'expense';
  category: string;
  amount: number;
  taxAmount: number;
  date: string;
  description: string;
  vendorName?: string;
  invoiceNumber?: string;
  invoiceUrl?: string;
  projectId?: string;
}

interface TransactionsState {
  transactions: Transaction[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;
  filters: {
    type: 'all' | 'income' | 'expense';
    dateRange: { start: string | null; end: string | null };
    category: string | null;
  };
}

const initialState: TransactionsState = {
  transactions: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  filters: {
    type: 'all',
    dateRange: { start: null, end: null },
    category: null,
  },
};

export const fetchTransactions = createAsyncThunk(
  'transactions/fetchTransactions',
  async (_, { rejectWithValue }) => {
    try {
      const response = await transactionsApi.getTransactions();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch transactions');
    }
  }
);

export const createTransaction = createAsyncThunk(
  'transactions/createTransaction',
  async (transaction: Omit<Transaction, 'id'>, { rejectWithValue }) => {
    try {
      const response = await transactionsApi.createTransaction(transaction);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to create transaction');
    }
  }
);

const transactionsSlice = createSlice({
  name: 'transactions',
  initialState,
  reducers: {
    setTransactions: (state, action: PayloadAction<Transaction[]>) => {
      state.transactions = action.payload;
      state.lastUpdated = Date.now();
    },
    setFilters: (state, action: PayloadAction<Partial<TransactionsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = initialState.filters;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTransactions.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchTransactions.fulfilled, (state, action) => {
        state.isLoading = false;
        state.transactions = action.payload;
        state.lastUpdated = Date.now();
      })
      .addCase(fetchTransactions.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(createTransaction.fulfilled, (state, action) => {
        state.transactions.unshift(action.payload);
      });
  },
});

export const { setTransactions, setFilters, clearFilters, clearError } = transactionsSlice.actions;
export default transactionsSlice.reducer;
```

**File:** `mobile/src/store/slices/paymentsSlice.ts`

```typescript
/**
 * Payments State Slice
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { paymentsApi } from '@services/api/payments';

interface Payment {
  id: string;
  type: 'receivable' | 'payable';
  amount: number;
  dueDate: string;
  paidDate?: string;
  status: 'pending' | 'paid' | 'overdue' | 'cancelled';
  description: string;
  clientId?: string;
  clientName?: string;
  vendorId?: string;
  vendorName?: string;
}

interface PaymentsState {
  payments: Payment[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: number | null;
  overdueCount: number;
  upcomingCount: number;
}

const initialState: PaymentsState = {
  payments: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  overdueCount: 0,
  upcomingCount: 0,
};

export const fetchPayments = createAsyncThunk(
  'payments/fetchPayments',
  async (_, { rejectWithValue }) => {
    try {
      const response = await paymentsApi.getPayments();
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch payments');
    }
  }
);

export const recordPayment = createAsyncThunk(
  'payments/recordPayment',
  async ({ id, paidDate }: { id: string; paidDate: string }, { rejectWithValue }) => {
    try {
      const response = await paymentsApi.recordPayment(id, paidDate);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to record payment');
    }
  }
);

const paymentsSlice = createSlice({
  name: 'payments',
  initialState,
  reducers: {
    setPayments: (state, action: PayloadAction<Payment[]>) => {
      state.payments = action.payload;
      state.lastUpdated = Date.now();
      state.overdueCount = action.payload.filter((p) => p.status === 'overdue').length;
      state.upcomingCount = action.payload.filter(
        (p) => p.status === 'pending' && new Date(p.dueDate) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      ).length;
    },
    updatePayment: (state, action: PayloadAction<Payment>) => {
      const index = state.payments.findIndex((p) => p.id === action.payload.id);
      if (index !== -1) {
        state.payments[index] = action.payload;
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPayments.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPayments.fulfilled, (state, action) => {
        state.isLoading = false;
        state.payments = action.payload;
        state.lastUpdated = Date.now();
        state.overdueCount = action.payload.filter((p: Payment) => p.status === 'overdue').length;
        state.upcomingCount = action.payload.filter(
          (p: Payment) => p.status === 'pending' && new Date(p.dueDate) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
        ).length;
      })
      .addCase(fetchPayments.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(recordPayment.fulfilled, (state, action) => {
        const index = state.payments.findIndex((p) => p.id === action.payload.id);
        if (index !== -1) {
          state.payments[index] = action.payload;
        }
      });
  },
});

export const { setPayments, updatePayment, clearError } = paymentsSlice.actions;
export default paymentsSlice.reducer;
```

### 3.7 Create API Slice (RTK Query)

**File:** `mobile/src/store/api/apiSlice.ts`

```typescript
/**
 * RTK Query API Slice
 * Centralized API caching and invalidation
 */

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import * as Keychain from 'react-native-keychain';
import Config from 'react-native-config';

const baseQuery = fetchBaseQuery({
  baseUrl: Config.API_URL || 'http://localhost:5000/api/v1',
  prepareHeaders: async (headers) => {
    try {
      const credentials = await Keychain.getGenericPassword({
        service: 'com.logiaccounting.tokens',
      });
      
      if (credentials) {
        const tokens = JSON.parse(credentials.password);
        headers.set('Authorization', `Bearer ${tokens.accessToken}`);
      }
    } catch (error) {
      console.error('Error getting token:', error);
    }
    
    return headers;
  },
});

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery,
  tagTypes: ['Dashboard', 'Inventory', 'Projects', 'Transactions', 'Payments', 'Analytics'],
  endpoints: (builder) => ({
    // Dashboard
    getDashboard: builder.query({
      query: () => '/dashboard',
      providesTags: ['Dashboard'],
    }),
    
    // Inventory
    getMaterials: builder.query({
      query: () => '/materials',
      providesTags: ['Inventory'],
    }),
    getMaterial: builder.query({
      query: (id) => `/materials/${id}`,
      providesTags: (result, error, id) => [{ type: 'Inventory', id }],
    }),
    
    // Projects
    getProjects: builder.query({
      query: () => '/projects',
      providesTags: ['Projects'],
    }),
    getProject: builder.query({
      query: (id) => `/projects/${id}`,
      providesTags: (result, error, id) => [{ type: 'Projects', id }],
    }),
    
    // Analytics
    getAnalyticsDashboard: builder.query({
      query: () => '/analytics/dashboard',
      providesTags: ['Analytics'],
    }),
    getHealthScore: builder.query({
      query: () => '/analytics/health-score',
      providesTags: ['Analytics'],
    }),
  }),
});

export const {
  useGetDashboardQuery,
  useGetMaterialsQuery,
  useGetMaterialQuery,
  useGetProjectsQuery,
  useGetProjectQuery,
  useGetAnalyticsDashboardQuery,
  useGetHealthScoreQuery,
} = apiSlice;
```

---

## Continue to Part 2 for Navigation and Authentication Screens

---

*Phase 11 Tasks Part 1 - LogiAccounting Pro*
*Project Setup, Theme, and Redux Store*
