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
