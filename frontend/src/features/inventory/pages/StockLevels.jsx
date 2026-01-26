import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Package, AlertTriangle, Download, Filter } from 'lucide-react';
import { inventoryAPI } from '../services/inventoryAPI';

export default function StockLevels() {
  const [filters, setFilters] = useState({
    search: '',
    warehouse_id: '',
    has_stock_only: true,
  });
  const [page, setPage] = useState(1);

  const { data: warehouses } = useQuery({
    queryKey: ['warehouses'],
    queryFn: () => inventoryAPI.getWarehouses(),
  });

  const { data, isLoading } = useQuery({
    queryKey: ['stock-levels', filters, page],
    queryFn: () => inventoryAPI.getStockLevels({ ...filters, page }),
  });

  const { data: lowStock } = useQuery({
    queryKey: ['low-stock', filters.warehouse_id],
    queryFn: () => inventoryAPI.getLowStock(filters.warehouse_id),
  });

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Stock Levels</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Current inventory across all locations
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      {/* Low Stock Alert */}
      {lowStock?.products?.length > 0 && (
        <div className="mb-6 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <div className="flex items-center gap-2 text-amber-800 dark:text-amber-200">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">{lowStock.products.length} products below reorder point</span>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search products..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
          />
        </div>
        <select
          value={filters.warehouse_id}
          onChange={(e) => setFilters({ ...filters, warehouse_id: e.target.value })}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg"
        >
          <option value="">All Warehouses</option>
          {warehouses?.warehouses?.map((wh) => (
            <option key={wh.id} value={wh.id}>{wh.name}</option>
          ))}
        </select>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={filters.has_stock_only}
            onChange={(e) => setFilters({ ...filters, has_stock_only: e.target.checked })}
            className="rounded"
          />
          <span className="text-sm">Has stock only</span>
        </label>
      </div>

      {/* Stock Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Warehouse</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Lot</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">On Hand</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Reserved</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Available</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {data?.stock_levels?.map((stock) => (
              <tr key={stock.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center">
                      <Package className="w-4 h-4 text-gray-400" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{stock.product_sku}</p>
                      <p className="text-sm text-gray-500 truncate max-w-xs">{stock.product_name}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm">{stock.warehouse_code}</td>
                <td className="px-6 py-4 text-sm font-mono">{stock.location_code}</td>
                <td className="px-6 py-4 text-sm">{stock.lot_number || '-'}</td>
                <td className="px-6 py-4 text-sm text-right font-medium">{stock.quantity_on_hand}</td>
                <td className="px-6 py-4 text-sm text-right text-orange-600">{stock.quantity_reserved}</td>
                <td className="px-6 py-4 text-sm text-right font-medium text-green-600">{stock.quantity_available}</td>
                <td className="px-6 py-4 text-sm text-right">${stock.total_value?.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data?.total > 50 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * 50 + 1} to {Math.min(page * 50, data.total)} of {data.total}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * 50 >= data.total}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
