/**
 * Authentication Service
 * Handles login, logout, token management
 */

import * as Keychain from 'react-native-keychain';
import apiClient from '../api/client';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

const TOKEN_SERVICE = 'com.logiaccounting.tokens';
const USER_SERVICE = 'com.logiaccounting.user';

export const authService = {
  /**
   * Login with email and password
   */
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
    const { user, tokens } = response.data;

    // Store tokens securely
    await Keychain.setGenericPassword('tokens', JSON.stringify(tokens), {
      service: TOKEN_SERVICE,
    });

    // Store user info
    await Keychain.setGenericPassword('user', JSON.stringify(user), {
      service: USER_SERVICE,
    });

    return response.data;
  },

  /**
   * Logout and clear tokens
   */
  logout: async (): Promise<void> => {
    try {
      // Notify server
      await apiClient.post('/auth/logout');
    } catch (error) {
      // Continue with local logout even if server call fails
    }

    // Clear stored credentials
    await Keychain.resetGenericPassword({ service: TOKEN_SERVICE });
    await Keychain.resetGenericPassword({ service: USER_SERVICE });
  },

  /**
   * Refresh access token
   */
  refreshToken: async (): Promise<AuthTokens> => {
    const credentials = await Keychain.getGenericPassword({
      service: TOKEN_SERVICE,
    });

    if (!credentials) {
      throw new Error('No tokens found');
    }

    const tokens = JSON.parse(credentials.password) as AuthTokens;
    const response = await apiClient.post<AuthTokens>('/auth/refresh', {
      refreshToken: tokens.refreshToken,
    });

    const newTokens = response.data;

    // Store new tokens
    await Keychain.setGenericPassword('tokens', JSON.stringify(newTokens), {
      service: TOKEN_SERVICE,
    });

    return newTokens;
  },

  /**
   * Get stored tokens
   */
  getTokens: async (): Promise<AuthTokens | null> => {
    try {
      const credentials = await Keychain.getGenericPassword({
        service: TOKEN_SERVICE,
      });

      if (credentials) {
        return JSON.parse(credentials.password) as AuthTokens;
      }
    } catch (error) {
      console.error('Error getting tokens:', error);
    }
    return null;
  },

  /**
   * Get stored user
   */
  getUser: async (): Promise<User | null> => {
    try {
      const credentials = await Keychain.getGenericPassword({
        service: USER_SERVICE,
      });

      if (credentials) {
        return JSON.parse(credentials.password) as User;
      }
    } catch (error) {
      console.error('Error getting user:', error);
    }
    return null;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: async (): Promise<boolean> => {
    const tokens = await authService.getTokens();
    return !!tokens?.accessToken;
  },

  /**
   * Request password reset
   */
  forgotPassword: async (email: string): Promise<void> => {
    await apiClient.post('/auth/forgot-password', { email });
  },

  /**
   * Reset password with token
   */
  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    await apiClient.post('/auth/reset-password', { token, newPassword });
  },

  /**
   * Change password
   */
  changePassword: async (
    currentPassword: string,
    newPassword: string
  ): Promise<void> => {
    await apiClient.post('/auth/change-password', {
      currentPassword,
      newPassword,
    });
  },
};

export default authService;
