import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Search, ChevronRight, ChevronDown, Edit2, Trash2,
  Download, Upload, Filter, MoreVertical
} from 'lucide-react';
import { accountingAPI } from '../services/accountingAPI';
import AccountForm from '../components/AccountForm';
import AccountTree from '../components/AccountTree';

const ACCOUNT_TYPE_COLORS = {
  asset: 'bg-blue-100 text-blue-800',
  liability: 'bg-red-100 text-red-800',
  equity: 'bg-purple-100 text-purple-800',
  revenue: 'bg-green-100 text-green-800',
  expense: 'bg-orange-100 text-orange-800',
};

export default function ChartOfAccounts() {
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState('tree');
  const [showForm, setShowForm] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    accountType: '',
    isActive: true,
  });
  const [showFilters, setShowFilters] = useState(false);

  const { data: accountTree, isLoading: treeLoading } = useQuery({
    queryKey: ['accounts', 'tree'],
    queryFn: () => accountingAPI.getAccountTree(),
  });

  const { data: accountsList, isLoading: listLoading } = useQuery({
    queryKey: ['accounts', 'list', filters],
    queryFn: () => accountingAPI.getAccounts(filters),
    enabled: viewMode === 'list',
  });

  const { data: accountTypes } = useQuery({
    queryKey: ['accountTypes'],
    queryFn: () => accountingAPI.getAccountTypes(),
  });

  const { data: templates } = useQuery({
    queryKey: ['accountTemplates'],
    queryFn: () => accountingAPI.getAccountTemplates(),
  });

  const createMutation = useMutation({
    mutationFn: accountingAPI.createAccount,
    onSuccess: () => {
      queryClient.invalidateQueries(['accounts']);
      setShowForm(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => accountingAPI.updateAccount(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['accounts']);
      setEditingAccount(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: accountingAPI.deactivateAccount,
    onSuccess: () => {
      queryClient.invalidateQueries(['accounts']);
    },
  });

  const importTemplateMutation = useMutation({
    mutationFn: accountingAPI.importTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries(['accounts']);
    },
  });

  const handleCreate = (data) => {
    createMutation.mutate(data);
  };

  const handleUpdate = (data) => {
    updateMutation.mutate({ id: editingAccount.id, data });
  };

  const handleDelete = (accountId) => {
    if (window.confirm('Are you sure you want to deactivate this account?')) {
      deleteMutation.mutate(accountId);
    }
  };

  const handleImportTemplate = (templateName) => {
    if (window.confirm(`Import "${templateName}" template? This will create new accounts.`)) {
      importTemplateMutation.mutate(templateName);
    }
  };

  const isLoading = viewMode === 'tree' ? treeLoading : listLoading;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
                Chart of Accounts
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Manage your account structure and hierarchy
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden">
                <button
                  onClick={() => setViewMode('tree')}
                  className={`px-3 py-1.5 text-sm ${
                    viewMode === 'tree'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  Tree
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1.5 text-sm ${
                    viewMode === 'list'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                  }`}
                >
                  List
                </button>
              </div>

              <div className="relative group">
                <button className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700">
                  <Upload className="w-4 h-4" />
                  Import Template
                </button>
                <div className="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                  {templates?.map((template) => (
                    <button
                      key={template.id}
                      onClick={() => handleImportTemplate(template.id)}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      {template.name}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={() => setShowForm(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                Add Account
              </button>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search accounts..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-3 py-2 border rounded-lg ${
                showFilters ? 'border-blue-500 text-blue-600' : 'border-gray-300 dark:border-gray-600'
              }`}
            >
              <Filter className="w-4 h-4" />
              Filters
            </button>
          </div>

          {showFilters && (
            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg flex items-center gap-4">
              <select
                value={filters.accountType}
                onChange={(e) => setFilters({ ...filters, accountType: e.target.value })}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
              >
                <option value="">All Types</option>
                {accountTypes?.map((type) => (
                  <option key={type.name} value={type.name}>
                    {type.display_name}
                  </option>
                ))}
              </select>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={filters.isActive}
                  onChange={(e) => setFilters({ ...filters, isActive: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">Active only</span>
              </label>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : viewMode === 'tree' ? (
          <AccountTree
            data={accountTree}
            onEdit={setEditingAccount}
            onDelete={handleDelete}
          />
        ) : (
          <AccountList
            accounts={accountsList?.accounts || []}
            onEdit={setEditingAccount}
            onDelete={handleDelete}
          />
        )}
      </div>

      {(showForm || editingAccount) && (
        <AccountForm
          account={editingAccount}
          accountTypes={accountTypes}
          accounts={accountsList?.accounts || []}
          onSubmit={editingAccount ? handleUpdate : handleCreate}
          onClose={() => {
            setShowForm(false);
            setEditingAccount(null);
          }}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      )}
    </div>
  );
}

function AccountList({ accounts, onEdit, onDelete }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-900">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Code
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Name
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Balance
            </th>
            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {accounts.map((account) => (
            <tr key={account.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-white">
                {account.code}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                <span style={{ paddingLeft: `${account.level * 20}px` }}>
                  {account.name}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 py-1 text-xs rounded-full ${ACCOUNT_TYPE_COLORS[account.account_type?.name] || 'bg-gray-100'}`}>
                  {account.account_type?.display_name}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-mono">
                ${account.current_balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-center">
                <span className={`px-2 py-1 text-xs rounded-full ${
                  account.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {account.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right">
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => onEdit(account)}
                    className="p-1 text-gray-400 hover:text-blue-600"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  {!account.is_system && (
                    <button
                      onClick={() => onDelete(account.id)}
                      className="p-1 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
