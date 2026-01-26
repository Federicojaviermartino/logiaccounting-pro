/**
 * Bank Accounts Page
 * Manage bank accounts with balance tracking
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bankAccountsAPI } from '../services/bankingAPI';
import {
  Building2, Plus, Search, Filter, MoreVertical,
  TrendingUp, TrendingDown, Star, StarOff, Eye, Edit, Archive
} from 'lucide-react';

const BankAccounts = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({ is_active: true });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState(null);

  // Fetch accounts
  const { data: accountsData, isLoading } = useQuery({
    queryKey: ['bank-accounts', { search, ...filters }],
    queryFn: () => bankAccountsAPI.list({ search, ...filters }),
  });

  // Fetch cash position
  const { data: cashPosition } = useQuery({
    queryKey: ['cash-position'],
    queryFn: () => bankAccountsAPI.getCashPosition(),
  });

  // Set primary mutation
  const setPrimaryMutation = useMutation({
    mutationFn: (accountId) => bankAccountsAPI.setPrimary(accountId),
    onSuccess: () => queryClient.invalidateQueries(['bank-accounts']),
  });

  const accounts = accountsData?.data?.items || [];
  const total = accountsData?.data?.total || 0;
  const position = cashPosition?.data;

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount || 0);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Bank Accounts</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage your bank accounts and track balances</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={20} />
          Add Account
        </button>
      </div>

      {/* Cash Position Summary */}
      {position && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Cash Position</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {formatCurrency(position.total_cash, position.base_currency)}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
            <p className="text-sm text-gray-600 dark:text-gray-400">Active Accounts</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {position.accounts?.length || 0}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
            <p className="text-sm text-gray-600 dark:text-gray-400">Currencies</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {Object.keys(position.by_currency || {}).length}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
            <p className="text-sm text-gray-600 dark:text-gray-400">Last Updated</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {new Date(position.snapshot_date).toLocaleDateString()}
            </p>
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow mb-6">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search accounts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
          <select
            value={filters.is_active?.toString() || 'true'}
            onChange={(e) => setFilters({ ...filters, is_active: e.target.value === 'true' })}
            className="border rounded-lg px-4 py-2 dark:bg-gray-700 dark:border-gray-600"
          >
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
      </div>

      {/* Accounts List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">Loading accounts...</div>
        ) : accounts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No bank accounts found. Add your first account to get started.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Account</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Bank</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Balance</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {accounts.map((account) => (
                <tr key={account.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <Building2 className="text-blue-600 dark:text-blue-400" size={20} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 dark:text-white">{account.account_name}</span>
                          {account.is_primary && (
                            <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded-full">Primary</span>
                          )}
                        </div>
                        <span className="text-sm text-gray-500">{account.account_code} • {account.account_number_masked}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-900 dark:text-white">{account.bank_name}</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-600 rounded capitalize">
                      {account.account_type?.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className={`font-medium ${parseFloat(account.current_balance) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(account.current_balance, account.currency)}
                    </div>
                    <div className="text-xs text-gray-500">{account.currency}</div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      account.is_active
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-600 dark:text-gray-300'
                    }`}>
                      {account.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setPrimaryMutation.mutate(account.id)}
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded"
                        title={account.is_primary ? 'Primary Account' : 'Set as Primary'}
                      >
                        {account.is_primary ? (
                          <Star className="text-yellow-500" size={18} />
                        ) : (
                          <StarOff className="text-gray-400" size={18} />
                        )}
                      </button>
                      <button
                        onClick={() => setSelectedAccount(account)}
                        className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded"
                        title="View Details"
                      >
                        <Eye className="text-gray-500" size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Total count */}
      <div className="mt-4 text-sm text-gray-500">
        Showing {accounts.length} of {total} accounts
      </div>
    </div>
  );
};

export default BankAccounts;
