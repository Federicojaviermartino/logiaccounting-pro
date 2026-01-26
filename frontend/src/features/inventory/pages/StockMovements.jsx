import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search, Plus, ArrowDownLeft, ArrowUpRight, ArrowLeftRight,
  Settings, CheckCircle, XCircle, Clock
} from 'lucide-react';
import { inventoryAPI } from '../services/inventoryAPI';
import MovementForm from '../components/MovementForm';

const TYPE_ICONS = {
  receipt: ArrowDownLeft,
  issue: ArrowUpRight,
  transfer: ArrowLeftRight,
  adjustment: Settings,
};

const TYPE_COLORS = {
  receipt: 'text-green-600 bg-green-100',
  issue: 'text-red-600 bg-red-100',
  transfer: 'text-blue-600 bg-blue-100',
  adjustment: 'text-purple-600 bg-purple-100',
};

const STATUS_ICONS = {
  draft: Clock,
  done: CheckCircle,
  cancelled: XCircle,
};

export default function StockMovements() {
  const [filters, setFilters] = useState({ search: '', movement_type: '' });
  const [showForm, setShowForm] = useState(null); // 'receipt', 'issue', 'transfer', 'adjustment'
  const [page, setPage] = useState(1);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['movements', filters, page],
    queryFn: () => inventoryAPI.getMovements({ ...filters, page }),
  });

  const getIcon = (type) => {
    const Icon = TYPE_ICONS[type] || Settings;
    return Icon;
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Stock Movements</h1>
          <p className="text-gray-600 dark:text-gray-400">Track inventory transactions</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowForm('receipt')}
            className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <ArrowDownLeft className="w-4 h-4" />
            Receipt
          </button>
          <button
            onClick={() => setShowForm('issue')}
            className="flex items-center gap-2 px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            <ArrowUpRight className="w-4 h-4" />
            Issue
          </button>
          <button
            onClick={() => setShowForm('transfer')}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <ArrowLeftRight className="w-4 h-4" />
            Transfer
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search by number..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>
        <select
          value={filters.movement_type}
          onChange={(e) => setFilters({ ...filters, movement_type: e.target.value })}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="">All Types</option>
          <option value="receipt">Receipt</option>
          <option value="issue">Issue</option>
          <option value="transfer">Transfer</option>
          <option value="adjustment">Adjustment</option>
        </select>
      </div>

      {/* Movements Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Movement</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">From</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">To</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Quantity</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {data?.movements?.map((movement) => {
              const Icon = getIcon(movement.movement_type);
              const StatusIcon = STATUS_ICONS[movement.status] || Clock;
              return (
                <tr key={movement.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4">
                    <span className="font-mono text-sm">{movement.movement_number}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${TYPE_COLORS[movement.movement_type]}`}>
                      <Icon className="w-3 h-3" />
                      {movement.movement_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">{movement.product_sku}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {movement.source_warehouse ? `${movement.source_warehouse}/${movement.source_location}` : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {movement.dest_warehouse ? `${movement.dest_warehouse}/${movement.dest_location}` : '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-right font-medium">{movement.quantity}</td>
                  <td className="px-6 py-4 text-center">
                    <StatusIcon className={`w-5 h-5 mx-auto ${
                      movement.status === 'done' ? 'text-green-600' :
                      movement.status === 'cancelled' ? 'text-red-600' : 'text-yellow-600'
                    }`} />
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(movement.movement_date).toLocaleDateString()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Movement Form Modal */}
      {showForm && (
        <MovementForm
          type={showForm}
          onClose={() => setShowForm(null)}
          onSuccess={() => {
            setShowForm(null);
            refetch();
          }}
        />
      )}
    </div>
  );
}
