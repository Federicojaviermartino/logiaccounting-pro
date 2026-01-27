/**
 * Banking Feature Routes
 */

import { lazy } from 'react';

const BankAccounts = lazy(() => import('./pages/BankAccounts'));
const BankTransactions = lazy(() => import('./pages/BankTransactions'));
const PaymentBatches = lazy(() => import('./pages/PaymentBatches'));
const CashFlowForecast = lazy(() => import('./pages/CashFlowForecast'));

export const bankingRoutes = [
  {
    path: '/banking/accounts',
    element: <BankAccounts />,
    title: 'Bank Accounts',
  },
  {
    path: '/banking/transactions',
    element: <BankTransactions />,
    title: 'Bank Transactions',
  },
  {
    path: '/banking/payments',
    element: <PaymentBatches />,
    title: 'Payment Batches',
  },
  {
    path: '/banking/cashflow',
    element: <CashFlowForecast />,
    title: 'Cash Flow Forecast',
  },
];

export default bankingRoutes;
