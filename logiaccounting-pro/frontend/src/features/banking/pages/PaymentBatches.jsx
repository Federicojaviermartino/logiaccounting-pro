/**
 * Payment Batches Page
 * Manage payment batches and processing
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentsAPI, bankAccountsAPI } from '../services/bankingAPI';
import {
  CreditCard, Plus, Send, CheckCircle, XCircle,
  Clock, FileText, Download, Eye, Play
} from 'lucide-react';

const PaymentBatches = () => {
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({ status: '' });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState(null);

  // Fetch batches
  const { data: batchesData, isLoading } = useQuery({
    queryKey: ['payment-batches', filters],
    queryFn: () => paymentsAPI.listBatches(Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== '')
    )),
  });

  // Mutations
  const submitMutation = useMutation({
    mutationFn: (batchId) => paymentsAPI.submitForApproval(batchId),
    onSuccess: () => queryClient.invalidateQueries(['payment-batches']),
  });

  const approveMutation = useMutation({
    mutationFn: (batchId) => paymentsAPI.approveBatch(batchId, true),
    onSuccess: () => queryClient.invalidateQueries(['payment-batches']),
  });

  const processMutation = useMutation({
    mutationFn: (batchId) => paymentsAPI.processBatch(batchId),
    onSuccess: () => queryClient.invalidateQueries(['payment-batches']),
  });

  const batches = batchesData?.data?.items || [];
  const total = batchesData?.data?.total || 0;

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount || 0);
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: { color: 'bg-gray-100 text-gray-800', icon: FileText },
      pending_approval: { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      approved: { color: 'bg-blue-100 text-blue-800', icon: CheckCircle },
      processing: { color: 'bg-purple-100 text-purple-800', icon: Play },
      sent: { color: 'bg-indigo-100 text-indigo-800', icon: Send },
      completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      failed: { color: 'bg-red-100 text-red-800', icon: XCircle },
      cancelled: { color: 'bg-gray-100 text-gray-500', icon: XCircle },
    };
    return badges[status] || { color: 'bg-gray-100 text-gray-800', icon: FileText };
  };

  const getAvailableActions = (batch) => {
    const actions = [];

    if (batch.status === 'draft') {
      actions.push({ label: 'Submit', action: () => submitMutation.mutate(batch.id), icon: Send });
    }
    if (batch.status === 'pending_approval') {
      actions.push({ label: 'Approve', action: () => approveMutation.mutate(batch.id), icon: CheckCircle });
    }
    if (batch.status === 'approved') {
      actions.push({ label: 'Process', action: () => processMutation.mutate(batch.id), icon: Play });
    }

    return actions;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Payment Batches</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage and process payment batches</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={20} />
          Create Batch
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <p className="text-sm text-gray-600 dark:text-gray-400">Draft</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {batches.filter(b => b.status === 'draft').length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <p className="text-sm text-gray-600 dark:text-gray-400">Pending Approval</p>
          <p className="text-2xl font-bold text-yellow-600">
            {batches.filter(b => b.status === 'pending_approval').length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <p className="text-sm text-gray-600 dark:text-gray-400">Processing</p>
          <p className="text-2xl font-bold text-blue-600">
            {batches.filter(b => ['approved', 'processing', 'sent'].includes(b.status)).length}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
          <p className="text-2xl font-bold text-green-600">
            {batches.filter(b => b.status === 'completed').length}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow mb-6">
        <div className="flex gap-4">
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="border rounded-lg px-4 py-2 dark:bg-gray-700 dark:border-gray-600"
          >
            <option value="">All Status</option>
            <option value="draft">Draft</option>
            <option value="pending_approval">Pending Approval</option>
            <option value="approved">Approved</option>
            <option value="processing">Processing</option>
            <option value="sent">Sent</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Batches List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">Loading batches...</div>
        ) : batches.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No payment batches found. Create your first batch to get started.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Batch</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Payment Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Method</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Payments</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Total</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {batches.map((batch) => {
                const statusInfo = getStatusBadge(batch.status);
                const StatusIcon = statusInfo.icon;
                const actions = getAvailableActions(batch);

                return (
                  <tr key={batch.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                          <CreditCard className="text-blue-600 dark:text-blue-400" size={20} />
                        </div>
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{batch.batch_number}</div>
                          <div className="text-sm text-gray-500">{batch.batch_name || 'Untitled'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-900 dark:text-white">
                      {new Date(batch.payment_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-600 rounded uppercase">
                        {batch.payment_method}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right text-gray-900 dark:text-white">
                      {batch.payment_count}
                    </td>
                    <td className="px-6 py-4 text-right font-medium text-gray-900 dark:text-white">
                      {formatCurrency(batch.total_amount, batch.currency)}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full ${statusInfo.color}`}>
                        <StatusIcon size={14} />
                        {batch.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setSelectedBatch(batch)}
                          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded"
                          title="View Details"
                        >
                          <Eye className="text-gray-500" size={18} />
                        </button>
                        {actions.map((action, idx) => (
                          <button
                            key={idx}
                            onClick={action.action}
                            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded"
                            title={action.label}
                          >
                            <action.icon className="text-blue-500" size={18} />
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Total count */}
      <div className="mt-4 text-sm text-gray-500">
        Showing {batches.length} of {total} batches
      </div>
    </div>
  );
};

export default PaymentBatches;
