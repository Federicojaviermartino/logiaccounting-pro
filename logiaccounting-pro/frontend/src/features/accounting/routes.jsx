import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoadingSpinner from '@/components/LoadingSpinner';

const ChartOfAccounts = lazy(() => import('./pages/ChartOfAccounts'));
const JournalEntries = lazy(() => import('./pages/JournalEntries'));
const GeneralLedger = lazy(() => import('./pages/GeneralLedger'));
const TrialBalance = lazy(() => import('./pages/TrialBalance'));
const FinancialStatements = lazy(() => import('./pages/FinancialStatements'));
const BankReconciliation = lazy(() => import('./pages/BankReconciliation'));

const Wrapper = ({ children }) => (
  <Suspense fallback={<div className="flex justify-center p-12"><LoadingSpinner /></div>}>
    {children}
  </Suspense>
);

export default function AccountingRoutes() {
  return (
    <Routes>
      <Route path="accounts" element={<Wrapper><ChartOfAccounts /></Wrapper>} />
      <Route path="journal" element={<Wrapper><JournalEntries /></Wrapper>} />
      <Route path="ledger" element={<Wrapper><GeneralLedger /></Wrapper>} />
      <Route path="trial-balance" element={<Wrapper><TrialBalance /></Wrapper>} />
      <Route path="statements" element={<Wrapper><FinancialStatements /></Wrapper>} />
      <Route path="reconciliation" element={<Wrapper><BankReconciliation /></Wrapper>} />
      <Route path="" element={<Navigate to="accounts" replace />} />
    </Routes>
  );
}

export const ACCOUNTING_PATHS = {
  ROOT: '/accounting',
  ACCOUNTS: '/accounting/accounts',
  JOURNAL: '/accounting/journal',
  LEDGER: '/accounting/ledger',
  TRIAL_BALANCE: '/accounting/trial-balance',
  STATEMENTS: '/accounting/statements',
  RECONCILIATION: '/accounting/reconciliation',
};
