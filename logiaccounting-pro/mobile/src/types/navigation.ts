/**
 * Navigation Type Definitions
 * Type-safe navigation throughout the app
 */

import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { BottomTabScreenProps } from '@react-navigation/bottom-tabs';
import type { CompositeScreenProps, NavigatorScreenParams } from '@react-navigation/native';

// Root Stack (Auth vs Main)
export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
};

// Auth Stack
export type AuthStackParamList = {
  Login: undefined;
  Biometric: undefined;
  Pin: { mode: 'setup' | 'verify' };
  ForgotPassword: undefined;
};

// Main Tab Navigator
export type MainTabParamList = {
  DashboardTab: NavigatorScreenParams<DashboardStackParamList>;
  InventoryTab: NavigatorScreenParams<InventoryStackParamList>;
  TransactionsTab: NavigatorScreenParams<TransactionsStackParamList>;
  PaymentsTab: NavigatorScreenParams<PaymentsStackParamList>;
  MoreTab: NavigatorScreenParams<MoreStackParamList>;
};

// Dashboard Stack
export type DashboardStackParamList = {
  Dashboard: undefined;
  Notifications: undefined;
  QuickActions: undefined;
};

// Inventory Stack
export type InventoryStackParamList = {
  InventoryList: undefined;
  InventoryDetail: { materialId: string };
  InventoryMovement: { materialId: string; type: 'entry' | 'exit' };
  BarcodeScanner: { returnTo: keyof InventoryStackParamList };
  AddMaterial: undefined;
};

// Transactions Stack
export type TransactionsStackParamList = {
  TransactionsList: undefined;
  TransactionDetail: { transactionId: string };
  AddTransaction: { type?: 'income' | 'expense' };
  ScanReceipt: undefined;
};

// Payments Stack
export type PaymentsStackParamList = {
  PaymentsList: undefined;
  PaymentDetail: { paymentId: string };
  RecordPayment: { paymentId: string };
  AddPayment: { type: 'receivable' | 'payable' };
};

// More Stack (Settings, Profile, etc.)
export type MoreStackParamList = {
  MoreMenu: undefined;
  Profile: undefined;
  Settings: undefined;
  SecuritySettings: undefined;
  NotificationSettings: undefined;
  SyncSettings: undefined;
  Projects: undefined;
  ProjectDetail: { projectId: string };
  Reports: undefined;
  ReportDetail: { reportType: string };
  Analytics: undefined;
  Help: undefined;
  About: undefined;
};

// Screen Props Types
export type RootStackScreenProps<T extends keyof RootStackParamList> = NativeStackScreenProps<
  RootStackParamList,
  T
>;

export type AuthStackScreenProps<T extends keyof AuthStackParamList> = CompositeScreenProps<
  NativeStackScreenProps<AuthStackParamList, T>,
  RootStackScreenProps<keyof RootStackParamList>
>;

export type MainTabScreenProps<T extends keyof MainTabParamList> = CompositeScreenProps<
  BottomTabScreenProps<MainTabParamList, T>,
  RootStackScreenProps<keyof RootStackParamList>
>;

export type DashboardStackScreenProps<T extends keyof DashboardStackParamList> = CompositeScreenProps<
  NativeStackScreenProps<DashboardStackParamList, T>,
  MainTabScreenProps<keyof MainTabParamList>
>;

export type InventoryStackScreenProps<T extends keyof InventoryStackParamList> = CompositeScreenProps<
  NativeStackScreenProps<InventoryStackParamList, T>,
  MainTabScreenProps<keyof MainTabParamList>
>;

export type TransactionsStackScreenProps<T extends keyof TransactionsStackParamList> = CompositeScreenProps<
  NativeStackScreenProps<TransactionsStackParamList, T>,
  MainTabScreenProps<keyof MainTabParamList>
>;

export type PaymentsStackScreenProps<T extends keyof PaymentsStackParamList> = CompositeScreenProps<
  NativeStackScreenProps<PaymentsStackParamList, T>,
  MainTabScreenProps<keyof MainTabParamList>
>;

export type MoreStackScreenProps<T extends keyof MoreStackParamList> = CompositeScreenProps<
  NativeStackScreenProps<MoreStackParamList, T>,
  MainTabScreenProps<keyof MainTabParamList>
>;

// Declaration for useNavigation hook
declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
