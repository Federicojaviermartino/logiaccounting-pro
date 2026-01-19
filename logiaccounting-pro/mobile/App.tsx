/**
 * LogiAccounting Pro - Mobile App
 * React Native entry point
 */

import React, { useEffect } from 'react';
import { StatusBar, useColorScheme, LogBox } from 'react-native';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import { store, persistor } from '@store/index';
import { lightTheme, darkTheme } from '@app/theme';
import { AppNavigator } from '@navigation/AppNavigator';
import { LoadingSpinner, OfflineBanner } from '@components/common';
import { useAppState, useOffline } from '@hooks/index';
import { syncService } from '@services/index';
import '@i18n/index';

// Ignore specific warnings
LogBox.ignoreLogs([
  'Non-serializable values were found in the navigation state',
]);

// App container with providers
const AppContainer: React.FC = () => {
  const colorScheme = useColorScheme();
  const { isOnline, pendingCount } = useOffline();

  // Handle app state changes for auto-lock
  useAppState({
    onForeground: () => {
      console.log('App came to foreground');
    },
    onBackground: () => {
      console.log('App went to background');
    },
    autoLockEnabled: true,
  });

  // Determine theme
  const theme = colorScheme === 'dark' ? darkTheme : lightTheme;

  return (
    <PaperProvider theme={theme}>
      <SafeAreaProvider>
        <GestureHandlerRootView style={{ flex: 1 }}>
          <StatusBar
            barStyle={colorScheme === 'dark' ? 'light-content' : 'dark-content'}
            backgroundColor={theme.colors.background}
          />
          <OfflineBanner isOffline={!isOnline} pendingActions={pendingCount} />
          <AppNavigator />
        </GestureHandlerRootView>
      </SafeAreaProvider>
    </PaperProvider>
  );
};

// Root app component with Redux provider
const App: React.FC = () => {
  useEffect(() => {
    // Initialize sync service
    syncService.init();

    return () => {
      syncService.cleanup();
    };
  }, []);

  return (
    <Provider store={store}>
      <PersistGate
        loading={<LoadingSpinner fullScreen message="Loading..." />}
        persistor={persistor}
      >
        <AppContainer />
      </PersistGate>
    </Provider>
  );
};

export default App;
