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

// Declare __DEV__ for TypeScript
declare const __DEV__: boolean;
