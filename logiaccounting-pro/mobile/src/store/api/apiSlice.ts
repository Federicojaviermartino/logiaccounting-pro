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
      providesTags: (_result, _error, id) => [{ type: 'Inventory', id }],
    }),

    // Projects
    getProjects: builder.query({
      query: () => '/projects',
      providesTags: ['Projects'],
    }),
    getProject: builder.query({
      query: (id) => `/projects/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Projects', id }],
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
