/**
 * useAppState Hook
 * App lifecycle and state management
 */

import { useEffect, useRef, useCallback } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '@store/index';
import { setAuthenticated } from '@store/slices/authSlice';

interface UseAppStateOptions {
  onForeground?: () => void;
  onBackground?: () => void;
  autoLockEnabled?: boolean;
  autoLockTimeout?: number; // milliseconds
}

export const useAppState = (options: UseAppStateOptions = {}) => {
  const {
    onForeground,
    onBackground,
    autoLockEnabled = true,
    autoLockTimeout = 5 * 60 * 1000, // 5 minutes default
  } = options;

  const dispatch = useDispatch<AppDispatch>();
  const settings = useSelector((state: RootState) => state.settings);
  const appState = useRef(AppState.currentState);
  const backgroundTime = useRef<number | null>(null);

  const handleAppStateChange = useCallback(
    (nextAppState: AppStateStatus) => {
      // App coming to foreground
      if (
        appState.current.match(/inactive|background/) &&
        nextAppState === 'active'
      ) {
        // Check if auto-lock should trigger
        if (
          autoLockEnabled &&
          settings.security.autoLockEnabled &&
          backgroundTime.current
        ) {
          const elapsed = Date.now() - backgroundTime.current;
          const timeout = settings.security.autoLockTimeout || autoLockTimeout;

          if (elapsed >= timeout) {
            // Lock the app
            dispatch(setAuthenticated(false));
          }
        }

        backgroundTime.current = null;
        onForeground?.();
      }

      // App going to background
      if (
        appState.current === 'active' &&
        nextAppState.match(/inactive|background/)
      ) {
        backgroundTime.current = Date.now();
        onBackground?.();
      }

      appState.current = nextAppState;
    },
    [
      autoLockEnabled,
      autoLockTimeout,
      settings.security.autoLockEnabled,
      settings.security.autoLockTimeout,
      onForeground,
      onBackground,
      dispatch,
    ]
  );

  useEffect(() => {
    const subscription = AppState.addEventListener(
      'change',
      handleAppStateChange
    );

    return () => {
      subscription.remove();
    };
  }, [handleAppStateChange]);

  return {
    currentState: appState.current,
    isActive: appState.current === 'active',
    isBackground: appState.current === 'background',
    isInactive: appState.current === 'inactive',
  };
};

export default useAppState;
