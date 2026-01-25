import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { Search, Calendar, Download, Printer, ChevronDown } from 'lucide-react';
import { accountingAPI } from '../services/accountingAPI';
import AccountPicker from '../components/AccountPicker';
import LedgerTable from '../components/LedgerTable';

export default function GeneralLedger() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [selectedAccount, setSelectedAccount] = useState(
    searchParams.get('accountId') || null
  );
  const [dateRange, setDateRange] = useState({
    startDate: searchParams.get('startDate') || '',
    endDate: searchParams.get('endDate') || '',
  });
  const [includeUnposted, setIncludeUnposted] = useState(false);

  const { data: ledgerData, isLoading, error } = useQuery({
    queryKey: ['accountLedger', selectedAccount, dateRange, includeUnposted],
    queryFn: () =>
      accountingAPI.getAccountLedger(selectedAccount, {
        ...dateRange,
        includeUnposted,
      }),
    enabled: !!selectedAccount,
  });

  const handleAccountSelect = (account) => {
    setSelectedAccount(account?.id || null);
    if (account?.id) {
      searchParams.set('accountId', account.id);
      setSearchParams(searchParams);
    }
  };

  const handleExport = (format) => {
    console.log(`Export as ${format}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
                General Ledger
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                View account transaction history
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => handleExport('pdf')}
                disabled={!ledgerData}
                className="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
              >
                <Printer className="w-4 h-4" />
                Print
              </button>

              <div className="relative group">
                <button
                  disabled={!ledgerData}
                  className="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                >
                  <Download className="w-4 h-4" />
                  Export
                  <ChevronDown className="w-4 h-4" />
                </button>
                <div className="absolute right-0 mt-1 w-32 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                  <button
                    onClick={() => handleExport('excel')}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    Excel (.xlsx)
                  </button>
                  <button
                    onClick={() => handleExport('csv')}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    CSV
                  </button>
                  <button
                    onClick={() => handleExport('pdf')}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    PDF
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[300px]">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Select Account
              </label>
              <AccountPicker
                value={selectedAccount}
                onChange={handleAccountSelect}
                placeholder="Search and select an account..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={dateRange.startDate}
                onChange={(e) =>
                  setDateRange({ ...dateRange, startDate: e.target.value })
                }
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={dateRange.endDate}
                onChange={(e) =>
                  setDateRange({ ...dateRange, endDate: e.target.value })
                }
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
              />
            </div>

            <label className="flex items-center gap-2 pb-2">
              <input
                type="checkbox"
                checked={includeUnposted}
                onChange={(e) => setIncludeUnposted(e.target.checked)}
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Include unposted
              </span>
            </label>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {!selectedAccount ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-12 text-center">
            <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Select an Account
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              Choose an account from the dropdown to view its transaction history
            </p>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-6 text-center">
            <p className="text-red-600 dark:text-red-400">
              Error loading ledger data: {error.message}
            </p>
          </div>
        ) : (
          <>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 mb-6 border border-gray-200 dark:border-gray-700">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {ledgerData.account.code} - {ledgerData.account.name}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                    {ledgerData.account.type} Account
                    {' • '}
                    Normal Balance: {ledgerData.account.normal_balance}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Current Balance
                  </p>
                  <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                    ${ledgerData.closing_balance.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                    })}
                  </p>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-4 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div>
                  <p className="text-sm text-gray-500">Opening Balance</p>
                  <p className="text-lg font-medium">
                    ${ledgerData.opening_balance.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Debits</p>
                  <p className="text-lg font-medium text-green-600">
                    ${ledgerData.total_debit.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Credits</p>
                  <p className="text-lg font-medium text-red-600">
                    ${ledgerData.total_credit.toLocaleString('en-US', {
                      minimumFractionDigits: 2,
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Transactions</p>
                  <p className="text-lg font-medium">{ledgerData.transactions.length}</p>
                </div>
              </div>
            </div>

            <LedgerTable entries={ledgerData.transactions} />
          </>
        )}
      </div>
    </div>
  );
}
