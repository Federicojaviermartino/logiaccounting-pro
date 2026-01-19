/**
 * App Navigator
 * Root navigator handling auth state and navigation
 */

import React, { useEffect } from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { NavigationContainer } from '@react-navigation/native';
import { useSelector } from 'react-redux';
import { StatusBar, useColorScheme } from 'react-native';

import { RootState } from '@store/index';
import { AuthNavigator } from './AuthNavigator';
import { MainNavigator } from './MainNavigator';
import { lightTheme, darkTheme } from '@app/theme';
import type { RootStackParamList } from '@types/navigation';

const Stack = createNativeStackNavigator<RootStackParamList>();

// Navigation theme for React Navigation
const navigationLightTheme = {
  dark: false,
  colors: {
    primary: lightTheme.colors.primary,
    background: lightTheme.colors.background,
    card: lightTheme.colors.surface,
    text: lightTheme.colors.onSurface,
    border: lightTheme.colors.outline,
    notification: lightTheme.colors.error,
  },
};

const navigationDarkTheme = {
  dark: true,
  colors: {
    primary: darkTheme.colors.primary,
    background: darkTheme.colors.background,
    card: darkTheme.colors.surface,
    text: darkTheme.colors.onSurface,
    border: darkTheme.colors.outline,
    notification: darkTheme.colors.error,
  },
};

export const AppNavigator: React.FC = () => {
  const systemColorScheme = useColorScheme();
  const { isAuthenticated, sessionExpiry } = useSelector((state: RootState) => state.auth);
  const { theme: userTheme } = useSelector((state: RootState) => state.settings);

  // Determine effective theme
  const effectiveTheme = userTheme === 'system'
    ? systemColorScheme
    : userTheme;

  const isDark = effectiveTheme === 'dark';
  const navigationTheme = isDark ? navigationDarkTheme : navigationLightTheme;

  // Check if session is still valid
  const isSessionValid = sessionExpiry ? Date.now() < sessionExpiry : false;
  const shouldShowAuth = !isAuthenticated || !isSessionValid;

  return (
    <>
      <StatusBar
        barStyle={isDark ? 'light-content' : 'dark-content'}
        backgroundColor={isDark ? darkTheme.colors.background : lightTheme.colors.background}
      />
      <NavigationContainer theme={navigationTheme}>
        <Stack.Navigator
          screenOptions={{
            headerShown: false,
            animation: 'fade',
          }}
        >
          {shouldShowAuth ? (
            <Stack.Screen name="Auth" component={AuthNavigator} />
          ) : (
            <Stack.Screen name="Main" component={MainNavigator} />
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </>
  );
};

export default AppNavigator;
