import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Calendar, Download, Printer, CheckCircle, AlertCircle } from 'lucide-react';
import { accountingAPI } from '../services/accountingAPI';

export default function TrialBalance() {
  const [asOfDate, setAsOfDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [includeZeroBalances, setIncludeZeroBalances] = useState(false);
  const [groupByType, setGroupByType] = useState(true);

  const { data, isLoading, error } = useQuery({
    queryKey: ['trialBalance', asOfDate, includeZeroBalances, groupByType],
    queryFn: () =>
      accountingAPI.getTrialBalance({
        asOfDate,
        includeZeroBalances,
        groupByType,
      }),
  });

  const handleExport = (format) => {
    console.log(`Export trial balance as ${format}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
                Trial Balance
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Summary of all account balances
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => handleExport('pdf')}
                className="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <Printer className="w-4 h-4" />
                Print
              </button>
              <button
                onClick={() => handleExport('excel')}
                className="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                As of Date
              </label>
              <input
                type="date"
                value={asOfDate}
                onChange={(e) => setAsOfDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
              />
            </div>

            <label className="flex items-center gap-2 mt-6">
              <input
                type="checkbox"
                checked={includeZeroBalances}
                onChange={(e) => setIncludeZeroBalances(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Include zero balances
              </span>
            </label>

            <label className="flex items-center gap-2 mt-6">
              <input
                type="checkbox"
                checked={groupByType}
                onChange={(e) => setGroupByType(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Group by account type
              </span>
            </label>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-6 text-center">
            <p className="text-red-600 dark:text-red-400">
              Error loading trial balance: {error.message}
            </p>
          </div>
        ) : (
          <>
            <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
              data.is_balanced
                ? 'bg-green-50 dark:bg-green-900/20'
                : 'bg-red-50 dark:bg-red-900/20'
            }`}>
              {data.is_balanced ? (
                <>
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="text-green-800 dark:text-green-400">
                    Trial balance is in balance
                  </span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <span className="text-red-800 dark:text-red-400">
                    Trial balance is out of balance by ${Math.abs(data.difference).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </>
              )}
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                  Trial Balance as of {new Date(data.as_of_date).toLocaleDateString()}
                </h2>
              </div>

              <table className="min-w-full">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Account Code
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Account Name
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Debit
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Credit
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {groupByType ? (
                    data.by_type?.map((group) => (
                      <React.Fragment key={group.type}>
                        <tr className="bg-gray-100 dark:bg-gray-700">
                          <td colSpan={4} className="px-6 py-2 text-sm font-semibold text-gray-900 dark:text-white capitalize">
                            {group.type}
                          </td>
                        </tr>
                        {group.accounts.map((account) => (
                          <tr key={account.account_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                            <td className="px-6 py-3 text-sm font-mono text-gray-900 dark:text-white">
                              {account.account_code}
                            </td>
                            <td className="px-6 py-3 text-sm text-gray-900 dark:text-white">
                              {account.account_name}
                            </td>
                            <td className="px-6 py-3 text-sm text-right font-mono">
                              {account.debit > 0
                                ? `$${account.debit.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                                : ''}
                            </td>
                            <td className="px-6 py-3 text-sm text-right font-mono">
                              {account.credit > 0
                                ? `$${account.credit.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                                : ''}
                            </td>
                          </tr>
                        ))}
                        <tr className="bg-gray-50 dark:bg-gray-800 font-medium">
                          <td colSpan={2} className="px-6 py-2 text-sm text-gray-700 dark:text-gray-300">
                            Subtotal - {group.type}
                          </td>
                          <td className="px-6 py-2 text-sm text-right font-mono">
                            ${group.total_debit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                          <td className="px-6 py-2 text-sm text-right font-mono">
                            ${group.total_credit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      </React.Fragment>
                    ))
                  ) : (
                    data.accounts?.map((account) => (
                      <tr key={account.account_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-3 text-sm font-mono text-gray-900 dark:text-white">
                          {account.account_code}
                        </td>
                        <td className="px-6 py-3 text-sm text-gray-900 dark:text-white">
                          {account.account_name}
                        </td>
                        <td className="px-6 py-3 text-sm text-right font-mono">
                          {account.debit > 0
                            ? `$${account.debit.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                            : ''}
                        </td>
                        <td className="px-6 py-3 text-sm text-right font-mono">
                          {account.credit > 0
                            ? `$${account.credit.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                            : ''}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
                <tfoot className="bg-gray-100 dark:bg-gray-700">
                  <tr className="font-bold">
                    <td colSpan={2} className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                      TOTAL
                    </td>
                    <td className="px-6 py-4 text-sm text-right font-mono text-gray-900 dark:text-white">
                      ${data.total_debit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 text-sm text-right font-mono text-gray-900 dark:text-white">
                      ${data.total_credit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
