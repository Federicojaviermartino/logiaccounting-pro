/**
 * Payments Stack Navigator
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useTheme } from 'react-native-paper';

import { PaymentsListScreen } from '@screens/payments/PaymentsListScreen';
import { PaymentDetailScreen } from '@screens/payments/PaymentDetailScreen';
import { RecordPaymentScreen } from '@screens/payments/RecordPaymentScreen';
import { AddPaymentScreen } from '@screens/payments/AddPaymentScreen';
import type { PaymentsStackParamList } from '@types/navigation';

const Stack = createNativeStackNavigator<PaymentsStackParamList>();

export const PaymentsStack: React.FC = () => {
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
        name="PaymentsList"
        component={PaymentsListScreen}
        options={{
          title: 'Payments',
        }}
      />
      <Stack.Screen
        name="PaymentDetail"
        component={PaymentDetailScreen}
        options={{
          title: 'Payment Details',
        }}
      />
      <Stack.Screen
        name="RecordPayment"
        component={RecordPaymentScreen}
        options={{
          title: 'Record Payment',
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="AddPayment"
        component={AddPaymentScreen}
        options={({ route }) => ({
          title: route.params.type === 'receivable' ? 'New Receivable' : 'New Payable',
          presentation: 'modal',
        })}
      />
    </Stack.Navigator>
  );
};

export default PaymentsStack;
