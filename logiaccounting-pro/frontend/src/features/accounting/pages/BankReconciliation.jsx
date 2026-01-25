import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Building2, Upload, CheckCircle, XCircle, Link, Unlink,
  RefreshCw, FileText, AlertCircle
} from 'lucide-react';
import { accountingAPI } from '../services/accountingAPI';

export default function BankReconciliation() {
  const queryClient = useQueryClient();
  const [selectedBankAccount, setSelectedBankAccount] = useState(null);
  const [activeReconciliation, setActiveReconciliation] = useState(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [statementBalance, setStatementBalance] = useState('');

  const { data: bankAccounts } = useQuery({
    queryKey: ['bankAccounts'],
    queryFn: () => accountingAPI.getBankAccounts(),
  });

  const { data: reconSummary, refetch: refetchRecon } = useQuery({
    queryKey: ['reconciliation', activeReconciliation],
    queryFn: () => accountingAPI.getReconciliation(activeReconciliation),
    enabled: !!activeReconciliation,
  });

  const startReconMutation = useMutation({
    mutationFn: (data) => accountingAPI.startReconciliation(data),
    onSuccess: (data) => {
      setActiveReconciliation(data.id);
      refetchRecon();
    },
  });

  const autoMatchMutation = useMutation({
    mutationFn: (reconId) => accountingAPI.autoMatchTransactions(reconId),
    onSuccess: () => refetchRecon(),
  });

  const manualMatchMutation = useMutation({
    mutationFn: ({ transactionId, lineId }) =>
      accountingAPI.manualMatch(activeReconciliation, transactionId, lineId),
    onSuccess: () => refetchRecon(),
  });

  const completeReconMutation = useMutation({
    mutationFn: (reconId) => accountingAPI.completeReconciliation(reconId),
    onSuccess: () => {
      queryClient.invalidateQueries(['bankAccounts']);
      setActiveReconciliation(null);
    },
  });

  const handleStartReconciliation = () => {
    if (!selectedBankAccount || !statementBalance) return;

    startReconMutation.mutate({
      bankAccountId: selectedBankAccount.id,
      statementBalance: parseFloat(statementBalance),
      reconciliationDate: new Date().toISOString().split('T')[0],
    });
  };

  const handleAutoMatch = () => {
    if (activeReconciliation) {
      autoMatchMutation.mutate(activeReconciliation);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
                Bank Reconciliation
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Match bank transactions with your records
              </p>
            </div>

            {activeReconciliation && (
              <div className="flex items-center gap-3">
                <button
                  onClick={handleAutoMatch}
                  disabled={autoMatchMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 ${autoMatchMutation.isPending ? 'animate-spin' : ''}`} />
                  Auto-Match
                </button>
                <button
                  onClick={() => completeReconMutation.mutate(activeReconciliation)}
                  disabled={reconSummary?.difference !== 0}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <CheckCircle className="w-4 h-4" />
                  Complete
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {!activeReconciliation ? (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-6">
                Start New Reconciliation
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Select Bank Account
                  </label>
                  <select
                    value={selectedBankAccount?.id || ''}
                    onChange={(e) => {
                      const account = bankAccounts?.find((a) => a.id === e.target.value);
                      setSelectedBankAccount(account);
                    }}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  >
                    <option value="">Select an account...</option>
                    {bankAccounts?.map((account) => (
                      <option key={account.id} value={account.id}>
                        {account.bank_name} - {account.account_number}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedBankAccount && (
                  <>
                    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Building2 className="w-8 h-8 text-gray-400" />
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {selectedBankAccount.bank_name}
                          </p>
                          <p className="text-sm text-gray-500">
                            Last reconciled: {selectedBankAccount.last_reconciled_date || 'Never'}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Statement Ending Balance
                      </label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                          $
                        </span>
                        <input
                          type="number"
                          step="0.01"
                          value={statementBalance}
                          onChange={(e) => setStatementBalance(e.target.value)}
                          placeholder="0.00"
                          className="w-full pl-8 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-4 pt-4">
                      <button
                        onClick={handleStartReconciliation}
                        disabled={!statementBalance || startReconMutation.isPending}
                        className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      >
                        Start Reconciliation
                      </button>
                      <button
                        onClick={() => setShowImportModal(true)}
                        className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                      >
                        <Upload className="w-4 h-4" />
                        Import Statement
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-5 gap-4 mb-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500">Statement Balance</p>
                <p className="text-xl font-semibold">
                  ${reconSummary?.statement_balance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500">GL Balance</p>
                <p className="text-xl font-semibold">
                  ${reconSummary?.gl_balance?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500">Outstanding Deposits</p>
                <p className="text-xl font-semibold text-green-600">
                  ${reconSummary?.outstanding_deposits?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500">Outstanding Payments</p>
                <p className="text-xl font-semibold text-red-600">
                  ${reconSummary?.outstanding_payments?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className={`rounded-lg p-4 border-2 ${
                reconSummary?.difference === 0
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-500'
                  : 'bg-red-50 dark:bg-red-900/20 border-red-500'
              }`}>
                <p className="text-sm text-gray-500">Difference</p>
                <p className={`text-xl font-semibold ${
                  reconSummary?.difference === 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ${Math.abs(reconSummary?.difference || 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    Unmatched Bank Transactions ({reconSummary?.unmatched_bank?.length || 0})
                  </h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {reconSummary?.unmatched_bank?.length === 0 ? (
                    <p className="p-4 text-center text-gray-500">No unmatched transactions</p>
                  ) : (
                    <table className="min-w-full">
                      <thead className="bg-gray-50 dark:bg-gray-900 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Date</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Description</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Amount</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {reconSummary?.unmatched_bank?.map((trans) => (
                          <tr key={trans.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
                            <td className="px-4 py-2 text-sm">{trans.date}</td>
                            <td className="px-4 py-2 text-sm truncate max-w-[200px]">{trans.description}</td>
                            <td className={`px-4 py-2 text-sm text-right font-mono ${
                              trans.type === 'credit' ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {trans.type === 'credit' ? '+' : '-'}${trans.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    Unreconciled GL Entries ({reconSummary?.unreconciled_gl?.length || 0})
                  </h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {reconSummary?.unreconciled_gl?.length === 0 ? (
                    <p className="p-4 text-center text-gray-500">No unreconciled entries</p>
                  ) : (
                    <table className="min-w-full">
                      <thead className="bg-gray-50 dark:bg-gray-900 sticky top-0">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Date</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Description</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Debit</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">Credit</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {reconSummary?.unreconciled_gl?.map((entry) => (
                          <tr key={entry.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer">
                            <td className="px-4 py-2 text-sm">{entry.date}</td>
                            <td className="px-4 py-2 text-sm truncate max-w-[200px]">{entry.description}</td>
                            <td className="px-4 py-2 text-sm text-right font-mono text-green-600">
                              {entry.debit > 0 ? `$${entry.debit.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : ''}
                            </td>
                            <td className="px-4 py-2 text-sm text-right font-mono text-red-600">
                              {entry.credit > 0 ? `$${entry.credit.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : ''}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
