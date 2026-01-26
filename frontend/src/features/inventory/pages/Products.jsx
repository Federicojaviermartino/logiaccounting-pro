import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Package, Grid, List, Edit2, Trash2, BarChart2 } from 'lucide-react';
import { inventoryAPI } from '../services/inventoryAPI';
import ProductForm from '../components/ProductForm';

export default function Products() {
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState('grid');
  const [showForm, setShowForm] = useState(false);
  const [editProduct, setEditProduct] = useState(null);
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['products', { search, page }],
    queryFn: () => inventoryAPI.getProducts({ search, page }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => inventoryAPI.deactivateProduct(id),
    onSuccess: () => queryClient.invalidateQueries(['products']),
  });

  const handleEdit = (product) => {
    setEditProduct(product);
    setShowForm(true);
  };

  const handleClose = () => {
    setShowForm(false);
    setEditProduct(null);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Products</h1>
          <p className="text-gray-600 dark:text-gray-400">
            {data?.total || 0} products
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Add Product
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search products..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
          />
        </div>
        <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded ${viewMode === 'grid' ? 'bg-white dark:bg-gray-700 shadow' : ''}`}
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded ${viewMode === 'list' ? 'bg-white dark:bg-gray-700 shadow' : ''}`}
          >
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Products Grid/List */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {data?.products?.map((product) => (
            <div
              key={product.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                  <Package className="w-6 h-6 text-gray-400" />
                </div>
                <span className={`px-2 py-0.5 text-xs rounded-full ${
                  product.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {product.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <h3 className="font-medium text-gray-900 dark:text-white truncate">
                {product.name}
              </h3>
              <p className="text-sm text-gray-500 mb-2">SKU: {product.sku}</p>
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold text-gray-900 dark:text-white">
                  ${product.list_price?.toFixed(2)}
                </span>
                <div className="flex items-center gap-1">
                  <button onClick={() => handleEdit(product)} className="p-1 hover:bg-gray-100 rounded">
                    <Edit2 className="w-4 h-4 text-gray-400" />
                  </button>
                  <button onClick={() => deleteMutation.mutate(product.id)} className="p-1 hover:bg-gray-100 rounded">
                    <Trash2 className="w-4 h-4 text-gray-400" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {data?.products?.map((product) => (
                <tr key={product.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 text-sm font-mono">{product.sku}</td>
                  <td className="px-6 py-4 text-sm">{product.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{product.category?.name || '-'}</td>
                  <td className="px-6 py-4 text-sm text-right">${product.list_price?.toFixed(2)}</td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      product.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {product.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => handleEdit(product)} className="p-1 hover:bg-gray-100 rounded mr-1">
                      <Edit2 className="w-4 h-4 text-gray-400" />
                    </button>
                    <button onClick={() => deleteMutation.mutate(product.id)} className="p-1 hover:bg-gray-100 rounded">
                      <Trash2 className="w-4 h-4 text-gray-400" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Form Modal */}
      {showForm && (
        <ProductForm
          product={editProduct}
          onClose={handleClose}
          onSuccess={() => {
            handleClose();
            queryClient.invalidateQueries(['products']);
          }}
        />
      )}
    </div>
  );
}
