/**
 * Auth Store - Zustand state management for authentication
 */

import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { authService, LoginCredentials, User } from '@services/authService';
import { biometricService } from '@services/biometricService';

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'user_data';
const BIOMETRIC_ENABLED_KEY = 'biometric_enabled';

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  token: string | null;
  biometricEnabled: boolean;
  error: string | null;

  login: (credentials: LoginCredentials) => Promise<boolean>;
  loginWithBiometric: () => Promise<boolean>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  enableBiometric: () => Promise<boolean>;
  disableBiometric: () => Promise<void>;
  clearError: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  isAuthenticated: false,
  isLoading: true,
  user: null,
  token: null,
  biometricEnabled: false,
  error: null,

  login: async (credentials: LoginCredentials) => {
    set({ isLoading: true, error: null });

    try {
      const response = await authService.login(credentials);

      await SecureStore.setItemAsync(TOKEN_KEY, response.token);
      await SecureStore.setItemAsync(USER_KEY, JSON.stringify(response.user));

      set({
        isAuthenticated: true,
        user: response.user,
        token: response.token,
        isLoading: false,
      });

      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      set({ error: message, isLoading: false });
      return false;
    }
  },

  loginWithBiometric: async () => {
    const { biometricEnabled } = get();

    if (!biometricEnabled) {
      set({ error: 'Biometric authentication not enabled' });
      return false;
    }

    set({ isLoading: true, error: null });

    try {
      const isValid = await biometricService.authenticate('Authenticate to access LogiAccounting Pro');

      if (!isValid) {
        set({ error: 'Biometric authentication failed', isLoading: false });
        return false;
      }

      const tokenData = await SecureStore.getItemAsync(TOKEN_KEY);
      const userData = await SecureStore.getItemAsync(USER_KEY);

      if (!tokenData || !userData) {
        set({ error: 'No stored credentials found', isLoading: false });
        return false;
      }

      const isTokenValid = await authService.validateToken(tokenData);

      if (!isTokenValid) {
        await get().logout();
        set({ error: 'Session expired, please login again', isLoading: false });
        return false;
      }

      set({
        isAuthenticated: true,
        user: JSON.parse(userData),
        token: tokenData,
        isLoading: false,
      });

      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Biometric authentication failed';
      set({ error: message, isLoading: false });
      return false;
    }
  },

  logout: async () => {
    set({ isLoading: true });

    try {
      const token = get().token;
      if (token) {
        await authService.logout(token);
      }
    } catch (error) {
      console.error('Logout API error:', error);
    }

    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);

    set({
      isAuthenticated: false,
      user: null,
      token: null,
      isLoading: false,
      error: null,
    });
  },

  checkAuth: async () => {
    set({ isLoading: true });

    try {
      const [tokenData, userData, biometricEnabled] = await Promise.all([
        SecureStore.getItemAsync(TOKEN_KEY),
        SecureStore.getItemAsync(USER_KEY),
        SecureStore.getItemAsync(BIOMETRIC_ENABLED_KEY),
      ]);

      if (!tokenData || !userData) {
        set({ isLoading: false, biometricEnabled: biometricEnabled === 'true' });
        return;
      }

      const isValid = await authService.validateToken(tokenData);

      if (isValid) {
        set({
          isAuthenticated: true,
          user: JSON.parse(userData),
          token: tokenData,
          biometricEnabled: biometricEnabled === 'true',
          isLoading: false,
        });
      } else {
        await SecureStore.deleteItemAsync(TOKEN_KEY);
        await SecureStore.deleteItemAsync(USER_KEY);
        set({ isLoading: false, biometricEnabled: biometricEnabled === 'true' });
      }
    } catch (error) {
      console.error('Auth check error:', error);
      set({ isLoading: false });
    }
  },

  enableBiometric: async () => {
    try {
      const isAvailable = await biometricService.isAvailable();

      if (!isAvailable) {
        set({ error: 'Biometric authentication is not available on this device' });
        return false;
      }

      const enrolled = await biometricService.isEnrolled();

      if (!enrolled) {
        set({ error: 'No biometric credentials enrolled on this device' });
        return false;
      }

      const verified = await biometricService.authenticate('Verify your identity to enable biometric login');

      if (!verified) {
        set({ error: 'Biometric verification failed' });
        return false;
      }

      await SecureStore.setItemAsync(BIOMETRIC_ENABLED_KEY, 'true');
      set({ biometricEnabled: true, error: null });
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to enable biometric';
      set({ error: message });
      return false;
    }
  },

  disableBiometric: async () => {
    await SecureStore.deleteItemAsync(BIOMETRIC_ENABLED_KEY);
    set({ biometricEnabled: false });
  },

  clearError: () => set({ error: null }),

  updateUser: (userData: Partial<User>) => {
    const currentUser = get().user;
    if (currentUser) {
      const updatedUser = { ...currentUser, ...userData };
      set({ user: updatedUser });
      SecureStore.setItemAsync(USER_KEY, JSON.stringify(updatedUser));
    }
  },
}));
