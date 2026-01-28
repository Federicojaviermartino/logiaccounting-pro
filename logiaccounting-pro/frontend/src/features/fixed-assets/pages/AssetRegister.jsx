/**
 * Fixed Asset Register page.
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import {
  Plus, Search, Download, Upload, Filter,
  MoreVertical, Eye, Edit2, Trash2, Package
} from 'lucide-react';
import { assetsAPI, categoriesAPI } from '../services/fixedAssetsAPI';
import toast from '../../../utils/toast';

const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-700',
  active: 'bg-green-100 text-green-700',
  fully_depreciated: 'bg-blue-100 text-blue-700',
  disposed: 'bg-red-100 text-red-700',
};

const STATUS_LABELS = {
  draft: 'Draft',
  active: 'Active',
  fully_depreciated: 'Fully Depreciated',
  disposed: 'Disposed',
};

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount || 0);
};

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString();
};

export default function AssetRegister() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [filters, setFilters] = useState({
    search: '',
    category_id: '',
    status: '',
    fully_depreciated: '',
  });
  const [page, setPage] = useState(0);
  const [showFilters, setShowFilters] = useState(false);

  // Fetch categories for filter
  const { data: categories } = useQuery({
    queryKey: ['assetCategories'],
    queryFn: () => categoriesAPI.getAll().then(res => res.data),
  });

  // Fetch assets
  const { data: assetsData, isLoading } = useQuery({
    queryKey: ['fixedAssets', filters, page],
    queryFn: () => assetsAPI.getAll({
      ...filters,
      skip: page * 50,
      limit: 50,
    }).then(res => res.data),
  });

  // Fetch summary
  const { data: summary } = useQuery({
    queryKey: ['assetsSummary'],
    queryFn: () => assetsAPI.getSummary().then(res => res.data),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => assetsAPI.delete(id),
    onSuccess: () => queryClient.invalidateQueries(['fixedAssets']),
  });

  const handleDelete = (asset) => {
    if (asset.status !== 'draft') {
      toast.success('Only draft assets can be deleted');
      return;
    }
    if (confirm(`Delete asset ${asset.asset_number}?`)) {
      deleteMutation.mutate(asset.id);
    }
  };

  const handleExport = async () => {
    try {
      const response = await assetsAPI.export('xlsx', filters.category_id, filters.status);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `assets_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Fixed Asset Register</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage your company's fixed assets and equipment
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={handleExport} className="btn-secondary flex items-center gap-2">
            <Download size={18} />
            Export
          </button>
          <button
            onClick={() => navigate('/fixed-assets/import')}
            className="btn-secondary flex items-center gap-2"
          >
            <Upload size={18} />
            Import
          </button>
          <button
            onClick={() => navigate('/fixed-assets/new')}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={18} />
            New Asset
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Total Assets</div>
            <div className="text-2xl font-bold text-gray-900">{summary.total_assets}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Total Cost</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(summary.total_cost)}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Book Value</div>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(summary.total_book_value)}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Accumulated Depreciation</div>
            <div className="text-2xl font-bold text-orange-600">
              {formatCurrency(summary.total_depreciation)}
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="p-4 border-b flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search by asset number, name, serial..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="input-field pl-10"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn-secondary flex items-center gap-2 ${showFilters ? 'bg-gray-100' : ''}`}
          >
            <Filter size={18} />
            Filters
          </button>
        </div>

        {showFilters && (
          <div className="p-4 bg-gray-50 grid grid-cols-1 md:grid-cols-4 gap-4">
            <select
              value={filters.category_id}
              onChange={(e) => setFilters({ ...filters, category_id: e.target.value })}
              className="input-field"
            >
              <option value="">All Categories</option>
              {categories?.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="input-field"
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="fully_depreciated">Fully Depreciated</option>
              <option value="disposed">Disposed</option>
            </select>
            <select
              value={filters.fully_depreciated}
              onChange={(e) => setFilters({ ...filters, fully_depreciated: e.target.value })}
              className="input-field"
            >
              <option value="">Depreciation Status</option>
              <option value="false">Still Depreciating</option>
              <option value="true">Fully Depreciated</option>
            </select>
            <button
              onClick={() => setFilters({ search: '', category_id: '', status: '', fully_depreciated: '' })}
              className="btn-secondary"
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>

      {/* Assets Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Asset #</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Category</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Location</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Cost</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Book Value</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-600">Status</th>
              <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-gray-500">Loading...</td>
              </tr>
            ) : assetsData?.items?.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                  <Package size={48} className="mx-auto mb-2 text-gray-300" />
                  No assets found
                </td>
              </tr>
            ) : (
              assetsData?.items?.map(asset => (
                <tr key={asset.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/fixed-assets/${asset.id}`}
                      className="text-blue-600 hover:underline font-medium"
                    >
                      {asset.asset_number}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{asset.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{asset.category_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{asset.location || '-'}</td>
                  <td className="px-4 py-3 text-right font-mono">
                    {formatCurrency(asset.total_cost)}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    {formatCurrency(asset.book_value)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[asset.status]}`}>
                      {STATUS_LABELS[asset.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <Link
                        to={`/fixed-assets/${asset.id}`}
                        className="p-1 hover:bg-gray-200 rounded"
                        title="View"
                      >
                        <Eye size={18} className="text-gray-500" />
                      </Link>
                      <Link
                        to={`/fixed-assets/${asset.id}/edit`}
                        className="p-1 hover:bg-gray-200 rounded"
                        title="Edit"
                      >
                        <Edit2 size={18} className="text-blue-500" />
                      </Link>
                      {asset.status === 'draft' && (
                        <button
                          onClick={() => handleDelete(asset)}
                          className="p-1 hover:bg-gray-200 rounded"
                          title="Delete"
                        >
                          <Trash2 size={18} className="text-red-500" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {assetsData && assetsData.total > 50 && (
          <div className="px-4 py-3 border-t flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing {page * 50 + 1} to {Math.min((page + 1) * 50, assetsData.total)} of {assetsData.total}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="btn-secondary text-sm"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={(page + 1) * 50 >= assetsData.total}
                className="btn-secondary text-sm"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
