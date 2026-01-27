/**
 * useAuth Hook
 * Authentication state and actions
 */

import { useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '@store/index';
import { login, logout, setAuthenticated } from '@store/slices/authSlice';
import { authService, biometricService } from '@services/index';

export const useAuth = () => {
  const dispatch = useDispatch<AppDispatch>();
  const authState = useSelector((state: RootState) => state.auth);

  const handleLogin = useCallback(
    async (email: string, password: string) => {
      return dispatch(login({ email, password })).unwrap();
    },
    [dispatch]
  );

  const handleLogout = useCallback(async () => {
    return dispatch(logout()).unwrap();
  }, [dispatch]);

  const handleBiometricLogin = useCallback(async () => {
    const success = await biometricService.authenticate(
      'Authenticate to access LogiAccounting Pro'
    );

    if (success) {
      dispatch(setAuthenticated(true));
      return true;
    }
    return false;
  }, [dispatch]);

  const checkAuthStatus = useCallback(async () => {
    const isAuth = await authService.isAuthenticated();
    const user = await authService.getUser();

    if (isAuth && user) {
      dispatch(setAuthenticated(true));
      return true;
    }
    return false;
  }, [dispatch]);

  const refreshSession = useCallback(async () => {
    try {
      await authService.refreshToken();
      return true;
    } catch {
      await handleLogout();
      return false;
    }
  }, [handleLogout]);

  return {
    // State
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    error: authState.error,
    user: authState.user,
    biometricEnabled: authState.biometricEnabled,
    pinEnabled: authState.pinEnabled,

    // Actions
    login: handleLogin,
    logout: handleLogout,
    biometricLogin: handleBiometricLogin,
    checkAuthStatus,
    refreshSession,
  };
};

export default useAuth;
