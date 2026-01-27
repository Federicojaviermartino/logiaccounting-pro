/**
 * Inventory Stack Navigator
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from 'react-native-paper';

import { InventoryListScreen } from '@screens/inventory/InventoryListScreen';
import { InventoryDetailScreen } from '@screens/inventory/InventoryDetailScreen';
import { InventoryMovementScreen } from '@screens/inventory/InventoryMovementScreen';
import { BarcodeScannerScreen } from '@screens/inventory/BarcodeScannerScreen';
import { AddMaterialScreen } from '@screens/inventory/AddMaterialScreen';
import type { InventoryStackParamList } from '@types/navigation';

const Stack = createNativeStackNavigator<InventoryStackParamList>();

export const InventoryStack: React.FC = () => {
  const theme = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.colors.surface,
        },
        headerTintColor: theme.colors.onSurface,
        headerTitleStyle: {
          fontWeight: '600',
        },
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen
        name="InventoryList"
        component={InventoryListScreen}
        options={{
          title: 'Inventory',
        }}
      />
      <Stack.Screen
        name="InventoryDetail"
        component={InventoryDetailScreen}
        options={{
          title: 'Material Details',
        }}
      />
      <Stack.Screen
        name="InventoryMovement"
        component={InventoryMovementScreen}
        options={({ route }) => ({
          title: route.params.type === 'entry' ? 'Stock Entry' : 'Stock Exit',
        })}
      />
      <Stack.Screen
        name="BarcodeScanner"
        component={BarcodeScannerScreen}
        options={{
          title: 'Scan Barcode',
          presentation: 'fullScreenModal',
        }}
      />
      <Stack.Screen
        name="AddMaterial"
        component={AddMaterialScreen}
        options={{
          title: 'Add Material',
          presentation: 'modal',
        }}
      />
    </Stack.Navigator>
  );
};

export default InventoryStack;
