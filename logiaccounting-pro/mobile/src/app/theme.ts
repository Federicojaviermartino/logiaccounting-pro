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
