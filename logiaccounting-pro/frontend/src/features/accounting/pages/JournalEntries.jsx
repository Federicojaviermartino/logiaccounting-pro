import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Plus, Search, Filter, Calendar, FileText, CheckCircle,
  XCircle, Clock, RotateCcw, Eye, Edit2, Trash2, MoreVertical
} from 'lucide-react';
import { accountingAPI } from '../services/accountingAPI';
import JournalEntryForm from '../components/JournalEntryForm';

const STATUS_CONFIG = {
  draft: { color: 'bg-gray-100 text-gray-800', icon: FileText },
  pending: { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  approved: { color: 'bg-blue-100 text-blue-800', icon: CheckCircle },
  posted: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
  reversed: { color: 'bg-purple-100 text-purple-800', icon: RotateCcw },
  voided: { color: 'bg-red-100 text-red-800', icon: XCircle },
};

export default function JournalEntries() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showForm, setShowForm] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [selectedEntries, setSelectedEntries] = useState([]);
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    entryType: '',
    startDate: '',
    endDate: '',
  });
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['journalEntries', filters, page],
    queryFn: () => accountingAPI.getJournalEntries({ ...filters, page }),
  });

  const createMutation = useMutation({
    mutationFn: accountingAPI.createJournalEntry,
    onSuccess: () => {
      queryClient.invalidateQueries(['journalEntries']);
      setShowForm(false);
    },
  });

  const submitMutation = useMutation({
    mutationFn: accountingAPI.submitEntry,
    onSuccess: () => refetch(),
  });

  const approveMutation = useMutation({
    mutationFn: ({ id, approved, notes }) =>
      accountingAPI.approveEntry(id, { approved, notes }),
    onSuccess: () => refetch(),
  });

  const postMutation = useMutation({
    mutationFn: accountingAPI.postEntry,
    onSuccess: () => refetch(),
  });

  const batchPostMutation = useMutation({
    mutationFn: accountingAPI.batchPostEntries,
    onSuccess: () => {
      refetch();
      setSelectedEntries([]);
    },
  });

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedEntries(
        data?.entries
          .filter((e) => e.status === 'approved')
          .map((e) => e.id) || []
      );
    } else {
      setSelectedEntries([]);
    }
  };

  const handleSelectEntry = (entryId, checked) => {
    if (checked) {
      setSelectedEntries([...selectedEntries, entryId]);
    } else {
      setSelectedEntries(selectedEntries.filter((id) => id !== entryId));
    }
  };

  const handleBatchPost = () => {
    if (selectedEntries.length > 0) {
      batchPostMutation.mutate(selectedEntries);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
                Journal Entries
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Create and manage journal entries
              </p>
            </div>

            <div className="flex items-center gap-3">
              {selectedEntries.length > 0 && (
                <button
                  onClick={handleBatchPost}
                  disabled={batchPostMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <CheckCircle className="w-4 h-4" />
                  Post Selected ({selectedEntries.length})
                </button>
              )}

              <button
                onClick={() => setShowForm(true)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                New Entry
              </button>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[200px] relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search entries..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
              />
            </div>

            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
            >
              <option value="">All Status</option>
              <option value="draft">Draft</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="posted">Posted</option>
            </select>

            <select
              value={filters.entryType}
              onChange={(e) => setFilters({ ...filters, entryType: e.target.value })}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
            >
              <option value="">All Types</option>
              <option value="standard">Standard</option>
              <option value="invoice">Invoice</option>
              <option value="bill">Bill</option>
              <option value="payment">Payment</option>
              <option value="adjustment">Adjustment</option>
            </select>

            <div className="flex items-center gap-2">
              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
              />
              <span className="text-gray-500">to</span>
              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500">Total Entries</p>
            <p className="text-2xl font-semibold">{data?.total || 0}</p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500">Total Debits</p>
            <p className="text-2xl font-semibold text-green-600">
              ${data?.total_debit?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500">Total Credits</p>
            <p className="text-2xl font-semibold text-red-600">
              ${data?.total_credit?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500">Pending Approval</p>
            <p className="text-2xl font-semibold text-yellow-600">
              {data?.entries?.filter((e) => e.status === 'pending').length || 0}
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 w-10">
                  <input
                    type="checkbox"
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Entry #
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Description
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Debit
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Credit
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  </td>
                </tr>
              ) : data?.entries?.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                    No journal entries found
                  </td>
                </tr>
              ) : (
                data?.entries?.map((entry) => {
                  const StatusIcon = STATUS_CONFIG[entry.status]?.icon || FileText;
                  return (
                    <tr key={entry.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-4 py-3">
                        {entry.status === 'approved' && (
                          <input
                            type="checkbox"
                            checked={selectedEntries.includes(entry.id)}
                            onChange={(e) => handleSelectEntry(entry.id, e.target.checked)}
                            className="rounded border-gray-300"
                          />
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm font-mono text-blue-600">
                        <button onClick={() => navigate(`/accounting/journal/${entry.id}`)}>
                          {entry.entry_number}
                        </button>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">
                        {new Date(entry.entry_date).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-sm capitalize text-gray-600 dark:text-gray-400">
                        {entry.entry_type}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900 dark:text-white max-w-xs truncate">
                        {entry.description}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-mono">
                        ${entry.total_debit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-mono">
                        ${entry.total_credit.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full ${STATUS_CONFIG[entry.status]?.color}`}>
                          <StatusIcon className="w-3 h-3" />
                          {entry.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <EntryActions
                          entry={entry}
                          onSubmit={() => submitMutation.mutate(entry.id)}
                          onApprove={() => approveMutation.mutate({ id: entry.id, approved: true })}
                          onReject={() => approveMutation.mutate({ id: entry.id, approved: false, notes: 'Rejected' })}
                          onPost={() => postMutation.mutate(entry.id)}
                          onEdit={() => setEditingEntry(entry)}
                          onView={() => navigate(`/accounting/journal/${entry.id}`)}
                        />
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>

          {data?.total > 50 && (
            <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Showing {((page - 1) * 50) + 1} to {Math.min(page * 50, data.total)} of {data.total}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page * 50 >= data.total}
                  className="px-3 py-1 border rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {(showForm || editingEntry) && (
        <JournalEntryForm
          entry={editingEntry}
          onSubmit={(data) => createMutation.mutate(data)}
          onClose={() => {
            setShowForm(false);
            setEditingEntry(null);
          }}
          isLoading={createMutation.isPending}
        />
      )}
    </div>
  );
}

function EntryActions({ entry, onSubmit, onApprove, onReject, onPost, onEdit, onView }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="p-1 text-gray-400 hover:text-gray-600"
      >
        <MoreVertical className="w-5 h-5" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-1 w-40 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10">
            <button
              onClick={() => { onView(); setOpen(false); }}
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
            >
              <Eye className="w-4 h-4" /> View
            </button>

            {entry.status === 'draft' && (
              <>
                <button
                  onClick={() => { onEdit(); setOpen(false); }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                >
                  <Edit2 className="w-4 h-4" /> Edit
                </button>
                <button
                  onClick={() => { onSubmit(); setOpen(false); }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-blue-600"
                >
                  <Clock className="w-4 h-4" /> Submit
                </button>
              </>
            )}

            {entry.status === 'pending' && (
              <>
                <button
                  onClick={() => { onApprove(); setOpen(false); }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-green-600"
                >
                  <CheckCircle className="w-4 h-4" /> Approve
                </button>
                <button
                  onClick={() => { onReject(); setOpen(false); }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-red-600"
                >
                  <XCircle className="w-4 h-4" /> Reject
                </button>
              </>
            )}

            {entry.status === 'approved' && (
              <button
                onClick={() => { onPost(); setOpen(false); }}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-green-600"
              >
                <CheckCircle className="w-4 h-4" /> Post
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
