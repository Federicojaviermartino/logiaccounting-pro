/**
 * API Client
 * Axios-based HTTP client with authentication and error handling
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import * as Keychain from 'react-native-keychain';
import Config from 'react-native-config';

const BASE_URL = Config.API_URL || 'http://localhost:5000/api/v1';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token refresh state
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

const onRefreshed = (token: string) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
};

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    try {
      const credentials = await Keychain.getGenericPassword({
        service: 'com.logiaccounting.tokens',
      });

      if (credentials) {
        const tokens = JSON.parse(credentials.password);
        config.headers.Authorization = `Bearer ${tokens.accessToken}`;
      }
    } catch (error) {
      console.error('Error getting token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Handle 401 - token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Wait for token refresh
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(apiClient(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const credentials = await Keychain.getGenericPassword({
          service: 'com.logiaccounting.tokens',
        });

        if (credentials) {
          const tokens = JSON.parse(credentials.password);

          // Refresh token
          const response = await axios.post(`${BASE_URL}/auth/refresh`, {
            refreshToken: tokens.refreshToken,
          });

          const newTokens = response.data;

          // Save new tokens
          await Keychain.setGenericPassword(
            'tokens',
            JSON.stringify(newTokens),
            { service: 'com.logiaccounting.tokens' }
          );

          // Retry failed requests
          onRefreshed(newTokens.accessToken);

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${newTokens.accessToken}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Clear tokens and redirect to login
        await Keychain.resetGenericPassword({
          service: 'com.logiaccounting.tokens',
        });
        // Dispatch logout action (handled by store)
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// API response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, string>;
}

// Helper functions
export const handleApiError = (error: AxiosError<ApiError>): string => {
  if (error.response) {
    return error.response.data?.message || 'An error occurred';
  }
  if (error.request) {
    return 'Network error. Please check your connection.';
  }
  return error.message || 'An unexpected error occurred';
};

export default apiClient;
