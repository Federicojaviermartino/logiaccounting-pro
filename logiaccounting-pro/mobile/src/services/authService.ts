/**
 * Auth Service - API calls for authentication
 */

import { apiClient } from './client';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  company?: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  company?: string;
  avatar?: string;
  preferences?: UserPreferences;
  createdAt: string;
}

export interface UserPreferences {
  currency: string;
  language: string;
  timezone: string;
  notifications: boolean;
}

export interface AuthResponse {
  token: string;
  refreshToken: string;
  user: User;
  expiresAt: string;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },

  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register', data);
    return response.data;
  },

  async logout(token: string): Promise<void> {
    await apiClient.post('/auth/logout', {}, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },

  async validateToken(token: string): Promise<boolean> {
    try {
      const response = await apiClient.get('/auth/validate', {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.status === 200;
    } catch {
      return false;
    }
  },

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/refresh', { refreshToken });
    return response.data;
  },

  async forgotPassword(email: string): Promise<{ message: string }> {
    const response = await apiClient.post('/auth/forgot-password', { email });
    return response.data;
  },

  async resetPassword(token: string, password: string): Promise<{ message: string }> {
    const response = await apiClient.post('/auth/reset-password', { token, password });
    return response.data;
  },

  async updateProfile(userId: string, data: Partial<User>): Promise<User> {
    const response = await apiClient.patch<User>(`/users/${userId}`, data);
    return response.data;
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    const response = await apiClient.post('/auth/change-password', {
      currentPassword,
      newPassword,
    });
    return response.data;
  },

  async updatePreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    const response = await apiClient.patch<UserPreferences>('/users/preferences', preferences);
    return response.data;
  },
};
