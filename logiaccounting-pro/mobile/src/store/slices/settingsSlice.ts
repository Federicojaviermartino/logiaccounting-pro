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
