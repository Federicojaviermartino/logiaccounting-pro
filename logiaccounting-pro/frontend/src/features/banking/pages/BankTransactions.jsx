/**
 * Bank Transactions Page
 * View and manage bank transactions
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { transactionsAPI, bankAccountsAPI } from '../services/bankingAPI';
import {
  ArrowDownLeft, ArrowUpRight, Search, Filter, Upload,
  Tag, Link, Unlink, Calendar, DollarSign
} from 'lucide-react';

const BankTransactions = () => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({
    account_id: '',
    start_date: '',
    end_date: '',
    direction: '',
    match_status: '',
    search: '',
  });
  const [selectedTransactions, setSelectedTransactions] = useState([]);
  const [showImportModal, setShowImportModal] = useState(false);

  // Fetch accounts for filter
  const { data: accountsData } = useQuery({
    queryKey: ['bank-accounts-summary'],
    queryFn: () => bankAccountsAPI.getSummary(),
  });

  // Fetch transactions
  const { data: transactionsData, isLoading } = useQuery({
    queryKey: ['bank-transactions', filters],
    queryFn: () => transactionsAPI.list(Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== '')
    )),
  });

  // Categorize mutation
  const categorizeMutation = useMutation({
    mutationFn: ({ transactionIds, category }) => transactionsAPI.categorize(transactionIds, category),
    onSuccess: () => {
      queryClient.invalidateQueries(['bank-transactions']);
      setSelectedTransactions([]);
    },
  });

  const accounts = accountsData?.data || [];
  const transactions = transactionsData?.data?.items || [];
  const total = transactionsData?.data?.total || 0;

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount || 0);
  };

  const getMatchStatusBadge = (status) => {
    const badges = {
      unmatched: 'bg-yellow-100 text-yellow-800',
      suggested: 'bg-blue-100 text-blue-800',
      matched: 'bg-green-100 text-green-800',
      reconciled: 'bg-purple-100 text-purple-800',
      exception: 'bg-red-100 text-red-800',
    };
    return badges[status] || 'bg-gray-100 text-gray-800';
  };

  const toggleSelectAll = () => {
    if (selectedTransactions.length === transactions.length) {
      setSelectedTransactions([]);
    } else {
      setSelectedTransactions(transactions.map(t => t.id));
    }
  };

  const toggleSelect = (id) => {
    if (selectedTransactions.includes(id)) {
      setSelectedTransactions(selectedTransactions.filter(t => t !== id));
    } else {
      setSelectedTransactions([...selectedTransactions, id]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Bank Transactions</h1>
          <p className="text-gray-600 dark:text-gray-400">View and manage imported transactions</p>
        </div>
        <button
          onClick={() => setShowImportModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Upload size={20} />
          Import Statement
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow mb-6">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          <select
            value={filters.account_id}
            onChange={(e) => setFilters({ ...filters, account_id: e.target.value })}
            className="border rounded-lg px-4 py-2 dark:bg-gray-700 dark:border-gray-600"
          >
            <option value="">All Accounts</option>
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>{acc.account_name}</option>
            ))}
          </select>

          <input
            type="date"
            value={filters.start_date}
            onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
            className="border rounded-lg px-4 py-2 dark:bg-gray-700 dark:border-gray-600"
            placeholder="Start Date"
          />

          <input
            type="date"
            value={filters.end_date}
            onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
            className="border rounded-lg px-4 py-2 dark:bg-gray-700 dark:border-gray-600"
            placeholder="End Date"
          />

          <select
            value={filters.direction}
            onChange={(e) => setFilters({ ...filters, direction: e.target.value })}
            className="border rounded-lg px-4 py-2 dark:bg-gray-700 dark:border-gray-600"
          >
            <option value="">All Directions</option>
            <option value="debit">Debits (Out)</option>
            <option value="credit">Credits (In)</option>
          </select>

          <select
            value={filters.match_status}
            onChange={(e) => setFilters({ ...filters, match_status: e.target.value })}
            className="border rounded-lg px-4 py-2 dark:bg-gray-700 dark:border-gray-600"
          >
            <option value="">All Status</option>
            <option value="unmatched">Unmatched</option>
            <option value="matched">Matched</option>
            <option value="reconciled">Reconciled</option>
          </select>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedTransactions.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <span className="text-blue-800 dark:text-blue-200">
              {selectedTransactions.length} transactions selected
            </span>
            <div className="flex gap-2">
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    categorizeMutation.mutate({
                      transactionIds: selectedTransactions,
                      category: e.target.value
                    });
                    e.target.value = '';
                  }
                }}
                className="border rounded-lg px-3 py-1 text-sm"
              >
                <option value="">Categorize as...</option>
                <option value="payroll">Payroll</option>
                <option value="utilities">Utilities</option>
                <option value="supplies">Supplies</option>
                <option value="rent">Rent</option>
                <option value="sales">Sales</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Transactions Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">Loading transactions...</div>
        ) : transactions.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No transactions found. Import a bank statement to get started.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedTransactions.length === transactions.length}
                    onChange={toggleSelectAll}
                    className="rounded"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Category</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Amount</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {transactions.map((txn) => (
                <tr key={txn.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedTransactions.includes(txn.id)}
                      onChange={() => toggleSelect(txn.id)}
                      className="rounded"
                    />
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {txn.direction === 'credit' ? (
                        <ArrowDownLeft className="text-green-500" size={16} />
                      ) : (
                        <ArrowUpRight className="text-red-500" size={16} />
                      )}
                      <span className="text-gray-900 dark:text-white">
                        {new Date(txn.transaction_date).toLocaleDateString()}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-gray-900 dark:text-white">{txn.payee_payer_name || 'Unknown'}</div>
                    <div className="text-sm text-gray-500 truncate max-w-xs">{txn.description}</div>
                  </td>
                  <td className="px-6 py-4">
                    {txn.category ? (
                      <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-600 rounded capitalize">
                        {txn.category}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className={txn.direction === 'credit' ? 'text-green-600' : 'text-red-600'}>
                      {txn.direction === 'credit' ? '+' : '-'}{formatCurrency(txn.amount, txn.currency)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-2 py-1 text-xs rounded-full ${getMatchStatusBadge(txn.match_status)}`}>
                      {txn.match_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {txn.match_status === 'unmatched' && (
                        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded" title="Match">
                          <Link className="text-gray-500" size={18} />
                        </button>
                      )}
                      {txn.match_status === 'matched' && (
                        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded" title="Unmatch">
                          <Unlink className="text-gray-500" size={18} />
                        </button>
                      )}
                      <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded" title="Categorize">
                        <Tag className="text-gray-500" size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination info */}
      <div className="mt-4 text-sm text-gray-500">
        Showing {transactions.length} of {total} transactions
      </div>
    </div>
  );
};

export default BankTransactions;
