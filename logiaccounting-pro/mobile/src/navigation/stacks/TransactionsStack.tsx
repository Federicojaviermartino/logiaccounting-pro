/**
 * Transactions Stack Navigator
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from 'react-native-paper';

import { TransactionsListScreen } from '@screens/transactions/TransactionsListScreen';
import { TransactionDetailScreen } from '@screens/transactions/TransactionDetailScreen';
import { AddTransactionScreen } from '@screens/transactions/AddTransactionScreen';
import { ScanReceiptScreen } from '@screens/transactions/ScanReceiptScreen';
import type { TransactionsStackParamList } from '@types/navigation';

const Stack = createNativeStackNavigator<TransactionsStackParamList>();

export const TransactionsStack: React.FC = () => {
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
        name="TransactionsList"
        component={TransactionsListScreen}
        options={{
          title: 'Transactions',
        }}
      />
      <Stack.Screen
        name="TransactionDetail"
        component={TransactionDetailScreen}
        options={{
          title: 'Transaction Details',
        }}
      />
      <Stack.Screen
        name="AddTransaction"
        component={AddTransactionScreen}
        options={({ route }) => ({
          title: route.params?.type === 'income' ? 'Add Income' :
                 route.params?.type === 'expense' ? 'Add Expense' : 'Add Transaction',
          presentation: 'modal',
        })}
      />
      <Stack.Screen
        name="ScanReceipt"
        component={ScanReceiptScreen}
        options={{
          title: 'Scan Receipt',
          presentation: 'fullScreenModal',
        }}
      />
    </Stack.Navigator>
  );
};

export default TransactionsStack;
