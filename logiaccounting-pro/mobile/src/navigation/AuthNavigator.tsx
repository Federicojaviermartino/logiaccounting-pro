/**
 * Auth Navigator
 * Handles authentication flow screens
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useSelector } from 'react-redux';

import { RootState } from '@store/index';
import { LoginScreen } from '@screens/auth/LoginScreen';
import { BiometricScreen } from '@screens/auth/BiometricScreen';
import { PinScreen } from '@screens/auth/PinScreen';
import { ForgotPasswordScreen } from '@screens/auth/ForgotPasswordScreen';
import type { AuthStackParamList } from '@types/navigation';

const Stack = createNativeStackNavigator<AuthStackParamList>();

export const AuthNavigator: React.FC = () => {
  const { biometricEnabled, pinEnabled } = useSelector((state: RootState) => state.auth);

  // Determine initial route based on auth settings
  const getInitialRouteName = (): keyof AuthStackParamList => {
    if (biometricEnabled) {
      return 'Biometric';
    }
    if (pinEnabled) {
      return 'Pin';
    }
    return 'Login';
  };

  return (
    <Stack.Navigator
      initialRouteName={getInitialRouteName()}
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
        gestureEnabled: true,
      }}
    >
      <Stack.Screen
        name="Login"
        component={LoginScreen}
        options={{
          animationTypeForReplace: 'push',
        }}
      />
      <Stack.Screen
        name="Biometric"
        component={BiometricScreen}
        options={{
          animation: 'fade',
        }}
      />
      <Stack.Screen
        name="Pin"
        component={PinScreen}
        options={{
          animation: 'fade',
        }}
      />
      <Stack.Screen
        name="ForgotPassword"
        component={ForgotPasswordScreen}
      />
    </Stack.Navigator>
  );
};

export default AuthNavigator;
